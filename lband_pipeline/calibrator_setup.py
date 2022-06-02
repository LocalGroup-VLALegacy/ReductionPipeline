
'''
Per calibrator spectral ranges to avoid.

For calibrators, this is mostly needed to flag absorption on the
bandpass and other calibration steps.

'''

import configparser
import os


def read_calibrator_absorption_cfg(filename='../config_files/lglbs_calibrators.cfg'):

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


calibrator_line_range_kms = read_calibrator_absorption_cfg(filename='../config_files/lglbs_calibrators.cfg')
