
'''

Routines for creating additional QA plots.

'''


import os
import numpy as np


def make_qa_scan_figures(ms_name, output_folder='scan_plots'):
    '''
    Make a series of plots per scan for QA and
    flagging purposes.

    TODO: Add more settings here for different types of plots, etc.

    Parameters
    ----------
    ms_name : str
        MS name
    output_folder : str, optional
        Output plot folder name.

    '''

    # Will need to updated for CASA 6
    from taskinit import tb

    from tasks import plotms

    # SPWs to loop through
    tb.open(os.path.join(ms_name, "SPECTRAL_WINDOW"))
    spws = range(len(tb.getcol("NAME")))
    nchans = tb.getcol('NUM_CHAN')
    tb.close()

    # Read the field names
    tb.open(os.path.join(ms_name, "FIELD"))
    names = tb.getcol('NAME')
    numFields = tb.nrows()
    tb.close()

    # Intent names
    tb.open(os.path.join(ms_name, 'STATE'))
    intentcol = tb.getcol('OBS_MODE')
    tb.close()

    tb.open(ms_name)
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
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    # Loop through SPWs and create plots.
    for spw_num in spws:
        casalog.post("On SPW {}".format(spw))

        # Plotting the HI spw (0) takes so so long.
        # Make some simplifications to save time
        # if spw_num == 0:
        #     avg_chan = "4"
        # else:

        # TODO: change appropriately for line SPWs with many channels
        avg_chan = "1"

        spw_folder = os.path.join(output_folder, "spw_{}".format(spw_num))
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
                plotms(vis=ms_name,
                       xaxis='time',
                       yaxis='amp',
                       ydatacolumn='corrected',
                       selectdata=True,
                       field=names[ii],
                       scan=str(jj),
                       spw=str(spw_num),
                       avgchannel=str(avg_chan),
                       correlation="RR,LL",
                       averagedata=True,
                       avgbaseline=True,
                       transform=False,
                       extendflag=False,
                       plotrange=[],
                       title='Amp vs Time: Field {0} Scan {1}'.format(names[ii], jj),
                       xlabel='Time',
                       ylabel='Amp',
                       showmajorgrid=False,
                       showminorgrid=False,
                       plotfile=os.path.join(spw_folder,
                                             'field_{0}_amp_scan_{1}.png'.format(names[ii], jj)),
                       overwrite=True,
                       showgui=False,
                       async=False)

                # Amp vs. channel
                plotms(vis=ms_name,
                       xaxis='chan',
                       yaxis='amp',
                       ydatacolumn='corrected',
                       selectdata=True,
                       field=names[ii],
                       scan=str(jj),
                       spw=str(spw_num),
                       avgchannel=str(avg_chan),
                       avgtime="1e8",
                       correlation="RR,LL",
                       averagedata=True,
                       avgbaseline=True,
                       transform=False,
                       extendflag=False,
                       plotrange=[],
                       title='Amp vs Chan: Field {0} Scan {1}'.format(names[ii], jj),
                       xlabel='Channel',
                       ylabel='Amp',
                       showmajorgrid=False,
                       showminorgrid=False,
                       plotfile=os.path.join(spw_folder,
                                             'field_{0}_amp_chan_scan_{1}.png'.format(names[ii], jj)),
                       overwrite=True,
                       showgui=False,
                       async=False)

                # Plot amp vs uvdist
                plotms(vis=ms_name,
                       xaxis='uvdist',
                       yaxis='amp',
                       ydatacolumn='corrected',
                       selectdata=True,
                       field=names[ii],
                       scan=str(jj),
                       spw=str(spw_num),
                       avgchannel=str(4096),
                       avgtime='1e8',
                       correlation="RR,LL",
                       averagedata=True,
                       avgbaseline=False,
                       transform=False,
                       extendflag=False,
                       plotrange=[],
                       title='Amp vs UVDist: Field {0} Scan {1}'.format(names[ii], jj),
                       xlabel='uv-dist',
                       ylabel='Amp',
                       showmajorgrid=False,
                       showminorgrid=False,
                       plotfile=os.path.join(spw_folder,
                                             'field_{0}_amp_uvdist_scan_{1}.png'.format(names[ii], jj)),
                       overwrite=True,
                       showgui=False,
                       async=False)

                # Skip the phase plots for the HI SPW (0)
                if is_calibrator[jj - 1]:
                    # Plot phase vs time
                    plotms(vis=ms_name,
                           xaxis='time',
                           yaxis='phase',
                           ydatacolumn='corrected',
                           selectdata=True,
                           field=names[ii],
                           scan=str(jj),
                           spw=str(spw_num),
                           correlation="RR,LL",
                           averagedata=True,
                           avgbaseline=False,
                           transform=False,
                           extendflag=False,
                           plotrange=[],
                           title='Phase vs Time: Field {0} Scan {1}'.format(names[ii], jj),
                           xlabel='Time',
                           ylabel='Phase',
                           showmajorgrid=False,
                           showminorgrid=False,
                           plotfile=os.path.join(spw_folder,
                                                 'field_{0}_phase_scan_{1}.png'.format(names[ii], jj)),
                           overwrite=True,
                           showgui=False,
                           async=False)

                    # Plot phase vs channel
                    plotms(vis=ms_name,
                           xaxis='chan',
                           yaxis='phase',
                           ydatacolumn='corrected',
                           selectdata=True,
                           field=names[ii],
                           scan=str(jj),
                           spw=str(spw_num),
                           correlation="RR,LL",
                           averagedata=True,
                           avgbaseline=False,
                           transform=False,
                           extendflag=False,
                           plotrange=[],
                           title='Phase vs Chan: Field {0} Scan {1}'.format(names[ii], jj),
                           xlabel='Chan',
                           ylabel='Phase',
                           showmajorgrid=False,
                           showminorgrid=False,
                           plotfile=os.path.join(spw_folder,
                                                 'field_{0}_phase_chan_scan_{1}.png'.format(names[ii], jj)),
                           overwrite=True,
                           showgui=False,
                           async=False)

                    # Plot phase vs uvdist
                    plotms(vis=ms_name,
                           xaxis='uvdist',
                           yaxis='phase',
                           ydatacolumn='corrected',
                           selectdata=True,
                           field=names[ii],
                           scan=str(jj),
                           spw=str(spw_num),
                           correlation="RR,LL",
                           avgchannel="4096",
                           avgtime='1e8',
                           averagedata=True,
                           avgbaseline=False,
                           transform=False,
                           extendflag=False,
                           plotrange=[],
                           title='Phase vs UVDist: Field {0} Scan {1}'.format(names[ii], jj),
                           xlabel='uv-dist',
                           ylabel='Phase',
                           showmajorgrid=False,
                           showminorgrid=False,
                           plotfile=os.path.join(spw_folder,
                                                 'field_{0}_phase_uvdist_scan_{1}.png'.format(names[ii], jj)),
                           overwrite=True,
                           showgui=False,
                           async=False)

                    # Plot amp vs phase
                    plotms(vis=ms_name,
                           xaxis='amp',
                           yaxis='phase',
                           ydatacolumn='corrected',
                           selectdata=True,
                           field=names[ii],
                           scan=str(jj),
                           spw=str(spw_num),
                           correlation="RR,LL",
                           avgchannel="4096",
                           avgtime='1e8',
                           averagedata=True,
                           avgbaseline=False,
                           transform=False,
                           extendflag=False,
                           plotrange=[],
                           title='Amp vs Phase: Field {0} Scan {1}'.format(names[ii], jj),
                           xlabel='Phase',
                           ylabel='Amp',
                           showmajorgrid=False,
                           showminorgrid=False,
                           plotfile=os.path.join(spw_folder,
                                                 'field_{0}_amp_phase_scan_{1}.png'.format(names[ii], jj)),
                           overwrite=True,
                           showgui=False,
                           async=False)
