
import os
import datetime
import numpy as np

from casatasks import (tclean, rmtables, exportfits, apparentsens)

from casatools import logsink
from casatools import ms
from casatools import imager
from casatools import synthesisutils
from casatools import msmetadata

casalog = logsink()

from lband_pipeline.spw_setup import linerest_dict_GHz

# from lband_pipeline.target_setup import (target_line_range_kms,
#                                          target_vsys_kms)
from lband_pipeline.read_config_files import read_target_vsys_cfg, read_targets_vrange_cfg


def cleanup_misc_quicklook(filename, remove_residual=True,
                           remove_psf=True,
                           remove_image=False):
    '''
    Reduce number of files that aren't needed for QA.
    '''

    rmtables(f"{filename}.model")
    rmtables(f"{filename}.sumwt")
    rmtables(f"{filename}.pb")
    rmtables(f"{filename}.mask")

    if remove_residual:
        rmtables(f"{filename}.residual")

    if remove_psf:
        rmtables(f"{filename}.psf")

    if remove_image:
        rmtables(f"{filename}.image")


def quicklook_line_imaging(myvis, thisgal, linespw_dict,
                           nchan_vel=5,
                           # channel_width_kms=20.,
                           niter=0, nsigma=5.,
                           imsize_max=512,
                           overwrite_imaging=False,
                           export_fits=True,
                           target_vsys_kms=None,
                           target_line_range_kms=None):

    if target_vsys_kms is None:
        # Will read from config file defined in `config_files/master_config.cfg`
        target_vsys_kms = read_target_vsys_cfg(filename=None)

    if target_line_range_kms is None:
        # Will read from config file defined in `config_files/master_config.cfg`
        target_line_range_kms = read_targets_vrange_cfg(filename=None)

    if not os.path.exists("quicklook_imaging"):
        os.mkdir("quicklook_imaging")

    this_vsys = target_vsys_kms[thisgal]

    # Pick our line range based on the HI for all lines.
    this_velrange = target_line_range_kms[thisgal]['HI']
    # We have a MW foreground window on some targets. Skip this for the galaxy range.
    if isinstance(this_velrange[0], list):
        for this_range in this_velrange:
            if min(this_range) < this_vsys < max(this_range):
                this_velrange = this_range
                break

    # Check that the search for the right velocity range didn't fail
    if isinstance(this_velrange[0], list):
        raise ValueError(f"Unable to find range with target vsys ({this_vsys}) from {this_velrange}."
                         f" Check the velocity ranges defined in target_setup.py for {thisgal}")

    # width_vel = channel_width_kms
    # width_vel_str = f"{width_vel}km/s"

    start_vel = f"{int(min(this_velrange))}km/s"

    # nchan_vel = int(abs(this_velrange[0] - this_velrange[1]) / width_vel)

    width_vel = int(round(abs(this_velrange[0] - this_velrange[1]) / float(nchan_vel)))
    width_vel_str = f"{width_vel}km/s"

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

    # record expected sensitivity
    exp_sens = {}

    t0 = datetime.datetime.now()

    # Loop through targets and line SPWs
    for target_field in target_fields:

        casalog.post(f"Quick look imaging of field {target_field}")

        # Loop through the SPWs to identify the biggest image size needed.
        # For ease downstream, we will use the same imsize for all SPWs.
        # NOTE: for L-band, that's a factor of ~2 difference. It may be more pronounced in other
        # bands

        cell_size = {}
        imsizes = []

        for thisspw_info in line_spws:

            thisspw, line_name = thisspw_info

            target_field_label = target_field.replace('-', '_')

            this_imagename = f"quicklook_imaging/quicklook-{target_field_label}-spw{thisspw}-{line_name}-{myvis}"

            if export_fits:
                check_exists = os.path.exists(f"{this_imagename}.image.fits")
            else:
                check_exists = os.path.exists(f"{this_imagename}.image")

            check_exists = check_exists or os.path.exists(f"{this_imagename}.empty")

            if check_exists and not overwrite_imaging:
                continue


            # Ask for cellsize
            this_im = imager()
            this_im.selectvis(vis=myvis, field=target_field, spw=str(thisspw))

            image_settings = this_im.advise()
            this_im.close()

            # When all data is flagged, uvmax = 0 so cellsize = 0.
            # Check for that case to avoid tclean failures
            # if image_settings[2]['value'] == 0.:
            #     casalog.post(f"All data flagged for {this_imagename}. Skipping")
            #     continue

            # NOTE: Rounding will only be reasonable for arcsec units with our L-band setup.
            # Could easily fail on ~<0.1 arcsec cell sizes.
            cell_size[thisspw] = [image_settings[2]['value'], image_settings[2]['unit']]

            # No point in estimating image size for an empty SPW.
            if image_settings[2]['value'] == 0.:
                casalog.post(f"All data flagged for {this_imagename}. Skipping")
                # Write out an empty file so we skip this one from additional uv checks
                os.system(f"touch {this_imagename}.empty")
                continue

            # For the image size, we will do an approx scaling was
            # theta_PB = 45 / nu (arcmin)
            this_msmd = msmetadata()
            this_msmd.open(myvis)
            mean_freq = this_msmd.chanfreqs(int(thisspw)).mean() / 1.e9 # Hz to GHz
            this_msmd.close()

            approx_pbsize = 1.2 * (45. / mean_freq) * 60 # arcsec
            approx_imsize = synthutil.getOptimumSize(int(approx_pbsize / image_settings[2]['value']))
            imsizes.append(approx_imsize)

        if len(imsizes) == 0:
            casalog.post(f"{target_field} is fully flagged. Skipping.")
            continue

        this_imsize = min(imsize_max, max(imsizes))

        for thisspw_info in line_spws:

            thisspw, line_name = thisspw_info

            casalog.post(f"Quick look imaging of field {target_field} SPW {thisspw}")

            target_field_label = target_field.replace('-', '_')

            this_imagename = f"quicklook_imaging/quicklook-{target_field_label}-spw{thisspw}-{line_name}-{myvis}"

            if export_fits:
                check_exists = os.path.exists(f"{this_imagename}.image.fits")
            else:
                check_exists = os.path.exists(f"{this_imagename}.image")

            check_exists = check_exists or os.path.exists(f"{this_imagename}.empty")

            if check_exists:
                if overwrite_imaging:
                    rmtables(f"{this_imagename}*")
                    os.remove(f"{this_imagename}.image.fits")
                else:
                    casalog.post(f"Found {this_imagename}. Skipping imaging.")
                    continue

            if cell_size[thisspw][0] == 0:
                casalog.post(f"All data flagged for {this_imagename}. Skipping")
                continue

            this_cellsize = f"{round(cell_size[thisspw][0] * 0.8, 1)}{cell_size[thisspw][1]}"

            this_pblim = 0.5

            this_nsigma = nsigma
            this_niter = niter

            # Clean up any possible imaging remnants first
            rmtables(f"{this_imagename}*")

            tclean(vis=myvis,
                   field=target_field,
                   spw=str(thisspw),
                   cell=this_cellsize,
                   imsize=this_imsize,
                   specmode='cube',
                   weighting='briggs',
                   robust=0.0,
                   start=start_vel,
                   width=width_vel_str,
                   nchan=nchan_vel,
                   niter=this_niter,
                   nsigma=this_nsigma,
                   imagename=this_imagename,
                   restfreq=f"{linerest_dict_GHz[line_name]}GHz",
                   pblimit=this_pblim)

            # Estimate the expected sensitivity
            out = apparentsens(myvis,
                               field=target_field,
                               spw=str(thisspw),
                               cell=this_cellsize,
                               imsize=this_imsize,
                               specmode='mfs',
                               weighting='briggs',
                               robust=0.0)

            # Can only do mfs mode here so approx scale to the channel
            # width used.
            bandwidth = linespw_dict[int(thisspw)]['bandwidth'] / 1.e9
            # v / c in km/s
            width_freq = (width_vel / 3.e5) * linerest_dict_GHz[line_name]
            chan_to_bandwidth_ratio = width_freq / bandwidth

            exp_sens[f"{target_field_label}-spw{thisspw}"] = \
                    out['effSens'] * np.sqrt(chan_to_bandwidth_ratio)

            # Remove any "apparentsens" image products
            rmtables(f"{myvis}*.apparentsens.*")

            if export_fits:
                exportfits(imagename=f"{this_imagename}.image",
                           fitsimage=f"{this_imagename}.image.fits",
                           history=False,
                           overwrite=True)

            # Clean-up extra imaging products if they are not needed.
            cleanup_misc_quicklook(this_imagename, remove_psf=True,
                                    remove_residual=this_niter == 0,
                                    remove_image=True if export_fits else False)

    # Save the dictionary of expected sensitivity
    np.save(f"quicklook_imaging/expected_sensitivity_dict.npy", exp_sens,
            allow_pickle=True)

    t1 = datetime.datetime.now()

    casalog.post(f"Quicklook line imaging took {t1 - t0}")


def quicklook_continuum_imaging(myvis, contspw_dict,
                                niter=0, nsigma=5.,
                                imsize_max=512,
                                overwrite_imaging=False,
                                export_fits=True):
    '''
    Per-SPW MFS, nterm=1, dirty images of the targets
    '''

    if not os.path.exists("quicklook_imaging"):
        os.mkdir("quicklook_imaging")


    # Select only the continuum SPWs (in case there are any line SPWs).
    continuum_spws = []
    for thisspw in contspw_dict:
        if "continuum" in contspw_dict[thisspw]['label']:
                continuum_spws.append(str(thisspw))

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

    # record expected sensitivity
    exp_sens = {}

    t0 = datetime.datetime.now()

    # Loop through targets and line SPWs
    for target_field in target_fields:

        casalog.post(f"Quick look imaging of field {target_field}")

        cell_size = {}
        imsizes = []

        for thisspw in continuum_spws:

            # First check if its already imaged
            target_field_label = target_field.replace('-', '_')

            this_imagename = f"quicklook_imaging/quicklook-{target_field_label}-spw{thisspw}-continuum-{myvis}"

            if export_fits:
                check_exists = os.path.exists(f"{this_imagename}.image.fits")
            else:
                check_exists = os.path.exists(f"{this_imagename}.image")

            check_exists = check_exists or os.path.exists(f"{this_imagename}.empty")

            if check_exists and not overwrite_imaging:
                continue

            # Ask for cellsize
            this_im = imager()
            this_im.selectvis(vis=myvis, field=target_field, spw=str(thisspw))

            image_settings = this_im.advise()
            this_im.close()

            # When all data is flagged, uvmax = 0 so cellsize = 0.
            # Check for that case to avoid tclean failures
            # if image_settings[2]['value'] == 0.:
            #     casalog.post(f"All data flagged for {this_imagename}. Skipping")
            #     continue

            # NOTE: Rounding will only be reasonable for arcsec units with our L-band setup.
            # Could easily fail on ~<0.1 arcsec cell sizes.
            cell_size[thisspw] = [image_settings[2]['value'], image_settings[2]['unit']]

            # No point in estimating image size for an empty SPW.
            if image_settings[2]['value'] == 0.:
                casalog.post(f"All data flagged for {this_imagename}. Skipping")
                # Write out an empty file so we skip this one from additional uv checks
                os.system(f"touch {this_imagename}.empty")
                continue

            # For the image size, we will do an approx scaling was
            # theta_PB = 45 / nu (arcmin)
            this_msmd = msmetadata()
            this_msmd.open(myvis)
            mean_freq = this_msmd.chanfreqs(int(thisspw)).mean() / 1.e9 # Hz to GHz
            this_msmd.close()

            approx_pbsize = 1.2 * (45. / mean_freq) * 60 # arcsec
            approx_imsize = synthutil.getOptimumSize(int(approx_pbsize / image_settings[2]['value']))
            imsizes.append(approx_imsize)

        if len(imsizes) == 0:
            casalog.post(f"{target_field} is fully flagged. Skipping.")
            continue

        this_imsize = min(imsize_max, max(imsizes))

        for thisspw in continuum_spws:

            casalog.post(f"Quick look imaging of field {target_field} SPW {thisspw}")

            target_field_label = target_field.replace('-', '_')

            this_imagename = f"quicklook_imaging/quicklook-{target_field_label}-spw{thisspw}-continuum-{myvis}"

            if export_fits:
                check_exists = os.path.exists(f"{this_imagename}.image.fits")
            else:
                check_exists = os.path.exists(f"{this_imagename}.image")

            check_exists = check_exists or os.path.exists(f"{this_imagename}.empty")

            if check_exists:
                if overwrite_imaging:
                    rmtables(f"{this_imagename}*")
                    os.remove(f"{this_imagename}.image.fits")
                else:
                    casalog.post(f"Found {this_imagename}. Skipping imaging.")
                    continue

            if cell_size[thisspw][0] == 0:
                casalog.post(f"All data flagged for {this_imagename}. Skipping")
                continue

            this_cellsize = f"{round(cell_size[thisspw][0] * 0.8, 1)}{cell_size[thisspw][1]}"

            this_pblim = 0.5

            this_nsigma = nsigma
            this_niter = niter

            # Clean up any possible imaging remnants first
            rmtables(f"{this_imagename}*")

            tclean(vis=myvis,
                   field=target_field,
                   spw=str(thisspw),
                   cell=this_cellsize,
                   imsize=this_imsize,
                   specmode='mfs',
                   nterms=1,
                   weighting='briggs',
                   robust=0.0,
                   niter=this_niter,
                   nsigma=this_nsigma,
                   fastnoise=True,
                   imagename=this_imagename,
                   pblimit=this_pblim)

            # Estimate the expected sensitivity
            out = apparentsens(myvis,
                               field=target_field,
                               spw=str(thisspw),
                               cell=this_cellsize,
                               imsize=this_imsize,
                               specmode='mfs',
                               weighting='briggs',
                               robust=0.0)
            exp_sens[f"{target_field_label}-spw{thisspw}"] = out['effSens']

            # Remove any "apparentsens" image products
            rmtables(f"{myvis}*.apparentsens.*")


            if export_fits:
                exportfits(imagename=f"{this_imagename}.image",
                           fitsimage=f"{this_imagename}.image.fits",
                           history=False,
                           overwrite=True)

            # Clean-up extra imaging products if they are not needed.
            cleanup_misc_quicklook(this_imagename, remove_psf=True,
                                    remove_residual=this_niter == 0,
                                    remove_image=True if export_fits else False)

    # Save the dictionary of expected sensitivity
    np.save(f"quicklook_imaging/expected_sensitivity_dict.npy", exp_sens,
            allow_pickle=True)

    t1 = datetime.datetime.now()

    casalog.post(f"Quicklook continuum imaging took {t1 - t0}")
