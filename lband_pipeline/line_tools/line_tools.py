
import os
from glob import glob
from copy import copy, deepcopy
import numpy as np
import shutil
import scipy.ndimage as nd

from tasks import bandpass

import pipeline.hif.heuristics.findrefant as findrefant


def bandpass_with_gap_interpolation_deprecated(myvis, context, refantignore="",
                                               search_string="test",
                                               task_string="hifv_testBPdcals"):
    '''
    Re-do the bandpass accounting for flagged gaps.

    Looks for and uses the standard pipeline naming from
    the VLA pipeline.

    Also see I-Da Chiang's implementation:
    https://github.com/z0mgs/EveryTHINGS/blob/master/everythings_bandpass.py

    DEPRECATED as of 22/07/20. See new gap interpolation method below.
    The `bandpass` task only uses nearest neighbour interpolation across the gap. We want to use
    more channels on each side for a better interpolation across the gap.

    '''

    # Look for BP table
    bpname = glob("{0}.{1}.s*_4.{2}BPcal.tbl".format(myvis, task_string, search_string))

    # test and final cal steps will have 1 match:
    if len(bpname) == 1:
        bpname = bpname[0]
    elif len(bpname) == 2:
        # One table for each semifinal cal call.
        # Grab the second call table.
        bpname = sorted(bpname,
                        key=lambda x: int(x.split("_4.BPcal.tbl")[0].split(".s")[-1]))[-1]
    elif len(bpname) == 0:
        raise ValueError("No matches to the BP table found.")
    else:
        raise ValueError("Found too many matches to the BP table."
                         " Unclear which should be used: {0}".format(bpname))

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

    del_tbl = glob("{0}.{1}.s*_2.{2}delay.tbl".format(myvis, task_string, search_string))

    # test and final cal steps will have 1 match:
    if len(del_tbl) == 1:
        del_tbl = del_tbl[0]
    elif len(del_tbl) == 2:
        # One table for each semifinal cal call.
        # Grab the second call table.
        del_tbl = sorted(del_tbl,
                        key=lambda x: int(x.split("_2.delay.tbl")[0].split(".s")[-1]))[-1]
    elif len(del_tbl) == 0:
        raise ValueError("No matches to the BP table found.")
    else:
        raise ValueError("Found too many matches to the delay table."
                         " Unclear which should be used: {0}".format(del_tbl))

    # Slight difference in BP initial gain table names
    if task_string == "hifv_testBPdcals":
        tabname_string = "BPdinitialgain"
    else:
        tabname_string = "BPinitialgain"

    BPinit_tbl = glob("{0}.{1}.s*_3.{2}{3}.tbl".format(myvis,
                                                       task_string,
                                                       search_string,
                                                       tabname_string))
    # test and final cal steps will have 1 match:
    if len(BPinit_tbl) == 1:
        BPinit_tbl = BPinit_tbl[0]
    elif len(BPinit_tbl) == 2:
        # One table for each semifinal cal call.
        # Grab the second call table.
        BPinit_tbl = sorted(BPinit_tbl,
                            key=lambda x: int(x.split("_3.{}.tbl".format(tabname_string))[0].split(".s")[-1]))[-1]
    elif len(BPinit_tbl) == 0:
        raise ValueError("No matches to the BP table found.")
    else:
        raise ValueError("Found too many matches to the BP initgain table."
                         " Unclear which should be used: {0}".format(BPinit_tbl))

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


def bandpass_with_gap_interpolation(myvis, hi_spwid,
                                    search_string="test",
                                    task_string="hifv_testBPdcals"):
    '''
    Improved interpolation across bandpass gaps. This time without needing to recompute the bandpass!

    Note that the code will work for any channel gap (of a reasonable width; ~<20% of channels) but
    we're only using it for HI right now. This is because the MW HI that is flagged on the BP calibrator
    is well-behaved and reasonably flat across the gap. Other SPW gaps (e.g., RFI in the OH1612 SPW) tend
    to fall at the edge of the SPW where the solutions have a large slope and the interpolation does not
    consistently improve the nearest neighbour interpolation (especially if residuals are re-added to match
    the noise level within the gap).

    Looks for and uses the standard pipeline naming from
    the VLA pipeline.

    Parameters
    ----------

    '''

    # Look for BP table
    bpname = glob("{0}.{1}.s*_4.{2}BPcal.tbl".format(myvis, task_string, search_string))

    # test and final cal steps will have 1 match:
    if len(bpname) == 1:
        bpname = bpname[0]
    elif len(bpname) == 2:
        # One table for each semifinal cal call.
        # Grab the second call table.
        bpname = sorted(bpname,
                        key=lambda x: int(x.split("_4.BPcal.tbl")[0].split(".s")[-1]))[-1]
    elif len(bpname) == 0:
        raise ValueError("No matches to the BP table found.")
    else:
        raise ValueError("Found too many matches to the BP table."
                         " Unclear which should be used: {0}".format(bpname))

    # Remove already-made version
    # rmtables(bpname)
    # Or copy to another name to check against
    # os.system("mv {0} {0}.orig".format(bpname))

    # Add better interpolation scheme. This should only be need for HI?

    interpolate_bandpass(bpname,
                         spw_ids=[hi_spwid],
                         window_size_frac=0.125, poly_order=2,  # Works well from Josh and Eric's testing
                         add_residuals=True,  # We re-add residuals to match the noise in the gap
                         backup_table=True,  # A backup table is always made.
                         test_output_nowrite=False,
                         test_print=False)

###############################
# Josh Marvil's code for bandpass interpolation across gaps.
# This is an implementation of Savitzky-Golay smoothing for masked arrays
###############################


def rolling_window(x, k):
    y = np.ma.zeros((len(x), k), dtype='complex128')
    k2 = (k - 1) // 2
    y[:, k2] = x
    for i in range(k2):
        j = k2 - i
        y[j:, i] = x[:-j]
        y[:j, i] = x[0]
        y[:-j, -(i + 1)] = x[j:]
        y[-j:, -(i + 1)] = x[-1]
    return y


def interpolate_bandpass(tablename,
                         spw_ids=None,
                         window_size_frac=0.125, poly_order=2,
                         add_residuals=True,
                         backup_table=True, test_output_nowrite=False,
                         test_print=False):

    from taskinit import tbtool

    if backup_table:
        original_table_backup = tablename + '.bak_from_interpbandpass'
        if not os.path.isdir(original_table_backup):
            shutil.copytree(tablename, original_table_backup)

    tb = tbtool()

    tb.open(tablename)
    all_spw_ids = np.unique(tb.getcol("SPECTRAL_WINDOW_ID"))
    tb.close()

    if spw_ids is None:
        spw_ids = all_spw_ids
    else:
        for spw in spw_ids:
            if spw not in all_spw_ids:
                raise ValueError("SPW {} specified does not exist in the table.".format(spw))

    # We'll just output the corrected data as numpy arrays instead of writing
    # back to the table.
    if test_output_nowrite:
        bp_pass_dict = dict()

    for spw in spw_ids:
        print('processing SPW {0}'.format(spw))

        tb.open(tablename)
        stb = tb.query('SPECTRAL_WINDOW_ID == {0}'.format(spw))
        dat = np.ma.array(stb.getcol('CPARAM'))
        dat.mask = stb.getcol('FLAG')
        stb.close()
        tb.close()

        # Identify if there are gaps to interpolate across
        # We ignore the edge masking in all cases.
        # The sum is over corr and ants. If there are only 2 gaps, no interpolation is needed.
        blank_slices = nd.find_objects(*nd.label(dat.sum(2).sum(0).mask))

        # If there's only 2 slices, it's the SPW edge flagging.
        # We can skip those.
        if len(blank_slices) == 2:
            print("no interpolation needed for {0}".format(spw))
            continue

        dat_shape = dat.shape

        # Define the window size based on the given fraction of the num of SPW channels
        window_size = int(np.floor(window_size_frac * dat_shape[1]))

        print("Using window size of {0} for SPW {1}".format(window_size, spw))

        # Force odd window size
        if window_size % 2 == 0:
            window_size += 1

        x_polyfit = np.arange(window_size) - np.floor(window_size / 2.)

        for ant in range(dat_shape[2]):
            print('processing antenna {0}'.format(ant))
            for pol in range(dat_shape[0]):

                # Skip if all flagged.
                if np.all(dat.mask[pol, :, ant]):
                    continue

                # Determine ranges to interpolate over
                blank_slices = nd.find_objects(*nd.label(dat[pol, :, ant].mask))

                # If there's only 2 slices, it's the SPW edge flagging.
                # No interpolation needed.
                if len(blank_slices) == 2:
                    continue

                # Otherwise we'll mask out the middle gaps
                # Remove the edges.
                blank_slices.pop(0)
                blank_slices.pop(-1)

                # Mask out the gap.
                smooth_dat = deepcopy(dat)

                for slicer in blank_slices:
                    smooth_dat.mask[(slice(pol, pol + 1), slicer[0], slice(ant, ant + 1))] = True

                rolled_array = rolling_window(smooth_dat[pol, :, ant], window_size)

                for i in range(dat_shape[1]):
                    # try:
                    smooth_dat[pol, i, ant] = np.ma.polyfit(x_polyfit, rolled_array[i], poly_order)[-1]
                    # What's the catch here? ValueError is all flagged?
                    # except:
                    #     pass

                print("replacing values with smoothed")

                if add_residuals:
                    resids = dat[pol, :, ant] - smooth_dat[pol, :, ant]

                # Add the interpolated values back to the original array
                for slicer in blank_slices:

                    dat[(slice(pol, pol + 1), slicer[0], slice(ant, ant + 1))] = \
                        smooth_dat[(slice(pol, pol + 1), slicer[0], slice(ant, ant + 1))]

                    # Optionally sample residuals from the difference and add to the interpolated
                    # region to keep a consistent noise level.
                    if add_residuals:

                        gap_size = slicer[0].stop - slicer[0].start
                        resid_samps = np.random.choice(resids[~resids.mask], size=gap_size)

                        # Pad some axes on.
                        resid_samps = resid_samps[np.newaxis, :, np.newaxis]

                        print(resid_samps.shape)

                        dat[(slice(pol, pol + 1), slicer[0], slice(ant, ant + 1))] += resid_samps

                    # Reset the mask across the interp region
                    dat.mask[(slice(pol, pol + 1), slicer[0], slice(ant, ant + 1))] = False

                # Keeping just for diagnosing issues
                if test_print:
                    print((slice(pol, pol + 1), slicer[0], slice(ant, ant + 1)))
                    print(dat[(slice(pol, pol + 1), slicer[0], slice(ant, ant + 1))].shape)
                    print(dat[(slice(pol, pol + 1), slicer[0], slice(ant, ant + 1))][:10])
                    print(smooth_dat[(slice(pol, pol + 1), slicer[0], slice(ant, ant + 1))][:10])

        print("writing out smoothed gaps to table for spw {}".format(spw))

        if test_output_nowrite:
            bp_pass_dict[spw] = dat
            continue

        tb.open(tablename, nomodify=False)
        stb = tb.query('SPECTRAL_WINDOW_ID == {0}'.format(spw))
        # Set new data
        stb.putcol('CPARAM', dat.data)
        # Set new flags
        stb.putcol('FLAG', dat.mask)
        stb.close()

        tb.clearlocks()
        tb.close()

    if test_output_nowrite:
        return bp_pass_dict
