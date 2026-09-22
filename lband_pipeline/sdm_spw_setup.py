

'''
SPW setup read directly from an SDM, before the MS is created.

The VLA pipeline needs `specline_spws` at `hifv_importdata` time, i.e. before
there is an MS to inspect. `spw_setup.create_spw_dict` cannot help there: it
opens the MS. This module reproduces the same classification from the SDM
instead, so the line SPWs handed to the pipeline are exactly the ones we would
have identified ourselves.

The heavy lifting is done by `casatasks.listsdm`, which parses the SDM XML
tables and *returns* a dictionary keyed on scan number (it also prints to the
logger). `casatools.sdm` only offers `summarystr()` and `asdmsummary` only logs,
so `listsdm` is the one API that hands back structured data.

`listsdm` does not report the SPW name string (e.g. "EVLA_L#A0C0#5"), which is
what gives us the baseband tag ("A0C0"), so `SpectralWindow.xml` is read
directly for that one field.

Two differences from `create_spw_dict`, neither of which can change a line
match here:

1. Frequencies are TOPO (built from `reffreq` + i * `chanwidth`) rather than
   LSRK via `ms.cvelfreqs`. The TOPO<->LSRK difference is at most ~30 km/s
   (~142 kHz at 1.42 GHz) against SPW bandwidths of >= 8 MHz.
2. The target galaxy is matched against the `source` name of OBSERVE_TARGET
   scans rather than against MS field names.

Because of (1), this dict is only used to choose `specline_spws`. The
authoritative SPW dict saved to `spw_definitions.npy` is still built from the MS
by `create_spw_dict` once the import has run.

'''

import os
from xml.dom import minidom

from lband_pipeline.spw_setup import linerest_dict_GHz
from lband_pipeline.line_tools.line_flagging import lines_rest2obs
from lband_pipeline.read_config_files import read_target_vsys_cfg


def read_sdm_spw_names(sdm_name):
    '''
    Return {sdm_spw_index: spw_name} from the SDM's SpectralWindow.xml.

    The name (e.g. "EVLA_L#A0C0#5") is copied verbatim by importasdm into
    SPECTRAL_WINDOW.NAME, so it is both the source of the baseband tag and the
    key used to check the SDM -> MS SPW mapping after import.

    Parameters
    ----------
    sdm_name : str
        Path to the (untarred) SDM directory.

    Returns
    -------
    dict
        Mapping of integer SDM SPW index to name. Every SPW in the table is
        included; the value is None when the row has no `name` element. All of
        them are needed because the MS SPW id is the rank within this table.
    '''

    xml_name = os.path.join(sdm_name, "SpectralWindow.xml")

    if not os.path.exists(xml_name):
        raise OSError("Unable to find {}".format(xml_name))

    spw_names = {}

    xml_spw = minidom.parse(xml_name)

    for rownode in xml_spw.getElementsByTagName("row"):

        row_spwid = rownode.getElementsByTagName("spectralWindowId")
        # "SpectralWindow_5" -> 5
        spwid = int(str(row_spwid[0].childNodes[0].nodeValue).split("_")[1])

        row_name = rownode.getElementsByTagName("name")
        if len(row_name) == 0 or len(row_name[0].childNodes) == 0:
            spw_names[spwid] = None
        else:
            spw_names[spwid] = str(row_name[0].childNodes[0].nodeValue)

    return spw_names


def _flatten_scan_values(value):
    '''
    Flatten one level of nesting from a `listsdm` per-scan list.

    `listsdm` indexes its per-config-description lists with a numpy array, so
    the per-scan 'spws'/'nchan'/'chanwidth'/'reffreq' entries can come back
    either flat ([0, 4, 5]) or wrapped in an extra list ([[0, 4, 5]]) depending
    on the CASA version. Normalise both to a flat list.
    '''

    if isinstance(value, (str, bytes)):
        return [value]

    try:
        items = list(value)
    except TypeError:
        return [value]

    flat = []

    for item in items:

        if isinstance(item, (str, bytes)):
            flat.append(item)
            continue

        try:
            flat.extend(list(item))
        except TypeError:
            # A plain scalar, i.e. the list was already flat.
            flat.append(item)

    return flat


def scan_spw_properties(scandict, scannum):
    '''
    Return the (spws, nchan, chanwidth, reffreq) lists for one scan of a
    `listsdm` dictionary, flattened and checked for consistent lengths.
    '''

    this_scan = scandict[scannum]

    keys = ['spws', 'nchan', 'chanwidth', 'reffreq']

    values = [_flatten_scan_values(this_scan[key]) for key in keys]

    lengths = set([len(val) for val in values])

    if len(lengths) > 1:
        raise ValueError("listsdm entries for scan {0} have mismatched lengths: {1}"
                         .format(scannum,
                                 dict(zip(keys, [len(val) for val in values]))))

    return values


def create_spw_dict_from_sdm(sdm_name,
                             target_vsys_kms=None,
                             min_continuum_chanwidth_kHz=50,
                             allow_failed_line_identification=True,
                             scandict=None):
    '''
    Create the SPW dict from SDM metadata, matching the record format of
    `spw_setup.create_spw_dict` so the same consumers work on either.

    Parameters
    ----------
    sdm_name : str
        Path to the (untarred) SDM directory.

    target_vsys_kms : dict, optional
        Target systemic velocities. Read from the config file defined in
        `config_files/master_config.cfg` when not given.

    min_continuum_chanwidth_kHz : float, optional
        Channel widths at or above this are continuum SPWs. Default is 50,
        matching `create_spw_dict`.

    allow_failed_line_identification : bool, optional
        Skip narrow SPWs that match no known line instead of raising.
        Default is True.

    scandict : dict, optional
        Pre-computed `casatasks.listsdm` output. Only intended for testing
        without CASA; normally left as None so listsdm is called here.

    Returns
    -------
    spw_dict : dict
        Keyed by the *predicted* MS SPW id (see below). Values match
        `create_spw_dict`, except that `centerfreq` and `freq_0_topo` are TOPO.

    target_sources : list
        Source names of the OBSERVE_TARGET scans, in order of first appearance.

    Notes
    -----
    asdm2MS writes SPECTRAL_WINDOW rows in ascending SDM SpectralWindow_N
    order, and only for the SPWs some scan actually uses, so the MS SPW id is
    predicted as the rank of each SDM index among the SPWs referenced by any
    scan. The prediction is checked against the real MS immediately after
    `hifv_importdata` rather than trusted.
    '''

    if scandict is None:
        from casatasks import listsdm

        scandict = listsdm(sdm_name)

    if target_vsys_kms is None:
        # Will read from config file defined in `config_files/master_config.cfg`
        target_vsys_kms = read_target_vsys_cfg(filename=None)

    spw_names = read_sdm_spw_names(sdm_name)

    # Collect the science scans and the SPWs they use.
    target_sources = []
    science_scans = []

    for scannum in sorted(scandict):
        if "OBSERVE_TARGET" not in scandict[scannum]['intent']:
            continue

        science_scans.append(scannum)

        this_source = scandict[scannum]['source']
        if this_source not in target_sources:
            target_sources.append(this_source)

    if len(science_scans) == 0:
        raise ValueError("Unable to find any OBSERVE_TARGET scans in {}".format(sdm_name))

    # Identify which target we're looking at.
    # Some of the archival data has a setup scan labeled as a target, so loop
    # until we find a source defined in our target dictionary.
    gal_vsys = None
    for this_source in target_sources:
        for gal in target_vsys_kms:
            if gal in this_source:
                gal_vsys = target_vsys_kms[gal]
                break

        if gal_vsys is not None:
            break

    if gal_vsys is None:
        raise ValueError("Cannot identify which target galaxy is observed"
                         " from source names {}".format(target_sources))

    # Convert rest to observed based on the target
    lineobs_dict_GHz = {}
    for line in linerest_dict_GHz:
        lineobs_dict_GHz[line] = lines_rest2obs(linerest_dict_GHz[line], gal_vsys)

    # Gather the per-SPW properties from the science scans. All science scans
    # share a correlator setup, but loop over all of them so a partial config
    # in the first scan cannot silently drop an SPW.
    sdm_spw_props = {}

    for scannum in science_scans:

        these_spws, these_nchan, these_chanwidth, these_reffreq = \
            scan_spw_properties(scandict, scannum)

        for idx, spwid in enumerate(these_spws):

            spwid = int(spwid)

            if spwid in sdm_spw_props:
                continue

            sdm_spw_props[spwid] = {'nchan': int(these_nchan[idx]),
                                    'chanwidth': float(these_chanwidth[idx]),
                                    'reffreq': float(these_reffreq[idx])}

    # Predicted MS SPW ids: the rank of the SDM index among every SPW that gets
    # imported, i.e. every SPW referenced by any scan. Rows in
    # SpectralWindow.xml that no scan uses are not written to the MS, while
    # SPWs used only by e.g. pointing scans are, so the union over all scans is
    # the right set -- not just the science scans.
    all_sdm_spwids = set()
    for scannum in scandict:
        these_spws = scan_spw_properties(scandict, scannum)[0]
        all_sdm_spwids.update([int(spwid) for spwid in these_spws])

    all_sdm_spwids = sorted(all_sdm_spwids)

    sdm_to_ms_spwid = dict((spwid, msid) for msid, spwid in enumerate(all_sdm_spwids))

    # Counters for continuum windows in basebands A0C0, B0D0.
    cont_A_count = 0
    cont_B_count = 0

    spw_dict = {}

    for spwid in sorted(sdm_spw_props):

        these_props = sdm_spw_props[spwid]

        nchan = these_props['nchan']
        chan_width = these_props['chanwidth']
        band_width = abs(chan_width) * nchan

        if spw_names.get(spwid) is None:
            raise ValueError("SPW {0} is used by a science scan but has no name in"
                             " SpectralWindow.xml of {1}".format(spwid, sdm_name))

        spw_name = spw_names[spwid]

        if spwid not in sdm_to_ms_spwid:
            raise ValueError("Unable to map SDM SPW {0} to an MS SPW id.".format(spwid))

        ms_spwid = sdm_to_ms_spwid[spwid]

        # TOPO channel edges. chanwidth is signed for lower-sideband windows.
        freq_a = these_props['reffreq']
        freq_b = freq_a + chan_width * (nchan - 1)

        freq_min_topo = min(freq_a, freq_b)
        freq_max_topo = max(freq_a, freq_b)

        # Convert from Hz to kHz to match `create_spw_dict`
        ctr_freq = (0.5 * (freq_min_topo + freq_max_topo)) / 1e3

        # Baseband
        try:
            bband = spw_name.split("#")[1]
        except IndexError:
            # Pre-JVLA data have a different spw naming scheme.
            bband = spw_name

        # Check if continuum or not. If so, assign a unique tag with
        # baseband and number.
        if abs(chan_width) >= min_continuum_chanwidth_kHz * 1e3:

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

                if obs_freq > freq_min_topo and obs_freq < freq_max_topo:

                    line_match.append(line)

            if len(line_match) == 0:
                if allow_failed_line_identification:
                    print("No spectral line found for SPW {}".format(ms_spwid))
                    continue
                else:
                    raise ValueError("Unable to match spectral line.")

            spw_label = "-".join(line_match)

        spw_dict[ms_spwid] = {'label': spw_label,
                              'origname': spw_name,
                              'chanwidth': chan_width,
                              'bandwidth': band_width,
                              'centerfreq': ctr_freq,
                              'baseband': bband,
                              'freq_0_topo': freq_min_topo}

    return spw_dict, target_sources


def compare_spw_dicts(sdm_spw_dict, ms_spw_dict):
    '''
    Check that the SPW dict predicted from the SDM matches the one built from
    the MS after import.

    A mismatch means the SDM -> MS SPW id prediction was wrong, so the
    `specline_spws` handed to `hifv_importdata` labelled the wrong windows.

    Parameters
    ----------
    sdm_spw_dict : dict
        Output of `create_spw_dict_from_sdm`.

    ms_spw_dict : dict
        Output of `spw_setup.create_spw_dict`.

    Returns
    -------
    mismatches : list
        Human-readable description of each disagreement. Empty when the two
        dicts agree.
    '''

    mismatches = []

    sdm_ids = set(sdm_spw_dict.keys())
    ms_ids = set(ms_spw_dict.keys())

    for spwid in sorted(sdm_ids - ms_ids):
        mismatches.append("SPW {0} ({1}) predicted from the SDM is not in the MS."
                          .format(spwid, sdm_spw_dict[spwid]['origname']))

    for spwid in sorted(ms_ids - sdm_ids):
        mismatches.append("SPW {0} ({1}) in the MS was not predicted from the SDM."
                          .format(spwid, ms_spw_dict[spwid]['origname']))

    for spwid in sorted(sdm_ids & ms_ids):

        for key in ['origname', 'label']:

            if sdm_spw_dict[spwid][key] != ms_spw_dict[spwid][key]:
                mismatches.append("SPW {0} {1}: SDM gives {2}, MS gives {3}."
                                  .format(spwid, key,
                                          sdm_spw_dict[spwid][key],
                                          ms_spw_dict[spwid][key]))

    return mismatches
