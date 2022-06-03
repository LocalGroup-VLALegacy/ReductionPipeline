
'''
Read the the master_config.cfg to identify the other config filenames.
'''

import configparser
from doctest import master
import os

def get_master_config():

    # Try finding the filename defined in the master_config file.
    filename = os.path.join(os.path.dirname(__file__), "..", "config_files", "master_config.cfg")

    if not os.path.exists(filename):
        raise OSError(f"Unable to find filename: {filename}")

    config = configparser.RawConfigParser()
    # This keeps the case of the line names (e.g. HI vs hi)
    config.optionxform = str

    config.read(filename)

    return config


def read_calibrator_absorption_cfg(filename=None):
    '''
    Read in the config file with absorption velocity ranges defined for calibrator sources.


    Parameters
    ----------
    filename : str, None
        Override the filename defined by `calibrators_filename` in the master configuration file.
    '''

    master_config = get_master_config()

    if filename is None:
        filename = os.path.join(os.path.dirname(__file__), "..", "config_files",
                                master_config['source_configs']['calibrators_filename'])

    if not os.path.exists(filename):
        raise OSError(f"Unable to find filename: {filename}")

    config = configparser.RawConfigParser()
    # This keeps the case of the line names (e.g. HI vs hi)
    config.optionxform = str

    config.read(filename)

    def get_config_section():
        if not hasattr(get_config_section, 'section_dict'):
            get_config_section.section_dict = {}

            for section in config.sections():
                get_config_section.section_dict[section] = dict(config.items(section))

        return get_config_section.section_dict

    out_dict = get_config_section()

    # Check expected format
    for source in out_dict:
        for line in out_dict[source]:
            vrange = [float(val) for val in out_dict[source][line].replace(" ", "").split(",")]
            out_dict[source][line] = vrange

    return out_dict



def read_target_vsys_cfg(filename=None):
    '''
    Read in the config file with the target Vsys values.


    Parameters
    ----------
    filename : str, None
        Override the filename defined by `calibrators_filename` in the master configuration file.
    '''

    master_config = get_master_config()

    if filename is None:
        filename = os.path.join(os.path.dirname(__file__), "..", "config_files",
                                master_config['source_configs']['targets_vsys_filename'])


    if not os.path.exists(filename):
        raise OSError(f"Unable to find filename: {filename}")

    config = configparser.RawConfigParser()
    # This keeps the case of the line names (e.g. HI vs hi)
    config.optionxform = str

    config.read(filename)

    def get_config_section():
        if not hasattr(get_config_section, 'section_dict'):
            get_config_section.section_dict = {}

            for section in config.sections():
                get_config_section.section_dict[section] = dict(config.items(section))

        return get_config_section.section_dict

    out_dict = get_config_section()

    assert "target_vsys_kms" in out_dict

    # Check expected format
    for source in out_dict['target_vsys_kms']:
        out_dict['target_vsys_kms'][source] = float(out_dict['target_vsys_kms'][source])

    return out_dict['target_vsys_kms']


def read_targets_vrange_cfg(filename=None):

    if not os.path.exists(filename):
        raise OSError(f"Unable to find filename: {filename}")

    config = configparser.RawConfigParser()
    # Keep case sensitive when reading
    config.optionxform = str

    config.read(filename)

    def get_config_section():
        if not hasattr(get_config_section, 'section_dict'):
            get_config_section.section_dict = {}

            for section in config.sections():
                get_config_section.section_dict[section] = dict(config.items(section))

        return get_config_section.section_dict

    out_dict = get_config_section()

    # Check expected format
    for source in out_dict:
        for line in out_dict[source]:
            vrange = [float(val) for val in out_dict[source][line].replace(" ", "").split(",")]

            # Make a nested loop in groups of 2. This supportws specifying multiple protected
            # ranges.
            if len(vrange) % 2 != 0:
                raise ValueError(f"vrange must have pairs of values specifying vhigh,vlow."
                                 f" Given {vrange} for {line} and {source}")

            npairs = len(vrange) // 2

            vrange_pairs = []
            for ii in range(npairs):
                vrange_pairs.append([vrange[2*ii], vrange[2*ii+1]])

            out_dict[source][line] = vrange_pairs

    return out_dict
