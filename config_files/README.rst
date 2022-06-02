
Adding target and calibrator definition
=======================================

The LGLBS version of the VLA pipeline includes add-ons for
avoiding the velocity range of absorption on calibrators and
protected frequency/velocity ranges on targets.

To add new targets (REQUIRED):

1. Add a new entry to the Vsys file (for LGLBS see `lglbs_targets_vsys.cfg`).
2. Add any protected velocity ranges to the Vrange file (for LGLBS see `lglbs_targets_vrange.cfg`).

To add new calibrators (OPTIONAL):

1. Add a new entry to the Vrange file for calibrators (for LGLBS see `lglbs_calibrators.cfg`).

The calibrator entry is optional and will not crash the pipeline. A missing target definition will.

The calibrator entry is optional as it is only important for calibrator sources with line absorption
within the coverage of relevant spectral windows. For LGLBS, 0 km/s is within the HI bandwidth
and so we often have Galactic HI absorption against the background calibrators.
