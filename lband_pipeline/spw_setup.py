

'''
SPW setup info for LG tracks.

The goal is to:
1) identify line and continuum SPWs,
2) Label the line SPWs,
3) Keep some basic metadata on each SPW (nchan, bandwidth, etc.)

Currently only tested for 20A-346, 13A-213 (NGC6822 track).

'''

import numpy as np
import os

from lband_pipeline.line_tools.line_flagging import lines_rest2obs
from lband_pipeline.read_config_files import read_target_vsys_cfg

# This is all lines in L-band that we care about
# Most of the RRLs aren't observed, this is just complete
# so every choice is always available to match.
linerest_dict_GHz = {"HI": 1.420405752,
                     "OH1612": 1.612231,
                     "OH1665": 1.66540180,
                     "OH1667": 1.66735900,
                     "OH1720": 1.72053,
                     "H186a": 1.01376730,
                     "H185a": 1.03025116,
                     "H184a": 1.04709434,
                     "H183a": 1.06430668,
                     "H182a": 1.08189835,
                     "H181a": 1.09987985,
                     "H180a": 1.11826206,
                     "H179a": 1.13705618,
                     "H178a": 1.15627383,
                     "H177a": 1.17592701,
                     "H176a": 1.19602811,
                     "H175a": 1.21658997,
                     "H174a": 1.23762588,
                     "H173a": 1.25914957,
                     "H172a": 1.28117526,
                     "H171a": 1.30371768,
                     "H170a": 1.32679206,
                     "H169a": 1.35041420,
                     "H168a": 1.37460043,
                     "H167a": 1.39936771,
                     "H166a": 1.42473359,
                     "H165a": 1.45071626,
                     "H164a": 1.47733457,
                     "H163a": 1.50460810,
                     "H162a": 1.53255712,
                     "H161a": 1.56120269,
                     "H160a": 1.59056662,
                     "H159a": 1.62067158,
                     "H158a": 1.65154111,
                     "H157a": 1.68319962,
                     "H156a": 1.71567248,
                     "H155a": 1.74898605,
                     "H154a": 1.78316770,
                     "H153a": 1.81824591,
                     "H152a": 1.85425027,
                     "H151a": 1.89121153,
                     "H150a": 1.92916170,
                     "H149a": 1.96813408,
                     }


def create_spw_dict(myvis,
                    continuum_only=False,
                    target_vsys_kms=None,
                    min_continuum_chanwidth_kHz=50,
                    save_spwdict=False,
                    spwdict_filename="spw_definitions.npy",
                    allow_failed_line_identification=True):
    '''
    Create the SPW dict from MS metadata. Split based on continuum and
    use the line dictionary to match line identifications.
    '''

    if target_vsys_kms is None and not continuum_only:
        # Will read from config file defined in `config_files/master_config.cfg`
        target_vsys_kms = read_target_vsys_cfg(filename=None)

    from casatools import ms

    myms = ms()
    myms.open(myvis)

    metadata = myms.metadata()

    # metadata = msmdtool()

    # metadata.open(myvis)

    spw_dict = {}

    science_scans = metadata.scansforintent("*TARGET*")
    science_field0 = metadata.fieldsforscan(science_scans[0])[0]

    # Our SPW setup is the same for all fields.
    spw_ids = metadata.spwsforfield(science_field0)

    gal_vsys = None

    # Identify which target we're looking at.
    # Some of the archival data has a setup scan labeled as a target.
    # Because of this, we will loop through targets until we find one defined
    # in our target dictionary.
    lineobs_dict_GHz = {}

    if not continuum_only:
        for targ_scan in science_scans:

            targ_fieldname = metadata.fieldnames()[metadata.fieldsforscan(targ_scan)[0]]

            gal_vsys = None
            for gal in target_vsys_kms:

                if gal in targ_fieldname:
                    gal_vsys = target_vsys_kms[gal]
                    break

            if gal_vsys is not None:
                break

        if gal_vsys is None:
            raise ValueError("Cannot identify which target galaxy is observed"
                            " from field name {}".format(targ_fieldname))

        # Below is a sketch of doing this for all target fields if there are
        # multiple target galaxies.
        # np.array(metadata.fieldnames())[metadata.fieldsforintent("*TARGET*")]

        # Convert rest to observed based on the target
        for line in linerest_dict_GHz:

            lineobs_dict_GHz[line] = lines_rest2obs(linerest_dict_GHz[line], gal_vsys)

    # Counters for continuum windows in basebands A0C0, B0D0.
    cont_A_count = 0
    cont_B_count = 0

    # Populate the SPW info.
    for spwid in spw_ids:

        # Original name
        spw_name = metadata.namesforspws(spwid)[0]

        # Channel width
        chan_width = metadata.chanwidths(spwid)[0]

        # Bandwidth
        band_width = metadata.bandwidths(spwid)

        # N chans
        nchan = metadata.nchan(spwid)

        # Centre freq.
        # ctr_freq = metadata.chanfreqs
        freqs_lsrk = myms.cvelfreqs(spwids=[spwid], outframe='LSRK')
        freqs_topo = myms.cvelfreqs(spwids=[spwid], outframe='TOPO')

        # Convert from Hz to kHz
        ctr_freq = freqs_lsrk[nchan // 2 - 1] / 1e3

        freq_0_topo = freqs_topo.min()

        # Baseband
        # Baseband
        try:
            bband = spw_name.split("#")[1]
        except IndexError:
            # Pre-JVLA data have a different spw naming scheme.
            bband = spw_name

        # Ncorr
        # ncorr = metadata.ncorrforpol(spwid)

        # Check if continuum or not. If so, assign a unique tag with
        # baseband and number.
        if chan_width >= min_continuum_chanwidth_kHz * 1e3:

            if bband.startswith("A"):
                spw_label = "continuum_A{}".format(cont_A_count)
                cont_A_count += 1
            else:
                spw_label = "continuum_B{}".format(cont_B_count)
                cont_B_count += 1

        # Otherwise do a line match
        else:

            line_match = []

            for line in lineobs_dict_GHz:

                obs_freq = lineobs_dict_GHz[line] * 1e9

                if obs_freq > freqs_lsrk.min() and obs_freq < freqs_lsrk.max():

                    line_match.append(line)

            if len(line_match) == 0:
                if allow_failed_line_identification:
                    print("No spectral line found for SPW {}".format(spwid))
                    continue
                else:
                    raise ValueError("Unable to match spectral line.")

            spw_label = "-".join(line_match)

        spw_dict[spwid] = {'label': spw_label,
                           'origname': spw_name,
                           'chanwidth': chan_width,
                           'bandwidth': band_width,
                           # 'ncorr': ncorr,
                           'centerfreq': ctr_freq,
                           'baseband': bband,
                           'freq_0_topo': freq_0_topo}

    myms.close()

    if save_spwdict:
        # Remove existing saved file
        if os.path.exists(spwdict_filename):
            os.remove(spwdict_filename)

        # Save a pickled version of the dictionary as a npy file
        np.save(spwdict_filename, spw_dict)

    return spw_dict


def build_target_velocity_table(spw_dict, thisgals, target_line_range_kms,
                                linerest_dict_GHz=linerest_dict_GHz):
    '''
    Build a per-(target, line, velocity range) table for QA plotting: the
    protected velocity range(s) for each identified spectral line, and that
    line's rest frequency, so QAPlotter can shade the corresponding
    frequency range on the per-field line-SPW plots without needing MS or
    casatools access itself.

    One row per (target, line, velocity-range pair) -- a line can have more
    than one disjoint protected velocity window (e.g. to dodge a
    Galactic-foreground HI/OH gap, see `config_files/lglbs_targets_vrange.cfg`),
    and a single SPW can contain more than one identified line (e.g. the
    OH 1665/1667 satellite lines both landing in the same SPW), each of
    which becomes its own row here and so its own shaded region.

    Velocities are LSRK km/s, matching the `.cfg` file convention (see
    `read_config_files.read_targets_vrange_cfg`); QAPlotter converts to an
    (approximate, TOPO-vs-LSRK-agnostic) frequency range itself using the
    plain radio-convention Doppler formula, the same approximation already
    accepted elsewhere in this codebase (see `sdm_spw_setup.py`).

    Parameters
    ----------
    spw_dict : dict
        From `create_spw_dict`. Used only for its per-spw 'label' strings
        to find which specific lines (e.g. "OH1665", not just "OH") were
        actually identified for this track.
    thisgals : list
        Science target names identified in this track (`identify_targets`).
    target_line_range_kms : dict
        From `read_config_files.read_targets_vrange_cfg`:
        {target: {line_key: [[vhigh, vlow], ...]}}, where `line_key` is a
        generic species key (e.g. "OH") matched against identified line
        names by substring, the same convention `build_cont_dat` uses.

    Returns
    -------
    astropy.table.Table with columns: target, line, restfreq_GHz, vlow_kms,
    vhigh_kms.
    '''

    from astropy.table import Table

    # All line names actually identified in any line SPW. Labels are e.g.
    # "HI" or "OH1665-OH1667"; continuum spws never carry a line label.
    identified_lines = set()
    for spwid in spw_dict:
        label = spw_dict[spwid]['label']
        if "continuum" in label:
            continue
        identified_lines.update(label.split("-"))

    rows = {'target': [], 'line': [], 'restfreq_GHz': [], 'vlow_kms': [], 'vhigh_kms': []}

    for target in thisgals:
        if target not in target_line_range_kms:
            continue

        for line in sorted(identified_lines):

            # Match the cfg's generic species key (e.g. "OH") against the
            # specific identified line name (e.g. "OH1665") by substring --
            # same convention as build_cont_dat.
            key_match = next((key for key in target_line_range_kms[target] if key in line), None)
            if key_match is None:
                continue

            restfreq = linerest_dict_GHz[line]

            for vhigh, vlow in target_line_range_kms[target][key_match]:
                rows['target'].append(target)
                rows['line'].append(line)
                rows['restfreq_GHz'].append(restfreq)
                rows['vlow_kms'].append(vlow)
                rows['vhigh_kms'].append(vhigh)

    return Table(rows)


def continuum_spws_with_hi(spw_dict):
    '''
    Return the SPW #s of continuum SPWs that contain the HI line.
    Our targets are local, so we're asssuming the HI rest frequency.
    '''

    # GHz -> kHz to match SPW dict
    hi_freq = linerest_dict_GHz['HI'] * 1e6

    contains_hi = []

    for name in spw_dict:

        this_spw_props = spw_dict[name]
        bandwidth_kHz = this_spw_props['bandwidth'] / 1e3

        low_freq = this_spw_props['centerfreq'] - bandwidth_kHz / 2.
        high_freq = this_spw_props['centerfreq'] + bandwidth_kHz / 2.

        if low_freq < hi_freq and high_freq > hi_freq:
            contains_hi.append(name)

    return contains_hi


def line_spw_ids(spw_dict):
    '''
    Return the sorted SPW #s of the spectral line SPWs.

    This is what feeds `specline_spws` in `hifv_importdata`. Note that the
    backup continuum window covering HI stays a *continuum* SPW here, which is
    what we want: it should be Hanning smoothed with the rest of the continuum.
    '''

    return sorted([spwid for spwid in spw_dict
                   if "continuum" not in spw_dict[spwid]['label']])


def continuum_spw_ids(spw_dict):
    '''
    Return the sorted SPW #s of the continuum SPWs.

    This is what feeds `spws_to_smooth` in `hifv_hanning`, which names the
    windows *to* smooth (there is no exclusion parameter).
    '''

    return sorted([spwid for spwid in spw_dict
                   if "continuum" in spw_dict[spwid]['label']])
