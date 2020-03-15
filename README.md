# jaeger-lab-data-to-nwb
Convert [Jaeger lab](https://scholarblogs.emory.edu/jaegerlab/) data to NWB format.<br>

Currently includes:
* FRET optical imaging (rsd)
* Intan electrophysiology (rhd)
* Labview behavioral data (txt)
* Optogenetics stimulation data (txt)
* Treadmill behavior (csv)
* Bpod behavioral data (mat)

Authors: Luiz Tauffer and Ben Dichter

# Install
To clone the repository and set up a conda environment, do:
```
$ git clone https://github.com/ben-dichter-consulting/jaeger-lab-to-nwb.git
$ conda env create -f jaeger_lab_to_nwb/make_env.yml
$ source activate jaeger_nwb
```

Alternatively, to install directly in an existing environment:
```
$ pip install git+https://github.com/ben-dichter-consulting/jaeger-lab-to-nwb.git
```

# Use
After activating the correct environment, the conversion function can be used in different forms:

**1. Imported and run from a python script:** <br/>
Here's an example: we'll grab the data from a specific experiment, with several electrophysiology and behavioral data files stored `base_path`, and save it to a single `nwb` file.
```python
import pynwb
from jaeger_lab_to_nwb.conversion_module import conversion_function
from pathlib import Path
import yaml

base_path = Path(PATH_TO_FILES)

# Source files
source_paths = dict()
source_paths['dir_ecephys_rhd'] = {'type': 'dir', 'path': base_path}
source_paths['file_electrodes'] = {'type': 'file', 'path': base_path.joinpath('UD09_impedance_1.csv')}
source_paths['dir_behavior_treadmill'] = {'type': 'dir', 'path': base_path}

# Output .nwb file
f_nwb = 'my_experiment.nwb'

# Load metadata from YAML file
metafile = 'metafile.yml'
with open(metafile) as f:
    metadata = yaml.safe_load(f)

# Lab-specific kwargs
kwargs_fields = {
    'add_rhd': True,
    'add_treadmill': True
}

conversion_function(source_paths=source_paths,
                    f_nwb=f_nwb,
                    metadata=metadata,
                    **kwargs_fields)

# Read nwb file and check its content
with pynwb.NWBHDF5IO(f_nwb, 'r') as io:
    nwb = io.read()
    print(nwb)
```
<br/>

**2. Command line:** <br/>
Similarly, the conversion function can be called from the command line in terminal:
```shell
$ python conversion_module.py [output_file] [metafile] [--file_behavior_bpod]
[--dir_behavior_treadmill] [--dir_ecephys_rhd] [--file_electrodes]
[--dir_behavior_labview] [--dir_cortical_imaging] [--add_bpod] [--add_rhd]
[--add_treadmill] [--add_labview] [--add_ophys]
```
<br/>

For example, the same experiment converted above with a python script could be converted with this command line input:
```shell
$ python conversion_module.py my_experiment.nwb metafile.yml --add_rhd --add_treadmill
--dir_behavior_treadmill PATH_TO_FILES --dir_ecepys_rhd PATH_TO_FILES
--file_electrodes PATH_TO_FILES\UD09_impedance_1.csv
```

**3. Graphical User Interface:** <br/>
To use the GUI, just type in the terminal:
```shell
$ nwbn-gui-jaeger [--experiment_name]
```
The GUI eases the task of editing the metadata of the resulting `nwb` file, it is integrated with the conversion module (conversion on-click) and allows for quick visual exploration the data in the end file with [nwb-jupyter-widgets](https://github.com/NeurodataWithoutBorders/nwb-jupyter-widgets).

![](media/gif_jaeger.gif)
