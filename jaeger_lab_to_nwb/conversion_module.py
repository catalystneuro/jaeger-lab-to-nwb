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
                acquisition_date = line.replace('acquisition_date', '').replace('=', '').strip()
            if 'sample_time' in line:
                aux = line.replace('sample_time', '').replace('=', '').replace('msec', '').strip()
                sample_time = float(aux)/1000.
                sample_rate = 1 / sample_time
            if 'page_frames' in line:
                aux = line.replace('page_frames', '').replace('=', '').strip()
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
    all_trials = ['100']#, '101', '102']

    # Get initial metadata
    meta_init = copy.deepcopy(metadata['NWBFile'])
    trial_meta_A = os.path.join(dir_cortical_imaging, "VSFP_01A0801-" + str(all_trials[0]) + "_A.rsh")
    trial_meta_B = os.path.join(dir_cortical_imaging, "VSFP_01A0801-" + str(all_trials[0]) + "_B.rsh")
    file_rsm_A, files_raw_A, acquisition_date_A, sample_rate_A, n_frames_A = read_trial_meta(trial_meta=trial_meta_A)
    file_rsm_B, files_raw_B, acquisition_date_B, sample_rate_B, n_frames_B = read_trial_meta(trial_meta=trial_meta_B)
    assert acquisition_date_A == acquisition_date_B, \
        "Initial acquisition date of channels do not match."
    meta_init['session_start_time'] = datetime.strptime(acquisition_date_A, '%Y/%m/%d %H:%M:%S')

    # Initialize a NWB object
    nwb = NWBFile(**meta_init)

    # Adds trials
    tr_stop = 0.
    for tr in all_trials:
        trial_meta_A = os.path.join(dir_cortical_imaging, "VSFP_01A0801-" + str(tr) + "_A.rsh")
        trial_meta_B = os.path.join(dir_cortical_imaging, "VSFP_01A0801-" + str(tr) + "_B.rsh")
        file_rsm_A, files_raw_A, acquisition_date_A, sample_rate_A, n_frames_A = read_trial_meta(trial_meta=trial_meta_A)
        file_rsm_B, files_raw_B, acquisition_date_B, sample_rate_B, n_frames_B = read_trial_meta(trial_meta=trial_meta_B)

        # Checks if Acceptor and Donor channels have the same basic parameters
        assert acquisition_date_A == acquisition_date_B, \
            "Acquisition date of channels do not match. Trial=" + str(tr)
        assert sample_rate_A == sample_rate_B, \
            "Sample rate of channels do not match. Trial=" + str(tr)
        assert n_frames_A == n_frames_B, \
            "Number of frames of channels do not match. Trial=" + str(tr)

        tr_start = tr_stop
        tr_stop += n_frames_A / sample_rate_A
        nwb.add_trial(start_time=tr_start, stop_time=tr_stop)

    # Iteratively opens files with raw imaging data
    if add_raw:
        def data_gen(channel):
            """channel = 'A' or 'B'"""
            n_trials = len(all_trials)
            chunk = 0
            # Iterates over trials, reads .rsd files for each trial number
            while chunk < n_trials:
                # Read trial-specific metadata file .rsh
                trial_meta = os.path.join(dir_cortical_imaging, "VSFP_01A0801-" + str(all_trials[chunk]) + "_" + channel + ".rsh")
                file_rsm, files_raw, acquisition_date, sample_rate, n_frames = read_trial_meta(trial_meta=trial_meta)

                # Iterates over all files within the same trial
                for fn, fraw in enumerate(files_raw):
                    print('adding channel ' + channel + ', trial: ', all_trials[chunk], ': ', 100*fn/len(files_raw), '%')
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
        data_donor = DataChunkIterator(
            data=data_gen(channel='A'),
            iter_axis=0,
            buffer_size=10000,
            maxshape=(None, 100, 100)
        )
        data_acceptor = DataChunkIterator(
            data=data_gen(channel='B'),
            iter_axis=0,
            buffer_size=10000,
            maxshape=(None, 100, 100)
        )

        # Create and add device
        device = Device(name=metadata['Ophys']['Device'][0]['name'])
        nwb.add_device(device)

        # Get FRETSeries metadata
        meta_fret_series = metadata['Ophys']['FRETSeries']
        if meta_fret_series[0]['name'] == 'donor':
            meta_donor = meta_fret_series[0]
            meta_acceptor = meta_fret_series[1]
        else:
            meta_donor = meta_fret_series[1]
            meta_acceptor = meta_fret_series[0]

        # OpticalChannels
        opt_ch_donor = OpticalChannel(
            name=meta_donor['optical_channel'][0]['name'],
            description=meta_donor['optical_channel'][0]['description'],
            emission_lambda=meta_donor['optical_channel'][0]['emission_lambda']
        )
        opt_ch_acceptor = OpticalChannel(
            name=meta_acceptor['optical_channel'][0]['name'],
            description=meta_acceptor['optical_channel'][0]['description'],
            emission_lambda=meta_acceptor['optical_channel'][0]['emission_lambda']
        )

        # FRETSeries
        frets_donor= FRETSeries(
            name=meta_donor['name'],
            fluorophore=meta_donor['fluorophore'],
            optical_channel=opt_ch_donor,
            device=device,
            emission_lambda=meta_donor['emission_lambda'],
            description=meta_donor['description'],
            data=data_donor,
            rate=meta_donor['rate'],
            unit=meta_donor['unit'],
        )
        frets_acceptor= FRETSeries(
            name=meta_acceptor['name'],
            fluorophore=meta_acceptor['fluorophore'],
            optical_channel=opt_ch_acceptor,
            device=device,
            emission_lambda=meta_acceptor['emission_lambda'],
            description=meta_acceptor['description'],
            data=data_acceptor,
            rate=meta_acceptor['rate'],
            unit=meta_acceptor['unit']
        )

        # Adds FRET to acquisition
        meta_fret = metadata['Ophys']['FRET'][0]
        fret = FRET(
            name=meta_fret['name'],
            excitation_lambda=meta_fret['excitation_lambda'],
            donor=frets_donor,
            acceptor=frets_acceptor
        )
        nwb.add_acquisition(fret)

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
