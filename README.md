# jaeger-lab-to-nwb
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

```
$ pip install jaeger-lab-to-nwb
```

# Use

**1. Imported and run from a python script:** <br/>
Examples for each experiment can be found [here](https://github.com/catalystneuro/jaeger-lab-to-nwb/tree/master/tutorials)


**2. Graphical User Interface:** <br/>
To use the GUI, just type in the terminal:
```shell
$ nwbgui-jaeger [experiment_name]
```
Current options for experiment names are: `fret`, `labview`, `treadmill` and `bpod`. The NWB-WebGUI should open in your browser. If it does not open automatically (and no error messages were printed in your terminal), just open your browser and navigate to `localhost:5000`.

The GUI eases the task of editing the metadata of the resulting `nwb` file, it is integrated with the conversion module (conversion on-click) and allows for quick visual exploration the data in the end file with [nwb-jupyter-widgets](https://github.com/NeurodataWithoutBorders/nwb-jupyter-widgets).
