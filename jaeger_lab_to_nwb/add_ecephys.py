from pynwb import NWBFile, NWBHDF5IO
from pynwb.device import Device
from pynwb.ecephys import ElectricalSeries

import spikeextractors as se
import os


def add_ecephys_rhd(nwbfile, source_file):
    """
    Reads extracellular electrophysiology data from .rhd file and adds it to nwbfile.
    """

    RX = se.IntanRecordingExtractor(file_path=source_file)
    traces = RX.get_traces()
    traces = traces.T
    n_electrodes, n_samples = traces.shape

    # Adds Device
    device = nwbfile.create_device(name='Device_ecephys')

    # Electrodes
    electrode_group = nwbfile.create_electrode_group(
        name='electrode_group',
        description='',
        location='location',
        device=device
    )
    for idx in range(n_electrodes):
        nwbfile.add_electrode(
            id=idx,
            x=0.0, y=0.0, z=0.0,
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
        name='ElectricalSeries',
        description='',
        data=traces,
        electrodes=electrode_table_region,
        rate=0.0,
        starting_time=0.0,
        conversion=1.0
    )
    nwbfile.add_acquisition(ephys_ts)
