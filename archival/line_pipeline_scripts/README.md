# Example scripts of the pipeline used for lines in archival projects

Notes
-----

* `casa_pipeline_lines.py`: Runs the standard pipeline with (i) no hanning smoothing; (ii) no rflag commands on target fields; (iii) requires a continuum frequencies to be defined in a `cont.dat` to run statwt (e-koch: this can be removed)
* `casa_pipeline_lines.py`: Bandpass is interpolated over Milky Way HI velocities. e.g., (https://github.com/LocalGroup-VLALegacy/ReductionPipeline/blob/master/archival/line_pipeline_scripts/casa_pipeline_lines.py#L69-L128). Most of this code is reproducing the pipeline product names. The flagging is defined in custom txt flagging scripts ([example](https://github.com/Astroua/LocalGroup-VLA/blob/master/15A-175/track_flagging/15A-175_01_29_16_lines_flags.txt#L7-L13)).
* `casa_pipelines.py`: A range of QA plots are made after [Line 296](https://github.com/LocalGroup-VLALegacy/ReductionPipeline/blob/master/archival/line_pipeline_scripts/casa_pipeline_lines.py#L296). These include (i) per SPW bandpass amp/phase plots; (ii) per-scan plots of several variable pairs. The goal of these is to rapidly identify "obvious" poor data for closer examination with `plotms`.
* `ms_split.py`: Example of splitting the line and continuum SPWs. The continuum and line SPW numbers are hard-coded in. There is also a hard-coded check for a custom flagging script from a git repository.


Using
-----
Both scripts are meant to be called from the command line with casa's `-c` flag. This should be the LAST input given to casa.

There are 3 command line inputs for the split: track_name, True/False make a multi-MS, and lines/cont/all to set which splits are done. Example:

`casa "other startup inputs" -c ms_split.py track_name.ms False all`

The pipeline script just needs the name of the split MS. Example:

`casa "other startup inputs" -c casa_pipeline_lines.py track_name.lines.ms`
