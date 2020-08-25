from __future__ import print_function, division
## (1) Import the python application layer

from imagerhelpers.input_parameters import ImagerParameters
from imagerhelpers.imager_base import PySynthesisImager
from imagerhelpers.imager_parallel_continuum import PyParallelContSynthesisImager 
import pickle
import subprocess
import shutil

def make_paramList(niter=0, mask=''):
     """
     Return paramList object with my default wproject
     parameters, except niter and mask, which I'll update
     after running Pybdsf.
     """
     return ImagerParameters(
          msname=msfile,\
          field='2',\
          phasecenter=2,\
          gridder='awproject',\
          wbawp=True,\
          conjbeams=True,\
          aterm=True,\
          psterm=False,\
          cfcache='3k_wbawp_w16.cf',\
          wprojplanes=16,\
          deconvolver='mtmfs',\
          nterms=2,\
          scales=[0,5,15,20],\
          weighting='briggs',\
          usemask='user',\
          mask=mask,\
          robust=0.7,\
          niter=niter,\
          cell='5arcsec',\
          pblimit = 0.0001,\
          imsize=3000,\
          interactive=False,\
          imagename=imname,\
          parallel=True)
     

#(1a)Remove previous files
imname = 'niter0_short'
msfile = '13A-213_May052013_continuum_targets.ms'
os.system('rm -rf {0}*'.format(imname))

## (2) Set up Input Parameters
paramList = make_paramList(niter=0)

## (3) Construct the PySynthesisImager object, with all input parameters

imager = PyParallelContSynthesisImager(params=paramList)

## (4) Initialize various modules.
## Initialize modules major cycle modules

imager.initializeImagers()
imager.initializeNormalizers()
imager.setWeighting()

## (5) Make the initial images
make_psf=True

imager.makePSF() # only for first time so we need some soft of check here
imager.makePB()
imager.runMajorCycle() # Make initial dirty / residual image

print("################################### Major Cycle Done#############################")
imager.deleteTools()

exportfits(imagename='niter0_short.residual.tt0', fitsimage='niter0_short.fits')

##########~~~~~~~ PYBDSF MASKING ~~~~~~~~~~~~~~~~~#########
#Run PyBDSF, Make island (1/0) image (FITS)                                
env_SIFS = os.environ.get('SIFS') #where my singularity images are located
subprocess.call(['singularity','run', env_SIFS+'/pybdsf_1.2.4.sif','python\
', 'run_bdsf.py', 'niter0_short.fits'],\
                env={'PYTHONPATH':''})

#Convert island FITS image to CASA image                                   
importfits(fitsimage='niter0_short.island_mask', imagename='pybdsf_mask_casa')

#Make coordinate correction                                                
ia.open('niter0_short.residual.tt0')
shp = ia.shape()
csys = ia.coordsys().torecord()
ia.close()
ia.open('pybdsf_mask_casa')
mask_shp = ia.shape()
mask_csys = ia.coordsys().torecord()
if np.all(shp == mask_shp):
     ia.setcoordsys(csys)
ia.close()
##########~~~~~~~ END PYBDSF MASKING ~~~~~~~~~~~~~~~~~#########

#RESTART PYSYNTHESIS
paramList = make_paramList(niter=1000, mask='niter0_short.mask')
if os.path.exists('niter0_short.mask'):
     shutil.rmtree('niter0_short.mask')
     shutil.copytree('test.mask','niter0_short.mask')
## (3) Construct the PySynthesisImager object, with all input parameters

imager = PySynthesisImager(params=paramList)

## Init minor cycle modules

imager.initializeDeconvolvers()
imager.initializeIterationControl()

imager.updateMask()

## (7) Run the iteration loops
while ( not imager.hasConverged() ):
    imager.runMinorCycle()

## (8) Finish up
imager.restoreImages()
