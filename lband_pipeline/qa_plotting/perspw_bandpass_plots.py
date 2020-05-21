
import os
from glob import glob


def make_spw_bandpass_plots(ms_active,
                            bp_folder="finalBPcal_plots",
                            outtype='png'):
    '''
    Make a per-SPW bandpass amp and phase plots for closer
    inspection.
    '''

    # Will need to updated for CASA 6
    from taskinit import tb

    from tasks import plotcal

    mySDM = ms_active.rstrip(".ms")

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
        filename = 'finalBPcal_amp_spw_' + str(ii) + outtype

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

        filename = 'finalBPcal_phase_spw_' + str(ii) + outtype
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
