import os
import struct

from binascii import hexlify

from utxo.chainstate import ldb_iter
from utxo.script import unwitness
from utxo.util import new_utxo_file


def snap_utxos(bitcoind, bitcoind_datadir, stop_block):

    cmd = "{} -reindex-chainstate -datadir={} -stopatheight={}".format(
        bitcoind, bitcoind_datadir, stop_block)
    print("running " + cmd)
    os.system(cmd)


def dump_utxos(datadir, output_dir, n, convert_segwit, maxT=0, debug=True):

    i = 0
    k = 0

    f = new_utxo_file(output_dir, k)
    for value in ldb_iter(datadir):

        tx_hash, height, index, amt, script = value
        if convert_segwit:
            script = unwitness(script)

        if debug:
            print(hexlify(tx_hash[::-1]), height, index, amt, hexlify(script))

        f.write(struct.pack('<QQ', amt, len(script)))
        f.write(script)
        f.write('\n')

        i += 1
        if i % n == 0:
            f.close()
            f = new_utxo_file(output_dir, k)
            k += 1

        if maxT != 0 and i >= maxT:
            break

    f.close()
