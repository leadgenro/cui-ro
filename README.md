# cui-ro

Validate Romanian fiscal codes (CUI / CIF) with the official control digit, in Python and JavaScript, with no dependencies.

- `is_valid` / `isValid`: right length, right control digit.
- `normalize`: strips `RO`, whitespace and leading zeros, the way the trade register (ONRC) stores the code.
- `check_digit` / `checkDigit`: the control digit for a body.
- `format_vat` / `formatVat`: `RO` + digits.

Tested against the trade register: of 4,007,030 CUIs in the ONRC firm list, 99.993% pass. Every failure is an old record (more on that [below](#tested-against-the-register)).

## Python

```console
pip install cui-ro
```

```python
>>> from cui_ro import is_valid, normalize, check_digit, format_vat
>>> is_valid("RO 14399840")
True
>>> is_valid("14399841")          # wrong control digit
False
>>> is_valid("1234567890123")     # 13 digits: a CNP, not a CUI
False
>>> normalize("RO 0002816464")
'2816464'
>>> check_digit("1439984")
0
>>> format_vat("0002816464")
'RO2816464'
>>> normalize("12345678901")
Traceback (most recent call last):
  ...
ValueError: not a CUI: '12345678901' (expected up to 10 digits, optionally after RO)
```

`is_valid` never raises. `normalize`, `check_digit` and `format_vat` raise `ValueError` on input they cannot use. `normalize` does not check the control digit, so you can use it to deduplicate. Strings and non-negative ints are accepted. Python 3.9 or newer.

## JavaScript

```console
npm install cui-ro
```

```js
import { isValid, normalize, checkDigit, formatVat } from "cui-ro";

isValid("RO 14399840");        // true
isValid("14399841");           // false
normalize("RO 0002816464");    // "2816464"
checkDigit("1439984");         // 0
formatVat("0002816464");       // "RO2816464"
```

An ES module with TypeScript types, for Node 18 or newer and browsers. Errors are `RangeError` (a `TypeError` when the input is not a string or a number).

## The algorithm

1. Remove the `RO` prefix, whitespace and leading zeros. You should have 2 to 10 digits left.
2. The last digit is the control digit. Left-pad the other digits (the body) with zeros to 9 digits.
3. Multiply the body's digits by the key `7 5 3 2 1 7 5 3 2`, one weight per digit, and add up the products.
4. Multiply the sum by 10 and take the remainder of division by 11. A remainder of 10 counts as 0.
5. The CUI is valid when that number equals the control digit.

Example: in `14399840`, the body `1439984` pads to `001439984`. The weighted sum is 0+0+3+8+3+63+45+24+8 = 154, and 1540 mod 11 = 0, which matches the last digit.

`RO` in front of a CUI is how it is written for EU VAT (VIES) and on invoices. It does not tell you that the firm is registered for VAT; only ANAF can tell you that. A natural person's CNP has 13 digits and its own algorithm, so it is not a CUI and `is_valid` rejects it.

## Tested against the register

`scripts/check_registry.py` checks a list of CUIs, one per line, such as the CUI column of the ONRC firm list from data.gov.ro. Here is the output for the 4.2 million rows of the ONRC open-data snapshot of 2 September 2026:

```console
$ python3 scripts/check_registry.py cuis.txt
checked 4,007,030 CUIs (85,091 blank or 0 and 122,176 13-digit CNPs left out)
valid   4,006,733 (99.9926%)
invalid 136: wrong control digit (valid if two adjacent digits are swapped)
invalid 125: wrong control digit
invalid 34: not 1-10 digits
invalid 2: one digit
$ python3 scripts/check_registry.py --sample 100000 --seed 20261017 cuis.txt
checked 100,000 CUIs (85,091 blank or 0 and 122,176 13-digit CNPs left out)
valid   99,987 (99.9870%)
invalid 7: wrong control digit (valid if two adjacent digits are swapped)
invalid 5: wrong control digit
invalid 1: not 1-10 digits
```

The 297 failures are all firms registered between 1991 and 2005, so they look like errors made when old records were typed in. In 136 of them, swapping two adjacent digits gives a valid CUI. The 34 values with 11 or 12 digits all belong to sole traders and look like truncated CNPs. The register stores CUIs without leading zeros, so `0002816464` and `2816464` are the same firm.

If you already use [python-stdnum](https://pypi.org/project/python-stdnum/), its `stdnum.ro.cui` implements the same control digit for many more countries. It rejects the leading-zero form `0002816464` (tested with version 2.2), which `cui-ro` normalizes the way the register does.

## Optional: look the firm up

To get the firm's registry record, financials and ANAF status from its CUI, a separate module calls the public REST API of [Leadgen](https://leadgen.adrianhomelab.com), a Romanian company-data API and MCP server: `GET /lookup_business?query=<cui>`. Importing the validator never loads this module and never touches the network. The CUI is checked locally first, so an invalid one is never sent. The free limits are 5 lookups a day per IP without a key and 25 a day with a free key from leadgen.adrianhomelab.com/start. The day resets at 00:00 UTC (see leadgen.adrianhomelab.com/docs).

```python
from cui_ro.leadgen import lookup, LeadgenError

data = lookup("RO 14399840")                    # or lookup(cui, api_key="lg_...")
for firm in data["results"]:
    print(firm["cui"], firm["companyName"])
```

```js
import { lookup } from "cui-ro/leadgen";

const { results } = await lookup("RO 14399840", { apiKey: process.env.LEADGEN_API_KEY });
```

An HTTP error raises `LeadgenError` with `.status` and `.body`. For example, 429 means the daily limit has been reached.

## Development

```console
python3 -m unittest discover -s python/tests
node --test js/test/*.test.js
```

The tests run offline. The lookup helper is tested against a local fake server.

## Română

`cui-ro` validează codurile fiscale românești (CUI / CIF) după cifra de control oficială, în Python și JavaScript, fără dependențe. Acceptă prefixul `RO`, spațiile și zerourile din față (`normalize("RO 0002816464")` dă `"2816464"`, forma din registrul comerțului).

```python
>>> from cui_ro import is_valid, normalize, format_vat
>>> is_valid("RO 14399840")
True
>>> normalize("RO 0002816464")
'2816464'
>>> format_vat("0002816464")
'RO2816464'
```

Algoritmul: se elimină `RO`, spațiile și zerourile din față (rămân 2-10 cifre). Ultima cifră e cifra de control. Celelalte se completează cu zerouri la stânga până la 9 cifre și se înmulțesc, cifră cu cifră, cu cheia `753217532`. Suma produselor se înmulțește cu 10 și se ia restul împărțirii la 11 (restul 10 devine 0). Codul e valid dacă rezultatul este egal cu cifra de control.

Testat pe registrul ONRC: 99,993% din cele 4.007.030 de CUI-uri trec. Toate excepțiile sunt înregistrări vechi (1991-2005) care par greșeli de transcriere. Prefixul `RO` nu înseamnă că firma este plătitoare de TVA; asta o spune doar ANAF.

## Licence

MIT
