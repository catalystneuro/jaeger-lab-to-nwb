# authors: Luiz Tauffer and Ben Dichter
# written for Jaeger Lab
# ------------------------------------------------------------------------------
from pynwb import NWBFile, NWBHDF5IO

from jaeger_lab_to_nwb.add_ophys import add_ophys_rsd, read_trial_meta
from jaeger_lab_to_nwb.add_behavior import add_behavior_labview

from datetime import datetime
import yaml
import copy
import os


def conversion_function(source_paths, f_nwb, metadata, add_raw,
                        add_behavior, **kwargs):
    """
    Copy data stored in a set of .npz files to a single NWB file.

    Parameters
    ----------
    source_paths : dict
        Dictionary with paths to source files/directories. e.g.:
        {'dir_cortical_imaging': {'type': 'dir', 'path': ''},
         'dir_behavior_labview': {'type': 'dir', 'path': ''}}
    f_nwb : str
        Path to output NWB file, e.g. 'my_file.nwb'.
    metadata : dict
        Metadata dictionary
    **kwargs : key, value pairs
        Extra keyword arguments
    """

    # Source files and directories
    dir_cortical_imaging = None
    dir_behavior_labview = None
    for k, v in source_paths.items():
        if v['path'] != '':
            if k == 'dir_cortical_imaging':
                dir_cortical_imaging = v['path']
            if k == 'dir_behavior_labview':
                dir_behavior_labview = v['path']

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

    # Adding raw imaging data
    if add_raw:
        nwbfile = add_ophys_rsd(
            nwbfile=nwbfile,
            source_dir=dir_cortical_imaging,
            metadata=metadata,
            trials=all_trials
        )

    # Adding behavior
    if add_behavior:
        nwbfile = add_behavior_labview(
            nwbfile=nwbfile,
            source_dir=dir_behavior_labview,
            metadata=metadata
        )

    # Saves to NWB file
    with NWBHDF5IO(f_nwb, mode='w') as io:
        io.write(nwbfile)
    print('NWB file saved with size: ', os.stat(f_nwb).st_size/1e6, ' mb')


# If called directly fom terminal
if __name__ == '__main__':
    import sys

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
