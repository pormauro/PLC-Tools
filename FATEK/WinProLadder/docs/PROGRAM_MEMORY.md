# Candidate program-memory image

Status: **strong empirical identification; minimal instruction words confirmed. Not yet a writer contract.**

## Exact size match

The first structural group begins at PDW offset `0x120` and consists of exactly 32 records of 1,280 bytes:

    32 * 1280 = 40960 bytes
    40960 / 2 = 20480 16-bit words
    20480 words = 20K words

FATEK documents the FBs control-program capacity as 20K Words. The size match is exact.

## Erased-record recovery

Records 1..31 are byte-identical inside every current fixture.

Assuming one repeated record represents 1,280 erased bytes filled with `0xFF`:

    key = encrypted_blank_record XOR FF...
    recovered_record = encrypted_record XOR key

the first 32 records recover coherently.

Observed in all fixtures:

- ASCII `FBS40003` near the beginning;
- marker `55 AA` at relative offset `0x01FE`;
- records 1..31 recover exactly to 0xFF;
- program code starts at relative byte offset `0x0202`, word 257.

## Re-save stability

Two independent semantic pairs were tested:

- VACIO.pdw vs VACIO-2.pdw;
- X0-Y0.pdw vs X0-Y0-2.pdw.

In both pairs the raw PDW changes in tens of thousands of bytes, but the recovered 40.960-byte image differs only at relative bytes 0x0000..0x0001.

Therefore:

- the recovery is stable across saves;
- bytes 0..1 are save-variant state;
- byte 2 onward is stable for identical program semantics in the current corpus.

The tool therefore exposes both:

- raw recovered SHA-256;
- semantic SHA-256 with the first recovered word normalized.

## Minimal ladder words — CONFIRMED

| Ladder | Word 257 | Word 258 |
|---|---:|---:|
| X0 NO -> Y0 | 0x0040 | 0x00C1 |
| X1 NO -> Y0 | 0x0140 | 0x00C1 |
| X0 NO -> Y1 | 0x0040 | 0x01C1 |
| X0 NC -> Y0 | 0x0050 | 0x00C1 |
| X0 NC -> Y1 | 0x0050 | 0x01C1 |

For the observed cases:

    word = (device_index << 8) | opcode

Confirmed low-byte opcodes:

- 0x40: ORG Xn, confirmed for X0/X1;
- 0x50: ORG NOT Xn, confirmed for X0;
- 0xC1: OUT Yn, confirmed for Y0/Y1.

The LDR export of NC X0 -> Y0 contains literally `50 00 C1 00`, independently confirming the same words and order.

## Metadata that changes with a minimal two-word rung

After normalizing the two save-variable bytes, only 13 bytes in the first 1.280-byte active record vary across the current semantic fixtures.

### Relative 0x00CA..0x00CD

| Fixture | bytes |
|---|---|
| VACIO | 23 00 FF FF |
| X0-Y0 | 2B FF 00 01 |
| X1-Y0 | 2B FF 00 02 |
| X0-Y1 | 2B FF 00 02 |
| NC-X0-Y0 | 2B FF 10 01 |
| NC-X0-Y1 | 2B FF 10 02 |

Observations only, not yet contract:

- 0x00CA changes with empty vs non-empty program;
- 0x00CC distinguishes NO (00) vs NC (10) in these fixtures;
- 0x00CD changes with the observed operand indices.

### Relative control bytes

| Offset | VACIO | all current two-word rungs |
|---:|---:|---:|
| 0x0103 | 01 | 00 |
| 0x0108 | 00 | 02 |
| 0x010A | FF | FD |
| 0x010E | 02 | 06 |
| 0x0110 | 02 | 06 |

The symmetry strongly suggests count/length/index fields, but their exact semantics require programs with 1, 3+ words and multiple networks.

### Relative code area

| Offset | Meaning |
|---:|---|
| 0x01FE | marker 55 AA |
| 0x0200..0x0201 | 00 FF in current fixtures |
| 0x0202 | first sequential word |
| 0x0204 | second sequential word |
| following | FF until more code exists |

## Experimental extraction

    python FATEK/WinProLadder/pdw_tools/analyze.py recover-program X0-Y0.pdw
    python FATEK/WinProLadder/pdw_tools/analyze.py recover-program X0-Y0.pdw --output program_candidate.bin

The source PDW is never modified.

## Writer gate

Before a PDW writer:

1. validate device-index encoding beyond 0/1;
2. map AND/OR/SET/RST/timer/counter;
3. map variable-length instructions;
4. prove control/count fields with different program lengths;
5. understand save-variant/integrity fields;
6. test multiple networks;
7. reconstruct a copy and open it successfully in WinProLadder;
8. verify semantic round-trip and project configuration preservation.
