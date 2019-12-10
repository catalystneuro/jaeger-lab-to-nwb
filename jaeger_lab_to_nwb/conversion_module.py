# authors: Luiz Tauffer and Ben Dichter
# written for Jaeger Lab
# ------------------------------------------------------------------------------
from pynwb import NWBFile, NWBHDF5IO, ProcessingModule
from pynwb.ophys import OpticalChannel, TwoPhotonSeries
from pynwb.device import Device

import numpy as np
import yaml
import struct
import re
import os

def conversion_function(source_paths, f_nwb, metadata, subject_id, **kwargs):
    """
    Copy data stored in a set of .npz files to a single NWB file.

    Parameters
    ----------
    source_paths : dict
        Dictionary with paths to source files/directories. e.g.:
        {'dir_cortical_imaging': {'type': 'dir', 'path': ''},
         'file2': {'type': 'file', 'path': ''}}
    f_nwb : str
        Path to output NWB file, e.g. 'my_file.nwb'.
    metadata : dict
        Metadata dictionary
    subject_id : int
        Subject ID to convert.
    **kwargs : key, value pairs
        Extra keyword arguments
    """

    # Source files and directories
    dir_cortical_imaging = None
    for k, v in source_paths.items():
        if source_paths[k]['path'] != '':
            fname = source_paths[k]['path']
            if k == 'dir_cortical_imaging':
                dir_cortical_imaging = v['path']

    # Read metadata file: .rsh
    metafile = os.path.join(dir_cortical_imaging, "VSFP_01A0801-" + str(subject_id) + ".rsh")

    # Open metafile and read line by line
    files_raw = []
    addftolist = False
    with open(metafile, "r") as f:
        line = f.readline()
        while line:
            print(line.strip())
            if 'acquisition_date' in line:
                acquisition_date = line.replace('acquisition_date=', '').strip()
            if 'sample_time' in line:
                aux = line.replace('sample_time=', '').replace('msec', '').strip()
                sample_time = float(aux)/1000.
                sample_rate = 1 / sample_time
            if addftolist:
                files_raw.append(line.strip())
            if 'Data-File-List' in line:
                addftolist = True
            line = f.readline()

    # Separate .rsm file (bitmap of monitor) from .rsd files (raw data)
    file_rsm = files_raw[0]
    files_raw = files_raw[1:]

    # Initialize a NWB object
    nwb = NWBFile(**metadata['NWBFile'])

    # Create and add device
    device = Device(name=metadata['Ophys']['Device'][0]['name'])
    nwb.add_device(device)

    # Read .rsd files for subject_id
    for fraw in files_raw:
        fpath = os.path.join(dir_cortical_imaging, fraw)

        # Open file as a byte array
        with open(fpath, "rb") as f:
            byte = f.read(1000000000)
        # Data as word array: 'h' signed, 'H' unsigned
        words = np.array(struct.unpack('h'*(len(byte)//2), byte))

        # Frames (nFrames, 100, 100)
        nFrames = int(len(words)/12800)
        words_reshaped = words.reshape(12800, nFrames, order='F')
        frames = np.zeros((nFrames, 100, 100))
        excess_frames = np.zeros((nFrames, 20, 100))
        for ifr in range(nFrames):
            iframe = words_reshaped[:, ifr].reshape(128, 100, order='F')
            frames[ifr, :, :] = iframe[20:120, :]
            excess_frames[ifr, :, :] = iframe[0:20, :]

        if fn == 0:
            all_frames = frames
            all_excess = excess_frames
        else:
            all_frames = np.concatenate((all_frames, frames), axis=0)
            all_excess = np.concatenate((all_frames, frames), axis=0)

        # Aanalog signals are taken from excess data variable
        analog_1 = np.squeeze(np.squeeze(excess_frames[:, 12, 0:80:4]).reshape(20*256, 1))
        analog_2 = np.squeeze(np.squeeze(excess_frames[:, 14, 0:80:4]).reshape(20*256, 1))
        stim_trg = np.squeeze(np.squeeze(excess_frames[:, 8, 0:80:4]).reshape(20*256, 1))

    print(all_frames.shape)

    # Saves to NWB file
    with NWBHDF5IO(f_nwb, mode='w') as io:
        io.write(nwb)
    print('NWB file saved with size: ', os.stat(f_nwb).st_size/1e6, ' mb')


# If called directly fom terminal
if __name__ == '__main__':
    import sys
    import yaml

    f1 = sys.argv[1]
    f2 = sys.argv[2]
    source_paths = {
        'file1': {'type': 'file', 'path': f1},
        'file2': {'type': 'file', 'path': f2},
    }
    f_nwb = sys.argv[4]
    metafile = sys.argv[5]

    # Load metadata from YAML file
    metafile = sys.argv[3]
    with open(metafile) as f:
       metadata = yaml.safe_load(f)

    conversion_function(source_paths=source_paths,
                        f_nwb=f_nwb,
                        metadata=metadata)
