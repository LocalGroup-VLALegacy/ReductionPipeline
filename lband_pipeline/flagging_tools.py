
from casatasks import flagdata
from casatools import table


def flag_quack_integrations(myvis, num_ints=2.5):

    tb = table()

    tb.open(myvis)
    int_time = tb.getcol('INTERVAL')[0]
    tb.close()

    this_quackinterval = num_ints * int_time

    flagdata(vis=myvis,
                flagbackup=False,
                mode='quack',
                quackmode='beg',
                quackincrement=False,
                quackinterval=this_quackinterval)
