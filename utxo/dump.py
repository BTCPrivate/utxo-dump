#!/usr/bin/env python

import os
import plyvel
import secp256k1
import struct
import sys

from binascii import hexlify, unhexlify
import b128

OP_DUP = chr(0x76)
OP_HASH160 = chr(0xa9)
OP_EQUALVERIFY = chr(0x88)
OP_CHECKSIG = chr(0xac)
OP_EQUAL = chr(0x87)


def snap_utxos(bitcoind, bitcoind_datadir, stop_block):

    cmd = "{} -reindex-chainstate -datadir={} -stopatheight={}".format(
        bitcoind, bitcoind_datadir, stop_block)
    print "running " + cmd
    os.system(cmd)


def dump_utxos(datadir, output, maxT=0):

    db = plyvel.DB(os.path.join(datadir, "chainstate"), compression=None)
    obf_key = map(ord, db.get((unhexlify("0e00") + "obfuscate_key"))[1:])

    f = open(output, 'wb')
    i = 0
    for key, value in db.iterator(prefix=b'C'):
        value = deobfuscate(obf_key, value)

        height, index, amt, script = parse_ldb_value(key, value)

        print height, index, amt, hexlify(script)

        f.write(struct.pack('<QQ', amt, len(script)))
        f.write(script)
        f.write('\n')

        i += 1
        if maxT != 0 and i >= maxT:
            break

    f.close()


def parse_ldb_value(key,raw):
    key = hexlify(key)
    index = b128.decode(key[66:])

    raw = hexlify(raw)

    code, raw = b128.read(raw)
    height = code >> 1

    amt_comp, raw = b128.read(raw)
    amt = b128.decompress_amount(amt_comp)

    script_code, raw = b128.read(raw)
    script = decompress_raw(script_code, unhexlify(raw))

    return height, index, amt, script


def decompress_raw(comp_type, data):

    if comp_type == 0:
        assert len(data) == 20
        return OP_DUP + OP_HASH160 + chr(20) + data + \
            OP_EQUALVERIFY + OP_CHECKSIG

    elif comp_type == 1:
        assert len(data) == 20
        return OP_HASH160 + chr(20) + data + OP_EQUAL

    elif comp_type == 2 or comp_type == 3:
        assert len(data) == 32

        return chr(33) + comp_type + data + OP_CHECKSIG

    elif comp_type == 4 or comp_type == 5:
        assert len(data) == 32

        comp_pubkey = chr(comp_type - 2) + data
        pubkey = secp256k1.PublicKey(
            comp_pubkey, raw=True).serialize(compressed=False)

        return chr(65) + pubkey + OP_CHECKSIG

    else:
        assert len(data) == comp_type - 6
        return data


def deobfuscate(key, obf):
    n = len(key)
    de = [chr(key[i % n] ^ ord(b)) for i, b in enumerate(obf)]

    return "".join(de)


def read_file(path):
    f = open(path, 'rb')

    head = f.read(16)
    while head != "":
        amt,sz = struct.unpack('<QQ', head)
        script = f.read(sz)

        assert f.read(1) == '\n'
        print amt, hexlify(script)
        head = f.read(16)

    f.close()

if __name__ == "__main__":
    action = sys.argv[1]
    if action == 'dump':
        (block, bitcoind, datadir, out_file) = sys.argv[1:]
        snap_utxos(bitcoind, datadir, block)
        dump_utxos(datadir, out_file)

    elif action == 'read':
        fn = sys.argv[2]
        read_file(fn)
