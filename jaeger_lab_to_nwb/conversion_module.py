# authors: Luiz Tauffer and Ben Dichter
# written for Jaeger Lab
# ------------------------------------------------------------------------------
from pynwb import NWBFile, NWBHDF5IO, ProcessingModule
from pynwb.ophys import OpticalChannel, TwoPhotonSeries
from pynwb.device import Device
from ndx_fret import FRET, FRETSeries
from hdmf.data_utils import DataChunkIterator

from datetime import datetime
import numpy as np
import yaml
import copy
import struct
import re
import os


def read_trial_meta(trial_meta):
    """Opens trial_meta file and read line by line."""
    files_raw = []
    addftolist = False
    with open(trial_meta, "r") as f:
        line = f.readline()
        while line:
            if 'acquisition_date' in line:
                acquisition_date = line.replace('acquisition_date=', '').strip()
            if 'sample_time' in line:
                aux = line.replace('sample_time=', '').replace('msec', '').strip()
                sample_time = float(aux)/1000.
                sample_rate = 1 / sample_time
            if 'page_frames' in line:
                aux = line.replace('page_frames=', '').strip()
                n_frames = int(aux)
            if addftolist:
                files_raw.append(line.strip())
            if 'Data-File-List' in line:
                addftolist = True   # indicates that next lines are file names to be added
            line = f.readline()

    # Separate .rsm file (bitmap of monitor) from .rsd files (raw data)
    file_rsm = files_raw[0]
    files_raw = files_raw[1:]
    return file_rsm, files_raw, acquisition_date, sample_rate, n_frames


def conversion_function(source_paths, f_nwb, metadata, add_raw=False, **kwargs):
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

    # All trials
    # TODO: some trials seem to be consecutive and others are spaced by larger time gaps
    # TODO: also they seem to have different data. We need to get a better description of trials
    # TODO: and handle them properly
    all_trials = ['100', '101', '102']

    # Get initial metadata
    meta_init = copy.deepcopy(metadata['NWBFile'])
    trial_meta = os.path.join(dir_cortical_imaging, "VSFP_01A0801-" + str(all_trials[0]) + ".rsh")
    file_rsm, files_raw, acquisition_date, sample_rate, n_frames = read_trial_meta(trial_meta=trial_meta)
    meta_init['session_start_time'] = datetime.strptime(acquisition_date, '%Y/%m/%d %H:%M:%S')

    # Initialize a NWB object
    nwb = NWBFile(**meta_init)

    # Adds trials
    tr_stop = 0.
    for tr in all_trials:
        trial_meta = os.path.join(dir_cortical_imaging, "VSFP_01A0801-" + str(tr) + ".rsh")
        file_rsm, files_raw, acquisition_date, sample_rate, n_frames = read_trial_meta(trial_meta=trial_meta)
        tr_start = tr_stop
        tr_stop += n_frames / sample_rate
        nwb.add_trial(start_time=tr_start, stop_time=tr_stop)

    # Create and add device
    device = Device(name=metadata['Ophys']['Device'][0]['name'])
    nwb.add_device(device)

    # Creates Imaging Plane
    fs = 200.
    for meta_ip in metadata['Ophys']['ImagingPlane']:
        # Optical channel
        opt_ch = OpticalChannel(
            name=meta_ip['optical_channel'][0]['name'],
            description=meta_ip['optical_channel'][0]['description'],
            emission_lambda=meta_ip['optical_channel'][0]['emission_lambda']
        )
        nwb.create_imaging_plane(
            name=meta_ip['name'],
            optical_channel=opt_ch,
            description=meta_ip['description'],
            device=device,
            excitation_lambda=meta_ip['excitation_lambda'],
            imaging_rate=fs,
            indicator=meta_ip['indicator'],
            location=meta_ip['location'],
        )

    # Adds raw imaging data
    if add_raw:
        def data_gen():
            n_trials = len(all_trials)
            chunk = 0
            # Iterates over trials, reads .rsd files for each trial number
            while chunk < n_trials:
                # Read trial-specific metadata file .rsh
                trial_meta = os.path.join(dir_cortical_imaging, "VSFP_01A0801-" + str(all_trials[chunk]) + ".rsh")
                file_rsm, files_raw, acquisition_date, sample_rate, n_frames = read_trial_meta(trial_meta=trial_meta)

                # Iterates over all files within the same trial
                for fn, fraw in enumerate(files_raw):
                    print('adding trial: ', all_trials[chunk], ': ', 100*fn/len(files_raw), '%')
                    fpath = os.path.join(dir_cortical_imaging, fraw)

                    # Open file as a byte array
                    with open(fpath, "rb") as f:
                        byte = f.read(1000000000)
                    # Data as word array: 'h' signed, 'H' unsigned
                    words = np.array(struct.unpack('h'*(len(byte)//2), byte))

                    # Iterates over frames within the same file (n_frames, 100, 100)
                    n_frames = int(len(words)/12800)
                    words_reshaped = words.reshape(12800, n_frames, order='F')
                    frames = np.zeros((n_frames, 100, 100))
                    excess_frames = np.zeros((n_frames, 20, 100))
                    for ifr in range(n_frames):
                        iframe = -words_reshaped[:, ifr].reshape(128, 100, order='F')
                        frames[ifr, :, :] = iframe[20:120, :]
                        excess_frames[ifr, :, :] = iframe[0:20, :]

                        yield iframe[20:120, :]
                chunk += 1

                #     # Analog signals are taken from excess data variable
                #     analog_1 = np.squeeze(np.squeeze(excess_frames[:, 12, 0:80:4]).reshape(20*256, 1))
                #     analog_2 = np.squeeze(np.squeeze(excess_frames[:, 14, 0:80:4]).reshape(20*256, 1))
                #     stim_trg = np.squeeze(np.squeeze(excess_frames[:, 8, 0:80:4]).reshape(20*256, 1))
                #

        # Create iterator
        tps_data = DataChunkIterator(
            data=data_gen(),
            iter_axis=0,
            buffer_size=16384,
            maxshape=(None, 100, 100)
        )

        # Add raw data as a TwoPhotonSeries in acquisition
        meta_tps = metadata['Ophys']['TwoPhotonSeries'][0]
        tps = TwoPhotonSeries(
            name=meta_tps['name'],
            imaging_plane=nwb.imaging_planes[meta_tps['imaging_plane']],
            data=tps_data,
            rate=fs
        )
        nwb.add_acquisition(tps)

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
