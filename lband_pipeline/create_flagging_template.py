
'''
Functions for producing custom flagging files to be
applied prior to reduction.
'''

import os


def flagtemplate_add(sdm, flagcmds=[], outfile=""):
    """
    Append additional flagging commands to the flagtemplate if they are not present already.
    Useful for L-band VLA HI obs: e.g. flagcmds=["mode='manual' spw='1,2:0~64,4'"]

    Author: Mladen Novak

    :param sdm: path to visibility data, will append .flagtemplate.txt to it
    :param flagcmds: list of commands to append into the template file
    :param outfile: override naming to custom filename
    :return: None
    """
    if outfile == "":
        outfile = sdm + ".flagtemplate.txt"

    if os.path.exists(outfile):
        with open(outfile, "r") as f:
            content = f.read().splitlines()
    else:
        content = [""]

    with open(outfile, "a") as f:
        for cmd in flagcmds:
            if cmd not in content:
                f.write("\n" + cmd + "\n")
