from pynwb.behavior import BehavioralTimeSeries, BehavioralEvents
from jaeger_lab_to_nwb.resources.create_nwbfile import create_nwbfile

from datetime import datetime
import pandas as pd
import numpy as np
import copy
import os


def add_behavior_bpod(nwbfile, metadata, source_file):
    """
    Reads behavioral data from bpod files and adds it to nwbfile.
    """
    from scipy.io import loadmat

    # Opens -.mat file and extracts data
    fdata = loadmat(source_file, struct_as_record=False, squeeze_me=True)

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
    nwbfile.add_trial_column(name='trial_type', description='')
    nwbfile.add_trial_column(name='led_type', description='')
    nwbfile.add_trial_column(name='reaching', description='')
    nwbfile.add_trial_column(name='outcome', description='')
    nwbfile.add_trial_column(name='states', description='', index=True)

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
            description='',
            data=state_data,
        )
        nwbfile.add_trial_column(
            name=state + '_dur',
            description='',
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

        nwbfile.add_trial_column(name='fail', description='')
        nwbfile.add_trial_column(name='reward_given', description='')
        nwbfile.add_trial_column(name='total_rewards', description='')
        nwbfile.add_trial_column(name='init_dur', description='')
        nwbfile.add_trial_column(name='light_dur', description='')
        nwbfile.add_trial_column(name='motor_dur', description='')
        nwbfile.add_trial_column(name='post_motor', description='')
        nwbfile.add_trial_column(name='speed', description='')
        nwbfile.add_trial_column(name='speed_mode', description='')
        nwbfile.add_trial_column(name='amplitude', description='')
        nwbfile.add_trial_column(name='period', description='')
        nwbfile.add_trial_column(name='deviation', description='')

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


def add_behavior_labview(nwbfile, source_dir, metadata):
    """
    Reads behavioral data from txt files and adds it to nwbfile.
    """

    # Adds trials
    fname_summary = 'GPi4_020619_AP3_4_OPTO_tr.txt'
    fpath_summary = os.path.join(source_dir, fname_summary)
    df_trials_summary = pd.read_csv(fpath_summary, sep='\t', index_col=False)

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
        name='sample_t',
        description="airpuff duration based on the LabView GUI parameter; not "
                    "the actually air-puff duration."
    )
    nwbfile.add_trial_column(
        name='prob_left',
        description="probability for left trials in order to keep the number of "
                    "left and right trials balanced within the session. "
    )
    nwbfile.add_trial_column(
        name='rew_t',
        description="reward Time based on the LabView GUI parameter. Not the "
                    "actually reward time of the trial. There is no reward if the animal "
                    "fails the trial."
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
        name='free_lick',
        description="whether the animal is allowed to lick the wrong side during "
                    "response period (1 yes; 0 no). This mode is rarely on."
    )
    nwbfile.add_trial_column(
        name='opto_cond',
        description="optical condition. Supposedly, it should indicate which type "
                    "of the optical stimulation is applied. However, this column does not"
                    "represent the correct optical conditions. *Correct optical conditions "
                    "is recovered based on 'processRaw_UpdateSum.m' file."
    )
    nwbfile.add_trial_column(
        name='opto_trial',
        description="pre-determined opto trials: 1 opto trial; 0 non-opto. However, "
                    "an opto-trial might not actually have optical stimulation if the animal "
                    "fails before the optical stimulation. *'processRaw_UpdateSum.m' also "
                    "goes through the raw data to update the wrongly labeled opto trials."
    )
    for index, row in df_trials_summary.iterrows():
        nwbfile.add_trial(
            start_time=row['StartT'],
            stop_time=row['EndT'],
            results=int(row['Result']),
            init_t=row['InitT'],
            sample_t=int(row['SampleT']),
            prob_left=row['ProbLeft'],
            rew_t=row['RewT'],
            l_rew_n=int(row['LRew#']),
            r_rew_n=int(row['RRew#']),
            inter_t=row['InterT'],
            l_trial=int(row['LTrial']),
            free_lick=int(row['Free Lick']),
            opto_cond=int(row['OptoCond']),
            opto_trial=int(row['OptoTrial']),
        )

    # Adds continuous behavioral data
    fname_lick = 'GPi4_020619_AP3_4_OPTO.txt'
    fpath_lick = os.path.join(source_dir, fname_lick)
    df_lick = pd.read_csv(fpath_lick, sep='\t', index_col=False)

    behavioral_ts = BehavioralTimeSeries()
    behavioral_ts.create_timeseries(
        name="left_lick",
        data=df_lick['Lick 1'].to_numpy(),
        timestamps=df_lick['Time'].to_numpy(),
        description="ADDME"
    )
    behavioral_ts.create_timeseries(
        name="right_lick",
        data=df_lick['Lick 2'].to_numpy(),
        timestamps=df_lick['Time'].to_numpy(),
        description="ADDME"
    )
    nwbfile.add_acquisition(behavioral_ts)

    return nwbfile
