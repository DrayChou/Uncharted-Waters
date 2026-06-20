import unittest

from uw2toolkit.render.kao import decode_3plane_8color


class KaoRenderTests(unittest.TestCase):
    def test_decode_3plane_size_mismatch_raises(self):
        with self.assertRaises(ValueError):
            decode_3plane_8color(b'\x00' * 3, width=16, height=16)

    def test_decode_single_8px_block(self):
        # 24 bits => one 8-pixel block. Make all pixels color index 0.
        arr = decode_3plane_8color(b'\x00\x00\x00', width=8, height=1)
        self.assertEqual(arr.shape, (1, 8, 3))
        self.assertTrue((arr == 0).all())


if __name__ == '__main__':
    unittest.main()
