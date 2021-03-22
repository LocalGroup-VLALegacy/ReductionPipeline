
'''
Per calibrator spectral ranges to avoid.

For calibrators, this is mostly needed to flag absorption on the
bandpass and other calibration steps.

'''

# Add in regions to skip for the different calibrators.
calibrator_line_range_kms = {}


# Velocities are in km/s in the LSRK frame.

# --------------------------------------------------------------
# Flux/BP/delay calibrators
# --------------------------------------------------------------

# 3C48 (WLM; IC10; IC1613; M31; M33)
# Fairly weak absorption, mostly from 0 to -40 km /s
calibrator_line_range_kms['3C48'] = {}
calibrator_line_range_kms['3C48']['HI'] = [50, -50]

# 1331+305=3C286 (NGC6822)
# Also a polarization angle cal
# 3C286
# Fairly weak and narrow absorption lines.
calibrator_line_range_kms['3C286'] = {}
calibrator_line_range_kms['3C286']['HI'] = [30, -60]
calibrator_line_range_kms['1331+305=3C286'] = {}
calibrator_line_range_kms['1331+305=3C286']['HI'] = [30, -60]

# --------------------------------------------------------------
# Polarization angle calibrators
# --------------------------------------------------------------
# NOTE: 3C286 is listed above already

# 3C138 (IC10; IC1613; M31; WLM; M33)
# Pol angle / backup flux/BP cal
# Strong absorption from 60 to -40 km/s
calibrator_line_range_kms['3C138'] = {}
calibrator_line_range_kms['3C138']['HI'] = [70, -70]


# --------------------------------------------------------------
# Polarization leakage calibrators
# --------------------------------------------------------------
# J0319+4130 (M31; IC10; WLM; M33)
# Pol leakage (at least C/D-config)
# Strong absorption from 30 to -40 km/s
calibrator_line_range_kms['J0319+4130'] = {}
calibrator_line_range_kms['J0319+4130']['HI'] = [50, -60]

# J2355+4950 (IC1613)
# Pol leakage

# J1407+2827 (NGC6822)
# Pol leakage

# --------------------------------------------------------------
# Gain calibrators
# --------------------------------------------------------------
# NOTE: 3C48 is the gain cal for M33

# J0029+3456 (M31)
# Gain cal. (at least C/D-config)
# Strong absorption from ~12 to -30 km/s
calibrator_line_range_kms['J0029+3456'] = {}
calibrator_line_range_kms['J0029+3456']['HI'] = [30, -50]

# J0038+4137 (M31)
# Gain cal
# No strong absorption. Pick fairly narrow region to be safe.
calibrator_line_range_kms['J0038+4137'] = {}
calibrator_line_range_kms['J0038+4137']['HI'] = [30, -30]

# J0059+0006 (IC1613)
# Gain cal
# calibrator_line_range_kms['J0059+0006'] = {}
# calibrator_line_range_kms['J0059+0006']['HI'] = [0, 0]

# J1923-2104 (NGC6822)
# Gain cal
# calibrator_line_range_kms['J1923-2104'] = {}
# calibrator_line_range_kms['J1923-2104']['HI'] = [0, 0]

# J0102+5824 (IC10)
# Gain cal
# calibrator_line_range_kms['J0102+5824'] = {}
# calibrator_line_range_kms['J0102+5824']['HI'] = [0, 0]

# J2321-1623 (WLM)
# Gain cal
# calibrator_line_range_kms['J2321-1623'] = {}
# calibrator_line_range_kms['J2321-1623']['HI'] = [0, 0]
