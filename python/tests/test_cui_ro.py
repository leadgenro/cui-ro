import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cui_ro  # noqa: E402
from cui_ro import check_digit, format_vat, is_valid, normalize  # noqa: E402

# Real registered firms (ONRC open data): DEDEMAN SRL, OMV PETROM SA, DANTE INTERNATIONAL SA (eMAG).
REAL = ["2816464", "1590082", "14399840"]


def make(body: str) -> str:
    return body + str(check_digit(body))


class CheckDigit(unittest.TestCase):
    def test_real_cuis(self):
        for cui in REAL:
            self.assertEqual(check_digit(cui[:-1]), int(cui[-1]), cui)

    def test_worked_example(self):
        # 1439984 -> 001439984; 0*7+0*5+1*3+4*2+3*1+9*7+9*5+8*3+4*2 = 154; 154*10 % 11 = 0
        self.assertEqual(check_digit("1439984"), 0)

    def test_remainder_ten_becomes_zero(self):
        body = next(b for b in (str(n) for n in range(1, 10000))
                    if sum(int(d) * int(k) for d, k in zip(b.zfill(9), "753217532")) * 10 % 11 == 10)
        self.assertEqual(check_digit(body), 0)
        self.assertTrue(is_valid(body + "0"))

    def test_padding_does_not_change_the_digit(self):
        self.assertEqual(check_digit("281646"), check_digit("000281646"))

    def test_int_body(self):
        self.assertEqual(check_digit(1439984), 0)

    def test_bad_bodies(self):
        for bad in ["", "1234567890", "12a", " 12", "-1", None, 1.5, True, "١٢٣"]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                check_digit(bad)


class Valid(unittest.TestCase):
    def test_real(self):
        for cui in REAL:
            self.assertTrue(is_valid(cui), cui)

    def test_accepted_forms(self):
        for form in ["RO14399840", "ro14399840", "RO 14399840", " 14399840 ", "14 399 840",
                     "RO\t14399840\n", "0014399840", "RO0002816464", "0002816464", 14399840]:
            self.assertTrue(is_valid(form), repr(form))

    def test_lengths(self):
        self.assertTrue(is_valid(make("1")))            # 2 digits, the shortest
        self.assertTrue(is_valid(make("123456789")))    # 10 digits, the longest
        self.assertFalse(is_valid("1"))
        self.assertFalse(is_valid("0"))
        self.assertFalse(is_valid("12345678901"))       # 11 digits
        self.assertFalse(is_valid("1234567890123"))     # 13 digits: a CNP, not a CUI

    def test_wrong_digit(self):
        for cui in REAL:
            for d in "0123456789":
                if d != cui[-1]:
                    self.assertFalse(is_valid(cui[:-1] + d), cui[:-1] + d)

    def test_transposition(self):
        self.assertFalse(is_valid("14399804"))
        self.assertFalse(is_valid("2861464"))

    def test_garbage(self):
        for bad in ["", "RO", "R014399840", "RO-14399840", "14399840RO", "1439984O", "abc",
                    "14399840.0", "+14399840", "١٤٣٩٩٨٤٠", None, -14399840, True, 14399840.0,
                    ["14399840"], "1" * 100]:
            self.assertFalse(is_valid(bad), repr(bad))


class Normalize(unittest.TestCase):
    def test_strips_like_the_registry(self):
        self.assertEqual(normalize("0002816464"), "2816464")
        self.assertEqual(normalize("RO 0002816464"), "2816464")
        self.assertEqual(normalize("ro14399840"), "14399840")
        self.assertEqual(normalize(" 14 399 840 "), "14399840")
        self.assertEqual(normalize(1590082), "1590082")

    def test_does_not_check_the_digit(self):
        self.assertEqual(normalize("14399841"), "14399841")

    def test_rejects_non_cuis(self):
        for bad in ["", "RO", "abc", "12345678901", "RO-123", None, 1.0]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                normalize(bad)


class FormatVat(unittest.TestCase):
    def test_format(self):
        self.assertEqual(format_vat("14399840"), "RO14399840")
        self.assertEqual(format_vat("ro 0002816464"), "RO2816464")
        self.assertEqual(format_vat(1590082), "RO1590082")

    def test_invalid(self):
        with self.assertRaises(ValueError):
            format_vat("14399841")


class Doc(unittest.TestCase):
    def test_readme_examples(self):
        import doctest
        readme = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "README.md")
        if not os.path.exists(readme):
            self.skipTest("README.md not found")
        import re
        with open(readme, encoding="utf-8") as f:
            blocks = re.findall(r"```python\n(.*?)```", f.read(), re.S)
        parser, runner = doctest.DocTestParser(), doctest.DocTestRunner(verbose=False)
        for i, block in enumerate(b for b in blocks if ">>>" in b):
            runner.run(parser.get_doctest(block, {}, f"README block {i}", readme, 0))
        result = runner.summarize(verbose=False)
        self.assertEqual(result.failed, 0)
        self.assertGreater(result.attempted, 5)

    def test_doctest(self):
        import doctest
        self.assertEqual(doctest.testmod(cui_ro, verbose=False).failed, 0)


if __name__ == "__main__":
    unittest.main()
