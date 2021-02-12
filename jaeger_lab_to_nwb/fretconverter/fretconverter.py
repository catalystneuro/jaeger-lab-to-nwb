from nwb_conversion_tools import NWBConverter
from nwb_conversion_tools.json_schema_utils import dict_deep_update
from .fretdatainterface import FRETDataInterface
from pathlib import Path
import yaml


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

        metadata = dict_deep_update(metadata, self.data_interface_objects['FRETDataInterface'].get_metadata())

        return metadata
