
import os
from glob import glob

from casatools import logsink

casalog = logsink()


def make_spw_bandpass_plots(ms_active,
                            bp_folder="finalBPcal_plots",
                            outtype='png'):
    '''
    Make a per-SPW bandpass amp and phase plots for closer
    inspection.
    '''

    # Will need to updated for CASA 6
    # from taskinit import tb
    from casatools import table

    from casatasks import plotcal

    mySDM = ms_active.rstrip(".ms")

    if not os.path.exists(bp_folder):
        os.mkdir(bp_folder)

    tb = table()

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
        filename = 'finalBPcal_amp_spw_' + str(ii) + "." + outtype

        if os.path.exists(os.path.join(bp_folder, filename)):
            syscommand = 'rm -f ' + filename
            os.system(syscommand)

        plotcal(caltable=finalbpcal_name,
                xaxis='freq',
                yaxis='amp',
                poln='',
                field='',
                antenna='',
                spw=str(ii),
                timerange='',
                subplot=111,
                overplot=False,
                clearpanel='Auto',
                iteration='',
                showflags=False,
                plotsymbol='o',
                plotcolor='blue',
                markersize=5.0,
                fontsize=10.0,
                showgui=False,
                figfile=os.path.join(bp_folder, filename))

        filename = 'finalBPcal_phase_spw_' + str(ii) + "." + outtype
        if os.path.exists(os.path.join(bp_folder, filename)):
            syscommand = 'rm -f ' + filename
            os.system(syscommand)

        plotcal(caltable=finalbpcal_name,
                xaxis='freq',
                yaxis='phase',
                poln='',
                field='',
                antenna='',
                spw=str(ii),
                timerange='',
                subplot=111,
                overplot=False,
                clearpanel='Auto',
                iteration='',
                showflags=False,
                plotsymbol='o',
                plotcolor='blue',
                markersize=5.0,
                fontsize=10.0,
                showgui=False,
                figfile=os.path.join(bp_folder, filename))


def make_bandpass_txt(ms_active, output_folder='finalBPcal_txt'):
    '''
    Output an amplitude and phase txt file from the bandpass
    table.

    Expects to find a the "*.finalBPcal.tbl" produced by the VLA pipeline.
    A `ValueError` is raise when no final BP cal table is found.

    Two output text files are created: freq. vs. amp and freq. vs. phase.

    '''

    # from taskinit import tb, casalog
    from casatools import table

    tb = table()

    from casaplotms import plotms

    casalog.post("Running make_bandpass_txt to export txt files for QA.")
    print("Running make_bandpass_txt to export txt files for QA.")

    mySDM = ms_active.rstrip(".ms")

    tb.open(ms_active + "/SPECTRAL_WINDOW")
    nspws = tb.getcol("NAME").shape[0]
    tb.close()

    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    # Final BP cal table now includes the stage number and step
    finalbpcal_name = glob(mySDM + '*.finalBPcal.tbl')
    if len(finalbpcal_name) == 0:
        raise ValueError("Cannot find finalBPcal table name.")
    # Blindly assume we want the first name
    finalbpcal_name = finalbpcal_name[0]

    # Make txt files per SPW.
    for ii in range(nspws):

        print("On spectral window: {}".format(ii))
        casalog.post("On spectral window: {}".format(ii))

        # Output text names
        amp_filename = '{0}_amp_spw{1}.txt'.format(os.path.splitext(finalbpcal_name)[0], ii)
        phase_filename = '{0}_phase_spw{1}.txt'.format(os.path.splitext(finalbpcal_name)[0], ii)

        thisplotfile = os.path.join(output_folder, amp_filename)

        if not os.path.exists(thisplotfile):

            plotms(vis=finalbpcal_name,
                   xaxis='freq',
                   yaxis='amp',
                   field='',
                   antenna='',
                   spw=str(ii),
                   timerange='',
                   showgui=False,
                   # avgtime='1e8',
                   averagedata=True,
                   plotfile=thisplotfile)
        else:
            casalog.post("File {} already exists. Skipping".format(thisplotfile))

        thisplotfile = os.path.join(output_folder, phase_filename)

        if not os.path.exists(thisplotfile):

            plotms(vis=finalbpcal_name,
                xaxis='freq',
                yaxis='phase',
                field='',
                antenna='',
                spw=str(ii),
                timerange='',
                showgui=False,
                # avgtime='1e8',
                averagedata=True,
                plotfile=thisplotfile)

        else:
            casalog.post("File {} already exists. Skipping".format(thisplotfile))
