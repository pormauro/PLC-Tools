# Timer / Counter reverse engineering

Status: **T0/C0, time-base selection, PV byte order and counter input operands confirmed. T/C index field candidate isolated.**

## Correction from `todooo.pdw`

The combined validation fixture disproved two earlier interpretations:

- `0x81FD` is **not T1**. With the same timer reference it displays T0 with **0.1S** time base.
- `0x41FD` / `0x42FD` are **not C1/C2**. WinProLadder displays them as function instructions FUN87 T.01S and FUN88 T.1S.

The official FATEK instruction table identifies:

- FUN87 = T.01S, 0.01 s accumulative timer;
- FUN88 = T.1S, 0.1 s accumulative timer;
- FUN89 = T1S, 1 s accumulative timer.

This matches the screenshots exactly for 0x41FD and 0x42FD.

## General timer block

Confirmed T0 examples:

    T0 .01S PV10:
    1B48 80FD 0A00 9003 FC6F 19C8

    T0 .01S PV25:
    1B48 80FD 1900 9003 FC6F 19C8

    T0 .1S PV25:
    1B48 81FD 1900 9003 FC6F 19C8

Interpretation:

- `1B48` = ORG M11;
- `80FD` = general timer, 0.01 s base, confirmed;
- `81FD` = general timer, 0.1 s base, confirmed;
- `9003` is unchanged while display remains T0, therefore it is the leading candidate for the T-device reference;
- `FC6F` remains structural/terminator-like;
- `19C8` = OUT M9.

Candidate, not yet confirmed:

    82FD = general timer, 1 s base

## General counter block

Confirmed C0:

    C0 PV100:
    1C48 1D68 40F9 6400 9005 FC6F 1AC8

    C0 PV25:
    1C48 1D68 40F9 1900 9005 FC6F 1AC8

Counter input mutation tests:

    1E48 1D68 ... -> top PLS/CUP input M14, lower CLR remains M13
    1C48 1F68 ... -> top input remains M12, lower CLR input M15

Therefore:

- top contact device encoding follows the known M contact rule;
- second input uses low byte `0x68` with the same M index base;
- `40F9` is part of the normal counter instruction form for C0;
- `9005` is unchanged while display remains C0, making it the leading candidate for the C-device reference.

## Preset encoding — CONFIRMED BYTE ORDER

Raw code bytes store the numeric preset high byte first:

| Value | raw bytes in code | little-endian diagnostic word |
|---:|---|---:|
| 10 | 00 0A | 0x0A00 |
| 25 | 00 19 | 0x1900 |
| 100 | 00 64 | 0x6400 |
| 300 | 01 2C | 0x2C01 |

The failed PV300 probe wrote `2C 01`; WinProLadder displayed **11265 = 0x2C01**. This directly proves the byte order.

Do not describe the preset as a little-endian immediate.

## Accumulative timer function forms found accidentally

The invalid C-index probes were useful semantic oracles:

    41FD ... -> FUN87 T.01S
    42FD ... -> FUN88 T.1S

These are function instructions, not C1/C2.

The bad T50 probe produced:

    B2F5 ... -> FUN43 NBM

That probe is rejected as a timer-index encoding.

## T/C index field candidate

Because changing `80FD -> 81FD` changes only the timer base while the displayed device stays T0, the T index is not encoded there.

The stable T0 block contains:

    9003

Likewise, the stable C0 block contains:

    9005

The LDR probes that changed `9003 -> 9103` and `9005 -> 9105` did **not** change the displayed devices. After saving `todo v2.pdw`, WinProLadder canonicalized them back to `9003` and `9005` while still displaying T0/C0.

Therefore these words are **not yet proven T/C index fields**, and that hypothesis is rejected for the LDR path.

A direct-PDW probe has now been prepared to bypass possible LDR-envelope normalization:

    C candidate: 40F9 ... 9105 ...
    T candidate: 80FD ... 9103 ...

This will determine whether the importer normalized a valid raw program form or whether the fields truly do not encode the device index.

## Current evidence levels

Confirmed:

- general timer .01S = 80FD for the observed block;
- general timer .1S = 81FD;
- C0 normal counter block uses 40F9;
- PV raw byte order;
- M14 top counter input;
- M15 CLR input;
- 41FD = FUN87 T.01S;
- 42FD = FUN88 T.1S;
- B2F5 is not the T50 form and is displayed as FUN43 NBM.

Pending:

- T index field;
- C index field;
- 1S general timer opcode;
- T50/C1/C2 once index encoding is proven;
- 16/32-bit counter families.


## todo v2 — failed import behavior

The user imported the 1S timer LDR probe twice. Each attempt shifted all existing networks down by one position but no visible instruction was inserted.

The saved PDW begins:

    EB5F
    EB5F
    [valid C0 PV300]
    [valid T0 .01S PV300]
    [valid C0 PV25]
    [valid T0 .01S PV25]

The two leading `0xEB5F` words correspond one-for-one with the two visibly blank N000/N001 networks.

Within this corpus:

    0xEB5F = empty network marker / empty-network sequential form

The exact reason the 1S LDR import collapses to an empty network is still open. A direct-PDW `82FD` probe is prepared to separate LDR-import behavior from raw PDW semantics.

The same project produced Syntax Check: 1 error, 7 warnings. Which specific networks account for those diagnostics has not yet been isolated.
