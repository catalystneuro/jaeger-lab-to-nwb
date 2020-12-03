from nwb_conversion_tools.basedatainterface import BaseDataInterface
from nwb_conversion_tools.utils import get_schema_from_hdmf_class
from nwb_conversion_tools.json_schema_utils import get_base_schema

from pynwb import NWBFile, TimeSeries
from datetime import datetime
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
        return metadata_schema

    def get_metadata(self):
        metadata = dict()
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
        
