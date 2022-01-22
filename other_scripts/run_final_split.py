
import sys

from casatasks import listobs

from lband_pipeline.spw_setup import (create_spw_dict)
from lband_pipeline.ms_split_tools import split_ms_final_all


myvis = sys.argv[-1]

spw_dict = create_spw_dict(myvis, save_spwdict=False)


# --------------------------------
# Split the calibrated column out into target and calibrator parts.
# --------------------------------

# Keep flags if continuum (to maintain the SPW structure for awproject imaging)
# For lines, don't keep flags.
if "continuum" in myvis:
    keep_flags = True
elif "speclines" in myvis:
    keep_flags = False
else:
    raise ValueError(f"Unsure of the type of data in MS: {myvis}")

split_ms_final_all(myvis,
                   spw_dict,
                   data_column='CORRECTED',
                   target_name_prefix="",
                   time_bin='0s',
                   keep_flags=keep_flags,
                   overwrite=False)

listobs(f"{myvis}.split")
listobs(f"{myvis}.split_calibrators")
