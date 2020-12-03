from jaeger_lab_to_nwb.resources.load_intan import load_intan, read_header
from nwb_conversion_tools.basedatainterface import BaseDataInterface
from nwb_conversion_tools.utils import get_schema_from_hdmf_class
from nwb_conversion_tools.json_schema_utils import get_base_schema

from pynwb import NWBFile
from pynwb.device import Device
from pynwb.ecephys import ElectricalSeries, ElectrodeGroup
from hdmf.data_utils import DataChunkIterator
from pathlib import Path
import pandas as pd
import numpy as np


class IntanDataInterface(BaseDataInterface):
    """Conversion class for intan data."""

    @classmethod
    def get_source_schema(cls):
        """Return a partial JSON schema indicating the input arguments and their types."""
        source_schema = super().get_source_schema()
        source_schema.update(
            required=[],
            properties=dict(
                dir_ecephys_rhd=dict(
                    type="string",
                    format="directory",
                    description="path to directory containing ecephys data in rhd files"
                ),
                file_electrodes=dict(
                    type="string",
                    format="file",
                    description="path to csv file containing electrodes data"
                )
            )
        )
        return source_schema

    def get_metadata_schema(self):
        metadata_schema = super().get_metadata_schema()

        # Ecephys metadata schema
        metadata_schema['properties']['Ecephys'] = get_base_schema()
        metadata_schema['properties']['Ecephys']['properties'] = dict(
            Device=get_schema_from_hdmf_class(Device),
            ElectricalSeries=get_schema_from_hdmf_class(ElectricalSeries),
        )
        return metadata_schema

    def get_metadata(self):
        """Get initial metadata"""
        # Gets header data from first file
        dir_ecephys_rhd = self.source_data['dir_ecephys_rhd']
        all_files = [str(file.resolve()) for file in Path(dir_ecephys_rhd).glob("*.rhd")]
        all_files.sort()
        fid = open(all_files[0], 'rb')
        header = read_header.read_header(fid)
        sampling_rate = header['sample_rate']

        metadata = dict(
            Ecephys=dict(
                Device=dict(
                    name="Device_ecephys"
                ),
                ElectricalSeries=dict(
                    name='ElectricalSeries',
                    description="Raw acquisition traces.",
                    rate=sampling_rate
                )
            )
        )
        return metadata

    def run_conversion(self, nwbfile: NWBFile, metadata: dict):
        """
        Run conversion for this data interface.
        Reads ecephys data from rhd files and adds it to nwbfile.

        Parameters
        ----------
        nwbfile : NWBFile
        metadata : dict
        """
        def data_gen(all_files):
            n_files = len(all_files)
            # Iterates over all files within the directory
            for ii, fname in enumerate(all_files):
                print("Converting ecephys rhd data: {}%".format(100 * ii / n_files))
                file_data = load_intan.read_data(filename=fname)
                # Gets only valid timestamps
                valid_ts = file_data['board_dig_in_data'][0]
                analog_data = file_data['amplifier_data'][:, valid_ts]
                n_samples = analog_data.shape[1]
                for sample in range(n_samples):
                    yield analog_data[:, sample]

        # Adds Device
        device = nwbfile.create_device(name=metadata['Ecephys']['Device']['name'])

        # Electrodes Groups
        meta_electrode_groups = metadata['Ecephys']['ElectrodeGroup']
        for meta in meta_electrode_groups:
            nwbfile.create_electrode_group(
                name=meta['name'],
                description=meta['description'],
                location=meta['location'],
                device=device
            )

        # Gets electrodes info from first rhd file
        dir_ecephys_rhd = self.source_data['dir_ecephys_rhd']
        all_files = [str(file.resolve()) for file in Path(dir_ecephys_rhd).glob("*.rhd")]
        all_files.sort()
        file_data = load_intan.read_data(filename=all_files[0])
        electrodes_info = file_data['amplifier_channels']
        n_electrodes = len(electrodes_info)

        # Electrodes
        file_electrodes = self.source_data.get('file_electrodes', None)
        if file_electrodes is not None:  # if an electrodes info file was provided
            df_electrodes = pd.read_csv(file_electrodes, index_col='Channel Number')
            for idx, elec in enumerate(electrodes_info):
                elec_name = elec['native_channel_name']
                elec_group = df_electrodes.loc[elec_name]['electrode_group']
                elec_imp = df_electrodes.loc[elec_name]['Impedance Magnitude at 1000 Hz (ohms)']
                nwbfile.add_electrode(
                    id=idx,
                    x=np.nan, y=np.nan, z=np.nan,
                    imp=float(elec_imp),
                    location='location',
                    filtering='none',
                    group=nwbfile.electrode_groups[elec_group]
                )
        else:  # if no electrodes file info was provided
            first_el_grp = list(nwbfile.electrode_groups.keys())[0]
            electrode_group = nwbfile.electrode_groups[first_el_grp]
            for idx in range(n_electrodes):
                nwbfile.add_electrode(
                    id=idx,
                    x=np.nan, y=np.nan, z=np.nan,
                    imp=np.nan,
                    location='location',
                    filtering='none',
                    group=electrode_group
                )

        electrode_table_region = nwbfile.create_electrode_table_region(
            region=list(np.arange(n_electrodes)),
            description='no description'
        )

        # Create iterator
        data_iter = DataChunkIterator(
            data=data_gen(all_files=all_files),
            iter_axis=0,
            buffer_size=10000,
            maxshape=(None, n_electrodes)
        )

        # Electrical Series
        # Gets electricalseries conversion factor
        es_conversion_factor = file_data['amplifier_data_conversion_factor']
        ephys_ts = ElectricalSeries(
            name=metadata['Ecephys']['ElectricalSeries']['name'],
            description=metadata['Ecephys']['ElectricalSeries']['description'],
            data=data_iter,
            electrodes=electrode_table_region,
            rate=float(metadata['Ecephys']['ElectricalSeries']['rate']),
            starting_time=0.0,
            conversion=es_conversion_factor
        )
        nwbfile.add_acquisition(ephys_ts)
