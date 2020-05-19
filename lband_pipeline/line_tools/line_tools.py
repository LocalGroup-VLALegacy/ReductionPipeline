
import os
from glob import glob
from copy import copy

from tasks import bandpass

import pipeline.hif.heuristics.findrefant as findrefant


def bandpass_with_gap_interpolation(myvis, context, refantignore="",
                                    search_string="test",
                                    task_string="hifv_testBPdcals"):
    '''
    Re-do the bandpass accounting for flagged gaps.

    Looks for and uses the standard pipeline naming from
    the VLA pipeline.

    TODO: Investigate using spline instead of nearest neighbour
    interpolation.

    '''

    # Look for BP table
    bpname = glob("{0}.{1}.s*_4.{1}BPcal.tbl".format(myvis, task_string, search_string))
    assert len(bpname) == 1
    bpname = bpname[0]

    # Remove already-made version
    # rmtables(bpname)
    # Or copy to another name to check against
    os.system("mv {0} {0}.orig".format(bpname))

    # Get the scan/field selections
    scanheur = context.evla['msinfo'][context.evla['msinfo'].keys()[0]]

    # Grab list of preferred refants
    refantfield = scanheur.calibrator_field_select_string
    refantobj = findrefant.RefAntHeuristics(vis=myvis, field=refantfield,
                                            geometry=True, flagging=True,
                                            intent='',
                                            spw='',
                                            refantignore=refantignore)
    RefAntOutput = refantobj.calculate()
    refAnt = ','.join(RefAntOutput)

    # Lastly get list of other cal tables to use in the solution
    gc_tbl = glob("{}.hifv_priorcals.s*_2.gc.tbl".format(myvis))
    assert len(gc_tbl) == 1

    opac_tbl = glob("{}.hifv_priorcals.s*_3.opac.tbl".format(myvis))
    assert len(opac_tbl) == 1

    rq_tbl = glob("{}.hifv_priorcals.s*_4.rq.tbl".format(myvis))
    assert len(rq_tbl) == 1

    # Check ant correction
    ant_tbl = glob("{}.hifv_priorcals.s*_6.ants.tbl".format(myvis))

    priorcals = [gc_tbl[0], opac_tbl[0], rq_tbl[0]]

    if len(ant_tbl) == 1:
        priorcals.extend(ant_tbl)

    del_tbl = glob("{0}.{1}.s*_2.{2}delay.tbl".format(myvis, task_string, search_string))
    assert len(del_tbl) == 1

    BPinit_tbl = glob("{0}.{1}.s*_3.{2}BPdinitialgain.tbl".format(myvis,
                                                                  task_string,
                                                                  search_string))
    assert len(BPinit_tbl) == 1

    gaintables = copy(priorcals)
    gaintables.extend([del_tbl[0], BPinit_tbl[0]])

    bandpass(vis=myvis,
             caltable=bpname,
             field=scanheur.bandpass_field_select_string,
             selectdata=True,
             scan=scanheur.bandpass_scan_select_string,
             solint='inf',
             combine='scan',
             refant=refAnt,
             minblperant=4,
             minsnr=5.0,
             solnorm=False,
             bandtype='B',
             smodel=[],
             append=False,
             fillgaps=400,
             docallib=False,
             gaintable=gaintables,
             gainfield=[''],
             interp=[''],
             spwmap=[],
             parang=True)
