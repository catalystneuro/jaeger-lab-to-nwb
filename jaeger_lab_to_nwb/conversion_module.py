# authors: Luiz Tauffer and Ben Dichter
# written for Jaeger Lab
# ------------------------------------------------------------------------------
from pynwb import NWBFile, NWBHDF5IO

from datetime import datetime
import numpy as np
import yaml
import copy
import struct
import re
import os


def read_trial_meta(trial_meta):
    """Opens trial_meta file and read line by line."""
    files_raw = []
    addftolist = False
    with open(trial_meta, "r") as f:
        line = f.readline()
        while line:
            if 'acquisition_date' in line:
                acquisition_date = line.replace('acquisition_date', '').replace('=', '').strip()
            if 'sample_time' in line:
                aux = line.replace('sample_time', '').replace('=', '').replace('msec', '').strip()
                sample_time = float(aux)/1000.
                sample_rate = 1 / sample_time
            if 'page_frames' in line:
                aux = line.replace('page_frames', '').replace('=', '').strip()
                n_frames = int(aux)
            if addftolist:
                files_raw.append(line.strip())
            if 'Data-File-List' in line:
                addftolist = True   # indicates that next lines are file names to be added
            line = f.readline()

    # Separate .rsm file (bitmap of monitor) from .rsd files (raw data)
    file_rsm = files_raw[0]
    files_raw = files_raw[1:]
    return file_rsm, files_raw, acquisition_date, sample_rate, n_frames


def conversion_function(source_paths, f_nwb, metadata, add_raw=False, **kwargs):
    """
    Copy data stored in a set of .npz files to a single NWB file.

    Parameters
    ----------
    source_paths : dict
        Dictionary with paths to source files/directories. e.g.:
        {'dir_cortical_imaging': {'type': 'dir', 'path': ''},
         'file2': {'type': 'file', 'path': ''}}
    f_nwb : str
        Path to output NWB file, e.g. 'my_file.nwb'.
    metadata : dict
        Metadata dictionary
    **kwargs : key, value pairs
        Extra keyword arguments
    """

    # Source files and directories
    dir_cortical_imaging = None
    for k, v in source_paths.items():
        if source_paths[k]['path'] != '':
            fname = source_paths[k]['path']
            if k == 'dir_cortical_imaging':
                dir_cortical_imaging = v['path']

    # All trials
    # TODO: some trials seem to be consecutive and others are spaced by larger time gaps
    # TODO: also they seem to have different data. We need to get a better description of trials
    # TODO: and handle them properly
    all_trials = ['100', '101', '102']

    # Get initial metadata
    meta_init = copy.deepcopy(metadata['NWBFile'])
    trial_meta_A = os.path.join(dir_cortical_imaging, "VSFP_01A0801-" + str(all_trials[0]) + "_A.rsh")
    trial_meta_B = os.path.join(dir_cortical_imaging, "VSFP_01A0801-" + str(all_trials[0]) + "_B.rsh")
    file_rsm_A, files_raw_A, acquisition_date_A, sample_rate_A, n_frames_A = read_trial_meta(trial_meta=trial_meta_A)
    file_rsm_B, files_raw_B, acquisition_date_B, sample_rate_B, n_frames_B = read_trial_meta(trial_meta=trial_meta_B)
    assert acquisition_date_A == acquisition_date_B, \
        "Initial acquisition date of channels do not match."
    meta_init['session_start_time'] = datetime.strptime(acquisition_date_A, '%Y/%m/%d %H:%M:%S')

    # Initialize a NWB object
    nwbfile = NWBFile(**meta_init)

    # Adding trials
    tr_stop = 0.
    for tr in all_trials:
        trial_meta_A = os.path.join(dir_cortical_imaging, "VSFP_01A0801-" + str(tr) + "_A.rsh")
        trial_meta_B = os.path.join(dir_cortical_imaging, "VSFP_01A0801-" + str(tr) + "_B.rsh")
        file_rsm_A, files_raw_A, acquisition_date_A, sample_rate_A, n_frames_A = read_trial_meta(trial_meta=trial_meta_A)
        file_rsm_B, files_raw_B, acquisition_date_B, sample_rate_B, n_frames_B = read_trial_meta(trial_meta=trial_meta_B)

        # Checks if Acceptor and Donor channels have the same basic parameters
        assert acquisition_date_A == acquisition_date_B, \
            "Acquisition date of channels do not match. Trial=" + str(tr)
        assert sample_rate_A == sample_rate_B, \
            "Sample rate of channels do not match. Trial=" + str(tr)
        assert n_frames_A == n_frames_B, \
            "Number of frames of channels do not match. Trial=" + str(tr)

        tr_start = tr_stop
        tr_stop += n_frames_A / sample_rate_A
        nwbfile.add_trial(start_time=tr_start, stop_time=tr_stop)

    # Adding raw imaging data
    if add_raw:
        add_ophys_rsd(
            nwbfile=nwbfile,
            source_dir=dir_cortical_imaging,
            metadata=metadata
        )

    # Adding ecephys
    if add_ecephys:
        add_ecephys_rhd(
            nwbfile=nwbfile,
            source_file='',
            metadata=metadata
        )

    # Saves to NWB file
    with NWBHDF5IO(f_nwb, mode='w') as io:
        io.write(nwbfile)
    print('NWB file saved with size: ', os.stat(f_nwb).st_size/1e6, ' mb')


# If called directly fom terminal
if __name__ == '__main__':
    import sys
    import yaml

    f1 = sys.argv[1]
    f2 = sys.argv[2]
    source_paths = {
        'file1': {'type': 'file', 'path': f1},
        'file2': {'type': 'file', 'path': f2},
    }
    f_nwb = sys.argv[4]
    metafile = sys.argv[5]

    # Load metadata from YAML file
    metafile = sys.argv[3]
    with open(metafile) as f:
       metadata = yaml.safe_load(f)

    conversion_function(source_paths=source_paths,
                        f_nwb=f_nwb,
                        metadata=metadata)
