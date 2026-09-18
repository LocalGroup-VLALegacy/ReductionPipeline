import bdsf
import sys
import os

infile = sys.argv[-1]

#Run pybdsf
img = bdsf.process_image( infile, thresh_isl =30, thresh_pix =50,  adaptive_rms_box=True, mean_map='zero', peak_fit=True, split_isl=True, group_by_isl=True)
 
#img = bdsf.process_image(infile)
 
print '\n=== Export images ===\n'
img.export_image(outfile=infile.split('.fits')[0]+'.island_mask',\
                 clobber=True,\
                 img_format='fits',\
                 img_type='island_mask')

