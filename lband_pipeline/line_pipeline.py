
import sys
import os
from glob import glob
import shutil

from qa_plotting.perspw_bandpass_plots import make_spw_bandpass_plots

from line_tools import bandpass_with_gap_interpolation


# Ignore any as refants??
refantignore = ""

mySDM = sys.argv[-1]
myvis = mySDM if mySDM.endswith("ms") else mySDM + ".ms"

# if not os.path.exists("cont.dat"):
#     raise ValueError("The cont.dat file is not in the pipeline directory.")

__rethrow_casa_exceptions = True
context = h_init()
context.set_state('ProjectSummary', 'observatory',
                  'Karl G. Jansky Very Large Array')
context.set_state('ProjectSummary', 'telescope', 'EVLA')
context.set_state('ProjectSummary', 'proposal_code', '15A-175')
context.set_state('ProjectSummary', 'piname', 'Adam Leroy')

try:
    hifv_importdata(ocorr_mode='co', nocopy=False, vis=[myvis],
                    createmms='automatic', asis='Receiver CalAtmosphere',
                    overwrite=False)
# Hanning smoothing is turned off in the following step.
# In the case of extreme RFI, Hanning smoothing, however,
# may still be required.
# Avoid Hanning smoothing spectral lines
# hifv_hanning(pipelinemode="automatic")
# Online flags applied when importing ASDM
    hifv_flagdata(intents='*POINTING*,*FOCUS*,*ATMOSPHERE*,*SIDEBAND_RATIO*, \
                  *UNKNOWN*, *SYSTEM_CONFIGURATION*, \
                  *UNSPECIFIED#UNSPECIFIED*',
                  flagbackup=False, scan=True, baseband=True, clip=True,
                  autocorr=True,
                  hm_tbuff='1.5int', template=True,
                  filetemplate="additional_flagging.txt",
                  online=False, tbuff=0.0,
                  fracspw=0.05, shadow=True, quack=True, edgespw=True)

    hifv_vlasetjy(fluxdensity=-1, scalebychan=True, reffreq='1GHz', spix=0)
    hifv_priorcals(tecmaps=False)
    hifv_testBPdcals(weakbp=False, refantignore=refantignore)

    # We need to interpolate over MW absorption in the bandpass
    # These channels should be flagged in the calibrators.

    bandpass_with_gap_interpolation(myvis, context,
                                    refantignore=refantignore,
                                    search_string='test',
                                    task_string='hifv_testBPdcals')

    hifv_flagbaddef(pipelinemode="automatic")
    hifv_checkflag(pipelinemode="automatic")

    hifv_semiFinalBPdcals(weakbp=False, refantignore=refantignore)
    hifv_checkflag(checkflagmode='semi')
    hifv_semiFinalBPdcals(weakbp=False, refantignore=refantignore)

    bandpass_with_gap_interpolation(myvis, context,
                                    refantignore=refantignore,
                                    search_string='',
                                    task_string='hifv_semiFinalBPdcals')

    hifv_solint(pipelinemode="automatic", refantignore=refantignore)
    hifv_fluxboot(pipelinemode="automatic", refantignore=refantignore)
    hifv_finalcals(weakbp=False, refantignore=refantignore)

    bandpass_with_gap_interpolation(myvis, context,
                                    refantignore=refantignore,
                                    search_string='final',
                                    task_string='hifv_finalcals')

    hifv_applycals(flagdetailedsum=True, gainmap=False, flagbackup=True, flagsum=True)
# Keep the following two steps in the script if cont.dat exists.
# Otherwise we recommend to comment out the next two tasks,
# or at least remove '*TARGET*' from the hifv_targetflag call
    if os.path.exists('cont.dat'):
        hifv_targetflag(intents='*CALIBRATE*, *TARGET*')
        hifv_statwt(pipelinemode="automatic")
    else:
        hifv_targetflag(intents='*CALIBRATE*')

    hifv_plotsummary(pipelinemode="automatic")

    hif_makeimlist(nchan=-1, calmaxpix=300, intent='PHASE,BANDPASS')

    hif_makeimages(tlimit=2.0, hm_minbeamfrac=-999.0, hm_dogrowprune=True,
                   hm_negativethreshold=-999.0, calcsb=False, target_list={},
                   hm_noisethreshold=-999.0, hm_masking='none', hm_minpercentchange=-999.0,
                   parallel='automatic', masklimit=4, hm_lownoisethreshold=-999.0,
                   hm_growiterations=-999, cleancontranges=False, hm_sidelobethreshold=-999.0)
    # Make a folder of products for restoring the pipeline solution
    if not os.path.exists("products"):
        os.mkdir('products/')

    hifv_exportdata(products_dir='products/')

finally:
    h_save()

# Make a new directory for the imaging outputs
if not os.path.exists("image_outputs"):
    os.mkdir("image_outputs")

image_files = glob("oussid*")

for fil in image_files:
    shutil.move(fil, "image_outputs/")

# Now make additional QA plots:

make_spw_bandpass_plots(myvis,
                        bp_folder="finalBPcal_plots",
                        outtype='png')

# Add in the longer QA function to make plots here.
