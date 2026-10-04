import unittest
from order import total
class CoreCheckoutTests(unittest.TestCase):
    def test_fractional_discount(self):
        self.assertEqual(total([10, 20], .1), 27)
    def test_no_discount(self):
        self.assertEqual(total([10, 20], 0), 30)
if __name__ == '__main__':
    unittest.main()
