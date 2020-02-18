# authors: Luiz Tauffer and Ben Dichter
# written for Jaeger Lab
# ------------------------------------------------------------------------------
from pynwb import NWBFile, NWBHDF5IO
from pynwb.file import Subject

from jaeger_lab_to_nwb.resources.add_ophys import add_ophys_rsd, read_trial_meta
from jaeger_lab_to_nwb.resources.add_behavior import add_behavior_labview

from datetime import datetime
import yaml
import copy
import os


def conversion_function(source_paths, f_nwb, metadata, add_ophys,
                        add_behavior, **kwargs):
    """
    Conversion function for Miao experiments.

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

    # Add subject metadata
    experiment_subject = Subject(
        age=metadata['Subject']['age'],
        subject_id=metadata['Subject']['subject_id'],
        species=metadata['Subject']['species'],
        description=metadata['Subject']['description'],
        genotype=metadata['Subject']['genotype'],
        date_of_birth=metadata['Subject']['date_of_birth'],
        weight=metadata['Subject']['weight'],
        sex=metadata['Subject']['sex']
    )
    nwbfile.subject = experiment_subject

    # Adding raw imaging data
    if add_ophys:
        nwbfile = add_ophys_rsd(
            nwbfile=nwbfile,
            metadata=metadata,
            source_dir=dir_cortical_imaging,
            trials=all_trials
        )

    # Adding behavior
    # The current behavior data files do nt correspond to Miao experiments
    add_behavior = False
    if add_behavior:
        nwbfile = add_behavior_labview(
            nwbfile=nwbfile,
            metadata=metadata,
            source_dir=dir_behavior_labview
        )
    # ----------------------------------------------------------------------

    # Saves to NWB file
    with NWBHDF5IO(f_nwb, mode='w') as io:
        io.write(nwbfile)
    print('NWB file saved with size: ', os.stat(f_nwb).st_size / 1e6, ' mb')


# If called directly fom terminal
if __name__ == '__main__':
    """
    Usage: python conversion_module.py [output_file] [metafile] [dir_cortical_imaging]
    [dir_behavior_labview] [-add_ecephys] [-add_behavior]
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "output_file", help="Output file to be created."
    )
    parser.add_argument(
        "metafile", help="The path to the metadata YAML file."
    )
    parser.add_argument(
        "dir_cortical_imaging", help="The path to the directory containing rsd files."
    )
    parser.add_argument(
        "dir_behavior_labview", help="The path to the directory containing labview behavior data files."
    )
    parser.add_argument(
        "--add_ophys",
        action="store_true",
        default=False,
        help="Whether to add the ophys data to the NWB file or not",
    )
    parser.add_argument(
        "--add_behavior",
        action="store_true",
        default=False,
        help="Whether to add the behavior data to the NWB file or not",
    )

    if not sys.argv[1:]:
        args = parser.parse_args(["--help"])
    else:
        args = parser.parse_args()

    source_paths = {
        'dir_cortical_imaging': {'type': 'dir', 'path': args.dir_cortical_imaging},
        'dir_behavior_labview': {'type': 'dir', 'path': args.dir_behavior_labview},
    }

    f_nwb = args.output_file

    # Load metadata from YAML file
    metafile = args.metafile
    with open(metafile) as f:
        metadata = yaml.safe_load(f)

    # Lab-specific kwargs
    kwargs_fields = {
        'add_ophys': args.add_ecephys,
        'add_behavior': args.add_behavior
    }

    conversion_function(source_paths=source_paths,
                        f_nwb=f_nwb,
                        metadata=metadata,
                        **kwargs_fields)
