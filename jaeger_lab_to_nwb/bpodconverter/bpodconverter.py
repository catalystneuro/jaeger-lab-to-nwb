from nwb_conversion_tools import NWBConverter
from .bpoddatainterface import BpodDataInterface
from scipy.io import loadmat
from pathlib import Path
import yaml
from datetime import datetime


class JaegerBpodConverter(NWBConverter):
    data_interface_classes = dict(
        BpodDataInterface=BpodDataInterface
    )

    def get_metadata(self):
        """Fetch metadat from bpod file"""
        # Initialize metadata from yaml file
        metadata_path = Path(__file__).parent.absolute() / 'metafile.yml'
        with open(metadata_path) as f:
            metadata = yaml.safe_load(f)

        # Opens .mat file and extracts metadata
        fdata = loadmat(
            self.data_interface_objects['BpodDataInterface'].source_data['file_behavior_bpod'],
            struct_as_record=False,
            squeeze_me=True
        )

        session_start_date = fdata['SessionData'].Info.SessionDate
        session_start_time = fdata['SessionData'].Info.SessionStartTime_UTC
        date_time_string = session_start_date + ' ' + session_start_time
        date_time_obj = datetime.strptime(date_time_string, '%d-%b-%Y %H:%M:%S')
        metadata['NWBFile']['session_start_time'] = date_time_obj

        return metadata
