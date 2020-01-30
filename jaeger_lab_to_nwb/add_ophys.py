from pynwb.ophys import OpticalChannel, TwoPhotonSeries
from pynwb.device import Device
from ndx_fret import FRET, FRETSeries
from hdmf.data_utils import DataChunkIterator

import numpy as np
import struct
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


def add_ophys_rsd(nwbfile, source_dir, metadata, trials):
    """
    Reads optophysiology raw data from .rsd files and adds it to nwbfile.
    XXXXXXX_A.rsd - Raw data from donor
    XXXXXXX_B.rsd - Raw data from acceptor
    XXXXXXXXX.rsh - Header data
    """
    def data_gen(channel):
        """channel = 'A' or 'B'"""
        n_trials = len(trials)
        chunk = 0
        # Iterates over trials, reads .rsd files for each trial number
        while chunk < n_trials:
            # Read trial-specific metadata file .rsh
            trial_meta = os.path.join(source_dir, "VSFP_01A0801-" + str(trials[chunk]) + "_" + channel + ".rsh")
            file_rsm, files_raw, acquisition_date, sample_rate, n_frames = read_trial_meta(trial_meta=trial_meta)

            # Iterates over all files within the same trial
            for fn, fraw in enumerate(files_raw):
                print('adding channel ' + channel + ', trial: ', trials[chunk], ': ', 100*fn/len(files_raw), '%')
                fpath = os.path.join(source_dir, fraw)

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
    nwbfile.add_device(device)

    # Get FRETSeries metadata
    meta_donor = metadata['Ophys']['FRET'][0]['donor']
    meta_acceptor = metadata['Ophys']['FRET'][0]['acceptor']

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
        name='donor',
        fluorophore=meta_donor['fluorophore'],
        optical_channel=opt_ch_donor,
        device=device,
        description=meta_donor['description'],
        data=data_donor,
        rate=meta_donor['rate'],
        unit=meta_donor['unit'],
    )
    frets_acceptor= FRETSeries(
        name='acceptor',
        fluorophore=meta_acceptor['fluorophore'],
        optical_channel=opt_ch_acceptor,
        device=device,
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
    nwbfile.add_acquisition(fret)

    return nwbfile
