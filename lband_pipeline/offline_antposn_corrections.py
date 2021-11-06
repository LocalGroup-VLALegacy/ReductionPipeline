
'''
Some clusters (like cedar) don't allow internet access to jobs. This
routine below will check a pre-downloaded text file for antenna corrections that
is updated prior to the pipeline run. `gencal` is then used to create the correction
cal table.

The reading in from a text file is adapted from Dyas Utomo and Adam Leroy
for the EveryTHINGS project.
'''

import os
import datetime
from glob import glob

import pipeline.infrastructure as infrastructure
from pipeline.hif.tasks.antpos import Antpos

try:
    import pipeline.infrastructure.casatools as casatools
except ImportError:
    import casatools

LOG = infrastructure.get_logger(__name__)

def correct_ant_posns(vis_name, print_offsets=False,
                      data_folder="VLA_antcorr_tables"):
    """
    Return antenna correction for the given measurement set.

    This function is identical to the VLA pipeline version except that we
    read from pre-downloaded files instead of querying the VLA baseline
    website. This is to allow for corrections when running on machines without
    internet access (e.g., clusters where job nodes have limited access).

    Use "https://github.com/LocalGroup-VLALegacy/AutoDataIngest/blob/master/autodataingest/download_vlaant_corrections.py"
    to download the corrections files.
    """

    MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
              'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    #
    # get start date+time of observation
    #
    with casatools.TableReader(vis_name+'/OBSERVATION') as table:
        # observation = tb.open(vis_name+'/OBSERVATION')
        time_range = table.getcol('TIME_RANGE')

    MJD_start_time = time_range[0][0] / 86400
    q1 = casatools.quanta.quantity(time_range[0][0], 's')
    date_time = casatools.quanta.time(q1, form='ymd')
    # date_time looks like: '2011/08/10/06:56:49'
    [obs_year, obs_month, obs_day, obs_time_string] = date_time[0].split('/')
    if (int(obs_year) < 2010):
        if (print_offsets):
            LOG.warn('Does not work for VLA observations')
        return [1, '', []]
    [obs_hour, obs_minute, obs_second] = obs_time_string.split(':')
    obs_time = 10000*int(obs_year) + 100*int(obs_month) + int(obs_day) + \
               int(obs_hour)/24.0 + int(obs_minute)/1440.0 + \
               int(obs_second)/86400.0

    #
    # get antenna to station mappings
    #
    with casatools.TableReader(vis_name+'/ANTENNA') as table:
        #observation = tb.open(vis_name+'/ANTENNA')
        ant_names = table.getcol('NAME')
        ant_stations = table.getcol('STATION')
    ant_num_stas = []
    for ii in range(len(ant_names)):
        ant_num_stas.append([int(ant_names[ii][2:]), ant_names[ii], ant_stations[ii], 0.0, 0.0, 0.0, False])

    correction_lines = []
    current_year = datetime.datetime.now().year
    # first, see if the internet connection is possible
    try:
        with open(data_folder + "/" + str(current_year) + ".txt", 'r') as f:
            lines = f.read()

    except FileNotFoundError as err:

        # LOG.warn('Cannot find antenna position correction txt file {}'.format(err.reason))
        LOG.warn('Cannot find antenna position correction txt file {}'.format(err))

        return [2, '', []]

    for year in range(2010, current_year+1):
        with open(data_folder + "/" + str(year) + ".txt", 'r') as f:
            lines = f.read()

        html_lines = lines.split('\n')

        for correction_line in html_lines:
            if len(correction_line) and correction_line[0] != '<' and correction_line[0] != ';':
                for month in MONTHS:
                    if month in correction_line:
                        correction_lines.append(str(year)+' '+correction_line)
                        break

    corrections_list = []
    for correction_line in correction_lines:
        correction_line_fields = correction_line.split()
        if (len(correction_line_fields) > 9):
            [c_year, moved_date, obs_date, put_date, put_time_str, ant, pad, Bx, By, Bz] = correction_line_fields
            s_moved = moved_date[:3]
            i_month = 1
            for month in MONTHS:
                if (moved_date.find(month) >= 0):
                    break
                i_month = i_month + 1
            moved_time = 10000 * int(c_year) + 100 * i_month + \
                         int(moved_date[3:])
        else:
            [c_year, obs_date, put_date, put_time_str, ant, pad, Bx, By, Bz] = correction_line_fields
            moved_date = '     '
            moved_time = 0
        s_obs = obs_date[:3]
        i_month = 1
        for month in MONTHS:
            if (s_obs.find(month) >= 0):
                break
            i_month = i_month + 1
        obs_time_2 = 10000 * int(c_year) + 100 * i_month + int(obs_date[3:])
        s_put = put_date[:3]
        i_month = 1
        for month in MONTHS:
            if (s_put.find(month) >= 0):
                break
            i_month = i_month + 1
        put_time = 10000 * int(c_year) + 100 * i_month + int(put_date[3:])
        [put_hr, put_min] = put_time_str.split(':')
        put_time += (int(put_hr)/24.0 + int(put_min)/1440.0)
        corrections_list.append([c_year, moved_date, moved_time, obs_date, obs_time_2, put_date, put_time, int(ant),
                                 pad, float(Bx), float(By), float(Bz)])

    for correction_list in corrections_list:
        [c_year, moved_date, moved_time, obs_date, obs_time_2, put_date, put_time, ant, pad, Bx, By, Bz] = correction_list
        ant_ind = -1
        for ii in range(len(ant_num_stas)):
            ant_num_sta = ant_num_stas[ii]
            if (ant == ant_num_sta[0]):
                ant_ind = ii
                break
        if ((ant_ind == -1) or (ant_num_sta[6])):
            # the antenna in this correction isn't in the observation, or is done,
            # so skip it
            pass
        ant_num_sta = ant_num_stas[ant_ind]
        if (moved_time):
            # the antenna moved
            if (moved_time > obs_time):
                # we are done considering this antenna
                ant_num_sta[6] = True
            else:
                # otherwise, it moved, so the offsets should be reset
                ant_num_sta[3] = 0.0
                ant_num_sta[4] = 0.0
                ant_num_sta[5] = 0.0
        if ((put_time > obs_time) and (not ant_num_sta[6]) and (pad == ant_num_sta[2])):
            # it's the right antenna/pad; add the offsets to those already accumulated
            ant_num_sta[3] += Bx
            ant_num_sta[4] += By
            ant_num_sta[5] += Bz

    ants = []
    parms = []
    for ii in range(len(ant_num_stas)):
        ant_num_sta = ant_num_stas[ii]
        if ((ant_num_sta[3] != 0.0) or (ant_num_sta[4] != 0.0) or (ant_num_sta[3] != 0.0)):
            if (print_offsets):
                LOG.info("offsets for antenna %4s : %8.5f  %8.5f  %8.5f" %
                         (ant_num_sta[1], ant_num_sta[3], ant_num_sta[4], ant_num_sta[5]))
            ants.append(ant_num_sta[1])
            parms.append(ant_num_sta[3])
            parms.append(ant_num_sta[4])
            parms.append(ant_num_sta[5])
    if ((len(parms) == 0) and print_offsets):
        LOG.info("No offsets found for this MS")
    ant_string = ','.join(["%s" % ii for ii in ants])
    return [0, ant_string, parms]


def make_offline_antpos_table(vis_name, data_folder="VLA_antcorr_tables",
                              skip_existing=False):
    '''
    Run `gencal` to create the baseline correction table using pre-downloaded
    correction files instead of querying the website.

    Reproduces the expected table name made by `hifv_priorcals`

    Use "https://github.com/LocalGroup-VLALegacy/AutoDataIngest/blob/master/autodataingest/download_vlaant_corrections.py"
    to download the corrections files.

    '''

    from casatasks import gencal

    # Search for an existing antpos file:
    priorcal_tbls = glob("{0}.hifv_priorcals.*".format(vis_name))

    antpos_tblname = None
    for tbl in priorcal_tbls:
        if 'ants' in tbl:
            if skip_existing:
                LOG.info("Antenna offset table already exists. Skipping.")
                return

            antpos_tblname = tbl
            os.system("rm -r {0}".format(tbl))

    try:
        antenna_offsets = correct_ant_posns(vis_name, data_folder=data_folder)
    except FileNotFoundError:
        LOG.warning("Unable to find downloaded antenna correction tables. Skipping.")
        return

    # Come up with the right name for the pipeline when it doesn't already exist
    if antpos_tblname is None:
        priorcal_tbls.sort()

        template_table = priorcal_tbls[-1]

        prefix = "_".join(template_table.split("_")[:2])

        antpos_tblname = "{0}_{1}.ants.tbl".format(prefix, len(priorcal_tbls) + 2)

    if (antenna_offsets[0] == 0):
        gencal(vis=vis_name,
               caltable=antpos_tblname,
               caltype='antpos',
               antenna=antenna_offsets[1],
               parameter=antenna_offsets[2])

    else:
        LOG.info("No antenna offsets found for this MS")
