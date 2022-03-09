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
Easiest to add to the `.casa/init.py` file.

# Using the pipeline

This pipeline should work for any any EVLA L-band data with a mixed line+continuum setup, where the two parts are split into the continuum and lines. The two places manual changes are needed are:

1. Adding the target name, Vsys and expected velocity range here: https://github.com/LocalGroup-VLALegacy/ReductionPipeline/blob/main/lband_pipeline/target_setup.py
2. Adding the calibrator names and Galactic HI absorption avoidance windows here: https://github.com/LocalGroup-VLALegacy/ReductionPipeline/blob/main/lband_pipeline/calibrator_setup.py

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
