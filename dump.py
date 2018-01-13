#!/usr/bin/env python

from argparse import ArgumentParser
from os.path import isdir

from utxo.dump import dump_utxos, snap_utxos

parser = ArgumentParser()
parser.add_argument('bitcoind_datadir')
parser.add_argument('utxo_dir')

parser.add_argument('--nperfile', type=int, default=10E3)
parser.add_argument('--transform_segwit', type=bool, default=True)

# to run bitcoind with -reindex-chainstate and -stopatheight provide all three
parser.add_argument('--reindex', type=bool, default=False)
parser.add_argument('--bitcoind')
parser.add_argument('--blockheight', type=int)

# debugging options
parser.add_argument('--verbose', default=False)
parser.add_argument('--maxutxos', type=int, default=0)

args = parser.parse_args()

if not isdir(args.utxo_dir):
    raise Exception("invalid utxo_dir")

if not isdir(args.bitcoind_datadir):
    raise Exception("invalid bitcoind_datadir")

if(args.reindex or args.bitcoind or args.blockheight):
    assert args.reindex and args.bitcoind is not None and args.blockheight >= 0
    snap_utxos(args.bitcoind, args.bitcoind_datadir, args.blockheight)

dump_utxos(args.bitcoind_datadir, args.utxo_dir, args.nperfile,
           args.transform_segwit, args.maxutxos, debug=args.verbose)
