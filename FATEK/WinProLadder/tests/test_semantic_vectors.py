#!/usr/bin/env python3
"""Regression vectors from controlled WinProLadder fixtures."""

from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "ldr_tools" / "analyze.py"
spec = importlib.util.spec_from_file_location("fatek_ldr_analyze", MOD)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

assert module.be_value_from_diagnostic_word(0x0A00) == 10
assert module.be_value_from_diagnostic_word(0x1900) == 25
assert module.be_value_from_diagnostic_word(0x6400) == 100
assert module.be_value_from_diagnostic_word(0x2C01) == 300
assert module.be_value_from_diagnostic_word(0x012C) == 11265

timer, consumed = module.decode_timer_counter_block(
    [0x80FD, 0x1900, 0x9003, 0xFC6F], 0
)
assert consumed == 4
assert timer["kind"] == "general_timer"
assert timer["time_base"] == ".01S"
assert timer["pv"] == 25
assert timer["timer_index_candidate"] == 0
assert timer["timer_ref_evidence"] == "T0 visual-confirmed"

timer_01, _ = module.decode_timer_counter_block(
    [0x81FD, 0x1900, 0x9003, 0xFC6F], 0
)
assert timer_01["time_base"] == ".1S"
assert timer_01["timer_index_candidate"] == 0

counter, consumed = module.decode_timer_counter_block(
    [0x40F9, 0x6400, 0x9005, 0xFC6F], 0
)
assert consumed == 4
assert counter["kind"] == "general_counter"
assert counter["pv"] == 100
assert counter["counter_index_candidate"] == 0
assert counter["counter_ref_evidence"] == "C0 visual-confirmed"

assert module.decode_word(0x41FD)["text"] == "FUN87 T.01S"
assert module.decode_word(0x42FD)["text"] == "FUN88 T.1S"
assert module.decode_word(0xB2F5)["text"] == "FUN43 NBM"

print("FATEK semantic regression vectors: PASS")
