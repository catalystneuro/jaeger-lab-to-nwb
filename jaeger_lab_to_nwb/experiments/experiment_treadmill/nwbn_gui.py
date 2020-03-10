# Opens the NWB conversion GUI
# authors: Luiz Tauffer and Ben Dichter
# written for Jaeger Lab
# ------------------------------------------------------------------------------
from nwbn_conversion_tools.gui.nwbn_conversion_gui import nwbn_conversion_gui
from pathlib import Path


def main():
    here = Path(__file__).parent
    metafile = here / 'metafile.yml'
    conversion_module = here.parent.parent / 'conversion_module.py'

    # Source paths
    source_paths = dict()
    source_paths['dir_ecephys_rhd'] = {'type': 'dir', 'path': ''}
    source_paths['file_electrodes'] = {'type': 'file', 'path': ''}
    source_paths['dir_behavior_treadmill'] = {'type': 'dir', 'path': ''}

    # Lab-specific kwargs
    kwargs_fields = {
        'add_rhd': True,
        'add_treadmill': True
    }

    nwbn_conversion_gui(
        metafile=metafile,
        conversion_module=conversion_module,
        source_paths=source_paths,
        kwargs_fields=kwargs_fields,
    )


if __name__ == '__main__':
    main()
