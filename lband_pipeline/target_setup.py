
'''
Per target or calibrator ranges to avoid.

For targets, this is used in the creation of the cont.dat file.

For calibrators, this is mostly needed to flag absorption on the
bandpass and other calibration steps.

TODO: Define a restricted velocity range for each FIELD. This allows a much
smaller range to be flagged instead of the whole galaxy range (e.g., M31).

'''

# These shouldn't change, so just hard-code in for our targets.
target_line_range = {}


# Velocities are in km/s in the LSRK frame.

# --------------------------------------------------------------
# M31

target_line_range['M31'] = {}
# Based on EBHIS M31 map: CAR_C01.fits. And our archival D-config HI map from 14A-235.
# Also excludes MW foreground.
target_line_range['M31']['HI'] = [[-625, 50]]

# Limited to "bright" HI extent of M31
# For the 4 MHz SPWs, there's still 25% outside this region.
target_line_range['M31']['OH'] = [[-600, -20]]


# --------------------------------------------------------------
# M33

target_line_range['M33'] = {}

target_line_range['M33']['HI'] = [[-340, 40]]

target_line_range['M33']['OH'] = [[-280, -50]]

# --------------------------------------------------------------
# IC10

target_line_range['IC10'] = {}

target_line_range['IC10']['HI'] = [[-450, -240], [-140, 50]]

target_line_range['IC10']['OH'] = [[-410, -270]]


# --------------------------------------------------------------
# IC1613

target_line_range['IC1613'] = {}

# target_line_range['IC1613']['HI'] = [-290, -170]
# Include all foreground MW HI?
target_line_range['IC1613']['HI'] = [[-290, -170], [-60, 50]]


target_line_range['IC1613']['OH'] = [[-260, -200]]


# --------------------------------------------------------------
# WLM

target_line_range['WLM'] = {}

# target_line_range['WLM']['HI'] = [-210, -50]
# Include all foreground MW HI?
target_line_range['WLM']['HI'] = [[-210, -50], [-40, 50]]

target_line_range['WLM']['OH'] = [[-180, -70]]


# --------------------------------------------------------------
# NGC 6822

target_line_range['NGC6822'] = {}

# Include all foreground MW HI?
target_line_range['NGC6822']['HI'] = [[-150, 80]]

target_line_range['NGC6822']['OH'] = [[-120, -10]]


# Add in regions to skip for the different calibrators.
calibrator_line_range = {}

