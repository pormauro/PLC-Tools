# Minimal PDW writer validation

Status: **first real write/open/syntax-check gate passed on 2026-09-28**.

## Experiment

Source template:

    X0-Y0.pdw
    SHA-256 ed415db334e916eeec556f6da5df4eecb438ab304bcbe2677be2b1fac9446cb9

Target semantics:

    ORG X1
    OUT Y0

A derived file was produced by preserving the source PDW transformation and changing only the semantic bytes required by the controlled corpus.

Physical PDW bytes changed:

    0x001ED: 62 -> 61
    0x00323: 84 -> 85

Derived file:

    TEST-X1-Y0-FROM-X0-Y0.pdw
    SHA-256 4a19a3b9ab5a1f9a75a50482678e2169f5c1acc86f41af825a4c304f705258f7

## External validation in WinProLadder

User validation result:

- file opens successfully: PASS;
- ladder displays the intended X1 -> Y0 semantics: PASS;
- WinProLadder Syntax Check: PASS.

This is the first demonstrated PDW semantic write round-trip.

## What this proves

For the current minimal two-word rung family, it is possible to:

1. start from a valid PDW template;
2. derive its periodic transform from an erased program record;
3. recover the active program record;
4. edit confirmed semantic/control fields;
5. recalculate the observed additive code checksum;
6. reapply the original template transform;
7. produce a PDW accepted by WinProLadder.

The save/keystream generation algorithm does not need to be known to perform a safe template-preserving mutation in this narrow proven scope.

## What this does NOT prove

It does not yet authorize arbitrary PDW generation.

Still unknown:

- programs longer than the current 2-word rung family;
- multiple networks;
- variable-length instructions;
- regeneration of a PDW without a valid template;
- exact meaning/generation of save-state bytes;
- full integrity model;
- project tables, I/O, communications and expansion configuration.

## Guarded CLI

    python FATEK/WinProLadder/pdw_tools/analyze.py write-minimal template.pdw output.pdw --x 1 --y 0
    python FATEK/WinProLadder/pdw_tools/analyze.py write-minimal template.pdw output.pdw --x 0 --y 0 --nc

Rules:

- source and output must differ;
- writer refuses complex templates;
- output is verified by decoding after write;
- X/Y > 1 require `--allow-unconfirmed-index` until experimentally validated;
- source PDW is never overwritten.

## Next writer gate

Validate index 2:

    X2 -> Y0  expected words 0x0240 0x00C1  checksum 0x0300
    X0 -> Y2  expected words 0x0040 0x02C1  checksum 0x0300

If both open and pass Syntax Check, the high-byte device-index rule is confirmed beyond the original 0/1 corpus.
