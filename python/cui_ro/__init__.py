"""Romanian CUI / CIF validation: the official control digit, no dependencies.

>>> is_valid("RO 14399840")
True
>>> normalize("0002816464")
'2816464'
>>> check_digit("1439984")
0
>>> format_vat(" 1590082 ")
'RO1590082'

A CUI (cod unic de inregistrare, also called CIF, cod de identificare fiscala)
has 2 to 10 digits; the last is a control digit computed from the others with
the key 753217532. The optional "RO" prefix, spaces and leading zeros are
accepted, as the trade register (ONRC) and ANAF accept them.
"""
from __future__ import annotations

import re

__all__ = ["is_valid", "normalize", "check_digit", "format_vat"]
__version__ = "1.0.0"

KEY = "753217532"
_SHAPE = re.compile(r"^(?:RO)?0*([0-9]{1,10})$")
_MAX_INPUT = 64


def _compact(cui) -> str:
    if isinstance(cui, bool):
        raise ValueError("a CUI is a number, not a bool")
    if isinstance(cui, int):
        if cui < 0:
            raise ValueError("a CUI cannot be negative")
        cui = str(cui)
    if not isinstance(cui, str):
        raise ValueError(f"a CUI is a str or an int, not {type(cui).__name__}")
    if len(cui) > _MAX_INPUT:
        raise ValueError("too long to be a CUI")
    return re.sub(r"\s+", "", cui).upper()


def normalize(cui) -> str:
    """The CUI as the registry stores it: no "RO", no whitespace, no leading zeros.

    Raises ValueError unless what remains is 1 to 10 digits. The control digit
    is not checked here: use ``is_valid`` for that.
    """
    m = _SHAPE.match(_compact(cui))
    if not m:
        raise ValueError(f"not a CUI: {cui!r} (expected up to 10 digits, optionally after RO)")
    return m.group(1)


def check_digit(body) -> int:
    """The control digit for the CUI digits before it (1 to 9 digits)."""
    if isinstance(body, int) and not isinstance(body, bool) and body >= 0:
        body = str(body)
    if not isinstance(body, str) or not re.fullmatch(r"[0-9]{1,9}", body):
        raise ValueError(f"the body of a CUI is 1 to 9 digits, not {body!r}")
    total = sum(int(d) * int(k) for d, k in zip(body.zfill(9), KEY))
    return total * 10 % 11 % 10


def is_valid(cui) -> bool:
    """True when ``cui`` is a well-formed CUI (2-10 digits) with the right control digit."""
    try:
        digits = normalize(cui)
    except ValueError:
        return False
    return len(digits) >= 2 and check_digit(digits[:-1]) == int(digits[-1])


def format_vat(cui) -> str:
    """'RO' + the normalized CUI, the form used in EU VAT (VIES) and on invoices.

    Raises ValueError for an invalid CUI. The prefix is a format only: it does
    not tell you the firm is registered for VAT (ANAF does).
    """
    if not is_valid(cui):
        raise ValueError(f"not a valid CUI: {cui!r}")
    return "RO" + normalize(cui)
