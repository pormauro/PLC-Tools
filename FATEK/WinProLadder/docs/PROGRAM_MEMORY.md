# Candidate program-memory image

Status: **strong empirical identification; real WinProLadder write/open/check passed.**

## Exact size match

The first structural group begins at PDW offset `0x120` and consists of exactly 32 records of 1,280 bytes:

    32 * 1280 = 40960 bytes
    40960 / 2 = 20480 16-bit words
    20480 words = 20K words

The recovered image consistently contains `FBS40003`, marker `55 AA` at 0x01FE and erased 0xFF program space.

Program code begins at:

    byte 0x0202
    word 257

## Re-save stability

For both VACIO and X0->Y0 re-saves, the recovered 40,960-byte image differs only at bytes 0x0000..0x0001.

Those two bytes are treated as save-state/transform state, not ladder semantics.

## Program metadata — CONFIRMED

The `varios` fixture expands the program from 0/2 words to **36 words**, allowing several fields to be identified algebraically.

Let:

    n = number of sequential code words
    code = words starting at word 257

### Word count

Relative offset:

    0x0108 = n

Observed:

    VACIO       n=0   -> 0x0000
    minimal     n=2   -> 0x0002
    varios      n=36  -> 0x0024

### Count complement

Relative offset:

    0x010A = 0x4EFF - n

Observed:

    n=0   -> 0x4EFF
    n=2   -> 0x4EFD
    n=36  -> 0x4EDB

### Code end pointers

Relative offsets 0x010E and 0x0110 are identical:

    code_end = 0x0202 + 2*n

Observed:

    n=0   -> 0x0202
    n=2   -> 0x0206
    n=36  -> 0x024A

### Additive code checksum

Relative offset:

    0x00CC = (sum(code_words) - 1) & 0xFFFF

This now matches all current source fixtures, including the 36-word `varios.pdw`.

For `varios`:

    sum(words) - 1 = 0x4A57
    stored         = 0x4A57

For VACIO, an empty sum gives:

    -1 & 0xFFFF = 0xFFFF

which is exactly the stored value.

### Length-derived byte

Relative byte 0x00CA matches all current lengths:

    byte_0xCA = (0x23 + 4*n) & 0xFF

Observed:

    n=0   -> 0x23
    n=2   -> 0x2B
    n=36  -> 0xB3

Byte 0x00CB remains unresolved and must not yet be synthesized generically.

## Multiple networks

`varios.pdw` contains 8 networks and 36 sequential words.

Its recovered code area is the exact concatenation of the 8 `varios.ldr` network code payloads in ladder order N000 -> N007.

The previously identified second structural group still differs only in the same 8 save-state bytes, even between VACIO and this 8-network project.

Therefore no separate network-boundary table has yet been observed there.

## Writer status

The template-preserving writer has passed WinProLadder open + Syntax Check for:

- X0 -> Y0 transformed to X1 -> Y0;
- X2 -> Y0;
- X0 -> Y2.

The high-byte X/Y index rule is therefore confirmed for indices 0, 1 and 2.

## Still required before arbitrary PDW generation

- identify bytes 0x00CB and 0x0103;
- validate metadata at additional lengths/network counts;
- understand expansion beyond the first 1,280-byte active record;
- map more operand families;
- map variable-length function encodings;
- validate generated multi-network streams;
- preserve all non-program project resources.
