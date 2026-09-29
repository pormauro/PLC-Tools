from gxw_tools.audit import analyze_instructions
from gxw_tools.ladder import Instruction


def I(mnemonic, *operands):
    return Instruction(mnemonic, tuple(operands), ())


def test_missing_writer_and_external_whitelist():
    programs = {
        "A": [I("LD", "M70"), I("OUT", "Y5"), I("LD", "M100"), I("OUT", "M10")],
        "B": [I("LD", "X0"), I("PLS", "M11")],
    }
    report = analyze_instructions(programs, external_devices={"M100"})
    assert report["read_without_ladder_writer"] == {"M70": ["A"]}
    assert report["multiple_coil_writers"] == {}
    assert not report["ok"]


def test_multiple_coil_writer():
    programs = {
        "A": [I("OUT", "M10")],
        "B": [I("PLS", "M10")],
    }
    report = analyze_instructions(programs)
    assert report["multiple_coil_writers"] == {"M10": ["A", "B"]}
    assert not report["ok"]


def test_clean():
    programs = {
        "A": [I("LD", "X0"), I("OUT", "M10")],
        "B": [I("LD", "M10"), I("OUT", "Y0")],
    }
    report = analyze_instructions(programs)
    assert report["read_without_ladder_writer"] == {}
    assert report["multiple_coil_writers"] == {}
    assert report["ok"]
