
'''
Vsys for our targets.

Per target spectral ranges to avoid.

For targets, this is used in the creation of the cont.dat file.

TODO: Define a restricted velocity range for each FIELD. This allows a much
smaller range to be flagged instead of the whole galaxy range (e.g., M31).

'''

import configparser
import os

from casatools import logsink

casalog = logsink()


def read_target_vsys_cfg(filename='../config_files/lglbs_targets_vsys.cfg'):

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


def read_targets_vrange_cfg(filename='../config_files/lglbs_targets_vrange.cfg'):

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


# These shouldn't change, so just hard-code in for our targets.
target_vsys_kms = read_target_vsys_cfg(filename='../config_files/lglbs_targets_vsys.cfg')

target_line_range_kms = read_targets_vrange_cfg(filename='../config_files/lglbs_targets_vrange.cfg')


# Function to identify the target from field names in the MS

def identify_target(vis, fields=None, raise_missing_target=True):
    '''
    Identify the target in the MS that matches target_line_range_kms keys.
    '''

    if fields is None:
        fields = []

    from casatools import ms

    myms = ms()

    # if no fields are provided use observe_target intent
    # I saw once a calibrator also has this intent so check carefully
    # mymsmd.open(vis)
    myms.open(vis)

    mymsmd = myms.metadata()

    if len(fields) < 1:
        fields = mymsmd.fieldsforintent("*TARGET*", True)

    mymsmd.close()
    myms.close()

    if len(fields) < 1:
        casalog.post("ERROR: no fields given to identify.")
        return

    # Match target with the galaxy. Names should be unique enough to do this
    thisgal = None

    # generate a dictonary containing continuum chunks for every spw of every field
    for field in fields:

        for gal in target_line_range_kms:
            if gal in field:
                thisgal = gal
                break

    # Check for match after looping through all fields.
    if thisgal is None:
        if raise_missing_target:
            casalog.post("Unable to match fields to expected galaxy targets: {0}".format(fields))
            raise ValueError("Unable to match fields to expected galaxy targets: {0}".format(fields))


    return thisgal
