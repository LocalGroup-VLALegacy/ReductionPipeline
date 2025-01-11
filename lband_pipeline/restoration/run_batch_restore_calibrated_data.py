
'''
Runs restore_calibrated_data.py on a set of tracks.

Requires:
- Data and pipeline products with:
    - SDM.tar files
    - Archive pipeline tar files in "archive_products"
- 20A-346 csv file generated from the sign-up page.
- A copy of the ReductionPipeline repo (https://github.com/LocalGroup-VLALegacy/ReductionPipeline)

ipython run_batch_restore_calibrated_data.py
    <target>
    <config>
    <data_type>
    <csv_file>
    <data_path>
    <reductionpipeline_path>

'''

from pathlib import Path
import sys
import os
import subprocess

from astropy.table import Table


target = sys.argv[1]
config = sys.argv[2]
data_type = sys.argv[3]

# Read in csv file from 20A-346
csv_file = Path(sys.argv[4])

data_path = Path(sys.argv[5])
data_archive_path = data_path / "archive_products"
if not data_archive_path.exists():
    raise FileNotFoundError(f"Could not find archive_products in {data_path}")

output_data_path = data_path / "restored_data"
if not output_data_path.exists():
    output_data_path.mkdir()

repo_path = Path(sys.argv[6])


# casa_call = Path(sys.argv[4])
casa_call = "/py3opt/casa-6.6.1-17-pipeline-2024.1.0.8/bin/casa"

track_tab = Table.read(csv_file, format='csv')

matches = track_tab['IC10'] == target

# If all, check all configs
if config != "all":
    matches = matches & (track_tab['Configuration'] == config)


track_tab_matches = track_tab[matches]

print(f"Found {len(track_tab_matches)} matches for {target} {config}")
if len(track_tab_matches) == 0:
    raise ValueError("No matches found")

origdir = os.getcwd()

for ii, row in enumerate(track_tab_matches):

    this_trackname = row["Trackname"]
    this_sdm = row["Track Name"]

    print(f"Restoring {this_trackname}. {ii+1}/{len(track_tab_matches)}")

    # Check for products.
    all_products = list(data_archive_path.glob(f"*{this_trackname}*{data_type}*.tar"))
    if len(all_products) == 0:
        raise FileNotFoundError(f"Could not find any products for {vis}")

    # Check for the SDM file.
    this_sdm_tarfile = data_archive_path / f"{this_sdm}.tar"

    # Make the processing directory
    track_folder = data_archive_path / this_trackname

    if not track_folder.exists():
        track_folder.mkdir()

    # Move to the split directory:
    os.chdir(track_folder)

    # Untar the SDM here.
    os.system(f"tar -xf ../{this_sdm_tarfile.name}")

    # Make casa call.
    # casa -c mySDM both|lines|cont True|False data_archive_path output_data_path
    script_str = f"{this_sdm} {data_type} True {data_archive_path} {output_data_path}"
    restore_script = str(repo_path / "ReductionPipeline/lband_pipeline/restoration/restore_calibrated_data.py")

    print(f"Running: {casa_call} -c {script_str}")

    full_casa_call = f"{casa_call} -c {script_str}".split(" ")
    result = subprocess.run(full_casa_call,
                                 capture_output=True,)
    print(result.stdout.decode("utf-8"))

    print(f"Finished {this_trackname}.")

    os.chdir(origdir)
