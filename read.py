#!/usr/bin/env python

from argparse import ArgumentParser
from os.path import isfile, isdir
from utxo.util import read_utxos, utxo_file_name

parser = ArgumentParser()
parser.add_argument('utxo_dir')
parser.add_argument('--filenum', type=int)
args = parser.parse_args()

utxo_dir = args.utxo_dir
filenum = args.filenum
assert isdir(utxo_dir)

if filenum is not None:
    read_utxos(utxo_dir, filenum)
else:
    i = 1
    total_amount = 0
    while isfile(utxo_file_name(utxo_dir, i)):
        amt = read_utxos(utxo_dir, i)
        print "file: {}: amount: {}".format(i, amt)
        total_amount += amt
        i += 1

    print "total: amount: {}".format(total_amount)
