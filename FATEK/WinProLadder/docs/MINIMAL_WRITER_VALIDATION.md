# PDW/LDR writer validation

Status: **real WinProLadder write/open/check and LDR->PDW round-trip gates passed.**

## Minimal PDW gates

### X1

`TEST-X1-Y0-FROM-X0-Y0.pdw`

- opens: PASS
- X1 -> Y0: PASS
- Syntax Check: PASS

### X2 / Y2

`TEST-X2-Y0.pdw` and `TEST-X0-Y2.pdw`

- opens: PASS
- intended ladder: PASS
- check: PASS

X/Y index encoding is externally validated through index 2.

## Minimal LDR gate

`TEST-X0-Y0.ldr`, derived from NC-X0-Y0 by mutating `0x0050 -> 0x0040`:

- WinProLadder import: PASS
- resulting X0 -> Y0: PASS

## Generic short-stream PDW gate — C0/T0

A 13-word program was generated from the unrelated X0-Y0 template:

    Counter C0 PV25
    Timer   T0 PV25

Derived file:

    TEST-GENERATED-TIMER-COUNTER.pdw
    SHA-256 3b78597411f749a1d29d976183919d28c4c2503086f6641b683d48d6247c44cd

User validation:

- opens correctly: PASS
- Counter C0 PV25 visible: PASS
- Timer T0 PV25 visible: PASS
- CUP / CLR / TUP topology visible as intended: PASS

This validates the experimental sequential writer on a multi-network program containing variable-length Timer/Counter blocks.

## LDR -> WinProLadder -> PDW gate — T1/C1

Two standalone probes were imported:

- Timer T1 PV25
- Counter C1 PV25

The combined project was saved as:

    timer + counter 2.pdw
    SHA-256 6930b15b15d5172caebd07da07e198cf232d617be072926e912afded6041d491

Recovered canonical stream:

    1C48 1D68 41FD 1900 9005 FC6F 1AC8
    1B48 81FD 1900 9003 FC6F 19C8

Metadata:

    n          = 13
    checksum   = 0x9867
    complement = 0x4EF2
    code_end   = 0x021C

All documented metadata equations pass.

### Canonicalization discovery

The imported Counter C1 probe contained `0x41F9`.

After WinProLadder saved the project, the PDW contains `0x41FD`.

Therefore the importer accepts at least one non-canonical representation and normalizes it on save.

## Exact synthetic reconstruction

Starting from `X0-Y0.pdw`, the canonical 13-word C1/T1 stream was written using only the documented metadata formulas.

The recovered synthetic image is byte-identical to `timer + counter 2.pdw` from recovered offset 0x0002 through the end of the 20K-word image.

Only the two-byte save-state word differs.

This is strong evidence that the short sequential-program image is now reconstructible independently of the source project semantics.

## CLI

    python FATEK/WinProLadder/pdw_tools/analyze.py write-sequential-experimental       template.pdw output.pdw 0x1C48 0x1D68 0x41FD 0x1900 ...

Current guard: <=55 words while the high part of the length-derived 0xCA/0xCB field remains unmapped.
