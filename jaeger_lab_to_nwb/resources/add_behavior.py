from pynwb.behavior import BehavioralTimeSeries, BehavioralEvents
from pynwb.ogen import OptogeneticStimulusSite, OptogeneticSeries
from jaeger_lab_to_nwb.resources.create_nwbfile import create_nwbfile

from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import copy
import os


def add_behavior_bpod(nwbfile, metadata, file_behavior_bpod):
    """
    Reads behavioral data from bpod files and adds it to nwbfile.
    """
    from scipy.io import loadmat

    # Opens -.mat file and extracts data
    fdata = loadmat(file_behavior_bpod, struct_as_record=False, squeeze_me=True)

    session_start_date = fdata['SessionData'].Info.SessionDate
    session_start_time = fdata['SessionData'].Info.SessionStartTime_UTC

    # Get initial metadata
    meta_init = copy.deepcopy(metadata)
    if nwbfile is None:
        date_time_string = session_start_date + ' ' + session_start_time
        date_time_obj = datetime.strptime(date_time_string, '%d-%b-%Y %H:%M:%S')
        meta_init['NWBFile']['session_start_time'] = date_time_obj
        nwbfile = create_nwbfile(meta_init)

    # Summarized trials data
    n_trials = fdata['SessionData'].nTrials
    trials_start_times = fdata['SessionData'].TrialStartTimestamp
    trials_end_times = fdata['SessionData'].TrialEndTimestamp
    trials_types = fdata['SessionData'].TrialTypes
    trials_led_types = fdata['SessionData'].LEDTypes
    trials_reaching = fdata['SessionData'].Reaching
    trials_outcome = fdata['SessionData'].Outcome

    # Raw data - states
    trials_states_names_by_number = fdata['SessionData'].RawData.OriginalStateNamesByNumber
    all_trials_states_names = np.unique(np.concatenate(trials_states_names_by_number, axis=0))
    trials_states_numbers = fdata['SessionData'].RawData.OriginalStateData
    trials_states_timestamps = fdata['SessionData'].RawData.OriginalStateTimestamps
    trials_states_durations = [np.diff(dur) for dur in trials_states_timestamps]

    # # Add trials columns
    nwbfile.add_trial_column(name='trial_type', description='no description')
    nwbfile.add_trial_column(name='led_type', description='no description')
    nwbfile.add_trial_column(name='reaching', description='no description')
    nwbfile.add_trial_column(name='outcome', description='no description')
    nwbfile.add_trial_column(name='states', description='no description', index=True)

    # Trials table structure:
    # trial_number | start | end | trial_type | led_type | reaching | outcome | states (list)
    trials_states_names = []
    tup_ts = np.array([])
    port_1_in_ts = np.array([])
    port_1_out_ts = np.array([])
    port_2_in_ts = np.array([])
    port_2_out_ts = np.array([])
    for tr in range(n_trials):
        trials_states_names.append([trials_states_names_by_number[tr][number - 1]
                                    for number in trials_states_numbers[tr]])
        nwbfile.add_trial(
            start_time=trials_start_times[tr],
            stop_time=trials_end_times[tr],
            trial_type=trials_types[tr],
            led_type=trials_led_types[tr],
            reaching=trials_reaching[tr],
            outcome=trials_outcome[tr],
            states=trials_states_names[tr],
        )

        # Events names: ['Tup', 'Port2In', 'Port2Out', 'Port1In', 'Port1Out']
        trial_events_names = fdata['SessionData'].RawEvents.Trial[tr].Events._fieldnames
        t0 = trials_start_times[tr]
        if 'Port1In' in trial_events_names:
            timestamps = fdata['SessionData'].RawEvents.Trial[tr].Events.Port1In + t0
            port_1_in_ts = np.append(port_1_in_ts, timestamps)
        if 'Port1Out' in trial_events_names:
            timestamps = fdata['SessionData'].RawEvents.Trial[tr].Events.Port1Out + t0
            port_1_out_ts = np.append(port_1_out_ts, timestamps)
        if 'Port2In' in trial_events_names:
            timestamps = fdata['SessionData'].RawEvents.Trial[tr].Events.Port2In + t0
            port_2_in_ts = np.append(port_2_in_ts, timestamps)
        if 'Port2Out' in trial_events_names:
            timestamps = fdata['SessionData'].RawEvents.Trial[tr].Events.Port2Out + t0
            port_2_out_ts = np.append(port_2_out_ts, timestamps)
        if 'Tup' in trial_events_names:
            timestamps = fdata['SessionData'].RawEvents.Trial[tr].Events.Tup + t0
            tup_ts = np.append(tup_ts, timestamps)

    # Add states and durations
    # trial_number | ... | state1 | state1_dur | state2 | state2_dur ...
    for state in all_trials_states_names:
        state_data = []
        state_dur = []
        for tr in range(n_trials):
            if state in trials_states_names[tr]:
                state_data.append(True)
                dur = trials_states_durations[tr][trials_states_names[tr].index(state)]
                state_dur.append(dur)
            else:
                state_data.append(False)
                state_dur.append(np.nan)
        nwbfile.add_trial_column(
            name=state,
            description='no description',
            data=state_data,
        )
        nwbfile.add_trial_column(
            name=state + '_dur',
            description='no description',
            data=state_dur,
        )

    # Add events
    behavioral_events = BehavioralEvents()
    behavioral_events.create_timeseries(name='port_1_in', timestamps=port_1_in_ts)
    behavioral_events.create_timeseries(name='port_1_out', timestamps=port_1_out_ts)
    behavioral_events.create_timeseries(name='port_2_in', timestamps=port_2_in_ts)
    behavioral_events.create_timeseries(name='port_2_out', timestamps=port_2_out_ts)
    behavioral_events.create_timeseries(name='tup', timestamps=tup_ts)

    nwbfile.add_acquisition(behavioral_events)

    return nwbfile


def add_behavior_treadmill(nwbfile, metadata, dir_behavior_treadmill):
    """
    Reads treadmill experiment behavioral data from csv files and adds it to nwbfile.
    """
    # Detect relevant files: trials summary, treadmill data and nose data
    all_files = os.listdir(dir_behavior_treadmill)
    trials_file = [f for f in all_files if ('_tr.csv' in f and '~lock' not in f)][0]
    treadmill_file = trials_file.split('_tr')[0] + '.csv'
    nose_file = trials_file.split('_tr')[0] + '_mk.csv'

    trials_file = os.path.join(dir_behavior_treadmill, trials_file)
    treadmill_file = os.path.join(dir_behavior_treadmill, treadmill_file)
    nose_file = os.path.join(dir_behavior_treadmill, nose_file)

    # Get initial metadata
    meta_init = copy.deepcopy(metadata)
    if nwbfile is None:
        date_string = trials_file[0].split('.')[0].split('_')[1]
        time_string = trials_file[0].split('.')[0].split('_')[2]
        date_time_string = date_string + ' ' + time_string
        date_time_obj = datetime.strptime(date_time_string, '%y%m%d %H%M%S')
        meta_init['NWBFile']['session_start_time'] = date_time_obj
        nwbfile = create_nwbfile(meta_init)

    # Add trials
    if nwbfile.trials is not None:
        print('Trials already exist in current nwb file. Treadmill behavior trials not added.')
    else:
        df_trials_summary = pd.read_csv(trials_file)

        nwbfile.add_trial_column(name='fail', description='no description')
        nwbfile.add_trial_column(name='reward_given', description='no description')
        nwbfile.add_trial_column(name='total_rewards', description='no description')
        nwbfile.add_trial_column(name='init_dur', description='no description')
        nwbfile.add_trial_column(name='light_dur', description='no description')
        nwbfile.add_trial_column(name='motor_dur', description='no description')
        nwbfile.add_trial_column(name='post_motor', description='no description')
        nwbfile.add_trial_column(name='speed', description='no description')
        nwbfile.add_trial_column(name='speed_mode', description='no description')
        nwbfile.add_trial_column(name='amplitude', description='no description')
        nwbfile.add_trial_column(name='period', description='no description')
        nwbfile.add_trial_column(name='deviation', description='no description')

        t_offset = df_trials_summary.loc[0]['Start Time']
        for index, row in df_trials_summary.iterrows():
            nwbfile.add_trial(
                start_time=row['Start Time'] - t_offset,
                stop_time=row['End Time'] - t_offset,
                fail=row['Fail'],
                reward_given=row['Reward Given'],
                total_rewards=row['Total Rewards'],
                init_dur=row['Init Dur'],
                light_dur=row['Light Dur'],
                motor_dur=row['Motor Dur'],
                post_motor=row['Post Motor'],
                speed=row['Speed'],
                speed_mode=row['Speed Mode'],
                amplitude=row['Amplitude'],
                period=row['Period'],
                deviation=row['+/- Deviation'],
            )

    # Create BehavioralTimeSeries container
    behavioral_ts = BehavioralTimeSeries()
    meta_behavioral_ts = metadata['Behavior']['BehavioralTimeSeries']['time_series']

    # Treadmill continuous data
    df_treadmill = pd.read_csv(treadmill_file, index_col=False)

    # Nose position continuous data
    df_nose = pd.read_csv(nose_file, index_col=False)

    # All behavioral data
    df_all = pd.concat([df_treadmill, df_nose], axis=1, sort=False)

    t_offset = df_treadmill.loc[0]['Time']
    for meta in meta_behavioral_ts:
        behavioral_ts.create_timeseries(
            name=meta['name'],
            data=df_all[meta['name']].to_numpy(),
            timestamps=df_all['Time'].to_numpy() - t_offset,
            description=meta['description']
        )

    nwbfile.add_acquisition(behavioral_ts)

    return nwbfile


def add_behavior_labview(nwbfile, metadata, dir_behavior_labview):
    """
    Reads behavioral data from txt files and adds it to nwbfile.
    """
    # Get list of trial summary files
    all_files = os.listdir(dir_behavior_labview)
    trials_files = [f for f in all_files if '_sum.txt' in f]
    trials_files.sort()

    # Get session_start_time from first file timestamps
    labview_time_offset = datetime.strptime('01/01/1904 00:00:00', '%m/%d/%Y %H:%M:%S')  # LabView timestamps offset
    fpath = os.path.join(dir_behavior_labview, trials_files[0])
    colnames = ['Trial', 'StartT', 'EndT', 'Result', 'InitT', 'SpecificResults',
                'ProbLeft', 'OptoDur', 'LRew', 'RRew', 'InterT', 'LTrial',
                'ReactionTime', 'OptoCond', 'OptoTrial']
    df_0 = pd.read_csv(fpath, sep='\t', index_col=False, names=colnames)
    t0 = df_0['StartT'][0]   # initial time in Labview seconds
    session_start_time = labview_time_offset + timedelta(seconds=t0)

    # Create nwbfile / test for matching start_time in existing nwbfile
    meta_init = copy.deepcopy(metadata)
    if nwbfile is None:
        meta_init['NWBFile']['session_start_time'] = session_start_time
        nwbfile = create_nwbfile(meta_init)
    else:
        if session_start_time != nwbfile.session_start_time:
            print("Session start time in current nwbfile does not match the start time from Labview files.")
            print("Labview data conversion aborted.")
            return nwbfile

    # Add trials
    if nwbfile.trials is not None:
        print('Trials already exist in current nwb file. Labview behavior trials not added.')
    else:
        # Make dataframe
        frames = []
        for f in trials_files:
            fpath = os.path.join(dir_behavior_labview, f)
            frames.append(pd.read_csv(fpath, sep='\t', index_col=False, names=colnames))
        df_trials_summary = pd.concat(frames)

        nwbfile.add_trial_column(
            name='results',
            description="0 means sucess (rewarded trial), 1 means licks during intitial "
                        "period, which leads to a failed trial. 2 means early lick failure. 3 means "
                        "wrong lick or no response."
        )
        nwbfile.add_trial_column(
            name='init_t',
            description="duration of initial delay period."
        )
        nwbfile.add_trial_column(
            name='specific_results',
            description="Possible outcomes classified based on raw data & meta file (_tr.m)."
        )
        nwbfile.add_trial_column(
            name='prob_left',
            description="probability for left trials in order to keep the number of "
                        "left and right trials balanced within the session. "
        )
        nwbfile.add_trial_column(
            name='opto_dur',
            description="the duration of optical stimulation."
        )
        nwbfile.add_trial_column(
            name='l_rew_n',
            description="counting the number of left rewards."
        )
        nwbfile.add_trial_column(
            name='r_rew_n',
            description="counting the number of rightrewards."
        )
        nwbfile.add_trial_column(
            name='inter_t',
            description="inter-trial delay period."
        )
        nwbfile.add_trial_column(
            name='l_trial',
            description="trial type (which side the air-puff is applied). 1 means "
                        "left-trial, 0 means right-trial"
        )
        nwbfile.add_trial_column(
            name='reaction_time',
            description="if it is a successful trial or wrong lick during response "
                        "period trial: ReactionTime = time between the first decision "
                        "lick and the beginning of the response period. If it is a failed "
                        "trial due to early licks: reaction time = the duration of "
                        "the air-puff period (in other words, when the animal licks "
                        "during the sample period)."
        )
        nwbfile.add_trial_column(
            name='opto_cond',
            description="0: no opto. 1: opto is on during sample period. "
                        "2: opto is on half way through the sample period (0.5s) "
                        "and 0.5 during the response period. 3. opto is on during "
                        "the response period."
        )
        nwbfile.add_trial_column(
            name='opto_trial',
            description="1: opto trials. 0: Non-opto trials."
        )
        for index, row in df_trials_summary.iterrows():
            nwbfile.add_trial(
                start_time=row['StartT'] - t0,
                stop_time=row['EndT'] - t0,
                results=int(row['Result']),
                init_t=row['InitT'],
                specific_results=int(row['SpecificResults']),
                prob_left=row['ProbLeft'],
                opto_dur=row['OptoDur'],
                l_rew_n=int(row['LRew']),
                r_rew_n=int(row['RRew']),
                inter_t=row['InterT'],
                l_trial=int(row['LTrial']),
                reaction_time=int(row['ReactionTime']),
                opto_cond=int(row['OptoCond']),
                opto_trial=int(row['OptoTrial']),
            )

    # Get list of files: continuous data
    continuous_files = [f.replace('_sum', '') for f in trials_files]

    # Adds continuous behavioral data
    frames = []
    for f in continuous_files:
        fpath_lick = os.path.join(dir_behavior_labview, f)
        frames.append(pd.read_csv(fpath_lick, sep='\t', index_col=False))
    df_continuous = pd.concat(frames)

    # Behavioral data
    behavioral_ts = BehavioralTimeSeries()
    behavioral_ts.create_timeseries(
        name="left_lick",
        data=df_continuous['Lick 1'].to_numpy(),
        timestamps=df_continuous['Time'].to_numpy() - t0,
        description="no description"
    )
    behavioral_ts.create_timeseries(
        name="right_lick",
        data=df_continuous['Lick 2'].to_numpy(),
        timestamps=df_continuous['Time'].to_numpy() - t0,
        description="no description"
    )
    nwbfile.add_acquisition(behavioral_ts)

    # Optogenetics stimulation data
    ogen_device = nwbfile.create_device(name=metadata['Ogen']['Device'][0]['name'])

    meta_ogen_site = metadata['Ogen']['OptogeneticStimulusSite'][0]
    ogen_stim_site = OptogeneticStimulusSite(
        name=meta_ogen_site['name'],
        device=ogen_device,
        description=meta_ogen_site['description'],
        excitation_lambda=meta_ogen_site['excitation_lambda'],
        location=meta_ogen_site['location']
    )
    nwbfile.add_ogen_site(ogen_stim_site)

    meta_ogen_series = metadata['Ogen']['OptogeneticSeries'][0]
    ogen_series = OptogeneticSeries(
        name=meta_ogen_series['name'],
        data=df_continuous['Opto'].to_numpy(),
        site=ogen_stim_site,
        timestamps=df_continuous['Time'].to_numpy() - t0,
        description=meta_ogen_series['description'],
    )
    nwbfile.add_stimulus(ogen_series)

    return nwbfile
