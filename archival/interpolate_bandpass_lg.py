import numpy as np
import matplotlib.pyplot as plt
from copy import deepcopy
import shutil

tablename = 'test.tbl'

spw = 0
min_chan = 1200
max_chan = 1400
window_size = 501  # must be odd
poly_order = 2


###############


def rolling_window(x, k):
    y = np.ma.zeros((len(x), k), dtype='complex128')
    k2 = (k - 1) // 2
    y[:, k2] = x
    for i in range(k2):
        j = k2 - i
        y[j:, i] = x[:-j]
        y[:j, i] = x[0]
        y[:-j, -(i + 1)] = x[j:]
        y[-j:, -(i + 1)] = x[-1]
    return y


def interpolate_bandpass(spw, min_chan, max_chan, window_size, poly_order):

    original_table_backup = tablename + '.bak'
    if not os.path.isdir(original_table_backup):
        shutil.copytree(tablename, original_table_backup)

    tb.open(tablename)
    stb = tb.query('SPECTRAL_WINDOW_ID == {0}'.format(spw))
    dat = np.ma.array(stb.getcol('CPARAM'))
    dat.mask = stb.getcol('FLAG')
    stb.close()
    tb.close()

    smooth_dat = deepcopy(dat)
    smooth_dat.mask[:, min_chan:max_chan, :] = True

    dat_shape = dat.shape

    if window_size % 2 == 0:
        window_size += 1

    x_polyfit = np.arange(window_size) - np.floor(window_size / 2.)

    for ant in range(dat_shape[2]):
        print('processing antenna {0}'.format(ant))
        for pol in range(dat_shape[0]):

            if np.all(dat.mask[pol, :, ant]):
                continue

            rolled_array = rolling_window(smooth_dat[pol, :, ant], window_size)

            for i in range(dat_shape[1]):
                try:
                    smooth_dat[pol, i, ant] = np.ma.polyfit(
                        x_polyfit, rolled_array[i], poly_order)[-1]
                except:
                    pass

    dat[:, min_chan:max_chan, :] = smooth_dat[:, min_chan:max_chan, :]

    tb.open(tablename, nomodify=False)
    stb = tb.query('SPECTRAL_WINDOW_ID == {0}'.format(spw))
    stb.putcol('CPARAM', dat.data)
    stb.close()
    tb.close()


interpolate_bandpass(spw, min_chan, max_chan, window_size, poly_order)


#
