
'''
Summary plots from flagdata.
'''

import matplotlib.pyplot as plt
import numpy as np
import os

from casatools import logsink

casalog = logsink()


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

def make_all_flagsummary_data(myvis, output_folder='perfield_flagfraction'):

    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    make_flagsummary_freq_data(myvis, output_folder=output_folder)

    make_flagsummary_uvdist_data(myvis, output_folder=output_folder)


def make_flagsummary_freq_data(myvis, output_folder='perfield_flagfraction',
                               intent="*", overwrite=False):
    '''
    This mimics the summary plots made by flagdata, but removes the interactive
    part so we can save it.
    '''

    from casatools import ms

    from casatasks import flagdata

    myms = ms()

    myms.open(myvis)

    mymsmd = myms.metadata()

    fieldsnums = mymsmd.fieldsforintent(intent)

    if len(fieldsnums) == 0:
        raise ValueError("No calibrator intents are in this MS.")

    fields = np.array(mymsmd.fieldnames())[fieldsnums]

    spw_nums = mymsmd.spwsforscan(1)

    casalog.post(f"Selecting on fields: {fields}")
    print(f"Selecting on fields: {fields}")

    for field in fields:

        casalog.post(f"Creating freq. flagging fraction for {field}")
        print(f"Creating freq. flagging fraction for {field}")

        save_name = f"{output_folder}/field_{field}_flagfrac_freq.txt"

        if os.path.exists(save_name) and overwrite:
            os.system(f"rm {save_name}")

        if not os.path.exists(save_name):

            flag_dict = flagdata(vis=myvis, mode='summary', spwchan=True, action='calculate',
                                field=field)

            flag_data = []

            for spw in spw_nums:
                spw_freqs = mymsmd.chanfreqs(spw) / 1e9  # GHz

                spw_flagfracs = []
                for chan in range(len(spw_freqs)):
                    spw_flagfracs.append(flag_dict['spw:channel'][f"{spw}:{chan}"]['flagged'] / flag_dict['spw:channel'][f'{spw}:{chan}']['total'])

                # Make an equal length SPW column
                spw_labels = [spw] * len(spw_freqs)

                flag_data.append([spw_labels, np.arange(len(spw_freqs)), spw_freqs, spw_flagfracs])

            output_data = np.hstack(flag_data).T

            np.savetxt(save_name, output_data, header="spw,channel,freq,frac")

        else:
            casalog.post(message="File {} already exists. Skipping".format(save_name),
                         origin='make_qa_tables')


    mymsmd.close()
    myms.close()



def make_flagsummary_uvdist_data(myvis, nbin=25, output_folder="perfield_flagfraction",
                                 intent='*', overwrite=False):
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

    casalog.post(f"Selecting on fields: {fields}")
    print(f"Selecting on fields: {fields}")

    for field in fields:

        casalog.post(f"Creating uvdist flagging fraction for {field}")
        print(f"Creating uvdist flagging fraction for {field}")

        baseline_flagging_table = []

        save_name = f"{output_folder}/field_{field}_flagfrac_uvdist.txt"

        if os.path.exists(save_name) and overwrite:
            os.system(f"rm {save_name}")

        if not os.path.exists(save_name):

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

            baseline_flagging_table_hstack = np.hstack(baseline_flagging_table).T

            out_table = np.zeros(baseline_flagging_table_hstack.shape[0],
                                dtype=[("field", 'U32'),
                                        ('spw', int),
                                        ('uvdist', float),
                                        ('frac', float)])

            out_table['field'] = baseline_flagging_table_hstack[:, 0].astype('U32')
            out_table['spw'] = baseline_flagging_table_hstack[:, 1].astype(int)
            out_table['uvdist'] = baseline_flagging_table_hstack[:, 2].astype(float)
            out_table['frac'] = baseline_flagging_table_hstack[:, 3].astype(float)

            np.savetxt(save_name, out_table, fmt='%s %d %f %f', header="field,spw,uvdist,frac")


    mymsmd.close()
    myms.close()



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
    width = int(1.05 * max(dpoints[0]) / nbins)

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