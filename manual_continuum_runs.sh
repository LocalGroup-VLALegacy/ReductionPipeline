
export repo_path='/home/ekoch/ownCloud/observing_code/VLAXL/ReductionPipeline/lband_pipeline/'

export flagging_path='/home/ekoch/ownCloud/observing_code/VLAXL/FlagRepository/14A-235/Continuum/'

# export backup_path='/home/ekoch/work2/ekoch/VLA_backups/17B-162/Lines/'
export backup_path='/mnt/space/ekoch/VLA_tracks/20A-346/track_products/'
export ms_output_path='/mnt/space/ekoch/VLA_tracks/XL_continuum_ms/'

export casa_path='/home/ekoch/casa-pipeline-release-5.6.2-3.el7/bin/'

export track_name='14A-235.sb29590027.eb29596487.56890.46132725694'
export track_folder='M31_D_'${track_name}

export final_name='14A-235_15'

# Move the SDM file into the track folder
mkdir $track_folder
mv "${track_name}.tar" $track_folder
cd $track_folder
tar -xf "${track_name}".tar
${casa_path}/casa --nogui --log2term -c $repo_path/ms_split.py $track_name continuum
# Clean up intermediate data
rm "${track_name}.tar"
# rm -rf "${track_name}.ms"*
cd "${track_folder}_continuum"

# Copy the manual flagging txt file here
cp "${flagging_path}/${final_name}_manualflagging_v1.txt" manual_flagging.txt

${casa_path}/casa --pipeline --nogui --log2term -c $repo_path/continuum_pipeline.py "${track_name}.continuum.ms"
rm *.last

# Make QA output
cd products
python -c "import qaplotter; qaplotter.make_all_plots()"
cd ../

# Tar up the QA output and restore products.
tar -cf "${track_folder}_continuum_products-v2.tar" products

# Copy the final products to a common location
cp "${track_folder}_continuum_products-v2.tar" $backup_path/

# Copy to the naming used in the flagging spreadsheet.
cp -r ${track_name}.continuum.ms $ms_output_path/"${final_name}.ms"

# cd ../../