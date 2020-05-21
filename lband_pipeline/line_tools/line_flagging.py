
'''
Functions for flagging problematic velocities.
'''

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
