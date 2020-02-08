# authors: Luiz Tauffer and Ben Dichter
# written for Jaeger Lab
# ------------------------------------------------------------------------------
from pynwb import NWBFile, NWBHDF5IO

from jaeger_lab_to_nwb.lisu.add_ecephys import add_ecephys_rhd
from jaeger_lab_to_nwb.lisu.add_behavior import add_behavior_labview

from datetime import datetime
import yaml
import copy
import os


def conversion_function(source_paths, f_nwb, metadata, add_ecephys,
                        add_behavior, **kwargs):
    """
    Copy data stored in a set of .npz files to a single NWB file.

    Parameters
    ----------
    source_paths : dict
        Dictionary with paths to source files/directories. e.g.:
        {'file_ecepys_rhd': {'type': 'file', 'path': ''},
         'dir_behavior_labview': {'type': 'dir', 'path': ''}}
    f_nwb : str
        Path to output NWB file, e.g. 'my_file.nwb'.
    metadata : dict
        Metadata dictionary
    **kwargs : key, value pairs
        Extra keyword arguments
    """

    # Source files and directories
    file_ecephys_rhd = None
    dir_behavior_labview = None
    for k, v in source_paths.items():
        if v['path'] != '':
            if k == 'file_ecephys_rhd':
                file_ecephys_rhd = v['path']
            if k == 'dir_behavior_labview':
                dir_behavior_labview = v['path']

    # Get initial metadata
    meta_init = copy.deepcopy(metadata['NWBFile'])
    #meta_init['session_start_time'] = datetime.strptime(acquisition_date_A, '%Y/%m/%d %H:%M:%S')

    # Initialize a NWB object
    nwbfile = NWBFile(**meta_init)

    # Adding ecephys
    if add_ecephys:
        nwbfile = add_ecephys_rhd(
            nwbfile=nwbfile,
            source_file=file_ecephys_rhd,
            metadata=metadata
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
