from pynwb import NWBFile, NWBHDF5IO
from pynwb.device import Device

import numpy as np


def add_behavior_labview(nwbfile, source_dir, metadata):
    """
    Reads behavioral data from CSV files and adds it to nwbfile.
    """

    # Adds Device
    device = nwbfile.create_device(name=metadata['Behavior']['Device'][0]['name'])

    return nwbfile
