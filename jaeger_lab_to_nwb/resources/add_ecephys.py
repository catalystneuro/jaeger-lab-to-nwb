from pynwb.ecephys import ElectricalSeries
from hdmf.data_utils import DataChunkIterator
from jaeger_lab_to_nwb.resources.load_intan import load_intan, read_header
import numpy as np
import os


def add_ecephys_rhd(nwbfile, metadata, source_dir, electrodes_file=None):
    """
    Reads extracellular electrophysiology data from .rhd files and adds data to nwbfile.
    """

    def data_gen(source_dir):
        all_files = [os.path.join(source_dir, file) for file in os.listdir(source_dir) if file.endswith(".rhd")]
        # Iterates over all files within the directory
        for fname in all_files:
            file_data = load_intan.read_data(filename=fname)
            # Gets only valid timestamps
            valid_ts = file_data['board_dig_in_data'][0]
            analog_data = file_data['amplifier_data'][:, valid_ts].T
            yield analog_data

    # Gets header data from first file
    all_files = [os.path.join(source_dir, file) for file in os.listdir(source_dir) if file.endswith(".rhd")]
    fid = open(all_files[0], 'rb')
    header = read_header.read_header(fid)
    sampling_rate = header['sample_rate']
    n_electrodes = header['num_amplifier_channels']

    # Adds Device
    device = nwbfile.create_device(name=metadata['Ecephys']['Device'][0]['name'])

    # Electrodes
    electrode_group = nwbfile.create_electrode_group(
        name=metadata['Ecephys']['ElectrodeGroup'][0]['name'],
        description=metadata['Ecephys']['ElectrodeGroup'][0]['description'],
        location=metadata['Ecephys']['ElectrodeGroup'][0]['location'],
        device=device
    )
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
        description=''
    )

    # Create iterator
    data_iter = DataChunkIterator(
        data=data_gen(source_dir=source_dir),
        iter_axis=0,
        buffer_size=10000,
        maxshape=(None, n_electrodes)
    )

    # Electrical Series
    ephys_ts = ElectricalSeries(
        name=metadata['Ecephys']['ElectricalSeries'][0]['name'],
        description=metadata['Ecephys']['ElectricalSeries'][0]['description'],
        data=data_iter,
        electrodes=electrode_table_region,
        rate=sampling_rate,
        starting_time=0.0,
        conversion=metadata['Ecephys']['ElectricalSeries'][0]['conversion']
    )
    nwbfile.add_acquisition(ephys_ts)

    return nwbfile
