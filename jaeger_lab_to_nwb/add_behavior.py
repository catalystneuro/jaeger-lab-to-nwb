from pynwb import NWBFile, NWBHDF5IO
from pynwb.device import Device

import numpy as np
import pandas as pd


def add_behavior_labview(nwbfile, source_dir, metadata):
    """
    Reads behavioral data from txt files and adds it to nwbfile.
    """

    fname = 'GPi4_020619_AP3_4_OPTO_tr.txt'
    fpath = os.path.join(source_dir, fname)
    df_trials_summary = pd.read_csv(fpath, sep='\t', index_col=False)

    # Adds Device
    device = nwbfile.create_device(name=metadata['Behavior']['Device'][0]['name'])

    return nwbfile
