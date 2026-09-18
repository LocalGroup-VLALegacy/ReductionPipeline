
'''
Vsys for our targets.

Per target spectral ranges to avoid.

For targets, this is used in the creation of the cont.dat file.

TODO: Define a restricted velocity range for each FIELD. This allows a much
smaller range to be flagged instead of the whole galaxy range (e.g., M31).

'''

from lband_pipeline.read_config_files import read_target_vsys_cfg

from casatools import logsink

casalog = logsink()

# Function to identify the target from field names in the MS

def identify_targets(vis, fields=None, raise_missing_target=True):
    '''
    Identify every target in the MS that matches target_line_range_kms keys.

    A track can hold more than one science galaxy, so this returns a list.
    Use `identify_target` when a single name is needed.
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
        return []

    # Match targets with the galaxies. Names should be unique enough to do this
    thisgals = []

    target_vsys_kms = read_target_vsys_cfg()

    for field in fields:

        for gal in target_vsys_kms:
            if gal in field:
                if gal not in thisgals:
                    thisgals.append(gal)
                break

    # Check for match after looping through all fields.
    if len(thisgals) == 0:
        if raise_missing_target:
            casalog.post("Unable to match fields to expected galaxy targets: {0}".format(fields))
            raise ValueError("Unable to match fields to expected galaxy targets: {0}".format(fields))

    return thisgals


def identify_target(vis, fields=None, raise_missing_target=True):
    '''
    Identify the target in the MS that matches target_line_range_kms keys.

    Returns the first match. See `identify_targets` for tracks with more than
    one science galaxy.
    '''

    thisgals = identify_targets(vis, fields=fields,
                                raise_missing_target=raise_missing_target)

    if len(thisgals) == 0:
        return None

    return thisgals[0]
