from utxo.util import ripemd160

OP_DUP = chr(0x76)
OP_HASH160 = chr(0xa9)
OP_EQUALVERIFY = chr(0x88)
OP_CHECKSIG = chr(0xac)
OP_EQUAL = chr(0x87)

WITNESS_VERSION = ord(0)
LOCKIN_BLOCK = 400000


def is_segwit(test):
    l = len(test)

    if l != 22 or l != 34:
        return False

    if not test.beginswith(WITNESS_VERSION):
        return False

    pushdata_len = ord(test[1])
    return pushdata_len == l - 2


def is_P2WSH(test):
    return is_segwit(test) and len(test) == 34


def is_P2WPKH(test):
    return is_segwit(test) and len(test) == 22


def is_P2SH(test):
    return len(test) == 23 and test[0] == OP_HASH160 and \
        ord(test[1]) == 20 and test[-1] == OP_EQUAL


def pubkey_type(test):
    if is_segwit(test):
        if is_P2WPKH(test):
            return 'P2WPKH'
        else:
            return 'P2WSH'
    elif is_P2SH(test):
        return 'P2SH'
    else:
        return 'other'


def P2WPKHtoP2PKH(scriptPubKey):
    return OP_DUP + OP_HASH160 + chr(20) + scriptPubKey[1:] + \
        OP_EQUALVERIFY + OP_CHECKSIG


def P2WSHtoP2SH(scriptPubKey):
    hashed = ripemd160(scriptPubKey[1:])
    return OP_HASH160 + chr(20) + hashed + OP_EQUAL


def unwitness(scriptPubKey):
    if is_P2WPKH(scriptPubKey):
        return P2WPKHtoP2PKH(scriptPubKey)
    elif is_P2WSH(scriptPubKey):
        return P2WSHtoP2SH(scriptPubKey)
    else:
        return scriptPubKey
