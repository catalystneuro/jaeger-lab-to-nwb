# authors: Luiz Tauffer and Ben Dichter
# written for Jaeger Lab
# ------------------------------------------------------------------------------
from pynwb import NWBFile, NWBHDF5IO
from pynwb.file import Subject

from jaeger_lab_to_nwb.resources.add_behavior import add_behavior_bpod

from datetime import datetime
import yaml
import copy
import os


def conversion_function(source_paths, f_nwb, metadata, add_bpod, **kwargs):
    """
    Convert data from Bpod experiment.

    Parameters
    ----------
    source_paths : dict
        Dictionary with paths to source files/directories. e.g.:
        {'file_behavior_bpod': {'type': 'file', 'path': ''}}
    f_nwb : str
        Path to output NWB file, e.g. 'my_file.nwb'.
    metadata : dict
        Metadata dictionary
    **kwargs : key, value pairs
        Extra keyword arguments
    """

    # Source files and directories
    file_behavior_bpod = None
    for k, v in source_paths.items():
        if v['path'] != '':
            if k == 'file_behavior_bpod':
                file_behavior_bpod = v['path']

    # Get initial metadata
    meta_init = copy.deepcopy(metadata['NWBFile'])

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

    # Adding bpod behavioral data
    if add_bpod:
        nwbfile = add_behavior_bpod(
            nwbfile=nwbfile,
            metadata=metadata,
            source_file=file_behavior_bpod,
        )

    # Saves to NWB file
    with NWBHDF5IO(f_nwb, mode='w') as io:
        io.write(nwbfile)
    print('NWB file saved with size: ', os.stat(f_nwb).st_size / 1e6, ' mb')


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
