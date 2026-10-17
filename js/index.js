// cui-ro: Romanian CUI / CIF validation with the official control digit. No dependencies.
// A CUI has 2 to 10 digits; the last is a control digit computed from the others
// with the key 753217532. "RO", whitespace and leading zeros are accepted.

export const KEY = "753217532";
const SHAPE = /^(?:RO)?0*([0-9]{1,10})$/;
const MAX_INPUT = 64;

function compact(cui) {
  if (typeof cui === "number") {
    if (!Number.isSafeInteger(cui) || cui < 0) throw new RangeError(`not a CUI: ${cui}`);
    cui = String(cui);
  }
  if (typeof cui !== "string") throw new TypeError(`a CUI is a string or a number, not ${cui === null ? "null" : typeof cui}`);
  if (cui.length > MAX_INPUT) throw new RangeError("too long to be a CUI");
  return cui.replace(/\s+/g, "").toUpperCase();
}

/**
 * The CUI as the registry stores it: no "RO", no whitespace, no leading zeros.
 * Throws unless what remains is 1 to 10 digits. Does not check the control digit.
 */
export function normalize(cui) {
  const m = SHAPE.exec(compact(cui));
  if (!m) throw new RangeError(`not a CUI: ${JSON.stringify(cui)} (expected up to 10 digits, optionally after RO)`);
  return m[1];
}

/** The control digit for the CUI digits before it (1 to 9 digits). */
export function checkDigit(body) {
  if (typeof body === "number" && Number.isSafeInteger(body) && body >= 0) body = String(body);
  if (typeof body !== "string" || !/^[0-9]{1,9}$/.test(body)) {
    throw new RangeError(`the body of a CUI is 1 to 9 digits, not ${JSON.stringify(body)}`);
  }
  const padded = body.padStart(9, "0");
  let total = 0;
  for (let i = 0; i < 9; i++) total += Number(padded[i]) * Number(KEY[i]);
  return ((total * 10) % 11) % 10;
}

/** True when `cui` is a well-formed CUI (2-10 digits) with the right control digit. Never throws. */
export function isValid(cui) {
  let digits;
  try {
    digits = normalize(cui);
  } catch {
    return false;
  }
  return digits.length >= 2 && checkDigit(digits.slice(0, -1)) === Number(digits.at(-1));
}

/**
 * "RO" + the normalized CUI (EU VAT / VIES form). Throws for an invalid CUI.
 * The prefix is a format only: it does not mean the firm is registered for VAT.
 */
export function formatVat(cui) {
  if (!isValid(cui)) throw new RangeError(`not a valid CUI: ${JSON.stringify(cui)}`);
  return "RO" + normalize(cui);
}
