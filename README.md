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

# Legacy code (mostly HI)

M33 projects: https://github.com/e-koch/VLA_Lband

M31/dwarf projects: https://github.com/Astroua/LocalGroup-VLA
