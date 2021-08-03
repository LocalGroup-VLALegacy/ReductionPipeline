
'''
Summary plots from flagdata.
'''

import matplotlib.pyplot as plt
import numpy as np


def make_flagsummary_freq_plot(myvis, flag_dict=None, save_name=None):
    '''
    This mimics the summary plots made by flagdata, but removes the interactive
    part so we can save it.
    '''

    from casatools import ms

    from casatasks import flagdata

    myms = ms()

    myms.open(myvis)

    mymsmd = myms.metadata()

    if flag_dict is None or 'spw:channel' not in flag_dict:
        flag_dict = flagdata(vis=myvis, mode='summary', spwchan=True, action='calculate')

    fig = plt.figure()
    ax = fig.add_subplot(111)

    spw_nums = mymsmd.spwsforscan(1)

    for spw in spw_nums:
        spw_freqs = mymsmd.chanfreqs(spw) / 1e9  # GHz

        spw_flagfracs = []
        for chan in range(len(spw_freqs)):
            spw_flagfracs.append(flag_dict['spw:channel'][f"{spw}:{chan}"]['flagged'] / flag_dict['spw:channel'][f'{spw}:{chan}']['total'])

        # Plot it.
        plt.plot(spw_freqs, spw_flagfracs, drawstyle='steps-mid', label=f"SPW {spw}")

    mymsmd.close()
    myms.close()

    ax.set_ylim([0.0, 1.5])

    plt.legend(loc='upper center', frameon=True, ncol=4)

    if save_name is None:
        save_name = f"{myvis}_spw_flagfraction"

    fig.savefig(f"{save_name}.png")
    fig.savefig(f"{save_name}.pdf")

    plt.close()

def make_flagsummary_freq_data(myvis, flag_dict=None, save_name=None):
    '''
    This mimics the summary plots made by flagdata, but removes the interactive
    part so we can save it.
    '''

    from casatools import ms

    from casatasks import flagdata

    myms = ms()

    myms.open(myvis)

    mymsmd = myms.metadata()

    if flag_dict is None or 'spw:channel' not in flag_dict:
        flag_dict = flagdata(vis=myvis, mode='summary', spwchan=True, action='calculate')

    spw_nums = mymsmd.spwsforscan(1)

    flag_data = []

    for spw in spw_nums:
        spw_freqs = mymsmd.chanfreqs(spw) / 1e9  # GHz

        spw_flagfracs = []
        for chan in range(len(spw_freqs)):
            spw_flagfracs.append(flag_dict['spw:channel'][f"{spw}:{chan}"]['flagged'] / flag_dict['spw:channel'][f'{spw}:{chan}']['total'])

        # Make an equal length SPW column
        spw_labels = [spw] * len(spw_freqs)

        flag_data.append([spw_labels, np.arange(len(spw_freqs)), spw_freqs, spw_flagfracs])

    mymsmd.close()
    myms.close()

    output_data = np.hstack(flag_data).T

    if save_name is not None:
        np.savetxt(save_name, output_data, header="spw,channel,freq,frac")
    else:
        return output_data


def make_flagsummary_uvdist_data(myvis, nbin=25, save_name=None, intent='*CALIBRATE*'):
    '''
    Make a binned flagging fraction vs. uv-distance.
    '''

    from casatools import ms

    from casatasks import flagdata

    myms = ms()

    myms.open(myvis)

    mymsmd = myms.metadata()

    # Get VLA antenna ID
    antenna_names = mymsmd.antennanames() #returns a list that corresponds to antenna ID

    # Get fields matching intent
    fieldsnums = mymsmd.fieldsforintent(intent)

    if len(fieldsnums) == 0:
        raise ValueError("No calibrator intents are in this MS.")

    fields = np.array(mymsmd.fieldnames())[fieldsnums]

    # Get SPWs
    spw_list = mymsmd.spwsforfield(fieldsnums[0])

    baseline_flagging_table = []

    for field in fields:

        for spw in spw_list:

            flag_dict = flagdata(vis=myvis, mode='summary', basecnt=True, action='calculate',
                                 field=field, spw=str(spw))

            # Make plot of flagging statistics

            # Get information for flagging percentage vs. uvdistance
            myms.selectinit()
            myms.selectchannel(1, 0, 1, 1) # look at data just for first channel - easily translates
            gantdata = myms.getdata(['antenna1','antenna2','uvdist']) # get the points I need

            # create adictionary with flagging info
            base_dict = create_baseline_dict(antenna_names, gantdata)

            # match flagging data to dictionary entry
            datamatch = flag_match_baseline(flag_dict['baseline'], base_dict)

            # 25 is the number of uvdist bins such that there is minimal error in uvdist.
            binned_stats, barwidth = bin_statistics(datamatch, nbin)

            spw_vals = [spw] * len(binned_stats[0])
            field_vals = [field] * len(binned_stats[0])

            baseline_flagging_table.append([field_vals, spw_vals, binned_stats[0], binned_stats[1]])

            # if make_plot:
            #     plt.bar(binned_stats[0], binned_stats[1], width=barwidth, color='grey', align='edge')

    mymsmd.close()
    myms.close()

    baseline_flagging_table = np.hstack(baseline_flagging_table).T

    if save_name is not None:
        np.savetxt(save_name, baseline_flagging_table, header="field,spw,uvdist,frac")
    else:
        return baseline_flagging_table


##########################
# Code adapted from CHILES

def create_baseline_dict(antenna_names, antdata):
    '''create a dictionary to hold all UVdists for antenna pairs and correlate them to station IDs'''

    ##Create dictionary
    baseline_pairs = {}
    i = 0
    while i <= antdata['antenna1'].max(): #create a dictionary antenna for each antenna pair
        j = i + 1
        while j <= antdata['antenna2'].max():
            temp_dict_key = str(antenna_names[i]) + '&&' + str(antenna_names[j])
            baseline_pairs[temp_dict_key] = []
            j += 1
        i += 1
    #add distances to dictionary
    i = 0
    while i < len(antdata['antenna1']):
        temp_dict_key = str(antenna_names[antdata['antenna1'][i]]) + '&&' + str(antenna_names[antdata['antenna2'][i]])
        baseline_pairs[temp_dict_key].append(antdata['uvdist'][i])
        i += 1

    return baseline_pairs

def flag_match_baseline(flgdata, baselines):
    '''match the CASA flagging data to the baseline dictionaries and return flagging statitistics'''

    flagging_data = [[],[]] #list to fill data with
    i = 0
    dictkeys = list(flgdata.keys())
    while i < len(dictkeys):
        flagging_data[0].append(uvdist_max(baselines[dictkeys[i]])[0])
        flagging_data[1].append([flgdata[dictkeys[i]]['flagged'],flgdata[dictkeys[i]]['total']])
        i += 1

    return flagging_data


def uvdist_max(flg_data):
    '''find the max of the uvdist distribution'''

    yvals, edges = np.histogram(flg_data, bins = 20) #get some statistics on the histograms
    max_index = yvals.argmax() #index of maximum value
    uvdist_max = (edges[max_index] + edges[max_index+1])/2.
    return [uvdist_max, np.std(flg_data)]


def bin_statistics(dpoints, nbins):
    '''bin the data based on a desired width'''

    binned = [[],[]]
    i = 0
    width = int(max(dpoints[0]) / nbins)

    flg_tracker, tot_tracker = 0, 0
    while i < nbins: #loop through number of bins
        j = 0
        temp_flg, temp_total = 0., 0. #to be filled with flagging stats
        while j < len(dpoints[0]): #loop through data points
            if dpoints[0][j] >= (i*width) and dpoints[0][j] <= ((i+1)*width):
                temp_flg += dpoints[1][j][0]
                temp_total += dpoints[1][j][1]
                flg_tracker += dpoints[1][j][0]
                tot_tracker += dpoints[1][j][1]
            j += 1
        binned[0].append(i*width)
        if temp_total == 0:
            binned[1].append(0)
        else:
            binned[1].append(temp_flg/temp_total)
        i += 1

    # total = (flg_tracker / tot_tracker) * 100.

    return np.array(binned), width