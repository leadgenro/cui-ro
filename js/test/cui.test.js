import { test } from "node:test";
import assert from "node:assert/strict";
import { checkDigit, formatVat, isValid, normalize, KEY } from "../index.js";

// Real registered firms (ONRC open data): DEDEMAN SRL, OMV PETROM SA, DANTE INTERNATIONAL SA (eMAG).
const REAL = ["2816464", "1590082", "14399840"];
const make = (body) => body + String(checkDigit(body));

test("control digit of real CUIs", () => {
  for (const cui of REAL) assert.equal(checkDigit(cui.slice(0, -1)), Number(cui.at(-1)), cui);
  assert.equal(checkDigit("1439984"), 0);
  assert.equal(checkDigit(1439984), 0);
  assert.equal(checkDigit("281646"), checkDigit("000281646"));
  assert.equal(KEY, "753217532");
});

test("a remainder of 10 gives 0", () => {
  let body;
  for (let n = 1; n < 10000 && !body; n++) {
    const b = String(n).padStart(9, "0");
    let t = 0;
    for (let i = 0; i < 9; i++) t += Number(b[i]) * Number(KEY[i]);
    if ((t * 10) % 11 === 10) body = String(n);
  }
  assert.equal(checkDigit(body), 0);
  assert.ok(isValid(body + "0"));
});

test("bad bodies throw", () => {
  for (const bad of ["", "1234567890", "12a", " 12", "-1", null, undefined, 1.5, true, "١٢٣"]) {
    assert.throws(() => checkDigit(bad), RangeError, String(bad));
  }
});

test("valid forms", () => {
  for (const cui of REAL) assert.ok(isValid(cui), cui);
  for (const form of ["RO14399840", "ro14399840", "RO 14399840", " 14399840 ", "14 399 840",
    "RO\t14399840\n", "0014399840", "RO0002816464", "0002816464", 14399840]) {
    assert.ok(isValid(form), JSON.stringify(form));
  }
});

test("lengths", () => {
  assert.ok(isValid(make("1")));
  assert.ok(isValid(make("123456789")));
  assert.ok(!isValid("1"));
  assert.ok(!isValid("0"));
  assert.ok(!isValid("12345678901"));
  assert.ok(!isValid("1234567890123"));
});

test("wrong digit, transposition, garbage", () => {
  for (const cui of REAL) {
    for (const d of "0123456789") if (d !== cui.at(-1)) assert.ok(!isValid(cui.slice(0, -1) + d));
  }
  assert.ok(!isValid("14399804"));
  assert.ok(!isValid("2861464"));
  for (const bad of ["", "RO", "R014399840", "RO-14399840", "14399840RO", "1439984O", "abc",
    "14399840.0", "+14399840", "١٤٣٩٩٨٤٠", null, undefined, -14399840, true, 14399840.5,
    ["14399840"], {}, "1".repeat(100)]) {
    assert.ok(!isValid(bad), JSON.stringify(bad));
  }
});

test("normalize strips RO, whitespace and leading zeros", () => {
  assert.equal(normalize("0002816464"), "2816464");
  assert.equal(normalize("RO 0002816464"), "2816464");
  assert.equal(normalize("ro14399840"), "14399840");
  assert.equal(normalize(" 14 399 840 "), "14399840");
  assert.equal(normalize(1590082), "1590082");
  assert.equal(normalize("14399841"), "14399841");
  for (const bad of ["", "RO", "abc", "12345678901", "RO-123", 1.5]) assert.throws(() => normalize(bad), RangeError);
  assert.throws(() => normalize(null), TypeError);
});

test("formatVat", () => {
  assert.equal(formatVat("14399840"), "RO14399840");
  assert.equal(formatVat("ro 0002816464"), "RO2816464");
  assert.equal(formatVat(1590082), "RO1590082");
  assert.throws(() => formatVat("14399841"), RangeError);
});
