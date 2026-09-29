# Timer + Counter round-trip

Status: LDR parameter mutation -> WinProLadder -> PDW semantic round-trip confirmed.

## LDR parameter mutation

From varios.ldr two isolated resources were used.

Timer original:

    T0
    base .01S
    PV 10

Code:

    1B48 80FD 0A00 9003 FC6F 19C8

Changing only the PV word to:

    1900

was imported by WinProLadder as PV 25.

Counter original:

    C0
    PV 100

Code:

    1C48 1D68 40F9 6400 9005 FC6F 1AC8

Changing only the PV word to:

    1900

was imported as PV 25.

Observed immediate values:

    10  -> 0x0A00
    25  -> 0x1900
    100 -> 0x6400

This proves the field for these values. Larger values still require a controlled test.

## PDW saved after import

File:

    timer + counter.pdw
    SHA-256 7d02f3902aebae236a41ae0cde16264592af4cd75af62478666522e7a8662c0a

Recovered stream:

    COUNTER
    1C48 1D68 40F9 1900 9005 FC6F 1AC8

    TIMER
    1B48 80FD 1900 9003 FC6F 19C8

Total:

    13 words

Metadata:

    count      0x000D
    complement 0x4EF2
    end        0x021C
    checksum   0x9663
    byte 0xCA  0x57

All fields match the general program formulas.

## Independent reconstruction

A new PDW was generated from the old X0-Y0.pdw template, without copying the supplied timer+counter PDW.

Only the 13 target words and the confirmed metadata formulas were used.

Derived file:

    TEST-GENERATED-TIMER-COUNTER.pdw
    SHA-256 3b78597411f749a1d29d976183919d28c4c2503086f6641b683d48d6247c44cd

After decoding:

    synthetic_program_image[2:]
        ==
    WinProLadder_saved_timer_counter_program_image[2:]

for the entire 40,960-byte recovered program image.

This is exact byte-for-byte equality.

## Pending external gate

Open TEST-GENERATED-TIMER-COUNTER.pdw in WinProLadder and verify:

- both networks are reconstructed correctly;
- timer PV=25;
- counter PV=25;
- Syntax Check passes.

If that passes, the short sequential template-preserving writer is externally validated for a real two-network function program.
