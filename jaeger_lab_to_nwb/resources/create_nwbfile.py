from pynwb import NWBFile
from pynwb.file import Subject


def create_nwbfile(metadata):
    """Creates a new NWBFile object with specific metadata information."""

    # Initialize a NWB object
    nwbfile = NWBFile(**metadata['NWBFile'])

    # Add subject metadata
    if 'Subject' in metadata:
        experiment_subject = Subject(**metadata['Subject'])
        nwbfile.subject = experiment_subject

    return nwbfile
