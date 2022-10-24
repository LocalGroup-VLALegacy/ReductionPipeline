
'''

Routines for creating additional QA plots.

'''


import os
import numpy as np

from casatools import logsink

casalog = logsink()


def make_qa_scan_figures(ms_name, output_folder='scan_plots',
                         outtype='png'):
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
    from casatools import table

    tb = table()

    # from taskinit import tb
    # from taskinit import casalog

    from casaplotms import plotms

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
            casalog.post("On field {}".format(names[ii]))
            for jj in field_scans[ii]:

                # Check if all of the data is flagged.
                if is_all_flagged[spw_num, jj - 1]:
                    casalog.post("All data flagged in SPW {0} scan {1}"
                                 .format(spw_num, jj))
                    continue

                casalog.post("On scan {}".format(jj))

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
                       correlation="",
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
                                             'field_{0}_amp_scan_{1}.{2}'.format(names[ii], jj, outtype)),
                       overwrite=True,
                       showgui=False)

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
                       correlation="",
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
                                             'field_{0}_amp_chan_scan_{1}.{2}'.format(names[ii], jj, outtype)),
                       overwrite=True,
                       showgui=False)

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
                       correlation="",
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
                                             'field_{0}_amp_uvdist_scan_{1}.{2}'.format(names[ii], jj, outtype)),
                       overwrite=True,
                       showgui=False)

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
                           correlation="",
                           averagedata=True,
                           avgbaseline=True,
                           transform=False,
                           extendflag=False,
                           plotrange=[],
                           title='Phase vs Time: Field {0} Scan {1}'.format(names[ii], jj),
                           xlabel='Time',
                           ylabel='Phase',
                           showmajorgrid=False,
                           showminorgrid=False,
                           plotfile=os.path.join(spw_folder,
                                                 'field_{0}_phase_time_scan_{1}.{2}'.format(names[ii], jj, outtype)),
                           overwrite=True,
                           showgui=False)

                    # Plot phase vs channel
                    plotms(vis=ms_name,
                           xaxis='chan',
                           yaxis='phase',
                           ydatacolumn='corrected',
                           selectdata=True,
                           field=names[ii],
                           scan=str(jj),
                           spw=str(spw_num),
                           avgchannel=str(avg_chan),
                           avgtime="1e8",
                           correlation="",
                           averagedata=True,
                           avgbaseline=True,
                           transform=False,
                           extendflag=False,
                           plotrange=[],
                           title='Phase vs Chan: Field {0} Scan {1}'.format(names[ii], jj),
                           xlabel='Chan',
                           ylabel='Phase',
                           showmajorgrid=False,
                           showminorgrid=False,
                           plotfile=os.path.join(spw_folder,
                                                 'field_{0}_phase_chan_scan_{1}.{2}'.format(names[ii], jj, outtype)),
                           overwrite=True,
                           showgui=False)

                    # Plot phase vs uvdist
                    plotms(vis=ms_name,
                           xaxis='uvdist',
                           yaxis='phase',
                           ydatacolumn='corrected',
                           selectdata=True,
                           field=names[ii],
                           scan=str(jj),
                           spw=str(spw_num),
                           correlation="",
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
                                                 'field_{0}_phase_uvdist_scan_{1}.{2}'.format(names[ii], jj, outtype)),
                           overwrite=True,
                           showgui=False)

                    # Plot amp vs phase
                    plotms(vis=ms_name,
                           xaxis='amp',
                           yaxis='phase',
                           ydatacolumn='corrected',
                           selectdata=True,
                           field=names[ii],
                           scan=str(jj),
                           spw=str(spw_num),
                           correlation="",
                           avgchannel="4096",
                           # avgtime='1e8',
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
                                                 'field_{0}_amp_phase_scan_{1}.{2}'.format(names[ii], jj, outtype)),
                           overwrite=True,
                           showgui=False)


def make_qa_tables(ms_name, output_folder='scan_plots_txt',
                   outtype='txt', overwrite=True,
                   chanavg=4096,):

    '''
    Specifically for saving txt tables. Replace the scan loop in
    `make_qa_scan_figures` to make fewer but larger tables.

    '''

    # Will need to updated for CASA 6
    # from taskinit import tb
    from casatools import table

    tb = table()

    from casaplotms import plotms

    casalog.post("Running make_qa_tables to export txt files for QA.")
    print("Running make_qa_tables to export txt files for QA.")

    # Make folder for scan plots
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)
    else:
        if overwrite:
            casalog.post(message="Removing plot tables in {}".format(output_folder), origin='make_qa_tables')
            print("Removing plot tables in {}".format(output_folder))
            os.system("rm -r {}/*".format(output_folder))
        else:
            casalog.post("{} already exists. Will skip existing files.".format(output_folder))
            # raise ValueError("{} already exists. Enable overwrite=True to rerun.".format(output_folder))

    # Read the field names
    tb.open(os.path.join(ms_name, "FIELD"))
    names = tb.getcol('NAME')
    numFields = tb.nrows()
    tb.close()

    # Intent names
    tb.open(os.path.join(ms_name, 'STATE'))
    intentcol = tb.getcol('OBS_MODE')
    tb.close()

    # Determine the fields that are calibrators.
    tb.open(ms_name)
    is_calibrator = np.empty((numFields,), dtype='bool')

    has_data = np.ones((numFields,), dtype='bool')

    for ii in range(numFields):
        subtable = tb.query('FIELD_ID==%s' % ii)

        # Is there any data for this field?
        has_data[ii] = subtable.nrows() > 0

        # Is the intent for calibration?
        scan_intents = intentcol[np.unique(subtable.getcol("STATE_ID"))]
        is_calib = False
        for intent in scan_intents:
            if "CALIBRATE" in intent:
                is_calib = True
                break

        is_calibrator[ii] = is_calib

    tb.close()

    casalog.post(message="Fields are: {}".format(names), origin='make_qa_tables')
    casalog.post(message="Calibrator fields are: {}".format(names[is_calibrator]), origin='make_qa_tables')

    print("Fields are: {}".format(names))
    print("Calibrator fields are: {}".format(names[is_calibrator]))

    # Loop through fields. Make separate tables only for different targets.

    for ii in range(numFields):
        casalog.post(message="On field {}".format(names[ii]), origin='make_qa_plots')
        print("On field {}".format(names[ii]))

        # If field has data, continue. If not skip and log it.
        if not has_data[ii]:
            casalog.post(message='Field {} has no data in the table. Skipping.'.format(names[ii]),
                         origin='make_qa_plots')
            continue

        # Amp vs. time
        amptime_filename = os.path.join(output_folder,
                                        'field_{0}_amp_time.{1}'.format(names[ii], outtype))

        if not os.path.exists(amptime_filename):

            plotms(vis=ms_name,
                xaxis='time',
                yaxis='amp',
                ydatacolumn='corrected',
                selectdata=True,
                field=names[ii],
                scan="",
                spw="",
                avgchannel=str(chanavg),
                correlation="",
                averagedata=True,
                avgbaseline=True,
                transform=False,
                extendflag=False,
                plotrange=[],
                # title='Amp vs Time: Field {0} Scan {1}'.format(names[ii], jj),
                xlabel='Time',
                ylabel='Amp',
                showmajorgrid=False,
                showminorgrid=False,
                plotfile=amptime_filename,
                overwrite=True,
                showgui=False)
        else:
            casalog.post(message="File {} already exists. Skipping".format(amptime_filename),
                         origin='make_qa_tables')

        # Amp vs. channel
        ampchan_filename = os.path.join(output_folder,
                                     'field_{0}_amp_chan.{1}'.format(names[ii], outtype))

        if not os.path.exists(ampchan_filename):

            plotms(vis=ms_name,
                xaxis='chan',
                yaxis='amp',
                ydatacolumn='corrected',
                selectdata=True,
                field=names[ii],
                scan="",
                spw="",
                avgchannel="1",
                avgtime="1e8",
                correlation="",
                averagedata=True,
                avgbaseline=True,
                transform=False,
                extendflag=False,
                plotrange=[],
                # title='Amp vs Chan: Field {0} Scan {1}'.format(names[ii], jj),
                xlabel='Channel',
                ylabel='Amp',
                showmajorgrid=False,
                showminorgrid=False,
                plotfile=ampchan_filename,
                overwrite=True,
                showgui=False)
        else:
            casalog.post(message="File {0} already exists. Skipping".format(ampchan_filename),
                        origin='make_qa_tables')

        # Plot amp vs uvdist
        ampuvdist_filename = os.path.join(output_folder,
                                     'field_{0}_amp_uvdist.{1}'.format(names[ii], outtype))

        if not os.path.exists(ampuvdist_filename):

            plotms(vis=ms_name,
                xaxis='uvdist',
                yaxis='amp',
                ydatacolumn='corrected',
                selectdata=True,
                field=names[ii],
                scan="",
                spw="",
                avgchannel=str(chanavg),
                avgtime='1e8',
                correlation="",
                averagedata=True,
                avgbaseline=False,
                transform=False,
                extendflag=False,
                plotrange=[],
                # title='Amp vs UVDist: Field {0} Scan {1}'.format(names[ii], jj),
                xlabel='uv-dist',
                ylabel='Amp',
                showmajorgrid=False,
                showminorgrid=False,
                plotfile=ampuvdist_filename,
                overwrite=True,
                showgui=False)
        else:
            casalog.post(message="File {} already exists. Skipping".format(ampuvdist_filename),
                         origin='make_qa_tables')

        # Make phase plots if a calibrator source.

        if is_calibrator[ii]:

            casalog.post("This is a calibrator. Exporting phase info, too.")
            print("This is a calibrator. Exporting phase info, too.")

            # Plot phase vs time

            phasetime_filename = os.path.join(output_folder,
                                         'field_{0}_phase_time.{1}'.format(names[ii], outtype))

            if not os.path.exists(phasetime_filename):

                plotms(vis=ms_name,
                    xaxis='time',
                    yaxis='phase',
                    ydatacolumn='corrected',
                    selectdata=True,
                    field=names[ii],
                    scan="",
                    spw="",
                    correlation="",
                    avgchannel=str(chanavg),
                    averagedata=True,
                    avgbaseline=True,
                    transform=False,
                    extendflag=False,
                    plotrange=[],
                    # title='Phase vs Time: Field {0} Scan {1}'.format(names[ii], jj),
                    xlabel='Time',
                    ylabel='Phase',
                    showmajorgrid=False,
                    showminorgrid=False,
                    plotfile=phasetime_filename,
                    overwrite=True,
                    showgui=False)
            else:
                casalog.post(message="File {} already exists. Skipping".format(phasetime_filename),
                            origin='make_qa_tables')

            # Plot phase vs channel
            phasechan_filename = os.path.join(output_folder,
                                         'field_{0}_phase_chan.{1}'.format(names[ii], outtype))

            if not os.path.exists(phasechan_filename):

                plotms(vis=ms_name,
                    xaxis='chan',
                    yaxis='phase',
                    ydatacolumn='corrected',
                    selectdata=True,
                    field=names[ii],
                    scan="",
                    spw="",
                    avgchannel="1",
                    avgtime="1e8",
                    correlation="",
                    averagedata=True,
                    avgbaseline=True,
                    transform=False,
                    extendflag=False,
                    plotrange=[],
                    # title='Phase vs Chan: Field {0} Scan {1}'.format(names[ii], jj),
                    xlabel='Chan',
                    ylabel='Phase',
                    showmajorgrid=False,
                    showminorgrid=False,
                    plotfile=phasechan_filename,
                    overwrite=True,
                    showgui=False)
            else:
                casalog.post(message="File {} already exists. Skipping".format(phasechan_filename),
                            origin='make_qa_tables')

            # Plot phase vs uvdist
            phaseuvdist_filename = os.path.join(output_folder,
                                         'field_{0}_phase_uvdist.{1}'.format(names[ii], outtype))

            if not os.path.exists(phaseuvdist_filename):

                plotms(vis=ms_name,
                    xaxis='uvdist',
                    yaxis='phase',
                    ydatacolumn='corrected',
                    selectdata=True,
                    field=names[ii],
                    scan="",
                    spw="",
                    correlation="",
                    avgchannel=str(chanavg),
                    avgtime='1e8',
                    averagedata=True,
                    avgbaseline=False,
                    transform=False,
                    extendflag=False,
                    plotrange=[],
                    # title='Phase vs UVDist: Field {0} Scan {1}'.format(names[ii], jj),
                    xlabel='uv-dist',
                    ylabel='Phase',
                    showmajorgrid=False,
                    showminorgrid=False,
                    plotfile=phaseuvdist_filename,
                    overwrite=True,
                    showgui=False)

            else:
                casalog.post(message="File {} already exists. Skipping".format(phaseuvdist_filename),
                            origin='make_qa_tables')

            # Plot amp vs phase
            ampphase_filename = os.path.join(output_folder,
                                         'field_{0}_amp_phase.{1}'.format(names[ii], outtype))

            if not os.path.exists(ampphase_filename):

                plotms(vis=ms_name,
                    xaxis='amp',
                    yaxis='phase',
                    ydatacolumn='corrected',
                    selectdata=True,
                    field=names[ii],
                    scan="",
                    spw="",
                    correlation="",
                    avgchannel=str(chanavg),
                    avgtime='1e8',
                    averagedata=True,
                    avgbaseline=False,
                    transform=False,
                    extendflag=False,
                    plotrange=[],
                    # title='Amp vs Phase: Field {0} Scan {1}'.format(names[ii], jj),
                    xlabel='Phase',
                    ylabel='Amp',
                    showmajorgrid=False,
                    showminorgrid=False,
                    plotfile=ampphase_filename,
                    overwrite=True,
                    showgui=False)
            else:
                casalog.post(message="File {} already exists. Skipping".format(ampphase_filename),
                            origin='make_qa_tables')

            # Plot uv-wave vs, amp - model residual
            # Check how good the point-source calibrator model is.

            ampresid_filename = os.path.join(output_folder,
                                         'field_{0}_ampresid_uvwave.{1}'.format(names[ii],
                                                                                outtype))

            if not os.path.exists(ampresid_filename):

                plotms(vis=ms_name,
                    xaxis='uvwave',
                    yaxis='amp',
                    ydatacolumn='corrected-model_scalar',
                    selectdata=True,
                    field=names[ii],
                    scan="",
                    spw="",
                    correlation="",
                    avgchannel=str(chanavg),
                    avgtime='1e8',
                    averagedata=True,
                    avgbaseline=False,
                    transform=False,
                    extendflag=False,
                    plotrange=[],
                    xlabel='uv-dist',
                    ylabel='Phase',
                    showmajorgrid=False,
                    showminorgrid=False,
                    plotfile=ampresid_filename,
                    overwrite=True,
                    showgui=False)

            else:
                casalog.post(message="File {} already exists. Skipping".format(ampresid_filename),
                             origin='make_qa_tables')

            # Plot amplitude vs antenna 1.
            # Check for ant outliers

            ampant_filename = os.path.join(output_folder,
                                         'field_{0}_amp_ant1.{1}'.format(names[ii],
                                                                         outtype))

            if not os.path.exists(ampant_filename):

                plotms(vis=ms_name,
                    xaxis='antenna1',
                    yaxis='amp',
                    ydatacolumn='corrected',
                    selectdata=True,
                    field=names[ii],
                    scan="",
                    spw="",
                    correlation="",
                    avgchannel=str(chanavg),
                    avgtime='1e8',
                    averagedata=True,
                    avgbaseline=False,
                    transform=False,
                    extendflag=False,
                    plotrange=[],
                    xlabel='antenna 1',
                    ylabel='Amp',
                    showmajorgrid=False,
                    showminorgrid=False,
                    plotfile=ampant_filename,
                    overwrite=True,
                    showgui=False)

            else:
                casalog.post(message="File {} already exists. Skipping".format(ampant_filename),
                             origin='make_qa_tables')


            # Plot phase vs antenna 1.
            # Check for ant outliers

            phaseant_filename = os.path.join(output_folder,
                                         'field_{0}_phase_ant1.{1}'.format(names[ii],
                                                                         outtype))

            if not os.path.exists(phaseant_filename):

                plotms(vis=ms_name,
                    xaxis='antenna1',
                    yaxis='phase',
                    ydatacolumn='corrected',
                    selectdata=True,
                    field=names[ii],
                    scan="",
                    spw="",
                    correlation="",
                    avgchannel=str(chanavg),
                    avgtime='1e8',
                    averagedata=True,
                    avgbaseline=False,
                    transform=False,
                    extendflag=False,
                    plotrange=[],
                    xlabel='antenna 1',
                    ylabel='Phase',
                    showmajorgrid=False,
                    showminorgrid=False,
                    plotfile=phaseant_filename,
                    overwrite=True,
                    showgui=False)

            else:
                casalog.post(message="File {} already exists. Skipping".format(phaseant_filename),
                             origin='make_qa_tables')



def extract_and_append_fieldnames(tablename, txtfilename,
                                  raise_importerror=False,
                                  overwrite_txt=False):
    '''
    plotms tables only contain the field ID numbers. Here we
    append a new column
    '''

    raise NotImplementedError("Table writing not yet implemented.")

    try:
        from astropy.table import Table, Column
    except ImportError as exc:
        if raise_importerror:
            raise exc
        else:
            casalog.post(message='astropy is not installed. Skipping adding field column.',
                         origin='extract_and_append_fieldnames')
            return

    from casatools import table

    tb = table()

    tb.open(f"{tablename}/FIELD")
    all_fieldnames = tb.getcol('NAME')
    tb.close()

    tab = Table.read(txtfilename,
                     format='ascii.commented_header',
                     header_start=header_start,
                     data_start=data_start)

    # Get field IDs
    field_id = tab['field']

    field_names = np.empty(field_id.shape, dtype=all_fieldnames.dtype)
    for idx in np.unique(field_id):
        field_names[field_id == idx] = all_fieldnames[idx]


    tab.append(Column(field_names, name='fieldname'))

    if overwrite_txt:
        tab.write(txtfilename, overwrite=True,
                  format='ascii.commented_header')
