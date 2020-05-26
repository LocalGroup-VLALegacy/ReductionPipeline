
'''
Tools for returning the desired SPW selection to split an MS (e.g., lines or continuum).

An example format of spw_dict is shown in 20A-246_spw_setup.py.

'''

import os
from copy import copy


def get_continuum_spws(spw_dict, baseband='both', return_string=True):
    '''
    Return the continuum SPWs, in one or both of the basebands.

    Parameters
    ----------
    spw_dict : dict
        SPW dictionary. Expects the 20A-346 setup but will
        eventually allow passing: (1) changes in the XL setup and
        (2) changes for the archival projects.

    baseband : str, optional
        Baseband to select continuum SPWs. Default is "both". Otherwise,
        basebands "B0D0" (all continuum) and "A0D0" (mostly lines) can also be
        chosen.

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

    for bb in spw_dict:

        if bb not in valids_bbs:
            continue

        for name in spw_dict[bb]:
            if "cont" in name:
                spw_list.append(spw_dict[bb][name]['num'])

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

    for bb in spw_dict:

        for name in spw_dict[bb]:

            # Check if the name begins with one of the line identifiers
            if any([name.startswith(lsearch) for lsearch in line_search_strs]):
                spw_list.append(spw_dict[bb][name]['num'])

            # Optionally keep the backup continuum SPWs
            if keep_backup_continuum:
                # None of the lines need the first continuum SPW in A0CO at ~1 GHz.
                if name == "contA0":
                    continue

                if bb == "A0C0" and "cont" in name:
                    spw_list.append(spw_dict[bb][name]['num'])

    spw_list.sort()

    if return_string:
        return ",".join([str(num) for num in spw_list])

    return spw_list


def return_spwsetup_dict(spw_dict, spw_list):
    '''
    Return a new dictionary of the SPW setup after splitting or a
    chosen subset (e.g. continuum or line only) given a
    list of SPW numbers.

    Parameters
    ----------
    spw_dict : dict
        SPW dictionary. Expects the 20A-346 setup but will
        eventually allow passing: (1) changes in the XL setup and
        (2) changes for the archival projects.
    spw_list : list
        List of integer SPW numbers. For example, from `get_line_spws`.

    Returns
    -------
    new_spw_dict : dict
        Dictionary with the SPW after splitting the MS.
    '''

    new_spw_dict = dict()

    # New SPW mapping.
    ii = 0

    # Redundant loop. But negligible time difference
    for spwnum in spw_list:

        for bb in spw_dict:

            for name in spw_dict[bb]:

                orignum = spw_dict[bb][name]['num']

                if orignum == spwnum:

                    new_spw_dict[name] = copy(spw_dict[bb][name])

                    # Update SPW numbers
                    new_spw_dict[name]["orig_num"] = orignum
                    new_spw_dict[name]['num'] = ii

                    ii += 1

    return new_spw_dict


def split_ms(ms_name,
             spw_dict,
             outfolder_prefix=None,
             split_type='all',
             continuum_kwargs={"baseband": 'both'},
             line_kwargs={"include_rrls": False,
                          "keep_backup_continuum": True},
             overwrite=False):
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


    '''

    from tasks import split

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
    elif split_type == 'line':
        do_split_lines = True
    else:
        raise ValueError("Unexpected input {} for split_type. ".format(split_type)
                         + "Accepted inputs are 'all', 'continuum', 'lines'.")

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

        split(vis=ms_name,
              outputvis="{0}/{1}.continuum.ms".format(continuum_folder,
                                                      ms_name_base),
              spw=continuum_spw_str, datacolumn='DATA',
              field="")

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

        split(vis=ms_name,
              outputvis="{0}/{1}.speclines.ms".format(lines_folder,
                                                      ms_name_base),
              spw=line_spw_str, datacolumn='DATA',
              field="")
