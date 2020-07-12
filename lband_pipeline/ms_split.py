
import sys
import os
from tasks import importasdm

from lband_pipeline.ms_split_tools import split_ms

# Import project spw setup
from lband_pipeline.spw_setup import spw_dict_20A346

'''
Identify the continuum and line SPWs and split into separate MSs and
directories.
'''

mySDM = sys.argv[-2]
# Split out the lines, continuum or both
split_type = sys.argv[-1]

ms_active = mySDM + ".ms"

print("Given inputs:")
print("SDM: {}".format(mySDM))
print("Splitting ms into: {}".format(split_type))

if not os.path.exists(ms_active):
    importasdm(asdm=mySDM, vis=ms_active, ocorr_mode='co',
               applyflags=True, savecmds=True, tbuff=1.5,
               outfile='{}.flagonline.txt'.format(mySDM),
               createmms=False)
else:
    print("MS already exists. Skipping importasdm")

# We're naming the parent file with the target, config,
# trackname and/or date. This keeps that info without explicitly
# needing to pass into this script
parentdir = os.getcwd().split("/")[-1]

split_ms(ms_active,
         spw_dict_20A346,
         outfolder_prefix=parentdir,
         split_type=split_type,
         continuum_kwargs={"baseband": 'both'},
         line_kwargs={"include_rrls": False,
                      "keep_backup_continuum": True},
         overwrite=False)
