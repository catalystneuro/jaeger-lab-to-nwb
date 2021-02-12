from nwb_conversion_tools.basedatainterface import BaseDataInterface
from nwb_conversion_tools.utils import get_schema_from_hdmf_class
from nwb_conversion_tools.json_schema_utils import get_base_schema

from pynwb import NWBFile, TimeSeries
from pynwb.device import Device
from pynwb.ogen import OptogeneticStimulusSite, OptogeneticSeries
from datetime import datetime, timedelta
from pathlib import Path
import pytz
import pandas as pd
import os


class LabviewDataInterface(BaseDataInterface):
    """Conversion class for Labview data."""

    @classmethod
    def get_source_schema(cls):
        """Return a partial JSON schema indicating the input arguments and their types."""
        source_schema = super().get_source_schema()
        source_schema.update(
            required=[],
            properties=dict(
                dir_behavior_labview=dict(
                    type="string",
                    format="directory",
                    description="path to directory containing behavioral data"
                )
            )
        )
        return source_schema

    def get_metadata_schema(self):
        metadata_schema = super().get_metadata_schema()

        # Ogen metadata schema
        metadata_schema['properties']['Ogen'] = get_base_schema()
        metadata_schema['properties']['Ogen']['properties'] = dict(
            Device=get_schema_from_hdmf_class(Device),
            OptogeneticStimulusSite=get_schema_from_hdmf_class(OptogeneticStimulusSite),
            OptogeneticSeries=get_schema_from_hdmf_class(OptogeneticSeries)
        )
        return metadata_schema

    def get_metadata(self):
        # Get list of trial summary files
        dir_behavior_labview = self.source_data['dir_behavior_labview']
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
        session_start_time_tzaware = pytz.timezone('EST').localize(session_start_time)

        metadata = dict(
            NWBFile=dict(
                session_start_time=session_start_time_tzaware.isoformat()
            )
        )
        return metadata

    def run_conversion(self, nwbfile: NWBFile, metadata: dict):
        """
        Run conversion for this data interface.
        Reads labview experiment behavioral data and adds it to nwbfile.

        Parameters
        ----------
        nwbfile : NWBFile
        metadata : dict
        """
        print("Converting Labview data...")
        # Get list of trial summary files
        dir_behavior_labview = self.source_data['dir_behavior_labview']
        all_files = os.listdir(dir_behavior_labview)
        trials_files = [f for f in all_files if '_sum.txt' in f]
        trials_files.sort()

        # Get session_start_time from first file timestamps
        fpath = os.path.join(dir_behavior_labview, trials_files[0])
        colnames = ['Trial', 'StartT', 'EndT', 'Result', 'InitT', 'SpecificResults',
                    'ProbLeft', 'OptoDur', 'LRew', 'RRew', 'InterT', 'LTrial',
                    'ReactionTime', 'OptoCond', 'OptoTrial']
        df_0 = pd.read_csv(fpath, sep='\t', index_col=False, names=colnames)
        t0 = df_0['StartT'][0]   # initial time in Labview seconds

        # Add trials
        print("Converting Labview trials data...")
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
        print("Converting Labview behavior data...")
        l1_ts = TimeSeries(
            name="left_lick",
            data=df_continuous['Lick 1'].to_numpy(),
            timestamps=df_continuous['Time'].to_numpy() - t0,
            description="no description"
        )
        l2_ts = TimeSeries(
            name="right_lick",
            data=df_continuous['Lick 2'].to_numpy(),
            timestamps=df_continuous['Time'].to_numpy() - t0,
            description="no description"
        )

        nwbfile.add_acquisition(l1_ts)
        nwbfile.add_acquisition(l2_ts)

        # Optogenetics stimulation data
        print("Converting Labview optogenetics data...")
        ogen_device = nwbfile.create_device(
            name=metadata['Ogen']['Device']['name'],
            description=metadata['Ogen']['Device']['description']
        )

        meta_ogen_site = metadata['Ogen']['OptogeneticStimulusSite']
        ogen_stim_site = OptogeneticStimulusSite(
            name=meta_ogen_site['name'],
            device=ogen_device,
            description=meta_ogen_site['description'],
            excitation_lambda=float(meta_ogen_site['excitation_lambda']),
            location=meta_ogen_site['location']
        )
        nwbfile.add_ogen_site(ogen_stim_site)

        meta_ogen_series = metadata['Ogen']['OptogeneticSeries']
        ogen_series = OptogeneticSeries(
            name=meta_ogen_series['name'],
            data=df_continuous['Opto'].to_numpy(),
            site=ogen_stim_site,
            timestamps=df_continuous['Time'].to_numpy() - t0,
            description=meta_ogen_series['description'],
        )
        nwbfile.add_stimulus(ogen_series)
