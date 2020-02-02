# Opens the NWB conversion GUI
# authors: Luiz Tauffer and Ben Dichter
# ------------------------------------------------------------------------------
from nwbn_conversion_tools.gui.nwbn_conversion_gui import nwbn_conversion_gui
from ndx_fret import FRET, FRETSeries
import os

def main():
    here = os.path.dirname(os.path.realpath(__file__))
    metafile = os.path.join(here, 'metafile.yml')
    conversion_module = os.path.join(here, 'conversion_module.py')

    # Source paths
    source_paths = dict()
    source_paths['dir_cortical_imaging'] = {'type': 'dir', 'path': ''}
    source_paths['file_ecephys_rhd'] = {'type': 'file', 'path': ''}
    source_paths['dir_behavior_labview'] = {'type': 'dir', 'path': ''}

    # Lab-specific kwargs
    kwargs_fields = {
        'add_raw':True,
        'add_ecephys':True,
        'add_behavior':True
    }

    nwbn_conversion_gui(
        metafile=metafile,
        conversion_module=conversion_module,
        source_paths=source_paths,
        kwargs_fields=kwargs_fields
    )
