
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

    from casatools import table
    from casatools import msmetadata

    tb = table()
    msmd = msmetadata()

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


# CASA/plotms Stokes correlation type codes (see casacore Stokes.h).
STOKES_CORR_TYPES = {
    1: 'I', 2: 'Q', 3: 'U', 4: 'V',
    5: 'RR', 6: 'RL', 7: 'LR', 8: 'LL',
    9: 'XX', 10: 'XY', 11: 'YX', 12: 'YY',
}


def _spw_metadata(ms_name):
    '''
    Per-spw channel frequencies, the DATA_DESC_ID to query for each spw,
    and the correlation labels (e.g. RR, LL) for each spw.
    '''

    from casatools import table
    tb = table()

    tb.open(os.path.join(ms_name, "SPECTRAL_WINDOW"))
    nspw = tb.nrows()
    chan_freqs = {spw: tb.getcell('CHAN_FREQ', spw) for spw in range(nspw)}
    tb.close()

    tb.open(os.path.join(ms_name, "DATA_DESCRIPTION"))
    dd_spw_id = tb.getcol('SPECTRAL_WINDOW_ID')
    dd_pol_id = tb.getcol('POLARIZATION_ID')
    tb.close()

    tb.open(os.path.join(ms_name, "POLARIZATION"))
    pol_corr_types = {pol: tb.getcell('CORR_TYPE', pol) for pol in range(tb.nrows())}
    tb.close()

    # Map each spw to the data_desc_id and correlation labels to query.
    # Normally spw and data_desc_id are 1-to-1, but build the mapping
    # explicitly from the DATA_DESCRIPTION table to be safe.
    spw_to_ddid = {}
    spw_to_corrlabels = {}
    for dd_id in range(len(dd_spw_id)):
        spw_id = dd_spw_id[dd_id]
        if spw_id in spw_to_ddid:
            continue
        spw_to_ddid[spw_id] = dd_id
        spw_to_corrlabels[spw_id] = [STOKES_CORR_TYPES.get(code, str(code))
                                     for code in pol_corr_types[dd_pol_id[dd_id]]]

    return chan_freqs, spw_to_ddid, spw_to_corrlabels


def _adaptive_chunk_nrows(nchan, ncorr, target_bytes=150_000_000,
                          min_rows=50, max_rows=20000):
    '''
    Pick a row-chunk size so that one chunk's DATA/FLAG/WEIGHT arrays
    stay near `target_bytes`. `target_bytes` is kept well below the
    ~2 GB memory budget to leave headroom for temporary arrays created
    while reducing each chunk.
    '''

    bytes_per_row = nchan * ncorr * 25  # complex128 data + bool flag + float weight
    nrows = target_bytes // max(bytes_per_row, 1)
    return int(np.clip(nrows, min_rows, max_rows))


def _get_weight_mask(sub, start, nrow, flag, use_weight_spectrum):
    '''
    Return a (ncorr, nchan, nrow) weight array with flagged visibilities
    zeroed out. Prefers WEIGHT_SPECTRUM (per-channel) when it is actually
    populated for this selection, otherwise falls back to WEIGHT
    (per-correlation, broadcast over channel) -- WEIGHT_SPECTRUM is
    frequently present in the MS schema but left unfilled.
    '''

    if use_weight_spectrum:
        weight = sub.getcol('WEIGHT_SPECTRUM', start, nrow)
    else:
        weight = sub.getcol('WEIGHT', start, nrow)[:, np.newaxis, :] * np.ones_like(flag, dtype=float)

    weight = np.where(flag, 0., weight)

    return weight


def _weight_spectrum_usable(sub):
    '''
    Cheap check: try reading a single row of WEIGHT_SPECTRUM. Returns
    False if the column is unpopulated for this selection.
    '''

    if 'WEIGHT_SPECTRUM' not in sub.colnames():
        return False

    try:
        sub.getcol('WEIGHT_SPECTRUM', 0, 1)
        return True
    except RuntimeError:
        return False


def _reduce_spw_scan_field(sub, nchan, corr_labels, ydatacolumn,
                           has_model, want_resid, chunk_nrows,
                           use_weight_spectrum):
    '''
    Single chunked pass over one (scan, field, spw) selection that builds
    all of the weighted, complex-averaged reductions needed for the QA
    tables in one read of the MS:

    - shape A: averaged over channel & baseline, resolved per timestamp
    - shape B: averaged over time & baseline, resolved per channel
    - shape C: averaged over channel & time, resolved per baseline
    - shape D: averaged over channel only, resolved per row (time x baseline)

    Complex visibilities are weight-averaged as complex numbers (never as
    separately-averaged amp/phase scalars) so that phase wrapping is
    handled correctly; amp/phase are only taken at the very end.

    Returns a dict of finalized per-spw numpy arrays.
    '''

    n = sub.nrows()
    ncorr = len(corr_labels)

    time_col = sub.getcol('TIME')
    ant1_col = sub.getcol('ANTENNA1')
    ant2_col = sub.getcol('ANTENNA2')
    uvw_col = sub.getcol('UVW')
    uvdist_col = np.hypot(uvw_col[0], uvw_col[1])
    # A row can have FLAG_ROW=True while its per-channel FLAG entries are
    # still False (a real, if inconsistent, MS state) -- respect it.
    flagrow_col = sub.getcol('FLAG_ROW')

    uniq_times, time_idx = np.unique(time_col, return_inverse=True)

    bl_key = ant1_col.astype(np.int64) * 2048 + ant2_col.astype(np.int64)
    uniq_bl_key, bl_idx = np.unique(bl_key, return_inverse=True)
    uniq_ant1 = (uniq_bl_key // 2048).astype(int)
    uniq_ant2 = (uniq_bl_key % 2048).astype(int)

    bl_counts = np.bincount(bl_idx, minlength=len(uniq_bl_key))
    bl_uvdist = np.bincount(bl_idx, weights=uvdist_col,
                            minlength=len(uniq_bl_key)) / bl_counts

    # Shape A accumulators: (ncorr, n_time)
    shapeA_sum = np.zeros((ncorr, len(uniq_times)), dtype=complex)
    shapeA_wsum = np.zeros((ncorr, len(uniq_times)))

    # Shape B accumulators: (ncorr, nchan)
    shapeB_sum = np.zeros((ncorr, nchan), dtype=complex)
    shapeB_wsum = np.zeros((ncorr, nchan))

    # Shape C accumulators: (ncorr, n_baseline)
    shapeC_sum = np.zeros((ncorr, len(uniq_bl_key)), dtype=complex)
    shapeC_wsum = np.zeros((ncorr, len(uniq_bl_key)))
    shapeC_model_sum = np.zeros((ncorr, len(uniq_bl_key)), dtype=complex)
    shapeC_model_wsum = np.zeros((ncorr, len(uniq_bl_key)))

    # Shape D: appended per chunk, then concatenated.
    shapeD_chunks = []

    for start in range(0, n, chunk_nrows):
        nr = min(chunk_nrows, n - start)

        data = sub.getcol(ydatacolumn, start, nr)
        flag = sub.getcol('FLAG', start, nr) | flagrow_col[start:start + nr][np.newaxis, np.newaxis, :]
        weight = _get_weight_mask(sub, start, nr, flag, use_weight_spectrum)

        # Shape B: sum over rows in this chunk.
        shapeB_sum += (data * weight).sum(axis=2)
        shapeB_wsum += weight.sum(axis=2)

        # Collapse over channel -> per-row, per-corr complex average.
        w_chan_sum = weight.sum(axis=1)
        data_chan_avg = np.divide((data * weight).sum(axis=1), w_chan_sum,
                                  out=np.zeros((ncorr, nr), dtype=complex),
                                  where=w_chan_sum > 0)

        chunk_time_idx = time_idx[start:start + nr]
        chunk_bl_idx = bl_idx[start:start + nr]

        for ci in range(ncorr):
            np.add.at(shapeA_sum[ci], chunk_time_idx, data_chan_avg[ci] * w_chan_sum[ci])
            np.add.at(shapeA_wsum[ci], chunk_time_idx, w_chan_sum[ci])

            np.add.at(shapeC_sum[ci], chunk_bl_idx, data_chan_avg[ci] * w_chan_sum[ci])
            np.add.at(shapeC_wsum[ci], chunk_bl_idx, w_chan_sum[ci])

        if want_resid and has_model:
            model = sub.getcol('MODEL_DATA', start, nr)
            model_chan_avg = np.divide((model * weight).sum(axis=1), w_chan_sum,
                                       out=np.zeros((ncorr, nr), dtype=complex),
                                       where=w_chan_sum > 0)
            # Keep the model average complex and accumulate it the same way
            # as the data (shapeC_sum/wsum) -- the scalar amplitude
            # difference is only taken once, after both averages are
            # complete (see `residC` below). Taking abs() before fully
            # averaging over channel+time would bias the result high
            # (Rician bias), especially for near-zero model amplitudes
            # (e.g. unpolarized-source cross-hand correlations).
            for ci in range(ncorr):
                np.add.at(shapeC_model_sum[ci], chunk_bl_idx, model_chan_avg[ci] * w_chan_sum[ci])
                np.add.at(shapeC_model_wsum[ci], chunk_bl_idx, w_chan_sum[ci])

        valid = w_chan_sum > 0
        shapeD_chunks.append({
            'ant1': np.broadcast_to(ant1_col[start:start + nr], (ncorr, nr))[valid],
            'ant2': np.broadcast_to(ant2_col[start:start + nr], (ncorr, nr))[valid],
            'time': np.broadcast_to(time_col[start:start + nr], (ncorr, nr))[valid],
            'corr': np.broadcast_to(np.array(corr_labels)[:, np.newaxis], (ncorr, nr))[valid],
            'data': data_chan_avg[valid],
        })

    def _finalize(csum, wsum):
        with np.errstate(invalid='ignore', divide='ignore'):
            avg = np.divide(csum, wsum, out=np.full_like(csum, np.nan), where=wsum > 0)
        return np.abs(avg), np.degrees(np.angle(avg))

    ampA, phaseA = _finalize(shapeA_sum, shapeA_wsum)
    ampB, phaseB = _finalize(shapeB_sum, shapeB_wsum)
    ampC, phaseC = _finalize(shapeC_sum, shapeC_wsum)

    # Amplitude of the fully-averaged (channel & time) model, subtracted
    # from the amplitude of the fully-averaged data -- abs() is applied
    # only once, after averaging, to avoid the Rician bias described above.
    with np.errstate(invalid='ignore', divide='ignore'):
        model_avg = np.divide(shapeC_model_sum, shapeC_model_wsum,
                              out=np.full_like(shapeC_model_sum, np.nan),
                              where=shapeC_model_wsum > 0)
    residC = ampC - np.abs(model_avg)

    shapeD = {}
    if shapeD_chunks:
        for key in ('ant1', 'ant2', 'time', 'corr'):
            shapeD[key] = np.concatenate([chunk[key] for chunk in shapeD_chunks])
        data_D = np.concatenate([chunk['data'] for chunk in shapeD_chunks])
        shapeD['amp'] = np.abs(data_D)
        shapeD['phase'] = np.degrees(np.angle(data_D))

    return dict(
        time=uniq_times, ampA=ampA, phaseA=phaseA, wsumA=shapeA_wsum,
        chan=np.arange(nchan), ampB=ampB, phaseB=phaseB, wsumB=shapeB_wsum,
        ant1=uniq_ant1, ant2=uniq_ant2, uvdist=bl_uvdist,
        ampC=ampC, phaseC=phaseC, wsumC=shapeC_wsum, residC=residC,
        wsum_residC=shapeC_model_wsum,
        shapeD=shapeD,
    )


def make_qa_tables(ms_name, output_folder='scan_plots_txt',
                   outtype='ecsv', overwrite=True,
                   chanavg=4096,):

    '''
    Export averaged amp/phase QA tables per field/scan, without plotms.

    Reproduces the same set of products as the old plotms-based version
    (amp/phase vs. time/chan/uvdist/antenna1, amp vs. phase, and the
    amp-model residual vs. uvwave for calibrators), but reads the MS
    directly with `casatools.table` in row-chunks and does the averaging
    with numpy, so a single scan/field/spw never needs more than a small,
    bounded amount of memory regardless of the number of channels or rows.

    Like the original plotms calls, spw="" here means "loop over every
    spw" (each spw's own channels are averaged within that spw), *not*
    "average across spws" -- matching plotms's own `avgspw=False` default.
    Each output table therefore keeps an `spw` column distinguishing rows
    from different spectral windows.

    NOTE: the on-disk format here (astropy ECSV) is not what the current
    QAPlotter weblog tool expects (it parses plotms's native txt export).
    A small follow-up change to QAPlotter's `read_casa_txt()` (read the
    ECSV directly with `Table.read`, use `tab.meta` for what used to be
    the header comment fields) is needed before the interactive weblog
    will pick these up again.
    '''

    from casatools import table
    from casatools import msmetadata
    from astropy.table import Table, vstack

    _C = 299792458.0  # speed of light, m/s

    tb = table()
    msmd = msmetadata()

    casalog.post("Running make_qa_tables to export QA tables (casatools, no plotms).")
    print("Running make_qa_tables to export QA tables (casatools, no plotms).")

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

    # Loop through scans
    scanlist_dict = {}

    # Loop through fields
    msmd.open(ms_name)
    for ii in range(numFields):
        scanlist_dict[names[ii]] = msmd.scansforfield(names[ii])
    msmd.close()

    casalog.post(message="Fields are: {}".format(names), origin='make_qa_tables')
    casalog.post(message="Calibrator fields are: {}".format(names[is_calibrator]), origin='make_qa_tables')

    print("Fields are: {}".format(names))
    print("Calibrator fields are: {}".format(names[is_calibrator]))

    chan_freqs, spw_to_ddid, spw_to_corrlabels = _spw_metadata(ms_name)
    all_spws = sorted(spw_to_ddid.keys())

    tb.open(ms_name)
    has_model = 'MODEL_DATA' in tb.colnames()

    # WEIGHT_SPECTRUM usability is a static property of a given spw's data
    # (it's either fully populated or entirely absent), so check it once
    # per spw rather than on every scan/field -- repeating the check is
    # wasteful and, when unusable, throws (and SEVERE-logs) an exception
    # on every call.
    spw_uses_weight_spectrum = {}
    for spw, ddid in spw_to_ddid.items():
        wspw_sub = tb.query("DATA_DESC_ID=={0}".format(ddid))
        spw_uses_weight_spectrum[spw] = (wspw_sub.nrows() > 0
                                         and _weight_spectrum_usable(wspw_sub))
        wspw_sub.close()

    # Loop through fields. Make separate tables only for different targets.

    for ii in range(numFields):
        casalog.post(message="On field {}".format(names[ii]), origin='make_qa_plots')
        print("On field {}".format(names[ii]))

        # If field has data, continue. If not skip and log it.
        if not has_data[ii]:
            casalog.post(message='Field {} has no data in the table. Skipping.'.format(names[ii]),
                         origin='make_qa_plots')
            continue

        this_is_calib = is_calibrator[ii]

        # Loop through scans
        for this_scan in scanlist_dict[names[ii]]:

            casalog.post(message="On scan {}".format(this_scan), origin='make_qa_plots')
            print("On scan {}".format(this_scan))

            def outname(tab_type):
                return os.path.join(output_folder,
                                    'field_{0}_{1}.scan_{2}.{3}'.format(names[ii], tab_type,
                                                                        this_scan, outtype))

            kinds = ['amp_time', 'amp_chan', 'amp_uvdist']
            if this_is_calib:
                kinds += ['phase_time', 'phase_chan', 'phase_uvdist',
                         'amp_ant1', 'phase_ant1', 'amp_phase', 'ampresid_uvwave']

            if not overwrite and all(os.path.exists(outname(kind)) for kind in kinds):
                casalog.post(message="All tables for field {0} scan {1} already exist. Skipping."
                             .format(names[ii], this_scan), origin='make_qa_tables')
                continue

            if this_is_calib:
                casalog.post("This is a calibrator. Exporting phase info, too.")
                print("This is a calibrator. Exporting phase info, too.")

            # Per-kind row batches (one per spw with data), concatenated after the spw loop.
            rows = {kind: [] for kind in kinds}

            for spw in all_spws:
                ddid = spw_to_ddid[spw]
                corr_labels = spw_to_corrlabels[spw]
                nchan = len(chan_freqs[spw])
                ncorr = len(corr_labels)

                if nchan > chanavg:
                    # Original plotms behaviour used avgchannel=str(chanavg): a window
                    # smaller than nchan would produce several partially-averaged points
                    # rather than one. All current pipeline callers pass chanavg=4096,
                    # which is >= every spw's channel count, so full-spw averaging below
                    # is equivalent in practice; only warn if that assumption breaks.
                    casalog.post(message="spw {0} has {1} channels > chanavg={2}; "
                                 "averaging over the full spw anyway.".format(spw, nchan, chanavg),
                                 origin='make_qa_tables')

                sub = tb.query("SCAN_NUMBER=={0} AND FIELD_ID=={1} AND DATA_DESC_ID=={2}"
                               .format(this_scan, ii, ddid))
                if sub.nrows() == 0:
                    sub.close()
                    continue

                try:
                    chunk_nrows = _adaptive_chunk_nrows(nchan, ncorr)
                    want_resid = this_is_calib and has_model
                    red = _reduce_spw_scan_field(sub, nchan, corr_labels,
                                                 ydatacolumn='CORRECTED_DATA',
                                                 has_model=has_model,
                                                 want_resid=want_resid,
                                                 chunk_nrows=chunk_nrows,
                                                 use_weight_spectrum=spw_uses_weight_spectrum[spw])
                except Exception as exc:
                    casalog.post(message="Failed reducing field {0} scan {1} spw {2}: {3}"
                                 .format(names[ii], this_scan, spw, exc),
                                 origin='make_qa_tables')
                    continue
                finally:
                    sub.close()

                freq_mean = chan_freqs[spw].mean()

                for ci, corr in enumerate(corr_labels):

                    # Shape A: amp/phase vs. time (baseline & channel avg)
                    valid = red['wsumA'][ci] > 0
                    if valid.any():
                        rows['amp_time'].append(Table({
                            'spw': np.full(valid.sum(), spw), 'time': red['time'][valid],
                            'corr': [corr] * valid.sum(), 'amp': red['ampA'][ci][valid]}))
                        if this_is_calib:
                            rows['phase_time'].append(Table({
                                'spw': np.full(valid.sum(), spw), 'time': red['time'][valid],
                                'corr': [corr] * valid.sum(), 'phase': red['phaseA'][ci][valid]}))

                    # Shape B: amp/phase vs. channel (time & baseline avg)
                    validB = red['wsumB'][ci] > 0
                    if validB.any():
                        rows['amp_chan'].append(Table({
                            'spw': np.full(validB.sum(), spw), 'chan': red['chan'][validB],
                            'freq': chan_freqs[spw][validB],
                            'corr': [corr] * validB.sum(), 'amp': red['ampB'][ci][validB]}))
                        if this_is_calib:
                            rows['phase_chan'].append(Table({
                                'spw': np.full(validB.sum(), spw), 'chan': red['chan'][validB],
                                'freq': chan_freqs[spw][validB],
                                'corr': [corr] * validB.sum(), 'phase': red['phaseB'][ci][validB]}))

                    # Shape C: amp/phase vs. uvdist / antenna1 (chan & time avg, per baseline)
                    validC = red['wsumC'][ci] > 0
                    if validC.any():
                        n_valid = int(validC.sum())
                        base_cols = {
                            'spw': np.full(n_valid, spw),
                            'ant1': red['ant1'][validC], 'ant2': red['ant2'][validC],
                            'uvdist': red['uvdist'][validC], 'corr': [corr] * n_valid,
                        }
                        rows['amp_uvdist'].append(Table({**base_cols, 'amp': red['ampC'][ci][validC]}))
                        if this_is_calib:
                            rows['phase_uvdist'].append(Table({**base_cols, 'phase': red['phaseC'][ci][validC]}))
                            rows['amp_ant1'].append(Table({**base_cols, 'amp': red['ampC'][ci][validC]}))
                            rows['phase_ant1'].append(Table({**base_cols, 'phase': red['phaseC'][ci][validC]}))

                    # Amp-model residual vs. uvwave (calibrators only)
                    if this_is_calib and want_resid:
                        validR = red['wsum_residC'][ci] > 0
                        if validR.any():
                            n_valid = int(validR.sum())
                            rows['ampresid_uvwave'].append(Table({
                                'spw': np.full(n_valid, spw),
                                'ant1': red['ant1'][validR], 'ant2': red['ant2'][validR],
                                'uvdist': red['uvdist'][validR],
                                'uvwave': red['uvdist'][validR] * freq_mean / _C,
                                'corr': [corr] * n_valid,
                                'resid': red['residC'][ci][validR]}))

                # Shape D: amp vs. phase (channel avg only, per row)
                if this_is_calib and red['shapeD']:
                    n_valid = len(red['shapeD']['amp'])
                    if n_valid > 0:
                        rows['amp_phase'].append(Table({
                            'spw': np.full(n_valid, spw),
                            'ant1': red['shapeD']['ant1'], 'ant2': red['shapeD']['ant2'],
                            'time': red['shapeD']['time'], 'corr': red['shapeD']['corr'],
                            'amp': red['shapeD']['amp'], 'phase': red['shapeD']['phase']}))

            # Write out each requested table.
            for kind in kinds:
                fname = outname(kind)
                if not overwrite and os.path.exists(fname):
                    casalog.post(message="File {} already exists. Skipping".format(fname),
                                origin='make_qa_tables')
                    continue

                if not rows[kind]:
                    casalog.post(message="No valid data for field {0} scan {1} {2}. Skipping."
                                 .format(names[ii], this_scan, kind), origin='make_qa_tables')
                    continue

                out_table = vstack(rows[kind])
                # PyYAML's safe dumper (used by the ecsv writer) can't
                # represent numpy scalar types (e.g. numpy.str_ from
                # tb.getcol), so cast everything to plain Python types.
                out_table.meta.update(dict(field=str(names[ii]), scan=int(this_scan),
                                           vis=str(ms_name), ydatacolumn='corrected'))
                out_table.write(fname, format='ascii.ecsv', overwrite=True)

    tb.close()



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
