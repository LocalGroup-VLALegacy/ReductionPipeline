
'''
Summary plots from flagdata.
'''

import matplotlib.pyplot as plt


def make_flagsummary_spw_plot(myvis, flag_dict=None, save_name=None):
    '''
    This mimics the summary plots made by flagdata, but removes the interactive
    part so we can save it.
    '''

    from casatools import ms

    from casatasks import flagdata

    myms = ms()

    myms.open(myvis)

    mymsmd = myms.metadata()

    if flag_dict is None:
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
