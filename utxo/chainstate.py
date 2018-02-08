import b128
import binascii
import itertools
import os
import plyvel
import secp256k1

from binascii import unhexlify
from utxo.script import OP_DUP, OP_HASH160, OP_EQUAL, \
    OP_EQUALVERIFY, OP_CHECKSIG


def ldb_iter(datadir):
    db = plyvel.DB(os.path.join(datadir, "chainstate"), compression=None)
    obf_key = db.get((unhexlify("0e00") + "obfuscate_key"))

    if obf_key is not None:
        pre = 'C'
        obf_key = map(ord, obf_key[1:])
    else:
        pre = 'c'

    def norm(raw):
        key, value = raw
        if obf_key is not None:
            value = deobfuscate(obf_key, value)
            return parse_ldb_value(key, value)[0]

        else:
            return parse_ldb_value_old(key, value)

    it = db.iterator(prefix=pre)
    return itertools.imap(norm, it)


def parse_ldb_value(key, raw):
    tx_hash = key[1:33]

    index = b128.parse(key[33:])[0]

    code, raw = b128.read(raw)
    height = code >> 1

    amt_comp, raw = b128.read(raw)
    amt = b128.decompress_amount(amt_comp)

    script_code, raw = b128.read(raw)
    script = decompress_raw(script_code, raw)

    return tx_hash, height, index, amt, script


def parse_ldb_value_old(key, raw):
    tx_hash = key[1:]

    version, raw = b128.read(raw)
    code, raw = b128.read(raw)

    first_two = (code & (2 | 4)) >> 1
    n = (code >> 3) + (first_two == 0)

    offset = 0
    bitv = first_two
    if n > 0:
        while n:
            n -= (ord(raw[offset]) != 0)
            offset += 1
        bitv = (int(raw[:offset][::-1].encode('hex'), 16) << 2) | first_two
    raw = raw[offset:]

    i = 0
    utxos = []
    while bitv > 0:
        if bitv & 1:
            amt_comp, raw = b128.read(raw)
            amt = b128.decompress_amount(amt_comp)

            script_code, raw = b128.read(raw)
            script, raw = decompress_raw(script_code, raw, chomp=True)

            ut = (tx_hash, None, i, amt, script)
            utxos.append(ut)
        bitv >>= 1
        i += 1

    height, raw = b128.read(raw)

    ret = [u[:1] + (height,) + u[2:] for u in utxos]
    return ret


def decompress_raw(comp_type, raw, chomp=False):

    if comp_type == 0 or comp_type == 1:
        l = 20
    elif comp_type >= 2 and comp_type <= 5:
        l = 32
    else:
        l = comp_type - 6

    data = raw[:l]
    raw = raw[l:]

    if not chomp:
        assert len(raw) == 0

    if comp_type == 0:
        script = OP_DUP + OP_HASH160 + chr(20) + data + \
            OP_EQUALVERIFY + OP_CHECKSIG

    elif comp_type == 1:
        script = OP_HASH160 + chr(20) + data + OP_EQUAL

    elif comp_type == 2 or comp_type == 3:
        script = chr(33) + chr(comp_type) + data + OP_CHECKSIG

    elif comp_type == 4 or comp_type == 5:
        comp_pubkey = chr(comp_type - 2) + data
        pubkey = secp256k1.PublicKey(
            comp_pubkey, raw=True
        ).serialize(compressed=False)

        script = chr(65) + pubkey + OP_CHECKSIG

    else:
        script = data

    return script, raw


def deobfuscate(key, obf):
    n = len(key)
    de = [chr(key[i % n] ^ ord(b)) for i, b in enumerate(obf)]

    return "".join(de)
