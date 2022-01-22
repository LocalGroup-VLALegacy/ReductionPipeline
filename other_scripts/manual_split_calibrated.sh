#!/bin/bash
#SBATCH --time=72:00:00
#SBATCH --mem=20000M
#SBATCH --job-name=final_split-%J
#SBATCH --output=final_split-%J.out
#SBATCH --mail-user=ekoch@ualberta.ca
#SBATCH --mail-type=END
#SBATCH --mail-type=FAIL

module load nixpkgs/16.09
module load imagemagick/7.0.8-53
module load StdEnv

module load qt/4.8.7

source /home/ekoch/.bashrc

# This is what I had in preload.bash
export NIXDIR=/cvmfs/soft.computecanada.ca/nix/var/nix/profiles/16.09/lib/

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$HOME/usr/

export CASALD_LIBRARY_PATH=$LD_LIBRARY_PATH

cd /home/ekoch/scratch/final_splits/

cp -r ~/.casa .
echo "sys.path.append('/home/ekoch/ReductionPipeline/')" >> .casa/config.py

for tar_name in *.tar; do

    echo "Running on ${tar_name}"

    # Split out the MS name
    my_array=($(echo $tar_name | tr "_" "\n"))
    # Name and config
    targ_config_str="${my_array[0]}"_"${my_array[1]}"_

    track_name="${my_array[2]::-4}"

    echo $targ_config_str
    echo $track_name

    tar -xf $tar_name

    echo "Finished tar on ${tar_name}"

    xvfb-run -a ~/casa-6.2.1-7-pipeline-2021.2.0.128/bin/casa --nogui --log2term  --nocrashreport --pipeline -c ~/VLAXL/ReductionPipeline/other_scripts/run_final_split.py $track_name

    echo "Finished split on ${tar_name}"

    # Then tar it back up
    tar -cf "${targ_config_str}_${track_name}.split.tar" "${track_name}.split"
    tar -cf "${targ_config_str}_${track_name}.split_calibrators.tar" "${track_name}.split_calibrators"

    echo "Finished making tar for products on ${tar_name}"

    rm -r "${track_name}"
    rm -r "${track_name}.split"
    rm -r "${track_name}.split_calibrators"

    echo "Removed untar data for ${tar_name}"

done

