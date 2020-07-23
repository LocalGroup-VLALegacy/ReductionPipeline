from glob import glob
import os
import numpy as np
import matplotlib.pyplot as plt



# full path to input MS
ms_path = '/lustre/aoc/users/jmarvil/soma_data2/G035_K_band/19A-216.sb36333208.eb36430345.58543.55307241898.ms'

# full path to desired output directory
out_path = '/lustre/aoc/sciops/jmarvil/test'


if not os.path.isdir(out_path):
    os.mkdir(out_path)


# get metadata
msmd = casac.msmetadata()
msmd.open(ms_path)
cal_fields = np.unique( msmd.fieldsforintent('CALIBRATE*') )
field_names = msmd.namesforfields( cal_fields )
msmd.close()



# split calibrator visibilities
field_str = ','.join( [str(f) for f in cal_fields] )
split( vis=ms_path, field=field_str, keepflags=True, timebin='0s',outputvis=out_path + '/cal_fields.ms' )



# read from plotms output file
def get_uvdata( infile ):
    dat = np.genfromtxt(infile,  names=True, dtype=None, skip_header = 6)#, encoding=None)
    spws = sorted(np.unique(dat['spw']))
    median_flux = []
    for spw in spws:
       median_flux.append( np.median(dat[dat['spw']==spw]['y']) )
       dat['y'][dat['spw']==spw] = 100.*(dat['y'][dat['spw']==spw]/np.median(dat[dat['spw']==spw]['y']) - 1.)
    x=dat['x']
    y=dat['y']
    xi = x.argsort()
    x=x[xi]
    y=y[xi]
    return dat, np.median(median_flux)


# put data in bins; may need to combine SPWs here
# current alternative functions for VLASS use hard-coded SPW ranges
def bin_uvdata( dat ):
    list_x,list_y,list_yerr = [],[],[]
    for ant1 in np.unique(dat['ant1']):
            for ant2 in np.unique(dat['ant2']):
                hits=np.where( (dat['ant1']==ant1)  & (dat['ant2']==ant2))[0]
                if len(hits) > 5:
                    q25,q50,q75 = np.percentile(dat['y'][hits],[25,50,75])
                    iqr = (1/1.35)*(q75-q25)
                    bin_median = q50
                    bin_std = np.abs(iqr)/np.sqrt(len(hits))
                    bin_x = np.median(dat['x'][hits])
                    list_x.append(bin_x)
                    list_y.append(bin_median)
                    list_yerr.append(bin_std)
    return np.array( [list_x,list_y,list_yerr] )


def bin_uvdata_perscan( dat ):
    list_x,list_y,list_yerr = [],[],[]
    for ant1 in np.unique(dat['ant1']):
            for ant2 in np.unique(dat['ant2']):
                for scan in np.unique(dat['scan']):
                    hits=np.where( (dat['ant1']==ant1)  & (dat['ant2']==ant2) & (dat['scan'] == scan))[0]
                    if len(hits) > 5:
                        q25,q50,q75 = np.percentile(dat['y'][hits],[25,50,75])
                        iqr = (1/1.35)*(q75-q25)
                        bin_median = q50
                        bin_std = np.abs(iqr)/np.sqrt(len(hits))
                        bin_x = np.median(dat['x'][hits])
                        list_x.append(bin_x)
                        list_y.append(bin_median)
                        list_yerr.append(bin_std)
    return np.array( [list_x,list_y,list_yerr] )





# make plots
def plot_uvdata_perscan( binned_dat_perscan, binned_dat, infile, bin_type='combined'):

    fig0=plt.figure()
    ax1=fig0.gca()

    markers, caps, bars = ax1.errorbar( (1e-3*binned_dat_perscan[0])**.5, binned_dat_perscan[1],yerr=binned_dat_perscan[2],linestyle='None', fmt='.',markersize=0,alpha=0, color='black', capsize=0, elinewidth=3, label='per-scan')
    [bar.set_alpha(0.20) for bar in bars]
    markers2, caps2, bars2 = ax1.errorbar( (1e-3*binned_dat[0])**.5, binned_dat[1],yerr=binned_dat[2],linestyle='None', fmt='.',markersize=0,alpha=0, color='#ff6d00', capsize=0, elinewidth=3, label='all scans')
    [bar2.set_alpha(0.8) for bar2 in bars2]

    ax1.set_xlabel('UVwave (kilolambda)')
    ax1.set_ylabel('Residual Amplitude (%)')

    xticks = plt.xticks()
    plt.xticks( xticks[0],[x**2 for x in xticks[0]]  )
    plt.legend(loc='upper right')
    plt.title(infile.split('/')[-1].replace('plotms_amp_uvwave_','').replace('.txt',''))
    figname = infile.replace('.txt', '_{0}.png'.format(bin_type))
    fig0.set_size_inches(8,6)
    plt.savefig(figname)
#    mpld3.save_html(fig0, figname.replace('.png','.html'))
    plt.close(fig0)
    plt.close()




# main function
def run_all_uvstats( out_path, cal_fields, field_names, uv_threshold=3, uv_nsigma=3  ):

    skip_fields = ['3C286','3C48','3C147','3C138']

    for field_name in field_names:

        if np.any( [field_name in skip1 for skip1 in skip_fields] ): continue

        plotms_outfile = out_path + '/plotms_amp_uvwave_field_{0}.txt'.format(field_name)
        print('Exporting from plotms: {0}'.format(plotms_outfile))
        plotms(vis=out_path+'/cal_fields.ms', field=field_name, xaxis='UVwave',yaxis='Amp',ydatacolumn='data', averagedata=True, scalar=False, avgchannel='64', avgtime='1000', avgscan=False, correlation='RR,LL', plotfile=plotms_outfile, showgui=False, overwrite=True )

        infile = out_path + '/plotms_amp_uvwave_field_{0}.txt'.format(field_name)
        print('Analyzing UV stats for {0}'.format(infile))
        dat,median_flux = get_uvdata( infile )
        n_scans = len(np.unique(dat['scan']))
        binned_dat = bin_uvdata( dat )
        binned_dat_perscan = bin_uvdata_perscan( dat )
        if binned_dat.shape[1] == 0: continue
        if binned_dat_perscan.shape[1] == 0: continue
        plot_uvdata_perscan( binned_dat_perscan, binned_dat, infile, bin_type='combined')

        # try phase-only selfcal
        try:
            gaincal(vis=out_path + '/cal_fields.ms', caltable=out_path + '/cal_field_{0}.g'.format(field_name), field=field_name, solint='int', refant='',calmode='p' )
            applycal(vis=out_path + '/cal_fields.ms', gaintable=out_path + '/cal_field_{0}.g'.format(field_name), field=field_name, calwt=False )

            plotms_outfile = out_path + '/plotms_amp_uvwave_cal_field_{0}.txt'.format(field_name)
            print('Exporting from plotms: {0}'.format(plotms_outfile))
            plotms(vis=out_path+'/cal_fields.ms', field=field_name, xaxis='UVwave',yaxis='Amp',ydatacolumn='corrected', averagedata=True, scalar=False, avgchannel='64', avgtime='1000', avgscan=False, correlation='RR,LL', plotfile=plotms_outfile, showgui=False, overwrite=True )

            infile = out_path + '/plotms_amp_uvwave_cal_field_{0}.txt'.format(field_name)
            print('Analyzing UV stats for {0}'.format(infile))
            dat,median_flux = get_uvdata( infile )
            n_scans = len(np.unique(dat['scan']))
            binned_dat = bin_uvdata( dat )
            binned_dat_perscan = bin_uvdata_perscan( dat )
            if binned_dat.shape[1] == 0: continue
            if binned_dat_perscan.shape[1] == 0: continue
            plot_uvdata_perscan( binned_dat_perscan, binned_dat, infile, bin_type='combined')
        except:
            print('Problem calibrating field {0}'.format(field_name))



run_all_uvstats( out_path, cal_fields, field_names )
