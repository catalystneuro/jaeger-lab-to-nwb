from pynwb.behavior import BehavioralTimeSeries

import pandas as pd
import numpy as np
import os


def add_behavior_bpod(nwbfile, metadata, source_file):
    """
    Reads behavioral data from bpod files and adds it to nwbfile.
    """
    from scipy.io import loadmat

    # Opens -.mat file and extracts data
    fdata = loadmat(source_file, struct_as_record=False, squeeze_me=True)

    n_trials = fdata['SessionData'].nTrials
    session_start_date = fdata['SessionData'].Info.SessionDate
    session_start_time = fdata['SessionData'].Info.SessionStartTime_UTC

    # Summarized trials data
    trials_start_times = fdata['SessionData'].TrialStartTimestamp
    trials_end_times = fdata['SessionData'].TrialEndTimestamp
    trials_types = fdata['SessionData'].TrialTypes
    trials_led_types = fdata['SessionData'].LEDTypes
    trials_reaching = fdata['SessionData'].Reaching

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
    nwbfile.add_trial_column(name='states', description='', index=True)

    # Trials table structure:
    # trial_number | start | end | states (list) | tag1 | tag1_dur | tag2 | tag2_dur ...
    trials_states_names = []
    for tr in range(n_trials):
        trials_states_names.append([trials_states_names_by_number[tr][number - 1]
                                    for number in trials_states_numbers[tr]])
        nwbfile.add_trial(
            start_time=trials_start_times[tr],
            stop_time=trials_end_times[tr],
            trial_type=trials_types[tr],
            led_type=trials_led_types[tr],
            reaching=trials_reaching[tr],
            states=trials_states_names[tr],
        )

    # Add states tags and durations
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

    return nwbfile


def add_behavior_treadmill(nwbfile, metadata, treadmill_file, nose_file):
    """
    Reads treadmill experiment behavioral data from csv files and adds it to nwbfile.
    """
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
