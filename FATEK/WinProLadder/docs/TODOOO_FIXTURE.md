# Fixture `todooo.pdw` — validation of good and bad probes

SHA-256:

    8c47cc0a83cc393ca48837abb4e928d8af275168c31c4d582c07f8edbd9525d7

Size: 98,871 bytes.

This project contains the previously generated two-network PDW plus the six imported LDR probes.

## PDW metadata

Recovered code:

    n = 53 words
    checksum = 0x4551
    complement = 0x4ECA
    code end = 0x026C
    byte 0xCA = 0xF7

All previously derived metadata formulas still match:

    checksum = (sum(code_words) - 1) & 0xFFFF
    complement = 0x4EFF - n
    code_end = 0x0202 + 2*n
    byte_0xCA = (0x23 + 4*n) & 0xFF

## Networks and visual interpretation

### N000

    1C48 1D68 41FD 1900 9005 FC6F 1AC8

WinProLadder shows FUN87 `T.01S`, CV=C0, PV=25, with M12/M13 inputs and M10 output.

Conclusion:

    41FD != C1
    41FD = FUN87 T.01S in this context

### N001

    1B48 81FD 1900 9003 FC6F 19C8

WinProLadder shows general timer:

    .1S
    T0
    25

Conclusion:

    81FD != T1
    81FD selects .1S timer base while T device remains T0

### N002

    1B48 B2F5 1900 9003 FC6F 19C8

WinProLadder shows FUN43 NBM rather than a timer.

Conclusion: the former T50 guess is rejected.

### N003

    1B48 81FD 012C 9003 FC6F 19C8

WinProLadder shows T0 .1S with value **11265**.

Raw bytes for the attempted preset are:

    2C 01

and:

    0x2C01 = 11265

This proves the preset field uses raw bytes `01 2C` for decimal 300.

### N004

    1C48 1D68 42FD 1900 9005 FC6F 1AC8

WinProLadder shows FUN88 `T.1S`, CV=C0, PV=25.

Conclusion:

    42FD != C2
    42FD = FUN88 T.1S in this context

### N005

    1C48 1D68 41FD 012C 9005 FC6F 1AC8

WinProLadder shows FUN87 T.01S with PV=11265, confirming both the function interpretation and preset byte order.

### N006

    1E48 1D68 40F9 1900 9005 FC6F 1AC8

WinProLadder shows:

- top input M14;
- lower CLR M13;
- C0 PV25;
- output M10.

The M12 -> M14 probe passed.

### N007

    1C48 1F68 40F9 1900 9005 FC6F 1AC8

WinProLadder shows:

- top input M12;
- lower CLR M15;
- C0 PV25;
- output M10.

The M13 -> M15 CLR probe passed.

## Main result

This fixture is intentionally valuable because it contains both successful and failed hypotheses. It prevents the reverse-engineering documentation from overfitting importer acceptance.

The next isolated probes move T/C index in the stable words `9003` / `9005`, not in the timer-base/counter-opcode words.
