
'''
Vsys for our targets.

Per target spectral ranges to avoid.

For targets, this is used in the creation of the cont.dat file.

TODO: Define a restricted velocity range for each FIELD. This allows a much
smaller range to be flagged instead of the whole galaxy range (e.g., M31).

'''

from casatools import logsink

casalog = logsink()

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
