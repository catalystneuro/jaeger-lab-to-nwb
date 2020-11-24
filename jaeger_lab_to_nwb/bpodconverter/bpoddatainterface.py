from nwb_conversion_tools.basedatainterface import BaseDataInterface
from pynwb import NWBFile
from ndx_events import Events
from scipy.io import loadmat
import numpy as np


class BpodDataInterface(BaseDataInterface):
    """Conversion class for Bpod behavioral data."""

    @classmethod
    def get_source_schema(cls):
        """Return a partial JSON schema indicating the input arguments and their types."""
        source_schema = super().get_source_schema()
        source_schema.update(
            required=[
                "file_behavior_bpod"
            ],
            properties=dict(
                file_behavior_bpod=dict(
                    type="string",
                    format="file",
                    description="path to bpod data file"

                )
            )
        )
        return source_schema

    def run_conversion(self, nwbfile: NWBFile, metadata: dict):
        """
        Run conversionfor the custom Bpod data interface.

        Parameters
        ----------
        nwbfile : NWBFile
        metadata : dict
        """
        # Opens .mat file and extracts data
        fdata = loadmat(
            self.source_data['file_behavior_bpod'],
            struct_as_record=False,
            squeeze_me=True
        )

        # Summarized trials data
        n_trials = fdata['SessionData'].nTrials
        trials_start_times = fdata['SessionData'].TrialStartTimestamp
        trials_end_times = fdata['SessionData'].TrialEndTimestamp
        trials_types = fdata['SessionData'].TrialTypes
        trials_led_types = fdata['SessionData'].LEDTypes
        trials_reaching = fdata['SessionData'].Reaching
        trials_outcome = getattr(fdata['SessionData'], 'Outcome', ['no outcome'] * n_trials)

        # Raw data - states
        trials_states_names_by_number = fdata['SessionData'].RawData.OriginalStateNamesByNumber
        all_trials_states_names = np.unique(np.concatenate(trials_states_names_by_number, axis=0))
        trials_states_numbers = fdata['SessionData'].RawData.OriginalStateData
        trials_states_timestamps = fdata['SessionData'].RawData.OriginalStateTimestamps
        trials_states_durations = [np.diff(dur) for dur in trials_states_timestamps]

        # Add trials columns
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
        nwbfile.add_acquisition(Events(
            name='Port1In',
            description='no description',
            timestamps=port_1_in_ts
        ))
        nwbfile.add_acquisition(Events(
            name='Port1Out',
            description='no description',
            timestamps=port_1_out_ts
        ))
        nwbfile.add_acquisition(Events(
            name='Port2In',
            description='no description',
            timestamps=port_2_in_ts
        ))
        nwbfile.add_acquisition(Events(
            name='Port2Out',
            description='no description',
            timestamps=port_2_out_ts
        ))
        nwbfile.add_acquisition(Events(
            name='Tup',
            description='no description',
            timestamps=tup_ts
        ))
