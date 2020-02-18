from pynwb import NWBFile
from pynwb.file import Subject


def create_nwbfile(metadata):
    """Creates a new NWBFile object with specific metadata information."""
    # Initialize a NWB object
    nwbfile = NWBFile(**metadata['NWBFile'])

    # Add subject metadata
    experiment_subject = Subject(
        age=metadata['Subject']['age'],
        subject_id=metadata['Subject']['subject_id'],
        species=metadata['Subject']['species'],
        description=metadata['Subject']['description'],
        genotype=metadata['Subject']['genotype'],
        date_of_birth=metadata['Subject']['date_of_birth'],
        weight=metadata['Subject']['weight'],
        sex=metadata['Subject']['sex']
    )
    nwbfile.subject = experiment_subject

    return nwbfile
