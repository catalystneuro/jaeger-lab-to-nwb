from pynwb.ecephys import ElectricalSeries
from jaeger_lab_to_nwb.lisu.load_intan import load_intan
import numpy as np


def add_ecephys_rhd(nwbfile, source_file, metadata):
    """
    Reads extracellular electrophysiology data from .rhd file and adds it to nwbfile.
    """

    file_data = load_intan.read_data(filename=source_file)
    # Gets only valid timestamps
    valid_ts = file_data['board_dig_in_data'][0]
    analog_data = file_data['amplifier_data'][:, valid_ts].T
    n_samples, n_electrodes = analog_data.shape

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

    return nwbfile
