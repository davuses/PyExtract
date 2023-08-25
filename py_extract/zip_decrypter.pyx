# cython: language_level=3
# distutils: language = c
# cython: cdivision = True
# cython: boundscheck = False
# cython: wraparound = False
# cython: nonecheck = False
# cython: profile = False
# https://github.com/ziyuang/czipfile/blob/ba592c44c79d830a063210d598737f91f4333035/czipfile.pyx

"""
cython implementation of zip decryption
"""

cimport cpython

cdef class _ZipDecrypter:
    """Class to handle decryption of files stored within a ZIP archive.
    ZIP supports a password-based form of encryption. Even though known
    plaintext attacks have been found against it, it is still useful
    to be able to get data out of such a file.
    Usage:
        zd = _ZipDecrypter(mypwd)
        plain_text = zd(cypher_text)
    The original usage of:
        plain_text = map(zd, cypher_text)
    is still supported, but will be slower (by a factor of 10 or so, by
    my measurements) than simply calling it with the full cypher_text.
    """

    # I guess to make these C vars, we must declare them out here?
    cdef unsigned long crctable[256]
    cdef unsigned long key0
    cdef unsigned long key1
    cdef unsigned long key2

    cdef void _GenerateCRCTable(self):
        """Generate a CRC-32 table.
        ZIP encryption uses the CRC32 one-byte primitive for scrambling some
        internal keys. We noticed that a direct implementation is faster than
        relying on binascii.crc32().
        """
        cdef unsigned long poly = 0xedb88320
        cdef unsigned long crc, i, j
        for 0 <= i < 256:
            crc = i
            for 0 <= j < 8:
                if crc & 1:
                    crc = ((crc >> 1) & 0x7FFFFFFF) ^ poly
                else:
                    crc = ((crc >> 1) & 0x7FFFFFFF)
            self.crctable[i] = crc

    cdef unsigned long _crc32(self, unsigned char ch, unsigned long crc):
        """Compute the CRC32 primitive on one byte."""
        return ((crc >> 8) & 0xffffff) ^ self.crctable[(crc ^ ch) & 0xff]

    def __init__(self, pwd):
        self.key0 = 305419896
        self.key1 = 591751049
        self.key2 = 878082192

        # Generate the CRC table; previously done outside of any method
        self._GenerateCRCTable()

        # Update our keys, given the password
        for p in pwd:
            self._UpdateKeys(p)

    cdef void _UpdateKeys(self, unsigned char c):
        self.key0 = self._crc32(c, self.key0)
        self.key1 = (self.key1 + (self.key0 & 255)) & 4294967295UL
        self.key1 = (self.key1 * 134775813 + 1) & 4294967295UL
        self.key2 = self._crc32((self.key1 >> 24) & 255, self.key2)

    def __call__(self, data):
        cdef unsigned long k
        cdef Py_ssize_t i, datalen
        cdef char *data_s
        cdef char *ret_s

        cpython.PyBytes_AsStringAndSize(data, &data_s, &datalen)
        ret = cpython.PyBytes_FromStringAndSize(NULL, datalen)
        ret_s = cpython.PyBytes_AsString(ret)
        for 0 <= i < datalen:
            k = self.key2 | 2
            ret_s[i] = data_s[i] ^ (((k * (k^1)) >> 8) & 255);
            # The proper way to do this is to call _UpdateKeys here, like so:
            #self._UpdateKeys(ret_s[i])
            # ... but we can cut runtime by about a third if we unroll the
            # function.  So, we're doing so.  Yes, it's duplication.  Ah well...
            self.key0 = ((self.key0 >> 8) & 0xFFFFFF) ^ self.crctable[(self.key0 ^ ret_s[i]) & 0xFF]
            self.key1 = (self.key1 + (self.key0 & 255)) & 4294967295UL
            self.key1 = (self.key1 * 134775813 + 1) & 4294967295UL
            self.key2 = ((self.key2 >> 8) & 0xFFFFFF) ^ self.crctable[(self.key2 ^ ((self.key1 >> 24) & 255)) & 0xFF]

        return ret
