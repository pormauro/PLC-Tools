# Candidate program-memory image

Status: **program image and short-program metadata strongly confirmed; writer remains guarded.**

## Program image

The first structural group is exactly:

    32 * 1280 = 40960 bytes
    40960 / 2 = 20480 words
    20480 words = 20K words

Recovered invariants include:

- `FBS40003`;
- marker `55 AA` at 0x01FE;
- code starts at byte 0x0202 / word 257;
- unused program memory recovers as 0xFF.

## Save-state stability

Independent re-saves of VACIO and X0->Y0 change only recovered bytes 0x0000..0x0001. Byte 2 onward is stable for identical ladder semantics.

## Program metadata — confirmed across 0, 2, 13 and 36 code words

Let:

    n = number of sequential code words
    code = words starting at word 257

### Word count

    u16 @0x0108 = n

Observed:

    n=0   VACIO
    n=2   minimal rung
    n=13  timer + counter
    n=36  varios

### Count complement

    u16 @0x010A = 0x4EFF - n

Examples:

    n=13 -> 0x4EF2
    n=36 -> 0x4EDB

### Code end pointers

Both fields are identical:

    u16 @0x010E
    u16 @0x0110

and:

    code_end = 0x0202 + 2*n

Examples:

    n=13 -> 0x021C
    n=36 -> 0x024A

### Additive code checksum

    u16 @0x00CC = (sum(code_words) - 1) & 0xFFFF

Examples:

    minimal X0->Y0 -> 0x0100
    timer+counter  -> 0x9663
    varios         -> 0x4A57
    empty          -> 0xFFFF

### Length-derived byte

For every observed length:

    byte @0x00CA = (0x23 + 4*n) & 0xFF

Examples:

    n=0  -> 0x23
    n=2  -> 0x2B
    n=13 -> 0x57
    n=36 -> 0xB3

Current observed non-empty fixtures also have:

    byte @0x00CB = 0xFF
    byte @0x0103 = 0x00

Those two values are still treated conservatively because their wider-range behavior is not proven.

## Independent semantic reconstruction — strongest current evidence

Source template:

    X0-Y0.pdw

Target stream, independently produced by WinProLadder in `timer + counter.pdw`:

    1C48 1D68 40F9 1900 9005 FC6F 1AC8
    1B48 80FD 1900 9003 FC6F 19C8

A synthetic recovered program image was constructed from the X0-Y0 template by:

1. erasing code from 0x0202 onward;
2. inserting the 13 target words;
3. setting count=13;
4. setting complement=0x4EF2;
5. setting end=0x021C in both end fields;
6. setting checksum=0x9663;
7. setting byte 0xCA=0x57;
8. preserving the template save-state word.

Result:

    synthetic_image[2:] == WinProLadder_saved_timer_counter_image[2:]

for the entire 40,960-byte recovered program image.

That is exact byte-for-byte equality, not a similarity metric.

## Multiple networks

The 13-word timer+counter PDW contains two sequential function blocks. The 36-word `varios` fixture contains 8 networks.

No changing auxiliary network-boundary table has been found. LDR provides boundaries; PDW stores the resulting sequential stream.

## Writer scope

Validated externally so far:

- X1 -> Y0;
- X2 -> Y0;
- X0 -> Y2.

An experimental short sequential writer is available for <=55 words:

    python FATEK/WinProLadder/pdw_tools/analyze.py \
      write-sequential-experimental template.pdw output.pdw \
      0x1C48 0x1D68 0x40F9 0x1900 0x9005 0xFC6F 0x1AC8 \
      0x1B48 0x80FD 0x1900 0x9003 0xFC6F 0x19C8

The <=55 limit deliberately avoids testing the unresolved wrap behavior of the 0xCA/0xCB length fields.

## Still open

- behavior of 0xCA/0xCB beyond the current range;
- programs crossing larger internal boundaries;
- full grammar needed to infer network boundaries without LDR;
- complete timer/counter parameter encoding;
- arbitrary project generation without a valid PDW template.
