# Opens the NWB conversion GUI
# authors: Luiz Tauffer and Ben Dichter
# written for Jaeger Lab
# ------------------------------------------------------------------------------
import sys
import importlib


def main():
    """
    Command line use:
    $ nwbn-gui-jaeger [experiment]

    experiment : str (e.g.: miao, lisu)
        experiment is optional, it should hold the name of the subdirectory in
        the repo holding experiment-specific metafile.yml, conversion_module.py
        and nwbn_gui.py
    """
    if len(sys.argv) > 1:
        experiment = sys.argv[1]

        # Tests if module exists
        module_spec = importlib.util.find_spec("jaeger_lab_to_nwb." + experiment)
        if module_spec is not None:
            print("Importing experiment configuration from " + experiment)
            # Generating the submodule name from string
            full_module_name = "jaeger_lab_to_nwb." + experiment + ".nwbn_gui"

            # Import gui submodule
            gui = importlib.import_module(full_module_name)

            # Run GUI
            print("Running nwbn-gui for experiment: ", experiment)
            gui.main()
        else:
            print("Module" + experiment + " does not exist. Running nwbn-gui without specific metadata.")
            from nwbn_conversion_tools.gui import command_line as gui
            gui.main()
    else:
        print("Running nwbn-gui without specific metadata.")
        from nwbn_conversion_tools.gui import command_line as gui
        gui.main()
