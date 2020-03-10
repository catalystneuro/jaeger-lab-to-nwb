# Opens the NWB conversion GUI
# authors: Luiz Tauffer and Ben Dichter
# written for Jaeger Lab
# ------------------------------------------------------------------------------
from nwbn_conversion_tools.gui.nwbn_conversion_gui import nwbn_conversion_gui
from ndx_fret.nwbn_gui_forms import GroupFRET, GroupFRETSeries
from pathlib import Path


def main():
    here = Path(__file__).parent
    metafile = here / 'metafile.yml'
    conversion_module = here.parent.parent / 'conversion_module.py'

    # Source paths
    source_paths = dict()
    source_paths['dir_cortical_imaging'] = {'type': 'dir', 'path': ''}

    # Lab-specific kwargs
    kwargs_fields = {
        'add_ophys': True,
    }

    # Extensions modules and classes
    extension_modules = {
        'ndx_fret': ['FRET', 'FRETSeries']
    }

    # Extension-specific gui forms
    extension_forms = {
        'FRET': GroupFRET,
        'FRETSeries': GroupFRETSeries
    }

    nwbn_conversion_gui(
        metafile=metafile,
        conversion_module=conversion_module,
        source_paths=source_paths,
        kwargs_fields=kwargs_fields,
        extension_modules=extension_modules,
        extension_forms=extension_forms
    )


if __name__ == '__main__':
    main()
