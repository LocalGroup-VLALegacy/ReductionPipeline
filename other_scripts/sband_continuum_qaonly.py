
'''
Additional QA plotting products only.
Expects that the VLA pipeline has already been run, including the optional hifv_exportdata.
See continuum_pipeline.py for an example
'''


import sys
import os

# Additional QA plotting routines
from lband_pipeline.qa_plotting import (make_qa_tables,
                                        run_all_uvstats,
                                        make_all_caltable_txt,
                                        make_all_flagsummary_data)

# Info for SPW setup
from lband_pipeline.spw_setup import (create_spw_dict)

# Quicklook imaging
from lband_pipeline.quicklook_imaging import quicklook_continuum_imaging


# Command line inputs.

mySDM = sys.argv[-1]
myvis = mySDM if mySDM.endswith("ms") else mySDM + ".ms"

# Get the SPW mapping for the continuum MS.
spwdict_filename = "spw_definitions.npy"
contspw_dict = create_spw_dict(myvis,
                               continuum_only=True,
                               save_spwdict=True,
                               spwdict_filename=spwdict_filename)

# --------------------------------
# Make quicklook images of targets
# --------------------------------
run_quicklook = True

# Run dirty imaging only for a quicklook
if run_quicklook:
    # NOTE: We will attempt a very light clean as it can really highlight
    # which SPWs have significant RFI.
    # TODO: Need to check how much added time this results in for A/B config.
    quicklook_continuum_imaging(myvis, contspw_dict,
                                niter=0, nsigma=5.)

# ----------------------------
# Now make additional QA plots:
# -----------------------------

# Hard-code in making txt files
text_output = True

if text_output:

    make_all_caltable_txt(myvis)

    make_qa_tables(myvis,
                   output_folder='scan_plots_txt',
                   outtype='txt',
                   overwrite=False,
                   chanavg=4096,)


###
### In a normal python environment, run qaplotter to create interactive plots
### Install QAPlotter with `pip install -e .` from the repository here: https://github.com/LocalGroup-VLALegacy/QAPlotter
### import qaplotter
### qaplotter.make_all_plots(msname=myvis)
###

### Define a flag file txt file (https://casadocs.readthedocs.io/en/stable/api/tt/casatasks.flagging.flagdata.html#inpfile)
### e.g. https://github.com/e-koch/VLA_Lband/blob/master/17B-162/pipeline_scripts/track_flagging/17B-162_09_23_17_continuum_flags.txt
### Pass to hifv_flagdata with the `filetemplate` kwarg (https://github.com/LocalGroup-VLALegacy/ReductionPipeline/blob/main/lband_pipeline/continuum_pipeline.py#L203)
### If flagging required on the calibrators, re-run the pipeline from the original SDM.
### If flagging only on the target, apply flags with `flagdata` and continue to imaging.

