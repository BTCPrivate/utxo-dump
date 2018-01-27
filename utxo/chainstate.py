import b128
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
        obf_key = map(ord, obf_key[1:])

    def norm(raw):
        key, value = raw
        if obf_key is not None:
            value = deobfuscate(obf_key, value)
            return parse_ldb_value(key, value)

        else:
            return parse_ldb_value_old(value)
        _
    it = db.iterator(prefix=b'C')
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


def parse_ldb_value_old(raw):
    version, raw = b128.read(raw)
    code, raw = b128.read(raw)

    is_coinbase = code & 1
    vout = [code & 0x02, code & 0x04]
    if not vout[0] and not vout[1]:
        n = (code >> 3) + 1

    else:
        pass


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

        return chr(33) + chr(comp_type) + data + OP_CHECKSIG

    elif comp_type == 4 or comp_type == 5:
        assert len(data) == 32

        comp_pubkey = chr(comp_type - 2) + data
        pubkey = secp256k1.PublicKey(
            comp_pubkey, raw=True
        ).serialize(compressed=False)

        return chr(65) + pubkey + OP_CHECKSIG

    else:
        assert len(data) == comp_type - 6
        return data


def deobfuscate(key, obf):
    n = len(key)
    de = [chr(key[i % n] ^ ord(b)) for i, b in enumerate(obf)]

    return "".join(de)
