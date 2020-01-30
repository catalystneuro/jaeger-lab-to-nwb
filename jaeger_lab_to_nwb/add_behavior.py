from pynwb import NWBFile, NWBHDF5IO
from pynwb.device import Device

import numpy as np
import pandas as pd
import os


def add_behavior_labview(nwbfile, source_dir, metadata):
    """
    Reads behavioral data from txt files and adds it to nwbfile.
    """

    fname = 'GPi4_020619_AP3_4_OPTO_tr.txt'
    fpath = os.path.join(source_dir, fname)
    df_trials_summary = pd.read_csv(fpath, sep='\t', index_col=False)

    # Adds trials
    nwbfile.add_trial_column(
        name='results',
        description="0 means sucess (rewarded trial), 1 means licks during intitial "\
            "period, which leads to a failed trial. 2 means early lick failure. 3 means "\
            "wrong lick or no response."
    )
    nwbfile.add_trial_column(
        name='init_t',
        description="duration of initial delay period."
    )
    nwbfile.add_trial_column(
        name='sample_t',
        description="airpuff duration based on the LabView GUI parameter; not "\
            "the actually air-puff duration."
    )
    nwbfile.add_trial_column(
        name='prob_left',
        description="probability for left trials in order to keep the number of "\
            "left and right trials balanced within the session. "
    )
    nwbfile.add_trial_column(
        name='rew_t',
        description="reward Time based on the LabView GUI parameter. Not the "\
            "actually reward time of the trial. There is no reward if the animal "\
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
        description="trial type (which side the air-puff is applied). 1 means "\
            "left-trial, 0 means right-trial"
    )
    nwbfile.add_trial_column(
        name='free_lick',
        description="whether the animal is allowed to lick the wrong side during "\
            "response period (1 yes; 0 no). This mode is rarely on."
    )
    nwbfile.add_trial_column(
        name='opto_cond',
        description="optical condition. Supposedly, it should indicate which type "\
            "of the optical stimulation is applied. However, this column does not"\
            "represent the correct optical conditions. *Correct optical conditions "\
            "is recovered based on 'processRaw_UpdateSum.m' file."
    )
    nwbfile.add_trial_column(
        name='opto_trial',
        description="pre-determined opto trials: 1 opto trial; 0 non-opto. However, "\
            "an opto-trial might not actually have optical stimulation if the animal "\
            "fails before the optical stimulation. *'processRaw_UpdateSum.m' also "\
            "goes through the raw data to update the wrongly labeled opto trials."
    )
    for index, row in df_trials_summary.iterrows():
        nwbfile.add_trial(
            start_time=row['StartT'],
            stop_time=row['EndT'],
            results=row['Result'],
            init_t=row['InitT'],
            sample_t=row['SampleT'],
            prob_left=row['ProbLeft'],
            rew_t=row['RewT'],
            l_rew_n=row['LRew#'],
            r_rew_n=row['RRew#'],
            inter_t=row['InterT'],
            l_trial=row['LTrial'],
            free_lick=row['Free Lick'],
            opto_cond=row['OptoCond'],
            opto_trial=row['OptoTrial'],
        )

    # Adds Device
    device = nwbfile.create_device(name=metadata['Behavior']['Device'][0]['name'])

    return nwbfile
