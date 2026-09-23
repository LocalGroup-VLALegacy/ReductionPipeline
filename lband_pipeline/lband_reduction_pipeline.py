
'''
Unified L-band calibration pipeline for LGLBS.

Replaces the old three-job workflow (ms_split.py -> continuum_pipeline.py +
line_pipeline.py) with a single pass over the raw SDM. The VLA pipeline
(2025.1.0.36 / CASA 6.6.6-18) can now treat line and continuum SPWs differently
within one MS, so there is no reason to split them up front:

  - `hifv_importdata(specline_spws=...)` tags the spectral line windows,
  - `hifv_hanning(spws_to_smooth=...)` smooths only the continuum windows,
  - `cont.dat` protects the line ranges from `hifv_checkflag(target-vla)` and
    `hifv_statwt`.

The LGLBS-specific steps from `line_pipeline.py` are all kept: MW HI absorption
flagging on the calibrators, interpolation over the MW HI gap in the bandpass,
`cont.dat` construction from the per-target protected velocity ranges, extra
quacking, offline antenna position tables, the final target/calibrator splits,
quicklook imaging, and the QA text products.

The pipeline's own imaging stages (`hif_makeimlist` / `hif_makeimages`) are not
run; `quicklook_imaging` covers that.

Run as:
    casa --pipeline -c lband_reduction_pipeline.py <SDM_name>

from within the track folder, with the SDM untarred there.
'''

import sys
import os
import traceback
from glob import glob

# `casa --pipeline -c` injects casalog, but importing it explicitly keeps the
# script usable from an interactive CASA session too. The pipeline tasks
# (h_init/h_save/hifv_*) are only available in the pipeline namespace, so in a
# CASA shell this must be run with `run -i`, not `run`.
from casatasks import casalog

# Additional QA plotting routines
from lband_pipeline.qa_plotting import (make_qa_scan_figures,
                                        make_qa_tables,
                                        run_all_uvstats,
                                        make_all_caltable_txt,
                                        make_all_flagsummary_data)

# Functions for altering the standard pipeline for spectral lines
# 1. Flag HI frequencies due to MW absorption
# 2. interpolation over BP with MW HI aborption
# 3. Build `cont.dat` to protect line range with signal
from lband_pipeline.line_tools import (bandpass_with_gap_interpolation,
                                       flag_hi_foreground,
                                       build_cont_dat)

# Info for SPW setup
from lband_pipeline.spw_setup import (create_spw_dict, linerest_dict_GHz,
                                      continuum_spws_with_hi,
                                      line_spw_ids, continuum_spw_ids)

# SPW setup read from the SDM, before the MS exists.
from lband_pipeline.sdm_spw_setup import (create_spw_dict_from_sdm,
                                          compare_spw_dicts)

# Protected velocity range for different targets
# Used to build `cont.dat` for line SPWs
from lband_pipeline.target_setup import identify_targets

# For MW HI absorption flagging on calibrators:
from lband_pipeline.read_config_files import (read_calibrator_absorption_cfg,
                                              read_targets_vrange_cfg)

# Will read from the filenames defined in `config_files/master_config.cfg`
calibrator_line_range_kms = read_calibrator_absorption_cfg(filename=None)
target_line_range_kms = read_targets_vrange_cfg(filename=None)

# Handle runs where the internet query to the baseline correction site will
# fail
from lband_pipeline.offline_antposn_corrections import make_offline_antpos_table

from lband_pipeline.flagging_tools import flag_quack_integrations

from lband_pipeline.quicklook_imaging import (quicklook_line_imaging,
                                              quicklook_continuum_imaging)

from lband_pipeline.ms_split_tools import split_ms_final_all

# Check that DISPLAY is set. Otherwise, force an error
# We need DISPLAY set for plotms to export png or txt files.
if os.getenv('DISPLAY') is None:
    raise ValueError("DISPLAY is not set. Try using xvfb for remote systems.")

# Unset LD_LIBRARY_PATH. CASA isn't supposed to be using it anymore
os.environ['LD_LIBRARY_PATH'] = ""

# Read in to skip a refant if needed.
refant_ignore_filename = 'refant_ignore.txt'
if os.path.exists(refant_ignore_filename):
    with open(refant_ignore_filename, 'r') as file:
        refantignore = file.read().replace('\n', '')
else:
    refantignore = ""

mySDM = sys.argv[-1]

# The SDM name is given without a suffix. importasdm appends ".ms".
if mySDM.endswith(".ms"):
    raise ValueError("This pipeline runs on the raw SDM, not an MS. Given: {}".format(mySDM))

myvis = mySDM + ".ms"

# Tracks should follow the VLA format, starting with the project code
# e.g. 14B-088.sbXX.ebXX.mjd
proj_code = mySDM.split(".")[0]

spwdict_filename = "spw_definitions.npy"

products_folder = "products"

# Run the QA steps only when a previous run already exported the products.
# The job script deliberately invokes this file twice because repeated plotms
# calls become unreliable; the second call should not recalibrate.
#
# Completion is judged by the exported products plus a saved context, rather
# than by tracking each stage. `hifv_exportdata` writes all of these, so any
# one of them is enough to say the calibration finished.
export_markers = ["casa_piperestorescript.py",
                  "*pipeline_manifest.xml",
                  "*.calapply.txt"]

found_exports = any([len(glob(os.path.join(products_folder, this_marker))) > 0
                     for this_marker in export_markers])

skip_pipeline = found_exports and len(glob("pipeline*.context")) > 0

__rethrow_casa_exceptions = True

# ----------------------------------------------------------------------------
# Identify the SPWs from the SDM, before the MS is made.
#
# `hifv_importdata` needs `specline_spws` at import time and its 'auto' setting
# only looks at the number of channels. We require the line SPWs to be exactly
# the ones `create_spw_dict` identifies, so derive the same classification from
# the SDM and check it against the MS once the import has run.
# ----------------------------------------------------------------------------

if not skip_pipeline:
    sdm_spw_dict, sdm_target_sources = create_spw_dict_from_sdm(mySDM)

    specline_spw_str = ",".join([str(spwid) for spwid in line_spw_ids(sdm_spw_dict)])

    casalog.post("Spectral line SPWs identified from the SDM: {}".format(specline_spw_str))

    if len(specline_spw_str) == 0:
        raise ValueError("No spectral line SPWs identified in {}.".format(mySDM))

    context = h_init()

else:
    casalog.post("Found exported products. Running QA products only.")

    context = h_resume()

context.set_state('ProjectSummary', 'observatory',
                  'Karl G. Jansky Very Large Array')
context.set_state('ProjectSummary', 'telescope', 'EVLA')
context.set_state('ProjectSummary', 'proposal_code', proj_code)
context.set_state('ProjectSummary', 'piname', 'Adam Leroy')


if not skip_pipeline:

    try:

        hifv_importdata(vis=[mySDM],
                        specline_spws=specline_spw_str,
                        ocorr_mode='co',
                        nocopy=False,
                        createmms='automatic',
                        asis='Receiver CalAtmosphere',
                        overwrite=False)

        # --------------------------------------------------------------------
        # Check the SDM SPW identification against the MS that was just made.
        # A mismatch means `specline_spws` labelled the wrong windows, so stop
        # before any calibration is done.
        # --------------------------------------------------------------------
        spw_dict = create_spw_dict(myvis, save_spwdict=True,
                                   spwdict_filename=spwdict_filename)

        spw_mismatches = compare_spw_dicts(sdm_spw_dict, spw_dict)

        if len(spw_mismatches) > 0:
            for this_mismatch in spw_mismatches:
                casalog.post("SPW mismatch: {}".format(this_mismatch))

            raise ValueError("The SPWs identified from the SDM do not match the MS."
                             " `specline_spws` was set from the SDM, so the wrong windows"
                             " were tagged. Remove {0} and re-run.\n{1}"
                             .format(myvis, "\n".join(spw_mismatches)))

        # Identify which SPW is the HI line
        hi_spw = None
        for spwid in spw_dict:
            if "HI" in spw_dict[spwid]['label']:
                hi_spw = spwid
                break

        if hi_spw is None:
            raise ValueError("Unable to identify the HI SPW.")

        # Continuum SPWs that also cover the HI line. These need the same MW
        # absorption flagging on the calibrators.
        hi_spw_continuum = continuum_spws_with_hi(spw_dict)

        # Identify which of our targets are observed.
        thisgals = identify_targets(myvis)

        casalog.post("Identified targets: {}".format(thisgals))

        if not os.path.exists("cont.dat"):
            # Create cont.dat file based on the target name.
            # NOTE: the pipeline only runs hifv_checkflag(target-vla) and
            # hifv_statwt on the fields and SPWs listed here, so every target
            # field and every SPW must appear.
            build_cont_dat(myvis,
                           target_line_range_kms,
                           line_freqs=linerest_dict_GHz,
                           spw_dict=spw_dict,
                           fields=[],  # Empty list == all target fields
                           outfile="cont.dat",
                           overwrite=False,
                           append=False)

        # Hanning smooth the continuum SPWs only.
        #
        # `spws_to_smooth` is a CASA-style range naming the windows TO smooth;
        # there is no exclusion parameter. `maser_detection` only applies when
        # spws_to_smooth is None, so passing the list explicitly is what keeps
        # the line SPWs untouched -- the maser algorithm would otherwise smooth
        # the OH windows. maser_detection=False is passed as well to make that
        # intent obvious.
        smooth_spws = continuum_spw_ids(spw_dict)

        if len(smooth_spws) == 0:
            # An empty string is NOT "smooth nothing" to CASA, so do not risk
            # passing one -- skip the stage instead.
            casalog.post("No continuum SPWs found. Skipping hifv_hanning.")

        else:
            hifv_hanning(maser_detection=False,
                         spws_to_smooth=",".join([str(spwid) for spwid
                                                  in smooth_spws]))
            h_save()

        # Flag the MW HI absorption on the calibrators, in the HI SPW and in
        # any continuum SPW covering the same frequency.
        for thisspw in set([hi_spw] + list(hi_spw_continuum)):
            flag_hi_foreground(myvis,
                               calibrator_line_range_kms,
                               thisspw,
                               cal_intents=["CALIBRATE*"],
                               test_run=False,
                               test_print=True)

        # Additional quacking at the beginning of scans is disabled for the
        # unified pipeline. hifv_flagdata below still quacks (quack=True).
        # flag_quack_integrations(myvis, num_ints=3.0)

        hifv_flagdata(intents='*POINTING*,*FOCUS*,*ATMOSPHERE*,*SIDEBAND_RATIO*, \
                    *UNKNOWN*, *SYSTEM_CONFIGURATION*, \
                    *UNSPECIFIED#UNSPECIFIED*',
                      flagbackup=False,
                      scan=True,
                      baseband=True,
                      clip=True,
                      autocorr=True,
                      template=True,
                      filetemplate="manual_flagging.txt",
                      online=True,
                      hm_tbuff='1.5int',
                      tbuff=0.0,
                      fracspw=0.01,
                      shadow=True,
                      quack=True,
                      edgespw=True)
        h_save()

        hifv_vlasetjy(pipelinemode="automatic")

        # Remove existing iono correction images if they exist.
        os.system("rm -r iono.*.im")

        hifv_priorcals(pipelinemode="automatic")
        h_save()

        # Check offline tables (updated before each run) for antenna corrections
        # If the online tables were accessed and the correction table already exists,
        # skip remaking.
        make_offline_antpos_table(myvis,
                                  data_folder="VLA_antcorr_tables",
                                  skip_existing=True)

        hifv_syspower(pipelinemode="automatic",
                      apply=True)

        hifv_testBPdcals(pipelinemode="automatic",
                         weakbp=False,
                         refantignore=refantignore,
                         doflagundernspwlimit=True)
        h_save()

        # We need to interpolate over MW absorption in the bandpass
        # These channels should be flagged in the calibrators.
        bandpass_with_gap_interpolation(myvis, hi_spw,
                                        search_string="test",
                                        task_string="hifv_testBPdcals")

        hifv_checkflag(checkflagmode='bpd-vla')
        h_save()

        hifv_semiFinalBPdcals(pipelinemode="automatic",
                              weakbp=False,
                              refantignore=refantignore)

        hifv_checkflag(checkflagmode='allcals-vla')
        h_save()

        hifv_solint(pipelinemode="automatic",
                    refantignore=refantignore)

        hifv_fluxboot(pipelinemode="automatic",
                      fitorder=2,
                      refantignore=refantignore)
        h_save()

        hifv_finalcals(pipelinemode="automatic",
                       weakbp=False,
                       refantignore=refantignore)

        bandpass_with_gap_interpolation(myvis, hi_spw,
                                        search_string='final',
                                        task_string='hifv_finalcals')

        hifv_applycals(pipelinemode="automatic",
                       flagdetailedsum=True,
                       gainmap=False,
                       flagbackup=True,
                       flagsum=True)
        h_save()

        # RFI flagging on the targets. The line ranges with signal are
        # protected by cont.dat.
        hifv_checkflag(checkflagmode='target-vla')
        h_save()

        # Likewise, the weights are computed from the line-free ranges only.
        hifv_statwt(datacolumn='corrected')
        h_save()

        hifv_plotsummary(pipelinemode="automatic")

        # NOTE: the pipeline imaging stages (hif_makeimlist, hif_makeimages)
        # are deliberately skipped. See the quicklook imaging below.

        # Make a folder of products for restoring the pipeline solution
        if not os.path.exists(products_folder):
            os.mkdir(products_folder + '/')

        hifv_exportdata(products_dir=products_folder + '/',
                        gainmap=False,
                        exportmses=False,
                        exportcalprods=True)

    except Exception as ex:
        casalog.post("Encountered exception: {}".format(ex))

        casalog.post("Traceback: {}".format(traceback.print_exc()))

        h_save()

        print("Encountered exception: {}. Exiting with error code 1".format(ex))

        sys.exit(1)

    finally:

        h_save()

else:
    # Rebuild the pieces the post-processing below needs.
    spw_dict = create_spw_dict(myvis, save_spwdict=True,
                               spwdict_filename=spwdict_filename)

    thisgals = identify_targets(myvis)


# Copy the SPW dictionary file into products
if os.path.exists(spwdict_filename):
    os.system(f"cp {spwdict_filename} products/")

# Copy the cont.dat file to products
if os.path.exists("cont.dat"):
    os.system(f"cp cont.dat products/")

# --------------------------------
# Split the calibrated column out into target and calibrator parts.
# The MS holds both line and continuum SPWs, so the type is given explicitly.
# --------------------------------
split_ms_final_all(myvis,
                   spw_dict,
                   split_type='speclines',
                   data_column='CORRECTED',
                   target_name_prefix="",
                   time_bin='0s',
                   keep_flags=False,
                   overwrite=False)

split_ms_final_all(myvis,
                   spw_dict,
                   split_type='continuum',
                   data_column='CORRECTED',
                   target_name_prefix="",
                   time_bin='0s',
                   keep_flags=True,
                   overwrite=False)

# --------------------------------
# Make quicklook images of targets
# --------------------------------
run_quicklook = True

# Run dirty imaging only for a quicklook
if run_quicklook:

    for thisgal in thisgals:
        quicklook_line_imaging(myvis, thisgal, spw_dict,
                               # channel_width_kms=20.,
                               nchan_vel=5,
                               niter=0, nsigma=5.)

    # NOTE: We will attempt a very light clean as it can really highlight
    # which SPWs have significant RFI.
    quicklook_continuum_imaging(myvis, spw_dict,
                                niter=0, nsigma=5.)

    os.system("cp -r {0} {1}".format('quicklook_imaging', products_folder))

# ----------------------------
# Now make additional QA plots:
# -----------------------------

text_output = True

if text_output:
    make_all_caltable_txt(myvis)

    make_qa_tables(myvis,
                   output_folder='scan_plots_txt',
                   outtype='ecsv', overwrite=False,
                   chanavg=4096,)

    # make_all_flagsummary_data(myvis, output_folder='perfield_flagfraction_txt')

    # Move these folders to the products folder.
    os.system("cp -r {0} {1}".format('final_caltable_txt', products_folder))
    os.system("cp -r {0} {1}".format('scan_plots_txt', products_folder))
    # os.system("cp -r {0} {1}".format('perfield_flagfraction_txt', products_folder))

else:

    make_qa_scan_figures(myvis,
                         output_folder='scan_plots',
                         outtype='png')

    # Move these folders to the products folder.
    os.system("cp -r {0} {1}".format('scan_plots', products_folder))

# Make detailed uvresid plots.
# These are to check if any calibrators have source structure not accounted for.
# In that case, a flux.csv file needs to be provided for a subsequent pipeline run

uvresid_path = "uvresid_plots"

# Not being used right now. The LGLBS gain cals are well-modeled as pt. sources
do_uvstats = False

# Skip re-run if the folder already exists:
if do_uvstats:
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
