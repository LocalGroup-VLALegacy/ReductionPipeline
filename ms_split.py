
import sys
import os
from tasks import importasdm

from ms_split_tools import split_ms

# Import project spw setup
from spw_setup import spw_dict_20A346

'''
Identify the continuum and line SPWs and split into separate MSs and
directories.
'''

mySDM = sys.argv[-2]
# Split out the lines, continuum or both
which_split = sys.argv[-1]

ms_active = mySDM + ".ms"

print("Given inputs:")
print("SDM: {}".format(mySDM))
print("Splitting ms into: {}".format(which_split))

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
         split_type='all',
         continuum_kwargs={"baseband": 'both'},
         line_kwargs={"include_rrls": False,
                      "keep_backup_continuum": True},
         overwrite=False)
