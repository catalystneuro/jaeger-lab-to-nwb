# authors: Luiz Tauffer and Ben Dichter
# written for Jaeger Lab
# ------------------------------------------------------------------------------
from pynwb import NWBHDF5IO
from jaeger_lab_to_nwb.resources.add_behavior import (add_behavior_bpod, add_behavior_treadmill,
                                                      add_behavior_labview)
from jaeger_lab_to_nwb.resources.add_ecephys import add_ecephys_rhd
from jaeger_lab_to_nwb.resources.add_ophys import add_ophys_rsd
from nwb_conversion_tools import NWBConverter
import yaml
import os


class JaegerNWBConverter(NWBConverter):

    def add_bpod(self):
        pass

    def add_treadmill(self):
        pass

    def add_rhd(self):
        pass

    def add_labview(self):
        pass

    def add_ophys(self):
        pass


def conversion_function(source_paths, f_nwb, metadata, add_bpod=False, add_treadmill=False,
                        add_rhd=False, add_labview=False, add_ophys=False, **kwargs):
    """
    Convert data from a diversity of experiment types to nwb.

    Parameters
    ----------
    source_paths : dict
        Dictionary with paths to source files/directories. e.g.:
        {
        'file_behavior_bpod': {'type': 'file', 'path': ''},
        'dir_behavior_treadmill': {'type': 'dir', 'path': ''},
        'dir_ecepys_rhd': {'type': 'dir', 'path': ''},
        'file_electrodes': {'type': 'file', 'path': ''},
        'dir_behavior_labview': {'type': 'dir', 'path': ''},
        'dir_cortical_imaging': {'type': 'dir', 'path': ''}
        }
    f_nwb : str
        Path to output NWB file, e.g. 'my_file.nwb'.
    metadata : dict
        Metadata dictionary
    **kwargs : key, value pairs
        Extra keyword arguments
    """

    # Source files and directories
    file_behavior_bpod = None
    dir_behavior_treadmill = None
    dir_ecephys_rhd = None
    file_electrodes = None
    dir_cortical_imaging = None
    dir_behavior_labview = None
    for k, v in source_paths.items():
        if v['path'] != '':
            if k == 'file_behavior_bpod':
                file_behavior_bpod = v['path']
            if k == 'dir_behavior_treadmill':
                dir_behavior_treadmill = v['path']
            if k == 'dir_ecephys_rhd':
                dir_ecephys_rhd = v['path']
            if k == 'file_electrodes':
                file_electrodes = v['path']
            if k == 'dir_cortical_imaging':
                dir_cortical_imaging = v['path']
            if k == 'dir_behavior_labview':
                dir_behavior_labview = v['path']

    nwbfile = None

    # Adding bpod behavioral data
    if add_bpod:
        nwbfile = add_behavior_bpod(
            nwbfile=nwbfile,
            metadata=metadata,
            file_behavior_bpod=file_behavior_bpod,
        )

    # Adding ecephys
    if add_rhd:
        nwbfile = add_ecephys_rhd(
            nwbfile=nwbfile,
            metadata=metadata,
            source_dir=dir_ecephys_rhd,
            electrodes_file=file_electrodes,
        )

    # Adding treadmill behavior
    if add_treadmill:
        nwbfile = add_behavior_treadmill(
            nwbfile=nwbfile,
            metadata=metadata,
            dir_behavior_treadmill=dir_behavior_treadmill,
        )

    # Adding LabView behavioral data
    if add_labview:
        nwbfile = add_behavior_labview(
            nwbfile=nwbfile,
            metadata=metadata,
            dir_behavior_labview=dir_behavior_labview
        )

    # Adding optophys imaging data
    if add_ophys:
        nwbfile = add_ophys_rsd(
            nwbfile=nwbfile,
            metadata=metadata,
            dir_cortical_imaging=dir_cortical_imaging
        )

    # Saves to NWB file
    with NWBHDF5IO(f_nwb, mode='w') as io:
        io.write(nwbfile)
    print('NWB file saved with size: ', os.stat(f_nwb).st_size / 1e6, ' mb')


def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description='convert .mat file to NWB',
    )

    # Positional arguments
    parser.add_argument(
        "output_file",
        help="Output file to be created."
    )
    parser.add_argument(
        "metafile",
        help="The path to the metadata YAML file."
    )

    # Source dir/file arguments
    parser.add_argument(
        "--file_behavior_bpod",
        default=None,
        help="The path to the directory containing rhd files."
    )
    parser.add_argument(
        "--dir_behavior_treadmill",
        default=None,
        help="The path to the directory containing treadmill behavior data files."
    )
    parser.add_argument(
        "--dir_ecephys_rhd",
        default=None,
        help="The path to the directory containing rhd files."
    )
    parser.add_argument(
        "--file_electrodes",
        default=None,
        help="The path to the electrodes info file."
    )
    parser.add_argument(
        "--dir_behavior_labview",
        default=None,
        help="The path to the directory containing labviewl behavior data files."
    )
    parser.add_argument(
        "--dir_cortical_imaging",
        default=None,
        help="The path to the directory containing cortical imaging (rsd and rsh) data files."
    )

    # Boolean arguments
    parser.add_argument(
        "--add_bpod",
        action="store_true",
        default=False,
        help="Whether to add the Bpod behavior data to the NWB file or not",
    )
    parser.add_argument(
        "--add_rhd",
        action="store_true",
        default=False,
        help="Whether to add the ecephys data to the NWB file or not",
    )
    parser.add_argument(
        "--add_treadmill",
        action="store_true",
        default=False,
        help="Whether to add the treadmill behavior data to the NWB file or not",
    )
    parser.add_argument(
        "--add_labview",
        action="store_true",
        default=False,
        help="Whether to add the treadmill behavior data to the NWB file or not",
    )
    parser.add_argument(
        "--add_ophys",
        action="store_true",
        default=False,
        help="Whether to add the cortical imaging data to the NWB file or not",
    )

    if not sys.argv[1:]:
        args = parser.parse_args(["--help"])
    else:
        args = parser.parse_args()

    # Setting conversion function args and kwargs
    source_paths = {
        'file_behavior_bpod': {'type': 'dir', 'path': args.file_behavior_bpod},
        'dir_behavior_treadmill': {'type': 'dir', 'path': args.dir_behavior_treadmill},
        'dir_ecephys_rhd': {'type': 'dir', 'path': args.dir_ecephys_rhd},
        'file_electrodes': {'type': 'file', 'path': args.file_electrodes},
        'dir_behavior_labview': {'type': 'dir', 'path': args.dir_behavior_labview},
        'dir_cortical_imaging': {'type': 'dir', 'path': args.dir_cortical_imaging},
    }

    f_nwb = args.output_file

    # Load metadata from YAML file
    metafile = args.metafile
    with open(metafile) as f:
        metadata = yaml.safe_load(f)

    # Lab-specific kwargs
    kwargs_fields = {
        'add_bpod': args.add_bpod,
        'add_treadmill': args.add_treadmill,
        'add_rhd': args.add_rhd,
        'add_labview': args.add_labview,
        'add_ophys': args.add_ophys
    }

    conversion_function(
        source_paths=source_paths,
        f_nwb=f_nwb,
        metadata=metadata,
        **kwargs_fields
    )


# If called directly fom terminal
if __name__ == '__main__':
    main()
