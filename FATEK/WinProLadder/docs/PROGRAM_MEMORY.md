# Candidate program-memory image

Status: **strong empirical hypothesis**, not yet a writer contract.

## Exact size match

The first structural group begins at PDW offset `0x120` and consists of exactly
32 records of 1,280 bytes:

    32 * 1280 = 40960 bytes
    40960 / 2 = 20480 16-bit words
    20480 words = 20K words

FATEK documents the FBs control-program capacity as **20K Words**. This exact
size match, combined with the controlled fixture behavior below, strongly
identifies this first group as the serialized program-memory image.

## Erased-record experiment

Records 1..31 are byte-identical inside each fixture. Assume one such record is
the encrypted/obfuscated representation of 1,280 erased bytes, each `0xFF`.

Then:

    key = encrypted_blank_record XOR FF...
    plaintext_record = encrypted_record XOR key

Applying that to all 32 records produces a coherent candidate image.

Evidence recovered in BOTH fixtures:

- ASCII `FBS40003` at relative byte offset `0x0002`.
- marker `55 AA` at relative byte offset `0x01FE`.
- records 1..31 recover to pure `0xFF`.

This makes the 0xFF premise substantially stronger than a visual guess.

## Minimal ladder delta

In `VACIO.pdw`, from word 257 onward the candidate program area is erased
(`0xFFFF`).

In `X0-Y0.pdw` two additional 16-bit little-endian words appear:

| Word | Relative byte offset | Value |
|---:|---:|---:|
| 257 | 0x0202 | 0x0040 |
| 258 | 0x0204 | 0x00C1 |

The known ladder contains exactly two mnemonic instructions:

    ORG X0
    OUT Y0

Therefore `0x0040` and `0x00C1` are the first machine-word candidates for
those two instructions. **The mapping is not labelled as confirmed yet.**

To prove the mapping, compare:

- X1 -> Y0
- X0 -> Y1
- NOT X0 -> Y0

If only the expected bits/word fields move, instruction and operand encoding can
be derived algebraically.

## Experimental extraction

    python FATEK/WinProLadder/pdw_tools/analyze.py recover-program X0-Y0.pdw
    python FATEK/WinProLadder/pdw_tools/analyze.py recover-program X0-Y0.pdw --output program_candidate.bin

The source PDW is never modified.

## Writer gate

No PDW writer may depend on this hypothesis until:

1. operand encoding is proven with controlled fixtures;
2. instruction-type encoding is proven;
3. length/checksum/index fields are mapped;
4. the same decoder works on independently saved projects;
5. reconstructed files open and validate in WinProLadder;
6. round-trip preserves ladder and project configuration semantically.
