
'''
Functions for flagging problematic velocities.
'''

import numpy as np
import os


def target_foreground_hi_ranges(target):
    '''
    Return the velocity range to flag the bandpass and/or phase cal.

    EWK: We have a large (~800 km/s) bandwidth. So the flagged ranges can be
    chosen liberally and overly wide.

    Parameters
    ----------
    target : str
        Name of target. Should be a calibration source.

    Returns
    -------
    vel_range : list
        Lower and upper velocity limits to be flagged.
    '''

    raise NotImplementedError("")


def flag_hi_foreground(msname, context, hi_spw_num=None,
                       cal_intents=["BANDPASS", "PHASE"]):
    '''
    Define velocity regions to flag for all (or chosen) calibration
    fields based on intent.

    Parameters
    ----------
    msname : str
        MS name.
    context : VLA pipeline context class
        The pipeline context class to identify the calibration sources in
        a track.
    hi_spw_num : int, optional
        The SPW of HI in the MS. If None is given, the context is used to
        identify the SPW overlapping the HI line (where we can ignore wideband
        continuum SPWs).
    cal_intents : list, optional
        List of the calibrator field intents to apply flagging to.
        TODO: ensure the right intent names are being used here.

    '''

    # Check context for the calibration sources given the list of intents
    # to flag.

    # Loop through calibrator sources, calling target_foreground_hi_ranges
    # Flag the requested range.

    # Make a new flagging version marking these calls at the end.

    pass


def partition_cont_range(line_freqs=[], spw_start=1, spw_end=2,
                         test_print=False):
    """
    Cuts one continuum range into smaller ones to avoid lines.
    :param line_freqs: line frequencies in GHz. Given as a two component list for
        the start and end freqs.
    :param spw_start: start of the SPW in GHz
    :param spw_end: end of the SPW in GHz
    :return: list of continuum chunks, each defined as a dictionary with start and end
        freqs in GHz.
    """

    # make sure lists are treaded as float vectors
    line_freqs = np.array(line_freqs)

    # define line ranges that will be excluded
    # line_starts = line_freqs - 0.5 * line_widths
    # line_ends = line_freqs + 0.5 * line_widths

    if test_print:
        print("All line freqs {}".format(line_freqs))
        print("Start line freqs {}".format(line_freqs[:, 0]))
        print("End line freqs {}".format(line_freqs[:, 1]))

    line_starts = line_freqs[:, 0]
    line_ends = line_freqs[:, 1]

    # start with the whole spw as one continuum chunk
    cont_chunks = [dict(start=spw_start, end=spw_end)]

    if test_print:
        print("SPW limits: {}".format(cont_chunks))
        print("SPW len: {}".format(len(cont_chunks)))

    for i in range(len(line_starts)):
        # for each line loop over the continuum chunk collection and modify it in the process
        j = 0
        while j < len(cont_chunks):
            # line outside chunk, skip
            if line_ends[i] < cont_chunks[j]["start"] or line_starts[i] > cont_chunks[j]["end"]:
                pass

            # line covers whole chunk, delete it
            elif line_starts[i] <= cont_chunks[j]["start"] and line_ends[i] >= cont_chunks[j]["end"]:
                cont_chunks.pop(j)
                j = j - 1

            # line covers left edge only, edit cont chunk start
            elif line_starts[i] < cont_chunks[j]["start"] and line_ends[i] >= cont_chunks[j]["start"]:
                cont_chunks[j]["start"] = line_ends[i]

            # line covers right edge only, edit cont chunk end
            elif line_starts[i] <= cont_chunks[j]["end"] and line_ends[i] > cont_chunks[j]["end"]:
                cont_chunks[j]["end"] = line_starts[i]

            # line in the middle, splits chunk into two
            elif line_starts[i] > cont_chunks[j]["start"] and line_ends[i] < cont_chunks[j]["end"]:
                cont_chunks.insert(j + 1, dict(start=line_ends[i], end=cont_chunks[j]["end"]))
                cont_chunks[j]["end"] = line_starts[i]
                j = j + 1

            # other non-implemented scenarios (are all useful cases covered? any pathological edge case?)
            else:
                pass

            # progress to the next chunk
            j = j + 1

    if test_print:
        print("Found cont chunks: {}".format(cont_chunks))

    return cont_chunks


def build_cont_dat(vis, target_line_range_kms,
                   line_freqs={},
                   fields=[],
                   outfile="cont.dat", overwrite=False, append=False,
                   test_print=False):
    """
    Creates a cont.dat file for the VLA pipeline. Must be run in CASA (uses msmetadata).
    It currently reads SPW edges in the original observed frame (usually TOPO),
    but writes them down as LSRK. Should not matter much, edges should be flagged anyway.
    Example of cont.dat content from NRAO online documentation:
    https://science.nrao.edu/facilities/vla/data-processing/pipeline/#section-25
    :param vis: path to the measurement set
    :param line_freqs: line frequencies (obs frame, LSRK) in GHz
    :param line_widths: widths of lines (obs frame, LSRK) in GHz to cut from the continuum
    :param fields: science target fields. If empty, TARGET intent fields are used.
    :param outfile: path to the output cont.dat file
    :param overwrite: if True and the outfile exists, it will be overriten
    :param append: add at the end of existing cont.dat file, useful for optimising lines per field
    :return: None
    """

    from taskinit import msmdtool, mstool

    # need for metadata
    msmd = msmdtool()

    # TOPO -> LSRK conversion
    ms = mstool()

    # if no fields are provided use observe_target intent
    # I saw once a calibrator also has this intent so check carefully
    msmd.open(vis)
    ms.open(vis)

    if len(fields) < 1:
        # fields = msmd.fieldsforintent("*OBSERVE_TARGET*", True)
        fields = msmd.fieldsforintent("*TARGET*", True)

    if len(fields) < 1:
        print("ERROR: no fields!")
        return

    if os.path.exists(outfile) and not overwrite and not append:
        print("ERROR: file already exists!")
        return

    # generate a dictonary containing continuum chunks for every spw of every field
    cont_dat = {}
    for field in fields:
        spws = msmd.spwsforfield(field)
        cont_dat_field = {}

        # Match target with the galaxy. Names should be unique enough to do this
        thisgal = None
        for gal in target_line_range_kms:
            if gal in field:
                thisgal = gal
                break
        # Check for match
        if thisgal is None:
            raise ValueError("Unable to match field {} to expected galaxy targets".format(field))

        for spw in spws:
            # Get freq range of the SPW
            # chan_freqs = msmd.chanfreqs(spw)
            # SPW edges are reported in whichever frame was used for observing (usually TOPO)
            # TODO: implement some transformations to LSRK for the edges?

            # Grab freqs in LSRK and TOPO
            freqs_lsrk = ms.cvelfreqs(spwids=[spw], outframe='LSRK')
            freqs_topo = ms.cvelfreqs(spwids=[spw], outframe='TOPO')

            line_freqs_topo = []

            for line in line_freqs:

                restfreq = line_freqs[line] * 1e9

                # Only include if that line has a defined velocity range
                key_match = None
                for key in target_line_range_kms[thisgal]:
                    if key in line:
                        key_match = key
                        break

                if key_match is None:
                    continue

                for vel_range in target_line_range_kms[thisgal][key_match]:

                    vel_start, vel_stop = vel_range

                    freq_to_match_start = lines_rest2obs(restfreq, vel_start)
                    freq_to_match_stop = lines_rest2obs(restfreq, vel_stop)

                    if test_print:
                        print(spw, line, vel_start, vel_stop)
                        print(spw, line, freq_to_match_start, freq_to_match_stop)
                        print(freqs_lsrk.min(), freqs_lsrk.max())

                    # Not within range. Skip.
                    if freq_to_match_start > freqs_lsrk.max() or freq_to_match_stop < freqs_lsrk.min():
                        skip_line = True
                        break

                    skip_line = False

                    # Convert from Hz to GHz
                    freq_topo_start = freq_match_lsrk_to_topo(freq_to_match_start,
                                                              freqs_lsrk, freqs_topo) * 1e-9

                    freq_topo_stop = freq_match_lsrk_to_topo(freq_to_match_stop,
                                                             freqs_lsrk, freqs_topo) * 1e-9

                    if test_print:
                        print("Found range: {0}, {1}".format(freq_topo_start, freq_topo_stop))

                    line_freqs_topo.append([freq_topo_start, freq_topo_stop])

                if skip_line:
                    continue

                spw_start = np.min(freqs_topo) * 1e-9  # GHz
                spw_end = np.max(freqs_topo) * 1e-9  # GHz

                if test_print:
                    print("SPW {}: {}".format(spw, line_freqs_topo))

                cont_chunks = partition_cont_range(line_freqs_topo, spw_start, spw_end,
                                                   test_print=test_print)
                cont_dat_field.update({spw: cont_chunks})

            # print(spw, cont_chunks)
            # print(spw_start, spw_end)

        cont_dat.update({field: cont_dat_field})

    msmd.close()
    ms.close()

    # write the dictionary into a file usable by the CASA VLA pipeline
    access_mode = "a" if append else "w"
    with open(outfile, access_mode) as f:
        for field in cont_dat.keys():
            f.write("\nField: " + field + "\n")
            for spw in cont_dat[field].keys():
                if len(cont_dat[field][spw]) > 0:
                    f.write("\nSpectralWindow: " + str(spw) + "\n")
                    for chunk in cont_dat[field][spw]:
                        f.write(str(chunk["start"]) + "~" + str(chunk["end"]) + "GHz TOPO\n")
            f.write("\n")

    print("DONE: written in " + outfile)


def lines_rest2obs(line_freqs_rest, vrad0):
    """
    Get observed frame frequencies.

    :param line_freqs_rest: list of rest-frame line frequencies
    :param vrad0: systemic velocity of the galaxy in km/s
    :return: line_freqs, line_widths, both in GHz
    """
    # ckms = scipy.constants.c / 1000.
    ckms = 299792458.0 / 1000.
    line_freqs = np.array(line_freqs_rest) * (1 - vrad0 / ckms)

    return line_freqs


def freq_match_lsrk_to_topo(freq_to_match, freqs_lsrk, freqs_topo):
    '''
    Match channel in freq and return the freq. in TOPO.
    '''

    # Match in LSRK
    chan = np.abs(freqs_lsrk - freq_to_match).argmin()

    # Return channel in TOPO
    return freqs_topo[chan]
