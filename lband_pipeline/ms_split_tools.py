
'''
Tools for returning the desired SPW selection to split an MS (e.g., lines or continuum).

An example format of spw_dict is shown in 20A-246_spw_setup.py.

'''

import os

from numpy.lib.function_base import hanning

from lband_pipeline.spw_setup import create_spw_dict


def get_continuum_spws(spw_dict, baseband='both', return_string=True):
    '''
    Return the continuum SPWs, in one or both of the basebands.

    Parameters
    ----------
    spw_dict : dict
        SPW dictionary. Expects the 20A-346 setup but will
        eventually allow passing: (1) changes in the XL setup and
        (2) changes for the archival projects.

    return_string : bool, optional
        Return the SPW list as a string to pass directly to CASA tasks.
        Default is True. Else the SPWs are returned as a list of integers.

    Return
    ------
    spw_list : list or str
        List or string of the chosen SPWs.

    '''

    all_valids_bbs = ['A0C0', 'B0D0']

    if baseband == 'both':
        valids_bbs = all_valids_bbs
    else:
        valids_bbs = [baseband]

    # Check all given basebands are valid
    check_bbs = [bb in all_valids_bbs for bb in valids_bbs]
    if not all(check_bbs):
        raise ValueError("Found invalid baseband selection: {0}. Must be one of: {1}"
                         .format(valids_bbs, all_valids_bbs))

    spw_list = []

    for spwid in spw_dict:

        if "continuum" not in spw_dict[spwid]['label']:
            continue

        if spw_dict[spwid]['baseband'] in valids_bbs:
            spw_list.append(spwid)

    spw_list.sort()

    if return_string:
        return ",".join([str(num) for num in spw_list])

    return spw_list


def get_line_spws(spw_dict, include_rrls=False, return_string=True,
                  keep_backup_continuum=True):
    '''
    Returns different selections of line SPWs. Currently the option is to keep
    or remove the RRLs.

    Parameters
    ----------
    spw_dict : dict
        SPW dictionary. Expects the 20A-346 setup but will
        eventually allow passing: (1) changes in the XL setup and
        (2) changes for the archival projects.

    include_rrls : bool, optional
        Includes the RRL SPWs when enabled. Default is False.

    return_string : bool, optional
        Return the SPW list as a string to pass directly to CASA tasks.
        Default is True. Else the SPWs are returned as a list of integers.

    keep_backup_continuum: bool, optional
        Keep the backup continuum SPWs in baseband A0 for calibration.
        Default is True.

    Returns
    -------
    spw_list : list or str
        List or string of the chosen SPWs.

    '''

    # Common start to all line names
    line_search_strs = ['HI', "OH", "H1"]

    if not include_rrls:
        # Remove search for Halps
        line_search_strs = line_search_strs[:2]

    spw_list = []

    for spwid in spw_dict:

        if keep_backup_continuum and "continuum" in spw_dict[spwid]['label']:

            if spw_dict[spwid]['baseband'] in "A0C0":
                spw_list.append(spwid)

            continue

        # Otherwise match up line labels
        name = spw_dict[spwid]['label']
        if any([name.startswith(lsearch) for lsearch in line_search_strs]):
            spw_list.append(spwid)

    spw_list.sort()

    if return_string:
        return ",".join([str(num) for num in spw_list])

    return spw_list


def split_ms(ms_name,
             outfolder_prefix=None,
             split_type='all',
             continuum_kwargs={"baseband": 'both'},
             line_kwargs={"include_rrls": False,
                          "keep_backup_continuum": True},
             overwrite=False,
             reindex=True,
             hanningsmooth_continuum=False):
    '''
    Split an MS into continuum and line SPWs.


    Parameters
    ----------
    ms_name : str
        Name of MS.

    spw_dict : dict
        Dictionary with SPW mapping. See 20A-346_spw_setup.py.

    outfolder_prefix : str, optional
        Basename of folder where the split MSs will be located.
        If None, this defaults to the ms_name + "continuum" or "speclines".
        When given, the folders will be outfolder_prefix + "continuum" or "speclines".

    split_type : str, optional
        Which SPW type to split out. Default is 'all' to split the continuum and lines.
        Otherwise use "continuum" or "line" to only split out one type.

    continuum_kwargs : dict, optional

    reindex : bool. optional
        Disable re-indexing the SPW numbers in mstransform. Defaults is True.

    hanningsmooth_continuum : bool, optional
        Apply Hanning smoothing to the continuum. Default is False.
        If enabled, do NOT use `hifv_hanning` in the pipeline!

    '''

    from casatasks import mstransform

    folder_base, ms_name_base = os.path.split(ms_name)

    ms_name_base = ms_name_base.rstrip(".ms")

    if outfolder_prefix is None:
        outfolder_prefix = ms_name_base

    do_split_continuum = False
    do_split_lines = False

    if split_type == "all":
        do_split_continuum = True
        do_split_lines = True
    elif split_type == 'continuum':
        do_split_continuum = True
    elif split_type == 'speclines':
        do_split_lines = True
    else:
        raise ValueError("Unexpected input {} for split_type. ".format(split_type)
                         + "Accepted inputs are 'all', 'continuum', 'speclines'.")

    # Define the spw mapping dictionary
    spw_dict = create_spw_dict(ms_name)

    if do_split_continuum:

        continuum_folder = os.path.join(folder_base, "{}_continuum".format(outfolder_prefix))

        if not os.path.exists(continuum_folder):
            os.mkdir(continuum_folder)
        else:
            # Delete existing version when overwrite is enabled
            if overwrite:
                os.system("rm -r {}/*".format(continuum_folder))

        continuum_spw_str = get_continuum_spws(spw_dict, return_string=True,
                                               **continuum_kwargs)

        mstransform(vis=ms_name,
                    outputvis="{0}/{1}.continuum.ms".format(continuum_folder,
                                                            ms_name_base),
                    spw=continuum_spw_str,
                    datacolumn='DATA',
                    hanning=hanningsmooth_continuum,
                    field="",
                    reindex=reindex)

    if do_split_lines:

        lines_folder = os.path.join(folder_base, "{}_speclines".format(outfolder_prefix))

        if not os.path.exists(lines_folder):
            os.mkdir(lines_folder)
        else:
            # Delete existing version when overwrite is enabled
            if overwrite:
                os.system("rm -r {}/*".format(lines_folder))

        line_spw_str = get_line_spws(spw_dict, return_string=True,
                                     **line_kwargs)

        mstransform(vis=ms_name,
                    outputvis="{0}/{1}.speclines.ms".format(lines_folder,
                                                            ms_name_base),
                    spw=line_spw_str,
                    datacolumn='DATA',
                    field="",
                    reindex=reindex)


def reorder_concat(continuum_vis, line_vis, remove_intermediate=True,
                   outputvis=None):
    '''
    Reorder the SPWs according the to the original VLA names to reset
    the order.

    e.g., based on EVLA_L#A0C0#0 where the last is the original SPW num.
    '''

    from casatasks import split, concat, clearstat

    from casatools import ms, logsink

    casalog = logsink()

    casalog.post("This re-ordered MS will NOT contain RQ and SWPOW information!")

    if outputvis is None:
        outputvis = "concat.ms"

    # Get SPW names in the different vis and map to the current split vis

    spw_dict = {}

    for myvis in [line_vis, continuum_vis]:

        myms = ms()
        myms.open(myvis)

        metadata = myms.metadata()

        # Our SPW setup is the same for all fields.
        spw_ids = metadata.spwsforfield(0)
        spw_names = metadata.namesforspws()

        myms.close()
        metadata.close()

        for id, name in zip(spw_ids, spw_names):
            spw_dict[name] = [myvis, id]

    # Split each SPW and then progressively concat back up

    keys_list = list(spw_dict.keys())

    split(vis=spw_dict[keys_list[0]][0], outputvis=outputvis,
          spw=spw_dict[keys_list[0]][1], datacolumn='DATA')

    for key in keys_list[1:]:
        casalog.post(f"Splitting and concatenating {key}")

        split(vis=spw_dict[key][0],
              outputvis=f"{spw_dict[key][0]}.split_spw{spw_dict[key][1]}",
              spw=spw_dict[key][1],
              datacolumn='DATA')

        concat(vis=[f"{spw_dict[key][0]}.split_spw{spw_dict[key][1]}"],
               concatvis=outputvis)

        clearstat()

        if remove_intermediate:
            os.system(f"rm -rf {spw_dict[key][0]}.split_spw{spw_dict[key][1]}")

