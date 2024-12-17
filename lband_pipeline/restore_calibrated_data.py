
'''
Place SDM and pipeline products in the same directory
to run this script.

Call as:
casa -c mySDM both|lines|cont True|False data_archive_path output_data_path

'''

import os
import sys
import re
import tarfile
from pathlib import Path

from casatasks import flagmanager, hanningsmooth

from lband_pipeline.ms_split_tools import split_ms

###
# Handle SPW mapping from when redindexing was used on split
###
spw_mappings = {'speclines': dict.fromkeys(range(7 + 1)),
                'continuum': dict.fromkeys(range(19 + 1))}

spw_mappings['speclines'][0] = 0
spw_mappings['speclines'][1] = 4
spw_mappings['speclines'][2] = 5
spw_mappings['speclines'][3] = 7
spw_mappings['speclines'][4] = 8
spw_mappings['speclines'][5] = 10
spw_mappings['speclines'][6] = 11
spw_mappings['speclines'][7] = 13

# 20 continuum SPWs in total, including the backups with the lines.
spw_mappings['continuum'] = dict.fromkeys(range(19 + 1))
spw_mappings['continuum'][0] = 0
spw_mappings['continuum'][1] = 4
spw_mappings['continuum'][2] = 8
spw_mappings['continuum'][3] = 11

# Continuum baseband starts at SPW 16.
for ii, key in enumerate(range(4, 19 + 1)):
    spw_mappings['continuum'][key] = ii + 16

mySDM = sys.argv[-5]
# Split out the lines, continuum or both
split_type = sys.argv[-4]
# Set whether to reindex the SPWs or not.
do_apply_hanning = True if sys.argv[-3] == "True" else False

data_archive_path = Path(sys.argv[-2])

output_data_path = Path(sys.argv[-1])


ms_active = mySDM + ".ms"

folder_base, ms_name_base = os.path.split(ms_active)
ms_name_base = ms_name_base.rstrip(".ms")

print("Given inputs:")
print("SDM: {}".format(mySDM))
print("Splitting ms into: {}".format(split_type))
print(f"Applying hanning smoothing: {do_apply_hanning}")


if not os.path.exists(ms_active):
    importasdm(asdm=mySDM, vis=ms_active, ocorr_mode='co',
               applyflags=True, savecmds=True, tbuff=7.5,
               outfile='{}.flagonline.txt'.format(mySDM),
               createmms=False)
else:
    print("MS already exists. Skipping importasdm")

# We're naming the parent file with the target, config,
# trackname and/or date. This keeps that info without explicitly
# needing to pass into this script
parentdir = os.getcwd().split("/")[-1]

# Only keep continuum SPWs as backup for 20A-346
# Otherwise drop for running on the archival projects
if '20A-346' in ms_active:
    keep_backup_continuum = True
else:
    keep_backup_continuum = False

reindex_spws = False
# reindex_spws = True

split_ms(ms_active,
         outfolder_prefix=parentdir,
         split_type=split_type,
         continuum_kwargs={"baseband": 'both'},
         line_kwargs={"include_rrls": False,
                      "keep_backup_continuum": keep_backup_continuum},
         reindex=reindex_spws,
         overwrite=False)

if split_type == 'both':
    restore_types = ['speclines', 'continuum']
elif split_type == "lines":
    restore_types = ['speclines']
else:
    restore_types = [split_type]


for this_type in restore_types:

    ###
    # Move to the split directory:
    ###
    os.chdir(f"{parentdir}_{this_type}")

    vis = f"{ms_name_base}.{this_type}.ms"
    if not os.path.exists(vis):
        raise FileNotFoundError(f"Cannot find {vis}")


    ###
    # Copy over the pipeline products
    ###
    all_products = list(data_archive_path.glob(f"*{ms_name_base}_{this_type}*.tar"))
    if len(all_products) == 0:
        raise FileNotFoundError(f"Could not find any products for {vis}")
    elif len(all_products) > 1:
        # Sort and grab the last one.
        all_products.sort()
        this_product_filename = all_products[-1]
    else:
        this_product_filename = all_products[0]

    os.system("cp -r {} .".format(this_product_filename))

    # Extract flags, caltables, and the applycal call
    flagname = "{}.flagversions.tgz".format(vis)
    with tarfile.TarFile(this_product_filename, 'r') as tar:
        tar.extract(f"products/{flagname}")
    os.system(f"mv products/{flagname} .")
    if not os.path.exists(flagname):
        raise FileNotFoundError("Cannot find flagversions.tgz: {}".format(flagname))

    tablename = "products/unknown.session_1.caltables.tgz"
    with tarfile.TarFile(this_product_filename, 'r') as tar:
        tar.extract(tablename)
    if not os.path.exists(tablename):
        raise FileNotFoundError("Cannot find caltables.tgz: {}".format(tablename))


    applyfile = 'products/{}.calapply.txt'.format(vis)
    with tarfile.TarFile(this_product_filename, 'r') as tar:
        tar.extract(applyfile)
    if not os.path.exists(applyfile):
        raise FileNotFoundError("Cannot find calapply file: {}".format(applyfile))


    ####
    # (Optional) apply hanning smoothing
    ####

    # Don't hanning smooth the lines bu default.
    if do_apply_hanning and this_type == "continuum":

        hanningsmooth(vis, outputvis=f"{vis}.temphanning")

        os.system(f"rm -rf {vis}")

        os.system(f"mv {vis}.temphanning {vis}")

    ####
    # Extract flagversions and caltables
    ####
    with tarfile.open(flagname, 'r:gz') as tar:
        tar.extractall(path="")

    # Assume this is the name for now. Should be fine for all single
    # track pipeline runs
    with tarfile.open(tablename, 'r:gz') as tar:
        tar.extractall(path="")


    ####
    # Restore final flagging version
    ####

    out = flagmanager(vis, mode='list')

    # Last item is 'MS'. Don't need that
    items = list(out.keys())
    items.remove('MS')

    # Check the name of the last version
    last_flag_vs = out[max(items)]

    casalog.post("Restoring last flag version: "
                 "{}.".format(out[max(items)]['name']))

    flagmanager(vis, mode='restore',
                versionname=out[max(items)]['name'])


    ###
    # Apply final calibration
    ###

    # Update directories in applycal.txt
    unix_path = re.compile('((?:\\/[\\w\\.\\-]+)+)',
                            re.IGNORECASE | re.DOTALL)

    # Assume everything is in the same directory, so no osjoin in the return
    def repfn(matchobj):
        basename = os.path.basename(matchobj.group(0))
        return basename

    with open(applyfile, 'r') as f:
        out = unix_path.sub(repfn, f.read())

    # NOTE: may need a custom SPW mapping here for before we turned off
    # re-indexing the SPW numbers.
    # Check for 0~7 or 0~20.

    # Create SPW map and add to out string.
    if "spw='0~7'" in out or "spw='0~20'" in out:
        spw_map = list(spw_mappings[this_type].values())

        num_tables = len(list(Path(".").glob("*.tbl")))

        spw_map_str = [spw_map] * num_tables
        spw_map_initial = "[], " * num_tables
        spw_map_initial = f"[{spw_map_initial[:-2]}]"

        # Split and insert the new spwmap
        split_parts = out.split(f"spwmap={spw_map_initial}")
        split_parts.insert(1, f"spwmap={spw_map_str}")
        out = "".join(split_parts)


    # Change the intents. Without wildcards, this part will fail
    out = re.sub(r"intent='[^']*'", f"intent=''", out)
    out = re.sub(r"spw='[^']*'", f"spw=''", out)

    # Run it.
    exec(out)


    ###
    # Clean up and finish restoration
    ###

    # Rename products folder to a unique name
    os.system(f"mv products {ms_name_base}_{this_type}_products")

    # Tar MS and flagversions.
    final_tarname = f'{parentdir}_{this_type}.tar'
    with tarfile.open(final_tarname, 'w') as tar:
        tar.add(vis)
        tar.add(flagname)  # add flagversions
        tar.add("products")  # add caltables and the calapply call.

    # Move to final directory
    os.system(f"mv {final_tarname} {output_data_path}")

    # Clean up products.
    os.system("rm -rf *.tbl")
    os.system(f"rm -rf {vis}")

    ###
    # Return to parent directory
    ###
    os.chdir("../")

    os.system(f"rm -rf {parentdir}_{this_type}")
