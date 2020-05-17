

'''
SPW setup info for 20A-346 tracks.
'''

spw_dict_20A346 = {}

# Map each baseband separately
# A0CO mostly lines
# Format:
# Name: [num, "fullname", nchan, chanwidth, totbw, ctrfreq, "corrs"]
spw_dict_20A346["A0C0"] = \
    {"contA0": {"num": 0, "origname": "EVLA_L#A0C0#0", "nchan": 64, "freq0": 1000.170,
                "chanwidth": 1000.000, "bandwidth": 64000.0, "centerfreq": 1031.6704,
                "corrs": "RR  RL  LR  LL"},
     "H175alp": {"num": 1, "origname": "EVLA_L#A0C0#1", "nchan": 128, "freq0": 1215.869,
                 "chanwidth": 31.250, "bandwidth": 4000.0, "centerfreq": 1217.8538,
                 "corrs": "RR  LL"},
     "H171alp": {"num": 2, "origname": "EVLA_L#A0C0#2", "nchan": 128, "freq0": 1303.077,
                 "chanwidth": 31.250, "bandwidth": 4000.0, "centerfreq": 1305.0610,
                 "corrs": "RR  LL"},
     "H170alp": {"num": 3, "origname": "EVLA_L#A0C0#3", "nchan": 128, "freq0": 1326.172,
                 "chanwidth": 31.250, "bandwidth": 4000.0, "centerfreq": 1328.1564,
                 "corrs": "RR  LL"},
     "contA1_HIbackup": {"num": 4, "origname": "EVLA_L#A0C0#4", "nchan": 64, "freq0": 1384.170,
                         "chanwidth": 1000.000, "bandwidth": 64000.0, "centerfreq": 1415.6704,
                         "corrs": "RR  RL  LR  LL"},
     "HI": {"num": 5, "origname": "EVLA_L#A0C0#5", "nchan": 4096, "freq0": 1417.883,
            "chanwidth": 1.953, "bandwidth": 8000.0, "centerfreq": 1421.8816,
            "corrs": "RR  LL"},
     "H166alp": {"num": 6, "origname": "EVLA_L#A0C0#6", "nchan": 128, "freq0": 1424.203,
                 "chanwidth": 31.250, "bandwidth": 4000.0, "centerfreq": 1426.1872,
                 "corrs": "RR  LL"},
     "OH1612": {"num": 7, "origname": "EVLA_L#A0C0#7", "nchan": 512, "freq0": 1611.884,
                "chanwidth": 7.812, "bandwidth": 4000.0, "centerfreq": 1613.8804,
                "corrs": "RR  LL"},
     "contA2_OHbackup1": {"num": 8, "origname": "EVLA_L#A0C0#8", "nchan": 64, "freq0": 1640.170,
                          "chanwidth": 1000.000, "bandwidth": 64000.0, "centerfreq": 1671.6704,
                          "corrs": "RR  RL  LR  LL"},
     "H158alp": {"num": 9, "origname": "EVLA_L#A0C0#9", "nchan": 128, "freq0": 1651.217,
                 "chanwidth": 31.250, "bandwidth": 4000.0, "centerfreq": 1653.2015,
                 "corrs": "RR  LL"},
     # THIS CHANGES WITH TARGETS! Will need to adjust!
     "OH1665_1667": {"num": 10, "origname": "EVLA_L#A0C0#10", "nchan": 1024, "freq0": 1664.083,
                     "chanwidth": 7.812, "bandwidth": 8000.0, "centerfreq": 1668.0796,
                     "corrs": "RR  LL"},
     "contA3_OHbackup2": {"num": 11, "origname": "EVLA_L#A0C0#11", "nchan": 64, "freq0": 1704.170,
                          "chanwidth": 1000.000, "bandwidth": 64000.0, "centerfreq": 1735.6704,
                          "corrs": "RR  RL  LR  LL"},
     "H156alp": {"num": 12, "origname": "EVLA_L#A0C0#12", "nchan": 128, "freq0": 1715.407,
                 "chanwidth": 31.250, "bandwidth": 4000.0, "centerfreq": 1717.3913,
                 "corrs": "RR  LL"},
     "OH1720": {"num": 13, "origname": "EVLA_L#A0C0#13", "nchan": 512, "freq0": 1720.170,
                "chanwidth": 7.812, "bandwidth": 4000.0, "centerfreq": 1722.1665,
                "corrs": "RR  LL"},
     "H154alp": {"num": 14, "origname": "EVLA_L#A0C0#14", "nchan": 128, "freq0": 1782.964,
                 "chanwidth": 31.250, "bandwidth": 4000.0, "centerfreq": 1784.9481,
                 "corrs": "RR  LL"},
     "H153alp": {"num": 15, "origname": "EVLA_L#A0C0#15", "nchan": 128, "freq0": 1818.074,
                 "chanwidth": 31.250, "bandwidth": 4000.0, "centerfreq": 1820.0583,
                 "corrs": "RR  LL"},
     }

# B0D0 dedicated continuum
spw_dict_20A346["B0D0"] = \
    {"contB0": {"num": 16, "origname": "EVLA_L#B0D0#16", "nchan": 64, "freq0": 988.000,
                "chanwidth": 1000.000, "bandwidth": 64000.0, "centerfreq": 1019.5000,
                "corrs": "RR  RL  LR  LL"},
     "contB1": {"num": 17, "origname": "EVLA_L#B0D0#17", "nchan": 64, "freq0": 1052.000,
                "chanwidth": 1000.000, "bandwidth": 64000.0, "centerfreq": 1083.5000,
                "corrs": "RR  RL  LR  LL"},
     "contB2": {"num": 18, "origname": "EVLA_L#B0D0#18", "nchan": 64, "freq0": 1116.000,
                "chanwidth": 1000.000, "bandwidth": 64000.0, "centerfreq": 1147.5000,
                "corrs": "RR  RL  LR  LL"},
     "contB3": {"num": 19, "origname": "EVLA_L#B0D0#19", "nchan": 64, "freq0": 1180.000,
                "chanwidth": 1000.000, "bandwidth": 64000.0, "centerfreq": 1211.5000,
                "corrs": "RR  RL  LR  LL"},
     "contB4": {"num": 20, "origname": "EVLA_L#B0D0#20", "nchan": 64, "freq0": 1244.000,
                "chanwidth": 1000.000, "bandwidth": 64000.0, "centerfreq": 1275.5000,
                "corrs": "RR  RL  LR  LL"},
     "contB5": {"num": 21, "origname": "EVLA_L#B0D0#21", "nchan": 64, "freq0": 1308.000,
                "chanwidth": 1000.000, "bandwidth": 64000.0, "centerfreq": 1339.5000,
                "corrs": "RR  RL  LR  LL"},
     "contB6": {"num": 22, "origname": "EVLA_L#B0D0#22", "nchan": 64, "freq0": 1372.000,
                "chanwidth": 1000.000, "bandwidth": 64000.0, "centerfreq": 1403.5000,
                "corrs": "RR  RL  LR  LL"},
     "contB7": {"num": 23, "origname": "EVLA_L#B0D0#23", "nchan": 64, "freq0": 1436.000,
                "chanwidth": 1000.000, "bandwidth": 64000.0, "centerfreq": 1467.5000,
                "corrs": "RR  RL  LR  LL"},
     "contB8": {"num": 24, "origname": "EVLA_L#B0D0#24", "nchan": 64, "freq0": 1500.000,
                "chanwidth": 1000.000, "bandwidth": 64000.0, "centerfreq": 1531.5000,
                "corrs": "RR  RL  LR  LL"},
     "contB9": {"num": 25, "origname": "EVLA_L#B0D0#25", "nchan": 64, "freq0": 1564.000,
                "chanwidth": 1000.000, "bandwidth": 64000.0, "centerfreq": 1595.5000,
                "corrs": "RR  RL  LR  LL"},
     "contB10": {"num": 26, "origname": "EVLA_L#B0D0#26", "nchan": 64, "freq0": 1628.000,
                 "chanwidth": 1000.000, "bandwidth": 64000.0, "centerfreq": 1659.5000,
                 "corrs": "RR  RL  LR  LL"},
     "contB11": {"num": 27, "origname": "EVLA_L#B0D0#27", "nchan": 64, "freq0": 1692.000,
                 "chanwidth": 1000.000, "bandwidth": 64000.0, "centerfreq": 1723.5000,
                 "corrs": "RR  RL  LR  LL"},
     "contB12": {"num": 28, "origname": "EVLA_L#B0D0#28", "nchan": 64, "freq0": 1756.000,
                 "chanwidth": 1000.000, "bandwidth": 64000.0, "centerfreq": 1787.5000,
                 "corrs": "RR  RL  LR  LL"},
     "contB13": {"num": 29, "origname": "EVLA_L#B0D0#29", "nchan": 64, "freq0": 1820.000,
                 "chanwidth": 1000.000, "bandwidth": 64000.0, "centerfreq": 1851.5000,
                 "corrs": "RR  RL  LR  LL"},
     "contB14": {"num": 30, "origname": "EVLA_L#B0D0#30", "nchan": 64, "freq0": 1884.000,
                 "chanwidth": 1000.000, "bandwidth": 64000.0, "centerfreq": 1915.5000,
                 "corrs": "RR  RL  LR  LL"},
     "contB15": {"num": 31, "origname": "EVLA_L#B0D0#31", "nchan": 64, "freq0": 1948.000,
                 "chanwidth": 1000.000, "bandwidth": 64000.0, "centerfreq": 1979.5000,
                 "corrs": "RR  RL  LR  LL"},
     }


def continuum_spws(baseband='both', return_string=True):
    '''
    Return the continuum SPWs, in one or both of the basebands.

    Parameters
    ----------
    baseband: str, optional
        Baseband to select continuum SPWs. Default is "both". Otherwise,
        basebands "B" (all continuum) and "A" (mostly lines) can also be
        chosen.

    return_string : bool, optional
        Return the SPW list as a string to pass directly to CASA tasks.
        Default is True. Else the SPWs are returned as a list of integers.

    Return
    ------
    spw_list : list or str
    '''

