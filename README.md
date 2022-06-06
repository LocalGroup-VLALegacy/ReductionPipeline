# ReductionPipeline
L-band VLA reduction pipeline

Current version works on version 6.2 of the VLA pipeline.

Pipeline scripts for older versions are maintained in separate branches
(though these are likely to be stale).

Add the repository path to the system path.
```
import sys
sys.path += ['/path/to/this/repository/']
```
Easiest to add to the `.casa/config.py` file (or `startup.py`) for CASA 6.

# Using the pipeline

This pipeline should work for any any EVLA L-band data with a mixed line+continuum setup, where the two parts are split into the continuum and lines. To use with non-LGLBS data,
you can create configuration files defining calibrator and target properties in the `config_files` folder, and give the configuration file names in `master_config.cfg`.
The LGLBS config files are in the same folder and are good examples on how to use with
other sources.

A README file in the `config_files` folder gives instructions for customizing the configuration for other L-band VLA data sets.

The LGLBS line and continuum pipeline use 3 different field configurations:
1. For calibrators and data sets with a 21-cm HI SPW covering near 0 km/s, a velocity range can be specified to flag this range to avoid incorporating Galactic HI absorption in the calibration solutions. For the bandpass, `lband_pipeline/line_pipeline.py` includes a routine to interpolate across this velocity range. Example for 3C48 flagging the HI line from 50 to -50 km/s:

        [3C48]
        HI = 50, -50

2. For targets, the Vsys of the science target should be specified. This is used in a few places, but notably finding the frequency range for quicklook imaging and target name matching in the SDM or measurement set. The latter means it is currently used by the continuum pipeline, though the actual Vsys value is not being used (and so could be set to something arbitrary). Example for M31:

        [target_vsys_kms]
        M31 = -296

3. For targets, the line pipeline requires a protected velocity range to avoid automated RFI flagging on spectral lines. We also use this velocity range to define the extent used in quicklook imaging of spectral lines. Multiple protected ranges can be given as pairs of velocity values (`vhigh1,vlow1,vhigh2,vlow2`, where `vlow1 > vhigh2`). This is useful for compact configurations to avoid flagging Galactic HI emission along the line of sight towards a background source. Example of velocity range for IC1613 of the HI (plus Galactic) and OH:

        [IC1613]
        HI = 50,-60,-170,-290
        OH = -200,-260



The pipeline is meant to run in 2 steps, calling the scripts in casa from the command lines:

1. ms_split.py (creates a continuum and line split MS in separate folder)
2. Then continuum_pipeline.py (close to standard pipeline) and line_pipeline.py (with extra handling for Galactic HI absorption, protected regions from RFI flagging). Both scripts include a number of plotms calls to create a series of text files that are used for the interactive plots, and makes per SPW per field dirty maps as a quicklook imaging check.

From this point, the interactive plotting and expanded weblog are created in a standard python >=3.8 environment using our [QAPlotter](https://github.com/LocalGroup-VLALegacy/QAPlotter) tool.

Additional support for continuum-only L-band data, or other VLA bands, may be added in the future.

# Calling the pipeline scripts

The scripts to run the pipeline steps are designed to be run from the command line:

    >>> casa --pipeline -c script.py args

The command line arguments for the scripts are:

MS import and continuum/lines split with `ms_split.py`

    >>> casa --pipeline -c ms_split.py SDM_name Split_Type Reindex_SPW_numbers

`Split_Type` accepts `all`, `continuum`, or `lines` (see [split_ms](https://github.com/LocalGroup-VLALegacy/ReductionPipeline/blob/main/lband_pipeline/ms_split_tools.py#L157)). `Reindex_SPW_numbers` is a boolean flag that accepts True/False and is passed to [mstransform](https://casadocs.readthedocs.io/en/stable/api/tt/casatasks.manipulation.mstransform.html?highlight=mstransform#reindex) to keep the original SPW numbering after splitting.

The continuum and line pipeline scripts use the same command line args:

    >>> casa --pipeline -c continuum_pipeline.py MS_name
    >>> casa --pipeline -c line_pipeline.py MS_name

The pipeline scripts should be run in the same directory as the split MS output of `ms_split.py` that, by default,
will be the name of the parent directory with "_continuum" or "_speclines" appended to the end. For example, if the
SDM is in the `M33_track` folder, the split MS will be in the `M33_track_continuum` and `M33_track_speclines`
folders.

# Legacy code (mostly HI)

M33 projects: https://github.com/e-koch/VLA_Lband

M31/dwarf projects: https://github.com/Astroua/LocalGroup-VLA
