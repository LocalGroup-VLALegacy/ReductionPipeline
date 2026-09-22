
import os
from glob import glob
import numpy as np

from casatools import logsink

casalog = logsink()

CALTABLE_MAPPING = {'bandpass_amp': {'output_folder': 'final_caltable_txt',
                                'search_string': '*.finalBPcal.tbl',
                                'x': 'freq',
                                'y': 'amp',
                                'iter': 'spw',
                                'colorby': 'ant'},
                    'bandpass_phase': {'output_folder': 'final_caltable_txt',
                                'search_string': '*.finalBPcal.tbl',
                                'x': 'freq',
                                'y': 'phase',
                                'iter': 'spw',
                                'colorby': 'ant'},
                    'delay': {'output_folder': 'final_caltable_txt',
                              'search_string': '*.finaldelay.tbl',
                              'x': 'freq',
                              'y': 'delay',
                              'iter': 'ant',
                              'colorby': 'spw'},
                    'BPinitialgain': {'output_folder': 'final_caltable_txt',
                                    'search_string': '*.finalBPinitialgain.tbl',
                                    'x': 'time',
                                    'y': 'phase',
                                    'iter': 'ant',
                                    'colorby': 'spw'},
                    'phaseshortgaincal': {'output_folder': 'final_caltable_txt',
                                    'search_string': '*.phaseshortgaincal.tbl',
                                    'x': 'time',
                                    'y': 'phase',
                                    'iter': 'ant',
                                    'colorby': 'spw'},
                    'ampgaincal_time': {'output_folder': 'final_caltable_txt',
                                    'search_string': '*.finalampgaincal.tbl',
                                    'x': 'time',
                                    'y': 'amp',
                                    'iter': 'ant',
                                    'colorby': 'spw'},
                    'ampgaincal_freq': {'output_folder': 'final_caltable_txt',
                                    'search_string': '*.finalampgaincal.tbl',
                                    'x': 'freq',
                                    'y': 'amp',
                                    'iter': 'ant',
                                    'colorby': 'spw'},
                    'phasegaincal': {'output_folder': 'final_caltable_txt',
                                    'search_string': '*.finalphasegaincal.tbl',
                                    'x': 'time',
                                    'y': 'phase',
                                    'iter': 'ant',
                                    'colorby': 'spw'}}


def _caltable_antenna_names(caltable_name):
    from casatools import table
    tb = table()
    tb.open(os.path.join(caltable_name, "ANTENNA"))
    names = tb.getcol('NAME')
    tb.close()
    return names


def _lookup_ant_names(ant_names, indices):
    '''
    ANTENNA2 in gain/delay/bandpass cal tables is the reference antenna
    used in the solve, but is -1 (no reference antenna recorded) for
    some table types (e.g. delay) -- plain fancy indexing would silently
    wrap a -1 around to the *last* antenna's name, so remap it to '*'
    (matching plotms's own placeholder for this case) instead.
    '''

    ant_names_ext = np.append(ant_names, '*')
    safe_idx = np.where(indices < 0, len(ant_names), indices)
    return ant_names_ext[safe_idx]


def _caltable_spw_freqs_ghz(caltable_name):
    '''
    Per-spw channel frequencies (GHz) from the cal table's own
    SPECTRAL_WINDOW subtable -- cal tables carry their own ANTENNA and
    SPECTRAL_WINDOW subtables, so this needs no access to the MS itself.
    '''
    from casatools import table
    tb = table()
    tb.open(os.path.join(caltable_name, "SPECTRAL_WINDOW"))
    nspw = tb.nrows()
    chan_freqs = {spw: tb.getcell('CHAN_FREQ', spw) / 1e9 for spw in range(nspw)}
    tb.close()
    return chan_freqs


def make_caltable_txt(ms_active, caltable_type,
                      caltable_mapping=CALTABLE_MAPPING,
                      outtype='ecsv', overwrite=False):
    '''
    Export calibration table solutions to per-spw or per-antenna tables
    for QA, reading the cal table directly with casatools instead of
    plotms. See definitions in `CALTABLE_MAPPING`.
    The naming convention follows the VLA pipeline table names from `hifv_finalcals`

    Cal tables (bandpass/delay/gain solutions) are tiny compared to the
    MS itself -- at most a few hundred thousand single-valued solutions,
    not per-channel visibilities -- so unlike `make_qa_tables`, there's
    no need to read them in chunks: each iteration value's rows and its
    CPARAM/FPARAM array are read in a single `getcol` call.

    The old plotms calls here never averaged (`averagedata=True` alone,
    with no `avgtime`/`avgchannel`/`avgbaseline` set, is a no-op), so
    this just flattens each unflagged (corr, chan, row) solution
    directly -- no weighted averaging is needed either.
    '''

    caltable_values = caltable_mapping[caltable_type]

    from casatools import table
    from astropy.table import Table
    tb = table()

    casalog.post(f"Running make_caltable_txt on {caltable_type} to export QA tables (casatools, no plotms).")
    print(f"Running make_caltable_txt on {caltable_type} to export QA tables (casatools, no plotms).")

    mySDM = ms_active.rstrip(".ms")

    output_folder = caltable_values['output_folder']
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    # Final BP cal table now includes the stage number and step
    caltable_name = glob(mySDM + caltable_values['search_string'])
    if len(caltable_name) == 0:
        raise ValueError("Cannot find {} table name.".format(caltable_values['search_string']))
    # Blindly assume we want the first name
    caltable_name = caltable_name[0]

    tb.open(caltable_name)
    partype = tb.getkeywords().get('ParType', 'Complex')
    data_col = 'CPARAM' if partype == 'Complex' else 'FPARAM'

    spw_vals = np.unique(tb.getcol("SPECTRAL_WINDOW_ID"))
    ant_vals = np.unique(tb.getcol("ANTENNA1"))
    tb.close()

    ant_names = _caltable_antenna_names(caltable_name)
    chan_freqs = _caltable_spw_freqs_ghz(caltable_name)

    # Make txt files per SPW (or per antenna).
    iteraxis = spw_vals if caltable_values['iter'] == 'spw' else ant_vals

    tb.open(caltable_name)

    for ii in iteraxis:

        print("On {0}: {1}".format(caltable_values['iter'], ii))
        casalog.post("On {0}: {1}".format(caltable_values['iter'], ii))

        # Output text names
        # name_xaxis_yaxis_iter num
        out_filename = '{0}_{1}_{2}_{3}{4}.{5}'.format(os.path.splitext(caltable_name)[0],
                                                       caltable_values['x'],
                                                       caltable_values['y'],
                                                       caltable_values['iter'],
                                                       ii, outtype)

        thisplotfile = os.path.join(output_folder, out_filename)

        if not overwrite and os.path.exists(thisplotfile):
            casalog.post("File {} already exists. Skipping".format(thisplotfile))
            continue

        if caltable_values['iter'] == 'spw':
            sub = tb.query("SPECTRAL_WINDOW_ID=={0}".format(ii))
        else:
            sub = tb.query("ANTENNA1=={0}".format(ii))

        if sub.nrows() == 0:
            sub.close()
            continue

        data = sub.getcol(data_col)
        flag = sub.getcol('FLAG')
        ant1 = sub.getcol('ANTENNA1')
        ant2 = sub.getcol('ANTENNA2')
        spw = sub.getcol('SPECTRAL_WINDOW_ID')
        scan = sub.getcol('SCAN_NUMBER')
        time = sub.getcol('TIME')
        sub.close()

        ncorr, nchan, _ = data.shape

        if caltable_values['y'] == 'amp':
            yval = np.abs(data)
        elif caltable_values['y'] == 'phase':
            yval = np.degrees(np.angle(data))
        elif caltable_values['y'] == 'delay':
            yval = data.real
        else:
            raise ValueError("Unrecognized y axis {}".format(caltable_values['y']))

        # The x axis' broadcasting shape differs between the channelized
        # (bandpass) and single-valued (delay/gain) cases.
        if caltable_values['x'] == 'freq':
            if nchan > 1:
                # spw is fixed (== ii) for every row here since iter == 'spw'.
                xval = np.broadcast_to(chan_freqs[ii][np.newaxis, :, np.newaxis], data.shape)
            else:
                # One representative (mean) frequency per row's spw --
                # matches the old plotms behaviour of plotting a
                # non-channelized solution against its spw's frequency.
                row_freq = np.array([chan_freqs[s].mean() for s in spw])
                xval = np.broadcast_to(row_freq[np.newaxis, np.newaxis, :], data.shape)
        elif caltable_values['x'] == 'time':
            xval = np.broadcast_to(time[np.newaxis, np.newaxis, :], data.shape)
        else:
            raise ValueError("Unrecognized x axis {}".format(caltable_values['x']))

        valid = ~flag
        if not valid.any():
            casalog.post("No unflagged solutions for {0} {1}. Skipping.".format(caltable_values['iter'], ii))
            continue

        corr_idx = np.broadcast_to(np.arange(ncorr)[:, np.newaxis, np.newaxis], data.shape)
        chan_idx = np.broadcast_to(np.arange(nchan)[np.newaxis, :, np.newaxis], data.shape)
        ant1_full = np.broadcast_to(ant1[np.newaxis, np.newaxis, :], data.shape)
        ant2_full = np.broadcast_to(ant2[np.newaxis, np.newaxis, :], data.shape)
        spw_full = np.broadcast_to(spw[np.newaxis, np.newaxis, :], data.shape)
        scan_full = np.broadcast_to(scan[np.newaxis, np.newaxis, :], data.shape)
        time_full = np.broadcast_to(time[np.newaxis, np.newaxis, :], data.shape)

        out_table = Table({
            'corr': corr_idx[valid],
            'chan': chan_idx[valid],
            'ant1': ant1_full[valid], 'ant1name': _lookup_ant_names(ant_names, ant1_full[valid]),
            'ant2': ant2_full[valid], 'ant2name': _lookup_ant_names(ant_names, ant2_full[valid]),
            'spw': spw_full[valid],
            'scan': scan_full[valid],
            'time': time_full[valid],
            caltable_values['x']: xval[valid],
            caltable_values['y']: yval[valid],
        })
        out_table.meta.update(dict(vis=str(caltable_name), caltable_type=caltable_type))
        out_table.write(thisplotfile, format='ascii.ecsv', overwrite=True)

    tb.close()


def make_all_caltable_txt(msname, caltable_mapping=CALTABLE_MAPPING):

    for key in caltable_mapping:
        make_caltable_txt(msname, key,
                          caltable_mapping=caltable_mapping)


# hifv_plotsummary amp vs freq coloured by ant1
# plotms(vis='14B-212.sb30132182.eb30190975.57045.74273331018.continuum.ms',
#        xaxis='freq', yaxis='amp', ydatacolumn='corrected', field='J1923-2104',
#        spw='0,1,2,3,4,5,6,7', correlation='LL,RR', intent='CALIBRATE_AMPLI#UNSPECIFIED,CALIBRATE_PHASE#UNSPECIFIED', avgtime='1e8', avgscan=True, avgantenna=True, coloraxis='antenna1', plotrange=[0, 0, 0, 0], plotfile='14B-212.sb30132182.eb30190975.57045.74273331018.continuum.ms-J1923-2104-bb12-PHASE-amp_vs_freq-LL_RR.png',
#        overwrite=True, showgui=False, clearplots=True)
