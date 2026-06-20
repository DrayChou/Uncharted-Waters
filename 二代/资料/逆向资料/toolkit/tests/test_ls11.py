import unittest

from uw2toolkit.ls11 import bits_from_bytes, decode_parts


class LS11Tests(unittest.TestCase):
    def test_bits_from_bytes_msb_first(self):
        self.assertEqual(list(bits_from_bytes(bytes([0b10100000])))[:4], [1, 0, 1, 0])

    def test_decode_parts_rejects_bad_magic(self):
        with self.assertRaises(ValueError):
            decode_parts(b'NOPE' + b'\x00' * 300)


if __name__ == '__main__':
    unittest.main()
