
import os
import datetime

from casatasks import tclean, rmtables

from casatools import logsink
from casatools import ms
from casatools import imager
from casatools import synthesisutils

casalog = logsink()

from lband_pipeline.spw_setup import linerest_dict_GHz

from lband_pipeline.target_setup import (target_line_range_kms,
                                         target_vsys_kms)


def quicklook_line_imaging(myvis, thisgal, linespw_dict):

    if not os.path.exists("quicklook_imaging"):
        os.mkdir("quicklook_imaging")

    this_vsys = target_vsys_kms[thisgal]

    # Pick our line range based on the HI for all lines.
    this_velrange = target_line_range_kms[thisgal]['HI']
    # We have a MW foreground window on some targets. Skip this for the galaxy range.
    if isinstance(this_velrange[0], list):
        for this_range in this_velrange:
            if this_vsys > this_range[1] and this_vsys < this_range[0]:
                this_velrange = this_range
                break


    width_vel = 20.
    width_vel_str = f"{width_vel}km/s"

    start_vel = f"{int(min(this_velrange))}km/s"
    nchan_vel = int(abs(this_velrange[0] - this_velrange[1]) / width_vel)

    # Select only the non-continuum SPWs
    line_spws = []
    for thisspw in linespw_dict:
        if "continuum" not in linespw_dict[thisspw]['label']:
            # Our 20A-346 tracks have a combined OH1665/1667 SPW. Split into separate cubes in this case
            line_labels = linespw_dict[thisspw]['label'].split("-")

            for line_label in line_labels:
                line_spws.append([str(thisspw), line_label])

    # Select our target fields. We will loop through
    # to avoid the time + memory needed for mosaics.

    synthutil = synthesisutils()

    myms = ms()

    # if no fields are provided use observe_target intent
    # I saw once a calibrator also has this intent so check carefully
    # mymsmd.open(vis)
    myms.open(myvis)

    mymsmd = myms.metadata()

    target_fields = mymsmd.fieldsforintent("*TARGET*", True)

    mymsmd.close()
    myms.close()

    t0 = datetime.datetime.now()

    # Loop through targets and line SPWs
    for target_field in target_fields:

        casalog.post(f"Quick look imaging of field {target_field}")

        for thisspw_info in line_spws:

            thisspw, line_name = thisspw_info

            casalog.post(f"Quick look imaging of field {target_field} SPW {thisspw}")

            this_imagename = f"quicklook_imaging/quicklook_{target_field}_spw{thisspw}_{line_name}_{myvis}"

            if os.path.exists(f"{this_imagename}.image"):
                rmtables(f"{this_imagename}*")

            # Ask for cellsize
            this_im = imager()
            this_im.selectvis(vis=myvis, field=target_field, spw=str(thisspw))

            image_settings = this_im.advise()
            this_im.close()

            # NOTE: Rounding will only be reasonable for arcsec units with our L-band setup.
            # Could easily fail on ~<0.1 arcsec cell sizes.
            this_cellsize = f"{round(image_settings[2]['value'] * 0.8, 1)}{image_settings[2]['unit']}"
            this_imsize = synthutil.getOptimumSize(int(image_settings[1] * 1.35))

            this_pblim = 0.5

            this_nsigma = 5.0
            this_niter = 0

            tclean(vis=myvis,
                   field=target_field,
                   spw=str(thisspw),
                   cell=this_cellsize,
                   imsize=this_imsize,
                   specmode='cube',
                   robust=0.0,
                   start=start_vel,
                   width=width_vel_str,
                   nchan=nchan_vel,
                   niter=this_niter,
                   nsigma=this_nsigma,
                   imagename=this_imagename,
                   restfreq=f"{linerest_dict_GHz[line_name]}GHz",
                   pblimit=this_pblim)

    t1 = datetime.datetime.now()

    casalog.post(f"Quicklook imaging took {t1 - t0}")
