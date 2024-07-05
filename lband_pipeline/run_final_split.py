
import sys
import os

import numpy as np

from lband_pipeline.ms_split_tools import split_ms_final_all
from lband_pipeline.spw_setup import create_spw_dict


mySDM = sys.argv[-1]
myvis = mySDM if mySDM.endswith("ms") else mySDM + ".ms"

output_path = sys.argv[-2]

spwdict_filename = "spw_definitions.npy"

if os.path.exists(spwdict_filename):
    spw_dict = np.load(spwdict_filename, allow_pickle=True).item()
else:
    spw_dict = create_spw_dict(myvis, save_spwdict=False)

# --------------------------------
# Split the calibrated column out into target and calibrator parts.
# --------------------------------
split_ms_final_all(myvis,
                   spw_dict,
                   data_column='CORRECTED',
                   target_name_prefix="",
                   time_bin='0s',
                   keep_flags=True,
                   overwrite=False,
                   output_path=output_path)
