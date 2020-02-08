# Opens the NWB conversion GUI
# authors: Luiz Tauffer and Ben Dichter
# written for Jaeger Lab
# ------------------------------------------------------------------------------
from nwbn_conversion_tools.gui.nwbn_conversion_gui import nwbn_conversion_gui
from ndx_fret import FRET, FRETSeries
from ndx_fret.nwbn_gui_forms import GroupFRET, GroupFRETSeries

metafile = 'metafile.yml'
conversion_module = 'conversion_module.py'

# Source paths
source_paths = dict()
source_paths['dir_cortical_imaging'] = {'type': 'dir', 'path': ''}
source_paths['file_ecephys_rhd'] = {'type': 'file', 'path': ''}
source_paths['dir_behavior_labview'] = {'type': 'dir', 'path': ''}

# Lab-specific kwargs
kwargs_fields = {
    'add_raw': False,
    'add_ecephys': False,
    'add_behavior': True
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
