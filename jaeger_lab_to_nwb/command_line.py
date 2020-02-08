# Opens the NWB conversion GUI
# authors: Luiz Tauffer and Ben Dichter
# written for Jaeger Lab
# ------------------------------------------------------------------------------
import sys


def main():
    """
    nwbn-gui-jaeger [experiment]

    experiment : miao, lisu
    """
    if len(sys.argv) > 1:
        experiment = sys.argv[1]
        if experiment == 'miao':
            from jaeger_lab_to_nwb.miao import nwbn_gui
        elif experiment == 'lisu':
            from jaeger_lab_to_nwb.lisu import nwbn_gui
        print("Running nwbn-gui for experiment: ", experiment)
        nwbn_gui.main()
    else:
        print("Running nwbn-gui without specific experiment")
