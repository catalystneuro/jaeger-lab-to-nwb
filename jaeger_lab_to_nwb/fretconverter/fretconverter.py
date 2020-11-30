from nwb_conversion_tools import NWBConverter
from .fretdatainterface import FRETDataInterface
from scipy.io import loadmat
from pathlib import Path
import yaml
from datetime import datetime


class JaegerFRETConverter(NWBConverter):
    data_interface_classes = dict(
        FRETDataInterface=FRETDataInterface
    )

    def get_metadata(self):
        """Fetch metadata"""
        # Initialize metadata from yaml file
        metadata_path = Path(__file__).parent.absolute() / 'metafile.yml'
        with open(metadata_path) as f:
            metadata = yaml.safe_load(f)

        return metadata
