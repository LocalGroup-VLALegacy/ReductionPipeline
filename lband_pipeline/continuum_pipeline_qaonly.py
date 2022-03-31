
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
contspw_dict = create_spw_dict(myvis, save_spwdict=True,
                               spwdict_filename=spwdict_filename)

# Created by hifv_exportdata. Must exist to run!
products_folder = "products"

if not os.path.exists(products_folder):
    raise ValueError("QAPlotter expects the product directory created by hifv_exportdata."
                     " Run hifv_exportdata in the pipeline first."
                     " If you don't need QAPlotter, comment this exception out.")

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

    os.system("cp -r {0} {1}".format('quicklook_imaging', products_folder))

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

    # make_all_flagsummary_data(myvis, output_folder='perfield_flagfraction_txt')

    # Move these folders to the products folder.
    os.system("cp -r {0} {1}".format('final_caltable_txt', products_folder))
    os.system("cp -r {0} {1}".format('scan_plots_txt', products_folder))
    # os.system("cp -r {0} {1}".format('perfield_flagfraction_txt', products_folder))


# Make detailed uvresid plots.
# These are to check if any calibrators have source structure not accounted for.
# In that case, a flux.csv file needs to be provided for a subsequent pipeline run

uvresid_path = "uvresid_plots"

# Skip re-run if the folder already exists:
if not os.path.exists(uvresid_path):

    run_all_uvstats(myvis, uvresid_path,
                    uv_threshold=3, uv_nsigma=3,
                    try_phase_selfcal=True,
                    cleanup_calsplit=True,
                    cleanup_phaseselfcal=True)

    # We're cleaning up the other data products to make these plots.
    # So just copy the whole folder over.
    os.system("cp -r {0} {1}".format(uvresid_path, products_folder))

else:
    casalog.post("Found existing uvresidual checks. Skipping.")


casalog.post("Finished! To create interactive figures, run QAPlotter in the products"
             " directory.")
