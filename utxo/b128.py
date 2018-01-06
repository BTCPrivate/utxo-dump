
#
# adapted from https://github.com/sr-gi/bitcoin_tools
#

def read(data):
    b,i = parse(data)
    return b,data[i:]

def parse(utxo, offset=0):
    """ Parses a given serialized UTXO to extract a base-128 varint.
    :param utxo: Serialized UTXO from which the varint will be parsed.
    :type utxo: hex str
    :param offset: Offset where the beginning of the varint if located in the UTXO.
    :type offset: int
    :return: The extracted varint, and the offset of the byte located right after it.
    :rtype: hex str, int
    """

    i = 0
    ret = 0

    go = True
    while go:
        next_byte = ord(utxo[i])
        go = bool(next_byte & 0x80)
        ret = (ret << 7 | next_byte & 0x7f) + go

        i += 1

    return ret,i

def decompress_amount(x):
    """ Decompresses the Satoshi amount of a UTXO stored in the LevelDB. Code is a port from the Bitcoin Core C++
    source:
        https://github.com/bitcoin/bitcoin/blob/v0.13.2/src/compressor.cpp#L161#L185
    :param x: Compressed amount to be decompressed.
    :type x: int
    :return: The decompressed amount of satoshi.
    :rtype: int
    """

    if x == 0:
        return 0
    x -= 1
    e = x % 10
    x /= 10
    if e < 9:
        d = (x % 9) + 1
        x /= 9
        n = x * 10 + d
    else:
        n = x + 1
    while e > 0:
        n *= 10
        e -= 1
    return n
