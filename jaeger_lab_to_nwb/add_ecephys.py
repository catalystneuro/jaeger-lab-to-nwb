from pynwb import NWBFile, NWBHDF5IO
from pynwb.device import Device
from pynwb.ecephys import ElectricalSeries

import spikeextractors as se
import numpy as np


def add_ecephys_rhd(nwbfile, source_file, metadata):
    """
    Reads extracellular electrophysiology data from .rhd file and adds it to nwbfile.
    """

    RX = se.IntanRecordingExtractor(file_path=source_file)
    traces = RX.get_traces()
    traces = traces.T
    n_samples, n_electrodes = traces.shape

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

    # Electrical Series
    ephys_ts = ElectricalSeries(
        name=metadata['Ecephys']['ElectricalSeries'][0]['name'],
        description=metadata['Ecephys']['ElectricalSeries'][0]['description'],
        data=traces,
        electrodes=electrode_table_region,
        rate=metadata['Ecephys']['ElectricalSeries'][0]['rate'],
        starting_time=metadata['Ecephys']['ElectricalSeries'][0]['starting_time'],
        conversion=metadata['Ecephys']['ElectricalSeries'][0]['conversion']
    )
    nwbfile.add_acquisition(ephys_ts)
