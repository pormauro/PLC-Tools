# Minimal PDW/LDR writer validation

Status: **real WinProLadder write/open/check gates passed on 2026-09-28**.

## PDW test 1 — X1

Source:

    X0-Y0.pdw
    SHA-256 ed415db334e916eeec556f6da5df4eecb438ab304bcbe2677be2b1fac9446cb9

Derived:

    TEST-X1-Y0-FROM-X0-Y0.pdw
    SHA-256 4a19a3b9ab5a1f9a75a50482678e2169f5c1acc86f41af825a4c304f705258f7

Validation:

- opens in WinProLadder: PASS
- displays X1 -> Y0: PASS
- Syntax Check: PASS

## PDW test 2 — X2

Derived:

    TEST-X2-Y0.pdw
    SHA-256 3b8b068e6c92c094b9d452cb839f3e95f783c40eecaed76512afe9dee46eb860

Expected:

    ORG X2
    OUT Y0

Validation reported by user:

- opens correctly: PASS
- intended ladder: PASS
- check: PASS

## PDW test 3 — Y2

Derived:

    TEST-X0-Y2.pdw
    SHA-256 6c1112d3bd9939fe7f2ff72767f94fc0370a5f31877b3acbfb6bbaf3de336bb7

Expected:

    ORG X0
    OUT Y2

Validation reported by user:

- opens correctly: PASS
- intended ladder: PASS
- check: PASS

These two tests extend the X/Y high-byte index rule through indices 0, 1 and 2.

## LDR mutation test

Source:

    NC-X0-Y0.ldr

Derived:

    TEST-X0-Y0.ldr
    SHA-256 406e2a75da3e4292135a83d71644a80f8f562a5c433e0257b9125259d1397589

Mutation:

    file offset 0x0106: 50 -> 40

Expected code:

    40 00 C1 00
    ORG X0
    OUT Y0

WinProLadder import: PASS.

This is the first demonstrated LDR semantic mutation accepted by WinProLadder.

## What is proven

For the current scope it is possible to:

1. recover semantic PDW program bytes;
2. preserve the source transformation;
3. modify confirmed instructions/operands;
4. recompute the additive program checksum;
5. produce a PDW accepted by WinProLadder;
6. mutate same-length LDR code and import it.

## Guarded CLI

    python FATEK/WinProLadder/pdw_tools/analyze.py write-minimal template.pdw output.pdw --x 2 --y 0

Indices 0..2 are now fixture/WinProLadder-confirmed. Higher indices remain experimental and require `--allow-unconfirmed-index`.

## Not yet authorized

This does not yet prove arbitrary PDW generation. Multi-network code, variable-length blocks and unresolved structural bytes are still under investigation.
