from nwb_conversion_tools.basedatainterface import BaseDataInterface
from nwb_conversion_tools.utils import get_schema_from_hdmf_class
from nwb_conversion_tools.json_schema_utils import get_base_schema

from pynwb import NWBFile, TimeSeries
from datetime import datetime
from pathlib import Path
import pytz
import pandas as pd
import os


class TreadmillDataInterface(BaseDataInterface):
    """Conversion class for Treadmill data."""

    @classmethod
    def get_source_schema(cls):
        """Return a partial JSON schema indicating the input arguments and their types."""
        source_schema = super().get_source_schema()
        source_schema.update(
            required=[],
            properties=dict(
                dir_behavior_treadmill=dict(
                    type="string",
                    format="directory",
                    description="path to directory containing behavioral data in csv files"
                )
            )
        )
        return source_schema

    def get_metadata_schema(self):
        metadata_schema = super().get_metadata_schema()
        return metadata_schema

    def get_metadata(self):
        # Detect relevant file and get initial metadata
        dir_behavior_treadmill = self.source_data['dir_behavior_treadmill']
        trials_file = [f for f in Path(dir_behavior_treadmill).glob('*_tr.csv') if '~lock' not in f.name][0]
        date_string = trials_file.name.split('.')[0].split('_')[1]
        time_string = trials_file.name.split('.')[0].split('_')[2]
        date_time_string = date_string + ' ' + time_string
        date_time_obj = datetime.strptime(date_time_string, '%Y%m%d %H%M%S')
        session_start_time_tzaware = pytz.timezone('EST').localize(date_time_obj)
        metadata = dict(
            NWBFile=dict(
                session_start_time=session_start_time_tzaware.isoformat()
            )
        )
        return metadata

    def run_conversion(self, nwbfile: NWBFile, metadata: dict):
        """
        Run conversion for this data interface.
        Reads treadmill experiment behavioral data from csv files and adds it to nwbfile.

        Parameters
        ----------
        nwbfile : NWBFile
        metadata : dict
        """
        # Detect relevant files: trials summary, treadmill data and nose data
        dir_behavior_treadmill = self.source_data['dir_behavior_treadmill']
        trials_file = [f for f in Path(dir_behavior_treadmill).glob('*_tr.csv') if '~lock' not in f.name][0]
        treadmill_file = trials_file.name.split('_tr')[0] + '.csv'
        nose_file = trials_file.name.split('_tr')[0] + '_mk.csv'

        trials_file = os.path.join(dir_behavior_treadmill, trials_file)
        treadmill_file = os.path.join(dir_behavior_treadmill, treadmill_file)
        nose_file = os.path.join(dir_behavior_treadmill, nose_file)

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

        # Treadmill continuous data
        df_treadmill = pd.read_csv(treadmill_file, index_col=False)

        # Nose position continuous data
        df_nose = pd.read_csv(nose_file, index_col=False)

        # All behavioral data
        df_all = pd.concat([df_treadmill, df_nose], axis=1, sort=False)

        meta_behavioral_ts = metadata['Behavior']
        t_offset = df_treadmill.loc[0]['Time']
        for meta in meta_behavioral_ts.values():
            ts = TimeSeries(
                name=meta['name'],
                data=df_all[meta['name']].to_numpy(),
                timestamps=df_all['Time'].to_numpy() - t_offset,
                description=meta['description']
            )
            nwbfile.add_acquisition(ts)
