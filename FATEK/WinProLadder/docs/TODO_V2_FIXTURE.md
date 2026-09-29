# Fixture `todo v2.pdw` — empty-network marker and LDR normalization

SHA-256:

    9add9b1724c295ffae817cf4ff9e9b20eeb13c25e098ad5d84806e7e39d85e0d

Size: 98,871 bytes.

## Visual state

WinProLadder shows:

- N000 empty
- N001 empty
- N002 C0 PV300
- N003 T0 .01S PV300
- N004 C0 PV25
- N005 T0 .01S PV25

The user reports that the final 1S-timer LDR was imported twice. Each attempt shifted the existing program down one network but inserted no visible instruction.

## Recovered sequential stream

28 words:

    EB5F
    EB5F
    1C48 1D68 40F9 2C01 9005 FC6F 1AC8
    1B48 80FD 2C01 9003 FC6F 19C8
    1C48 1D68 40F9 1900 9005 FC6F 1AC8
    1B48 80FD 1900 9003 FC6F 19C8

The two leading `EB5F` words align exactly with the two blank visible networks.

## Empty network token

Current confirmed interpretation:

    0xEB5F = empty network

This is the first explicit PDW sequential token tied directly to an empty network.

## Metadata

    n = 28
    checksum = 0x2987
    complement = 0x4EE3
    code end = 0x023A
    byte 0xCA = 0x93

All existing formulas match.

## T/C index LDR probes

The attempted LDR mutations:

    9003 -> 9103
    9005 -> 9105

did not change the displayed devices. WinProLadder displays T0/C0 and the saved PDW contains canonical `9003` / `9005` again.

This rejects those mutations as a proven LDR path for T1/C1.

It remains possible that the LDR envelope/trailer causes canonicalization, so direct PDW probes are the next discriminator.

## Diagnostics

The user ran Syntax Check and obtained:

    Error Count: 1
    Warning Count: 7

The exact diagnostic-to-network mapping has not yet been isolated; no cause is asserted from the count alone.
