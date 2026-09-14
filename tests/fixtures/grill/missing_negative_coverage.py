"""Tests for the discount calculator."""

import unittest

from discount import apply_discount


class DiscountTests(unittest.TestCase):
    def test_ten_percent_off_hundred(self) -> None:
        self.assertEqual(apply_discount(100, 10), 90)

    def test_zero_discount(self) -> None:
        self.assertEqual(apply_discount(100, 0), 100)
