
'''
Per calibrator spectral ranges to avoid.

For calibrators, this is mostly needed to flag absorption on the
bandpass and other calibration steps.

'''

# Add in regions to skip for the different calibrators.
calibrator_line_range_kms = {}


# Velocities are in km/s in the LSRK frame.

# --------------------------------------------------------------
# 3C48
# Fairly weak absorption, mostly from 0 to -40 km /s
calibrator_line_range_kms['3C48'] = {}
calibrator_line_range_kms['3C48']['HI'] = [50, -50]


# --------------------------------------------------------------
# 3C138
# Pol angle / backup flux/BP cal
# Strong absorption from 60 to -40 km/s
calibrator_line_range_kms['3C138'] = {}
calibrator_line_range_kms['3C138']['HI'] = [70, -70]


# --------------------------------------------------------------
# J0029+3456
# M31 phase cal. (at least C/D-config)
# Strong absorption from ~12 to -30 km/s
calibrator_line_range_kms['J0029+3456'] = {}
calibrator_line_range_kms['J0029+3456']['HI'] = [30, -50]


# --------------------------------------------------------------
# J0038+4137
# M31 phase cal. (at least C/D-config)
# No strong absorption. Pick fairly narrow region to be safe.
calibrator_line_range_kms['J0038+4137'] = {}
calibrator_line_range_kms['J0038+4137']['HI'] = [30, -30]

# --------------------------------------------------------------
# J0319+4130
# Pol leakage (at least C/D-config)
# Strong absorption from 30 to -40 km/s
calibrator_line_range_kms['J0319+4130'] = {}
calibrator_line_range_kms['J0319+4130']['HI'] = [50, -60]
