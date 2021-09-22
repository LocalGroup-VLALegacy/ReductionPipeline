
'''
Vsys for our targets.

Per target spectral ranges to avoid.

For targets, this is used in the creation of the cont.dat file.

TODO: Define a restricted velocity range for each FIELD. This allows a much
smaller range to be flagged instead of the whole galaxy range (e.g., M31).

'''

from casatools import logsink

casalog = logsink()


# km/s in LSRK
target_vsys_kms = {"M31": -296.,
                   "M33": -180.,
                   "NGC604": -180.,
                   "M33_Sarm": -180.,
                   "NGC6822": -44.,
                   "WLM": -122.,
                   "Wolf-Lundmark-": -122.,
                   "IC10": -340.,
                   "IC1613": -238.}


# These shouldn't change, so just hard-code in for our targets.
target_line_range_kms = {}


# Velocities are in km/s in the LSRK frame.

# --------------------------------------------------------------
# M31

target_line_range_kms['M31'] = {}
# Based on EBHIS M31 map: CAR_C01.fits. And our archival D-config HI map from 14A-235.
# Also excludes MW foreground.
target_line_range_kms['M31']['HI'] = [[50, -625]]

# Limited to "bright" HI extent of M31
# For the 4 MHz SPWs, there's still 25% outside this region.
target_line_range_kms['M31']['OH'] = [[-20, -600]]


# --------------------------------------------------------------
# M33

target_line_range_kms['M33'] = {}

target_line_range_kms['M33']['HI'] = [[40, -340]]

target_line_range_kms['M33']['OH'] = [[-50, -280]]

# The 16B A-configuration projects use field names "NGC604" and "M33_Sarm"
# While only single fields in M33, we will just adopt a consistent
# velocity range:
target_line_range_kms['NGC604'] = {}

target_line_range_kms['NGC604']['HI'] = [[40, -340]]

target_line_range_kms['NGC604']['OH'] = [[-50, -280]]


target_line_range_kms['M33_Sarm'] = {}

target_line_range_kms['M33_Sarm']['HI'] = [[40, -340]]

target_line_range_kms['M33_Sarm']['OH'] = [[-50, -280]]

# --------------------------------------------------------------
# IC10

target_line_range_kms['IC10'] = {}

target_line_range_kms['IC10']['HI'] = [[50, -140], [-240, -450]]

target_line_range_kms['IC10']['OH'] = [[-270, -410]]


# --------------------------------------------------------------
# IC1613

target_line_range_kms['IC1613'] = {}

# target_line_range_kms['IC1613']['HI'] = [-290, -170]
# Include all foreground MW HI?
target_line_range_kms['IC1613']['HI'] = [[50, -60], [-170, -290]]


target_line_range_kms['IC1613']['OH'] = [[-200, -260]]


# --------------------------------------------------------------
# WLM

target_line_range_kms['WLM'] = {}

# Include all foreground MW HI?
target_line_range_kms['WLM']['HI'] = [[50, -40], [-50, -210]]

target_line_range_kms['WLM']['OH'] = [[-70, -180]]

# Use target name Wolf-Lundmark- for the 13A-213 tracks
target_line_range_kms['Wolf-Lundmark-'] = {}

# Include all foreground MW HI?
target_line_range_kms['Wolf-Lundmark-']['HI'] = [[50, -40], [-50, -210]]

target_line_range_kms['Wolf-Lundmark-']['OH'] = [[-70, -180]]


# --------------------------------------------------------------
# NGC 6822

target_line_range_kms['NGC6822'] = {}

# Include all foreground MW HI?
target_line_range_kms['NGC6822']['HI'] = [[80, -150]]

target_line_range_kms['NGC6822']['OH'] = [[-10, -120]]


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

    # generate a dictonary containing continuum chunks for every spw of every field
    for field in fields:

        # Match target with the galaxy. Names should be unique enough to do this
        thisgal = None
        for gal in target_line_range_kms:
            if gal in field:
                thisgal = gal
                break
        # Check for match
        if thisgal is None:
            if raise_missing_target:
                raise ValueError("Unable to match field {} to expected galaxy targets".format(field))
            else:
                casalog.post("Unable to match field {} to expected galaxy targets. Skipping.".format(field))
                continue

        return thisgal
