
import sys
import os
from glob import glob
import shutil
import numpy as np

# Additional QA plotting routines
from lband_pipeline.qa_plotting import (make_spw_bandpass_plots,
                                        make_qa_scan_figures,
                                        make_qa_tables,
                                        make_bandpass_txt,
                                        run_all_uvstats)

# Function for altering the standard pipeline for spectral lines
# 1. Flag HI frequencies due to MW absorption
# 2. interpolation over BP with MW HI aborption
# 3. Build `cont.dat` to protect line range with signal
from lband_pipeline.line_tools import (bandpass_with_gap_interpolation,
                                       flag_hi_foreground,
                                       build_cont_dat)

# Info for SPW setup
from lband_pipeline.spw_setup import create_spw_dict, linerest_dict_GHz

# Protected velocity range for different targets
# Used to build `cont.dat` for line SPWs
from lband_pipeline.target_setup import target_line_range_kms

# For MW HI absorption flagging on calibrators:
from lband_pipeline.calibrator_setup import calibrator_line_range_kms

# Handle runs where the internet query to the baseline correction site will
# fail
from lband_pipeline.offline_antposn_corrections import make_offline_antpos_table

# TODO: read in to skip a refant if needed.
refantignore = ""

mySDM = sys.argv[-1]
myvis = mySDM if mySDM.endswith("ms") else mySDM + ".ms"

# Tracks should follow the VLA format, starting with the project code
proj_code = mySDM.split(".")[0]

# Get the SPW mapping for the line MS.

linespw_dict = create_spw_dict(myvis)

# Identify which SPW is the HI line
hi_spw = None
for spwid in linespw_dict:
    if linespw_dict[spwid]['label'] == "HI":
        hi_spw = spwid
        break

if hi_spw is None:
    raise ValueError("Unable to identify the HI SPW.")

products_folder = "products"

__rethrow_casa_exceptions = True


# Check if there's an existing pipeline run. If so, check status to
# restart at last position:
context_files = glob("pipeline*.context")
if len(context_files) > 0:

    # Will open the most recent context file
    context = h_resume()

    # Get pipeline calls:
    callorder = ['hifv_importdata',
                 'hifv_flagdata',
                 'hifv_vlasetjy',
                 'hifv_priorcals',
                 'hifv_testBPdcals',
                 'hifv_flagbaddef',
                 'hifv_checkflag',
                 'hifv_semiFinalBPdcals',
                 'hifv_checkflag',
                 'hifv_semiFinalBPdcals',
                 'hifv_solint',
                 'hifv_fluxboot2',
                 'hifv_finalcals',
                 'hifv_applycals',
                 'hifv_targetflag',
                 'hifv_statwt',
                 'hifv_plotsummary',
                 'hif_makeimlist',
                 'hif_makeimages',
                 'hifv_exportdata']

    # Get existing order to match with the call order:
    current_callorder = [result.read().pipeline_casa_task.split("(")[0] for result in context.results]

    # Make sure the order is what we expect
    matching_calls = np.array(current_callorder) == np.array(callorder[:len(current_callorder)])

    if not matching_calls.all():
        raise ValueError("Call order not expected for this script: Expected: {0}\nFound: {1}"
                         .format(callorder[:len(current_callorder)], current_callorder))

    # Do we just need to make additional QA plots?
    # i.e. the calibration did finish
    if len(current_callorder) == len(callorder):
        skip_pipeline = True

        restart_stage = len(callorder) + 1

        casalog.post("Calibration pipeline completed. Running QA plots only.")


    # Otherwise start from the next stage
    else:
        skip_pipeline = False

        restart_stage = len(callorder) + 1

        casalog.post("Restarting at stage: {0} {1}".format(restart_stage, callorder[restart_stage]))

# Otherwise this is a fresh run:
else:
    casalog.post("No context file found. Starting new pipeline run.")

    context = h_init()

    restart_stage = 0

    skip_pipeline = False

context.set_state('ProjectSummary', 'observatory',
                  'Karl G. Jansky Very Large Array')
context.set_state('ProjectSummary', 'telescope', 'EVLA')
context.set_state('ProjectSummary', 'proposal_code', proj_code)
context.set_state('ProjectSummary', 'piname', 'Adam Leroy')

if not skip_pipeline:

    try:

        if restart_stage == 0:

            hifv_importdata(ocorr_mode='co',
                            nocopy=False,
                            vis=[myvis],
                            createmms='automatic',
                            asis='Receiver CalAtmosphere',
                            overwrite=False)

        if not os.path.exists("cont.dat"):
            # Create cont.dat file based on the target name.
            build_cont_dat(myvis,
                        target_line_range_kms,
                        line_freqs=linerest_dict_GHz,
                        fields=[],  # Empty list == all target fields
                        outfile="cont.dat",
                        overwrite=False,
                        append=False)

        if restart_stage < 1:
            flag_hi_foreground(myvis,
                            calibrator_line_range_kms,
                            hi_spw,
                            cal_intents=["CALIBRATE*"],
                            test_run=False,
                            test_print=True)

            # Hanning smoothing is turned off for spectral lines.
            # hifv_hanning(pipelinemode="automatic")

            hifv_flagdata(intents='*POINTING*,*FOCUS*,*ATMOSPHERE*,*SIDEBAND_RATIO*, \
                        *UNKNOWN*, *SYSTEM_CONFIGURATION*, \
                        *UNSPECIFIED#UNSPECIFIED*',
                        flagbackup=False,
                        scan=True,
                        baseband=True,
                        clip=True,
                        autocorr=True,
                        hm_tbuff='1.5int',
                        template=True,
                        # TODO: ensure we consistently use the same filename
                        filetemplate="additional_flagging.txt",
                        online=False,
                        tbuff=0.0,
                        fracspw=0.05,
                        shadow=True,
                        quack=True,
                        edgespw=True)

        if restart_stage < 2:
            hifv_vlasetjy(fluxdensity=-1,
                        scalebychan=True,
                        reffreq='1GHz',
                        spix=0)

        if restart_stage < 3:
            hifv_priorcals(tecmaps=False)

            # Check offline tables (updated before each run) for antenna corrections
            # If the online tables were accessed and the correction table already exists,
            # skip remaking.
            make_offline_antpos_table(myvis,
                                    data_folder="VLA_antcorr_tables",
                                    skip_existing=True)

        if restart_stage < 4:
            hifv_testBPdcals(weakbp=False,
                            refantignore=refantignore)

            # We need to interpolate over MW absorption in the bandpass
            # These channels should be flagged in the calibrators.

            bandpass_with_gap_interpolation(myvis, hi_spw,
                                            search_string="test",
                                            task_string="hifv_testBPdcals")

        if restart_stage < 5:
            hifv_flagbaddef(pipelinemode="automatic")

        if restart_stage < 6:
            hifv_checkflag(pipelinemode="automatic")

        if restart_stage < 7:
            hifv_semiFinalBPdcals(weakbp=False,
                                refantignore=refantignore)

        if restart_stage < 8:
            hifv_checkflag(checkflagmode='semi')

        if restart_stage < 9:
            hifv_semiFinalBPdcals(weakbp=False,
                                refantignore=refantignore)

            bandpass_with_gap_interpolation(myvis, hi_spw,
                                            search_string='',
                                            task_string='hifv_semiFinalBPdcals')

        if restart_stage < 10:
            hifv_solint(pipelinemode="automatic",
                        refantignore=refantignore)

        if restart_stage < 11:
            hifv_fluxboot2(pipelinemode="automatic",
                        refantignore=refantignore)

        if restart_stage < 12:
            hifv_finalcals(weakbp=False,
                        refantignore=refantignore)

            bandpass_with_gap_interpolation(myvis, hi_spw,
                                            search_string='final',
                                            task_string='hifv_finalcals')

        if restart_stage < 13:
            hifv_applycals(flagdetailedsum=True,
                        gainmap=False,
                        flagbackup=True,
                        flagsum=True)

        # Keep the following step in the script if cont.dat exists.
        # Remove RFI flagging the lines in target fields.
        if restart_stage < 14:
            if os.path.exists('cont.dat'):
                hifv_targetflag(intents='*CALIBRATE*, *TARGET*')
            else:
                hifv_targetflag(intents='*CALIBRATE*')

        if restart_stage < 15:
            hifv_statwt(pipelinemode="automatic")

        if restart_stage < 16:
            hifv_plotsummary(pipelinemode="automatic")

        if restart_stage < 17:
            # TODO: Choose a representative target field to image?
            hif_makeimlist(nchan=-1,
                        calmaxpix=300,
                        intent='PHASE,BANDPASS')

        if restart_stage < 18:
            hif_makeimages(tlimit=2.0,
                        hm_minbeamfrac=-999.0,
                        hm_dogrowprune=True,
                        hm_negativethreshold=-999.0,
                        calcsb=False,
                        target_list={},
                        hm_noisethreshold=-999.0,
                        hm_masking='none',
                        hm_minpercentchange=-999.0,
                        parallel='automatic',
                        masklimit=4,
                        hm_lownoisethreshold=-999.0,
                        hm_growiterations=-999,
                        cleancontranges=False,
                        hm_sidelobethreshold=-999.0)

        if restart_stage < 19:
            # Make a folder of products for restoring the pipeline solution
            if not os.path.exists(products_folder):
                os.mkdir(products_folder + '/')

            # TODO: review whether we should be including additional products
            # here
            hifv_exportdata(products_dir=products_folder + '/')

    finally:

        h_save()

# Make a new directory for the imaging outputs
# Not required. I just like cleaning up the folder a bit.
if not os.path.exists("image_outputs"):
    os.mkdir("image_outputs")

image_files = glob("oussid*")

for fil in image_files:
    shutil.move(fil, "image_outputs/")

# ----------------------------
# Now make additional QA plots:
# -----------------------------

text_output = True

if text_output:
    make_bandpass_txt(myvis, output_folder='finalBPcal_txt')

    make_qa_tables(myvis,
                   output_folder='scan_plots_txt',
                   outtype='txt', overwrite=True,
                   chanavg=4096,)

    # Move these folders to the products folder.
    os.system("cp -r {0} {1}".format('finalBPcal_txt', products_folder))
    os.system("cp -r {0} {1}".format('scan_plots_txt', products_folder))

else:

    make_spw_bandpass_plots(myvis,
                            bp_folder="finalBPcal_plots",
                            outtype='png')

    make_qa_scan_figures(myvis,
                         output_folder='scan_plots',
                         outtype='png')

    # Move these folders to the products folder.
    os.system("cp -r {0} {1}".format('finalBPcal_plots', products_folder))
    os.system("cp -r {0} {1}".format('scan_plots', products_folder))

# Make detailed uvresid plots.
# These are to check if any calibrators have source structure not accounted for.
# In that case, a flux.csv file needs to be provided for a subsequent pipeline run

uvresid_path = "uvresid_plots"

run_all_uvstats(myvis, uvresid_path,
                uv_threshold=3, uv_nsigma=3,
                try_phase_selfcal=True,
                cleanup_calsplit=True,
                cleanup_phaseselfcal=True)

# We're cleaning up the other data products to make these plots.
# So just copy the whole folder over.
os.system("cp -r {0} {1}".format(uvresid_path, products_folder))


# Copy and zip into the pipeline products output.

# Zip, tag, and rename the products folder to copy out on completion.
