# authors: Luiz Tauffer and Ben Dichter
# written for Jaeger Lab
# ------------------------------------------------------------------------------
from pynwb import NWBHDF5IO
from jaeger_lab_to_nwb.resources.add_behavior import add_behavior_bpod
import yaml
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

    nwbfile = None

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


def main():
    """
    Usage: python conversion_module.py [output_file] [metafile] [file_behavior_bpod]
    [-add_behavior]
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
        "file_behavior_bpod", help="The path to the directory containing rhd files."
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
        'file_behavior_bpod': {'type': 'dir', 'path': args.dir_ecephys_rhd},
    }

    f_nwb = args.output_file

    # Load metadata from YAML file
    metafile = args.metafile
    with open(metafile) as f:
        metadata = yaml.safe_load(f)

    # Lab-specific kwargs
    kwargs_fields = {
        'add_behavior': args.add_behavior
    }

    conversion_function(source_paths=source_paths,
                        f_nwb=f_nwb,
                        metadata=metadata,
                        **kwargs_fields)


# If called directly fom terminal
if __name__ == '__main__':
    main()
