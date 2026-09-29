# Timer / Counter reverse engineering

Status: **T0/T1, C0/C1 and PV <=100 empirically mapped; next probes prepared.**

## Timer

Observed blocks:

    T0 PV10:  1B48 80FD 0A00 9003 FC6F 19C8
    T0 PV25:  1B48 80FD 1900 9003 FC6F 19C8
    T1 PV25:  1B48 81FD 1900 9003 FC6F 19C8

Stable context:

- `1B48` = ORG M11
- `19C8` = OUT M9
- `9003 FC6F` stayed constant in all current timer probes

Changes:

- T0 -> T1: `80FD -> 81FD`
- PV10 -> PV25: `0A00 -> 1900`

## Counter

Observed blocks:

    C0 PV100: 1C48 1D68 40F9 6400 9005 FC6F 1AC8
    C0 PV25:  1C48 1D68 40F9 1900 9005 FC6F 1AC8
    C1 PV25:  1C48 1D68 41FD 1900 9005 FC6F 1AC8  [canonical PDW]

Stable context:

- `1C48` = top input M12
- `1D68` = lower input M13
- `1AC8` = OUT M10
- `9005 FC6F` constant in current counter fixtures

### Importer normalization

The test LDR changed C0 `40F9` to `41F9`.

WinProLadder accepted the import, but saved the resulting C1 as `41FD`.

Do not encode arbitrary counters by extending the C0 form until C2 is checked.

## PV

Immediate word evidence:

| PV | word |
|---:|---:|
| 10 | 0x000A |
| 25 | 0x0019 |
| 100 | 0x0064 |

Prepared probe PV300 = `0x012C` will test full 16-bit little-endian storage.

## Time base

Official FBs documentation gives the default timer ranges:

- T0..T49: 0.01 s
- T50..T199: 0.1 s
- T200..T255: 1 s

Current binary evidence only covers T0/T1. A T50 probe is prepared to determine whether the time-base display follows timer range implicitly while the rest of the timer block remains unchanged.

## Prepared probes

- T50 PV25
- T1 PV300
- C2 PV25 using canonical-family candidate `0x42FD`
- C1 PV300 using canonical `0x41FD`
- counter top input M12 -> M14
- counter lower CLR input M13 -> M15

These are intentionally one-variable-at-a-time experiments.
