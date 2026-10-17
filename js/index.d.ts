/** The weights of the control digit, left to right. */
export const KEY: "753217532";
/** The CUI as the registry stores it: no "RO", no whitespace, no leading zeros. Throws unless 1-10 digits remain. */
export function normalize(cui: string | number): string;
/** The control digit (0-9) for the CUI digits before it (1 to 9 digits). Throws otherwise. */
export function checkDigit(body: string | number): number;
/** True when `cui` is a well-formed CUI (2-10 digits) with the right control digit. Never throws. */
export function isValid(cui: unknown): boolean;
/** "RO" + the normalized CUI. Throws for an invalid CUI. */
export function formatVat(cui: string | number): string;
