
import sys
import os
from glob import glob
import shutil

# Additional QA plotting routines
from lband_pipeline.qa_plotting import (make_spw_bandpass_plots,
                                        make_qa_scan_figures,
                                        make_qa_tables,
                                        make_bandpass_txt)

# Info for SPW setup
from lband_pipeline.spw_setup import create_spw_dict

# TODO: read in to skip a refant if needed.
refantignore = ""

mySDM = sys.argv[-1]
myvis = mySDM if mySDM.endswith("ms") else mySDM + ".ms"

# Tracks should follow the VLA format, starting with the project code
proj_code = mySDM.split(".")[0]

# Get the SPW mapping for the line MS.

contspw_dict = create_spw_dict(myvis)


__rethrow_casa_exceptions = True

context = h_init()
context.set_state('ProjectSummary', 'observatory',
                  'Karl G. Jansky Very Large Array')
context.set_state('ProjectSummary', 'telescope', 'EVLA')
context.set_state('ProjectSummary', 'proposal_code', proj_code)

try:
    hifv_importdata(vis=mySDM,
                    createmms='automatic',
                    asis='Receiver CalAtmosphere',
                    ocorr_mode='co',
                    nocopy=False,
                    overwrite=False)

    # TODO: introduce flag for re-runs to avoid smoothing again
    hifv_hanning(pipelinemode="automatic")

    hifv_flagdata(tbuff=0.0,
                  flagbackup=False,
                  scan=True,
                  fracspw=0.05,
                  intents='*POINTING*,*FOCUS*,*ATMOSPHERE*,*SIDEBAND_RATIO*,*UNKNOWN*,*SYSTEM_CONFIGURATION*,*UNSPECIFIED#UNSPECIFIED*',
                  clip=True,
                  baseband=True,
                  shadow=True,
                  quack=True,
                  edgespw=True,
                  autocorr=True,
                  hm_tbuff='1.5int',
                  template=True,
                  online=True)

    hifv_vlasetjy(fluxdensity=-1,
                  scalebychan=True,
                  spix=0,
                  reffreq='1GHz')

    hifv_priorcals(tecmaps=False)

    hifv_testBPdcals(weakbp=False)

    hifv_flagbaddef(doflagundernspwlimit=False)

    hifv_checkflag(pipelinemode="automatic")

    hifv_semiFinalBPdcals(weakbp=False)

    hifv_checkflag(checkflagmode='semi')

    hifv_semiFinalBPdcals(weakbp=False)

    hifv_solint(pipelinemode="automatic")

    hifv_fluxboot2(fitorder=-1)

    hifv_finalcals(weakbp=False)

    hifv_applycals(flagdetailedsum=True,
                   gainmap=False,
                   flagbackup=True,
                   flagsum=True)

    hifv_targetflag(intents='*CALIBRATE*,*TARGET*')

    hifv_statwt(datacolumn='corrected')

    hifv_plotsummary(pipelinemode="automatic")

    hif_makeimlist(nchan=-1,
                   calcsb=False,
                   intent='PHASE,BANDPASS',
                   robust=-999.0,
                   parallel='automatic',
                   per_eb=False,
                   calmaxpix=300,
                   specmode='cont',
                   clearlist=True)

    hif_makeimages(tlimit=2.0,
                   hm_perchanweightdensity=False,
                   hm_npixels=0,
                   hm_dogrowprune=True,
                   hm_negativethreshold=-999.0,
                   calcsb=False,
                   hm_noisethreshold=-999.0,
                   hm_fastnoise=True,
                   hm_masking='none',
                   hm_minpercentchange=-999.0,
                   parallel='automatic',
                   masklimit=4,
                   hm_nsigma=0.0,
                   target_list={},
                   hm_minbeamfrac=-999.0,
                   hm_lownoisethreshold=-999.0,
                   hm_growiterations=-999,
                   overwrite_on_export=True,
                   cleancontranges=False,
                   hm_sidelobethreshold=-999.0)

    # Make a folder of products for restoring the pipeline solution
    products_folder = "products"
    if not os.path.exists(products_folder):
        os.mkdir(products_folder + '/')

    # TODO: review whether we should be including additional products
    # here
    hifv_exportdata(products_dir=products_folder + '/',
                    gainmap=False,
                    exportmses=False,
                    exportcalprods=True)

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
