from nwb_web_gui import init_app
from pathlib import Path
import os


def parse_arguments():
    """
    Command line shortcut to open GUI editor.
    Usage:
    $ nwbgui-jaeger [experiment] [--data_path] [--port]

    experiment : str
        The name of the specfic experiment.
        Options: 'bpod' | 'fret' | 'labview' | 'treadmill'
    data_path : str
        Optional. Base path to experimental data.
    port : int
        Optional. Port where app will be running.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='NWB converter GUI, with automatic metadata fetching.',
    )

    parser.add_argument(
        "experiment",
        help="The name of the specfic experiment. Options: 'bpod' | 'fret' | 'labview' | 'treadmill'"
    )
    parser.add_argument(
        "--data_path",
        default='.',
        help="Path to datasets. Defaults to current working directory."
    )
    parser.add_argument(
        "--port",
        default='5000',
        help="Port where app will be running. Defaults to 5000."
    )
    parser.add_argument(
        "--dev",
        default=False,
        help="Run in development mode. Defaults to False."
    )

    # Parse arguments
    args = parser.parse_args()

    return args


def cmd_line_shortcut():
    run_args = parse_arguments()

    # Set ENV variables for app
    data_path = str(Path(run_args.data_path))
    os.environ['DATA_PATH'] = data_path
    os.environ['FLASK_ENV'] = 'production'
    os.environ['RENDER_CONVERTER'] = 'True'
    os.environ['RENDER_VIEWER'] = 'True'
    os.environ['RENDER_DASHBOARD'] = 'False'

    # Choose converter
    os.environ['NWB_CONVERTER_MODULE'] = 'jaeger_lab_to_nwb'
    if run_args.experiment == 'bpod':
        os.environ['NWB_CONVERTER_CLASS'] = 'JaegerBpodConverter'
    elif run_args.experiment == 'fret':
        os.environ['NWB_CONVERTER_CLASS'] = 'JaegerFRETConverter'
    elif run_args.experiment == 'labview':
        # os.environ['NWB_CONVERTER_CLASS'] = 'JaegerLabviewConverter'
        raise NotImplementedError('TODO')
    elif run_args.experiment == 'treadmill':
        os.environ['NWB_CONVERTER_CLASS'] = 'JaegerTreadmillConverter'

    print(f'NWB GUI running on localhost:{run_args.port}')
    print(f'Data path: {data_path}')
    if run_args.dev:
        os.environ['FLASK_ENV'] = 'development'
        print('Running in development mode')

    app = init_app()
    app.run(
        host='0.0.0.0',
        port=run_args.port,
        debug=run_args.dev,
        use_reloader=run_args.dev
    )
