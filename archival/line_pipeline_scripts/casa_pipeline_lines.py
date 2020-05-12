import sys
import os
from glob import glob
from copy import copy
import shutil
import numpy as np
from shutil import copyfile

from tasks import plotms, importasdm

# Need to calc refants for custom bandpass
import pipeline.hif.heuristics.findrefant as findrefant

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
    hifv_testBPdcals(weakbp=False, refantignore='')

    # We need to interpolate over MW absorption in the bandpass
    # These channels should be flagged in the calibrators.

    # Look for BP table
    bpname = glob("{}.hifv_testBPdcals.s*_4.testBPcal.tbl".format(myvis))
    assert len(bpname) == 1
    bpname = bpname[0]

    # Remove already-made version
    # rmtables(bpname)
    # Or copy to another name to check against
    os.system("mv {0} {0}.orig".format(bpname))

    # Get the scan/field selections
    scanheur = context.evla['msinfo'][context.evla['msinfo'].keys()[0]]

    # Grab list of preferred refants
    refantfield = scanheur.calibrator_field_select_string
    refantobj = findrefant.RefAntHeuristics(vis=myvis, field=refantfield,
                                            geometry=True, flagging=True,
                                            intent='',
                                            spw='',
                                            refantignore=refantignore)
    RefAntOutput = refantobj.calculate()
    refAnt = ','.join(RefAntOutput)

    # Lastly get list of other cal tables to use in the solution
    gc_tbl = glob("{}.hifv_priorcals.s*_2.gc.tbl".format(myvis))
    assert len(gc_tbl) == 1

    opac_tbl = glob("{}.hifv_priorcals.s*_3.opac.tbl".format(myvis))
    assert len(opac_tbl) == 1

    rq_tbl = glob("{}.hifv_priorcals.s*_4.rq.tbl".format(myvis))
    assert len(rq_tbl) == 1

    # Check ant correction
    ant_tbl = glob("{}.hifv_priorcals.s*_6.ants.tbl".format(myvis))

    priorcals = [gc_tbl[0], opac_tbl[0], rq_tbl[0]]

    if len(ant_tbl) == 1:
        priorcals.extend(ant_tbl)

    tstdel_tbl = glob("{}.hifv_testBPdcals.s*_2.testdelay.tbl".format(myvis))
    assert len(tstdel_tbl) == 1

    tstBPinit_tbl = glob("{}.hifv_testBPdcals.s*_3.testBPdinitialgain.tbl".format(myvis))
    assert len(tstBPinit_tbl) == 1

    gaintables = copy(priorcals)
    gaintables.extend([tstdel_tbl[0], tstBPinit_tbl[0]])

    bandpass(vis=myvis,
             caltable=bpname,
             field=scanheur.bandpass_field_select_string,
             selectdata=True,
             scan=scanheur.bandpass_scan_select_string,
             solint='inf',
             combine='scan',
             refant=refAnt,
             minblperant=4,
             minsnr=5.0,
             solnorm=False,
             bandtype='B',
             smodel=[],
             append=False,
             fillgaps=400,
             docallib=False,
             gaintable=gaintables,
             gainfield=[''],
             interp=[''],
             spwmap=[],
             parang=True)

    hifv_flagbaddef(pipelinemode="automatic")
    hifv_checkflag(pipelinemode="automatic")

    # NOTE we need to flag HI absorption in the bandpass here
    # I *think* we can run a custom bandpass cmd here and pass
    # the name of the table to 'bpcaltable' in applycal

    # bpcaltable = same as pipeline name
    # bandpass(fillgap=# chan flagged)
    # hifv_semiFinalBPdcals(weakbp=False, refantignore='',
    #                       bpcaltable=bpcaltable)
    #

    hifv_semiFinalBPdcals(weakbp=False, refantignore='')
    hifv_checkflag(checkflagmode='semi')
    hifv_semiFinalBPdcals(weakbp=False, refantignore='')

    # Make an interpolated-gaps BP after the second semifinal call
    bpname = glob("{}.hifv_semiFinalBPdcals.s*_4.BPcal.tbl".format(myvis))
    assert len(bpname) == 2
    # Take the second one
    bpname = bpname[-1]

    # Remove already-made version
    # rmtables(bpname)
    # Or copy to another name to check against
    os.system("mv {0} {0}.orig".format(bpname))

    # Get the scan/field selections
    scanheur = context.evla['msinfo'][context.evla['msinfo'].keys()[0]]

    # Grab list of preferred refants
    refantfield = scanheur.calibrator_field_select_string
    refantobj = findrefant.RefAntHeuristics(vis=myvis, field=refantfield,
                                            geometry=True, flagging=True,
                                            intent='',
                                            spw='',
                                            refantignore=refantignore)
    RefAntOutput = refantobj.calculate()
    refAnt = ','.join(RefAntOutput)

    # Semi final is run twice. Take the last one
    del_tbl = glob("{}.hifv_semiFinalBPdcals.s*_2.delay.tbl".format(myvis))
    assert len(del_tbl) == 2
    del_tbl = del_tbl[-1]

    BPinit_tbl = glob("{}.hifv_semiFinalBPdcals.s*_3.BPinitialgain.tbl".format(myvis))
    assert len(BPinit_tbl) == 2
    BPinit_tbl = BPinit_tbl[-1]

    gaintables = copy(priorcals)
    gaintables.extend([del_tbl, BPinit_tbl])

    bandpass(vis=myvis,
             caltable=bpname,
             field=scanheur.bandpass_field_select_string,
             selectdata=True,
             scan=scanheur.bandpass_scan_select_string,
             solint='inf',
             combine='scan',
             refant=refAnt,
             minblperant=4,
             minsnr=5.0,
             solnorm=False,
             bandtype='B',
             smodel=[],
             append=False,
             fillgaps=400,
             docallib=False,
             gaintable=gaintables,
             gainfield=[''],
             interp=[''],
             spwmap=[],
             parang=True)

    hifv_solint(pipelinemode="automatic", refantignore='')
    hifv_fluxboot(pipelinemode="automatic", refantignore='')
    hifv_finalcals(weakbp=False, refantignore='')

    # Make final BP table before apply call
    bpname = glob("{}.hifv_finalcals.s*_4.finalBPcal.tbl".format(myvis))
    assert len(bpname) == 1
    bpname = bpname[0]

    # Remove already-made version
    # rmtables(bpname)
    # Or copy to another name to check against
    os.system("mv {0} {0}.orig".format(bpname))

    # Get the scan/field selections
    scanheur = context.evla['msinfo'][context.evla['msinfo'].keys()[0]]

    # Grab list of preferred refants
    refantfield = scanheur.calibrator_field_select_string
    refantobj = findrefant.RefAntHeuristics(vis=myvis, field=refantfield,
                                            geometry=True, flagging=True,
                                            intent='',
                                            spw='',
                                            refantignore=refantignore)
    RefAntOutput = refantobj.calculate()
    refAnt = ','.join(RefAntOutput)

    del_tbl = glob("{}.hifv_finalcals.s*_2.finaldelay.tbl".format(myvis))
    assert len(del_tbl) == 1

    BPinit_tbl = glob("{}.hifv_finalcals.s*_3.finalBPinitialgain.tbl".format(myvis))
    assert len(BPinit_tbl) == 1

    gaintables = copy(priorcals)
    gaintables.extend([del_tbl[0], BPinit_tbl[0]])

    bandpass(vis=myvis,
             caltable=bpname,
             field=scanheur.bandpass_field_select_string,
             selectdata=True,
             scan=scanheur.bandpass_scan_select_string,
             solint='inf',
             combine='scan',
             refant=refAnt,
             minblperant=4,
             minsnr=5.0,
             solnorm=False,
             bandtype='B',
             smodel=[],
             append=False,
             fillgaps=400,
             docallib=False,
             gaintable=gaintables,
             gainfield=[''],
             interp=[''],
             spwmap=[],
             parang=True)

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

# Now make a bunch of scan plots to make it easier to identify bad data
ms_active = myvis

# Plot the bandpasses per SPW as well
bp_folder = "finalBPcal_plots"
if not os.path.exists(bp_folder):
    os.mkdir(bp_folder)

tb.open(ms_active + "/SPECTRAL_WINDOW")
nspws = tb.getcol("NAME").shape[0]
tb.close()

# Final BP cal table now includes the stage number and step
finalbpcal_name = glob(mySDM + '*.finalBPcal.tbl')
if len(finalbpcal_name) == 0:
    raise ValueError("Cannot find finalBPcal table name.")
# Blindly assume we want the first name
finalbpcal_name = finalbpcal_name[0]

for ii in range(nspws):
    filename = 'finalBPcal_amp_spw_' + str(ii) + '.png'
    syscommand = 'rm -rf ' + filename
    os.system(syscommand)

    default('plotcal')
    caltable = finalbpcal_name
    xaxis = 'freq'
    yaxis = 'amp'
    poln = ''
    field = ''
    antenna = ''
    spw = str(ii)
    timerange = ''
    subplot = 111
    overplot = False
    clearpanel = 'Auto'
    iteration = ''
    showflags = False
    plotsymbol = 'o'
    plotcolor = 'blue'
    markersize = 5.0
    fontsize = 10.0
    showgui = False
    figfile = os.path.join(bp_folder, filename)
    async = False
    plotcal()

for ii in range(nspws):
    filename = 'finalBPcal_phase_spw_' + str(ii) + '.png'
    syscommand = 'rm -rf ' + filename
    os.system(syscommand)

    antPlot = str(ii * 3) + '~' + str(ii * 3 + 2)

    default('plotcal')
    caltable = finalbpcal_name
    xaxis = 'freq'
    yaxis = 'phase'
    poln = ''
    field = ''
    antenna = ''
    spw = str(ii)
    timerange = ''
    subplot = 111
    overplot = False
    clearpanel = 'Auto'
    iteration = ''
    # plotrange=[0,0,-phaseplotmax,phaseplotmax]
    showflags = False
    plotsymbol = 'o'
    plotcolor = 'blue'
    markersize = 5.0
    fontsize = 10.0
    showgui = False
    figfile = os.path.join(bp_folder, filename)
    async = False
    plotcal()

# SPWs to loop through
tb.open(os.path.join(ms_active, "SPECTRAL_WINDOW"))
spws = range(len(tb.getcol("NAME")))
nchans = tb.getcol('NUM_CHAN')
tb.close()

# Read the field names
tb.open(os.path.join(ms_active, "FIELD"))
names = tb.getcol('NAME')
numFields = tb.nrows()
tb.close()

# Intent names
tb.open(os.path.join(ms_active, 'STATE'))
intentcol = tb.getcol('OBS_MODE')
tb.close()

tb.open(ms_active)
scanNums = np.unique(tb.getcol('SCAN_NUMBER'))
field_scans = []
is_calibrator = np.empty_like(scanNums, dtype='bool')
is_all_flagged = np.empty((len(spws), len(scanNums)), dtype='bool')
for ii in range(numFields):
    subtable = tb.query('FIELD_ID==%s' % ii)
    field_scan = np.unique(subtable.getcol('SCAN_NUMBER'))
    field_scans.append(field_scan)

    # Is the intent for calibration?
    scan_intents = intentcol[np.unique(subtable.getcol("STATE_ID"))]
    is_calib = False
    for intent in scan_intents:
        if "CALIBRATE" in intent:
            is_calib = True
            break

    is_calibrator[field_scan - 1] = is_calib

    # Are any of the scans completely flagged?
    for spw in spws:
        for scan in field_scan:
            scantable = \
                tb.query("SCAN_NUMBER=={0} AND DATA_DESC_ID=={1}".format(scan,
                                                                         spw))
            if scantable.getcol("FLAG").all():
                is_all_flagged[spw, scan - 1] = True
            else:
                is_all_flagged[spw, scan - 1] = False

tb.close()

# Make folder for scan plots
scan_dir = "scan_plots"

if not os.path.exists(scan_dir):
    os.mkdir(scan_dir)

for spw_num in spws:
    print("On SPW {}".format(spw))

    # Plotting the HI spw (0) takes so so long.
    # Make some simplifications to save time
    if spw_num == 0:
        avg_chan = "4"
    else:
        avg_chan = "1"

    spw_folder = os.path.join(scan_dir, "spw_{}".format(spw_num))
    if not os.path.exists(spw_folder):
        os.mkdir(spw_folder)
    else:
        # Make sure any old plots are removed first.
        os.system("rm {}/*.png".format(spw_folder))

    for ii in range(len(field_scans)):
        print("On field {}".format(names[ii]))
        for jj in field_scans[ii]:

            # Check if all of the data is flagged.
            if is_all_flagged[spw_num, jj - 1]:
                print("All data flagged in SPW {0} scan {1}"
                      .format(spw_num, jj))
                continue

            print("On scan {}".format(jj))

            # Amp vs. time
            default('plotms')
            vis = ms_active
            xaxis = 'time'
            yaxis = 'amp'
            ydatacolumn = 'corrected'
            selectdata = True
            field = names[ii]
            scan = str(jj)
            spw = str(spw_num)
            avgchannel = str(avg_chan)
            correlation = "RR,LL"
            averagedata = True
            avgbaseline = True
            transform = False
            extendflag = False
            plotrange = []
            title = 'Amp vs Time: Field {0} Scan {1}'.format(names[ii], jj)
            xlabel = ''
            ylabel = ''
            showmajorgrid = False
            showminorgrid = False
            plotfile = os.path.join(
                spw_folder, 'field_{0}_amp_scan_{1}.png'.format(names[ii], jj))
            overwrite = True
            showgui = False
            async = False
            plotms()

            # Amp vs. channel
            default('plotms')
            vis = ms_active
            xaxis = 'chan'
            yaxis = 'amp'
            ydatacolumn = 'corrected'
            selectdata = True
            field = names[ii]
            scan = str(jj)
            spw = str(spw_num)
            avgchannel = str(avg_chan)
            avgtime = "1e8"
            correlation = "RR,LL"
            averagedata = True
            avgbaseline = True
            transform = False
            extendflag = False
            plotrange = []
            title = 'Amp vs Chan: Field {0} Scan {1}'.format(names[ii], jj)
            xlabel = ''
            ylabel = ''
            showmajorgrid = False
            showminorgrid = False
            plotfile = os.path.join(
                spw_folder, 'field_{0}_amp_chan_scan_{1}.png'.format(names[ii], jj))
            overwrite = True
            showgui = False
            async = False
            plotms()

            # Plot amp vs uvdist
            default('plotms')
            vis = ms_active
            xaxis = 'uvdist'
            yaxis = 'amp'
            ydatacolumn = 'corrected'
            selectdata = True
            field = names[ii]
            scan = str(jj)
            spw = str(spw_num)
            avgchannel = str(4096)
            avgtime = '1e8'
            correlation = "RR,LL"
            averagedata = True
            avgbaseline = False
            transform = False
            extendflag = False
            plotrange = []
            title = 'Amp vs UVDist: Field {0} Scan {1}'.format(names[ii], jj)
            xlabel = ''
            ylabel = ''
            showmajorgrid = False
            showminorgrid = False
            plotfile = os.path.join(
                spw_folder, 'field_{0}_amp_uvdist_scan_{1}.png'.format(names[ii], jj))
            overwrite = True
            showgui = False
            async = False
            plotms()

            # Skip the phase plots for the HI SPW (0)
            if is_calibrator[jj - 1] and spw_num != 0:
                # Plot phase vs time
                default('plotms')
                vis = ms_active
                xaxis = 'time'
                yaxis = 'phase'
                ydatacolumn = 'corrected'
                selectdata = True
                field = names[ii]
                scan = str(jj)
                spw = str(spw_num)
                correlation = "RR,LL"
                averagedata = True
                avgbaseline = False
                transform = False
                extendflag = False
                plotrange = []
                title = 'Phase vs Time: Field {0} Scan {1}'.format(
                    names[ii], jj)
                xlabel = ''
                ylabel = ''
                showmajorgrid = False
                showminorgrid = False
                plotfile = os.path.join(
                    spw_folder, 'field_{0}_phase_scan_{1}.png'.format(names[ii], jj))
                overwrite = True
                showgui = False
                async = False
                plotms()

                # Plot phase vs channel
                default('plotms')
                vis = ms_active
                xaxis = 'chan'
                yaxis = 'phase'
                ydatacolumn = 'corrected'
                selectdata = True
                field = names[ii]
                scan = str(jj)
                spw = str(spw_num)
                correlation = "RR,LL"
                averagedata = True
                avgbaseline = False
                transform = False
                extendflag = False
                plotrange = []
                title = 'Phase vs Chan: Field {0} Scan {1}'.format(
                    names[ii], jj)
                xlabel = ''
                ylabel = ''
                showmajorgrid = False
                showminorgrid = False
                plotfile = os.path.join(
                    spw_folder, 'field_{0}_phase_chan_scan_{1}.png'.format(names[ii], jj))
                overwrite = True
                showgui = False
                async = False
                plotms()

                # Plot phase vs uvdist
                default('plotms')
                vis = ms_active
                xaxis = 'uvdist'
                yaxis = 'phase'
                ydatacolumn = 'corrected'
                selectdata = True
                field = names[ii]
                scan = str(jj)
                spw = str(spw_num)
                correlation = "RR,LL"
                avgchannel = "4096"
                avgtime = '1e8'
                averagedata = True
                avgbaseline = False
                transform = False
                extendflag = False
                plotrange = []
                title = 'Phase vs UVDist: Field {0} Scan {1}'.format(
                    names[ii], jj)
                xlabel = ''
                ylabel = ''
                showmajorgrid = False
                showminorgrid = False
                plotfile = os.path.join(
                    spw_folder, 'field_{0}_phase_uvdist_scan_{1}.png'.format(names[ii], jj))
                overwrite = True
                showgui = False
                async = False
                plotms()
