from pathlib import Path

from gxw_tools.comments import DeviceComment, parse_comment_qcd, serialize_comment_qcd
from gxw_tools.project import GXWProject


def test_estampadora_comment_roundtrip():
    path = Path(__file__).with_name("estampadora.gxw")
    if not path.exists():
        return
    p = GXWProject(path)
    raw = p.logical_bytes("COMMENT.qcd")
    table = parse_comment_qcd(raw)
    assert len(table.comments) == 133
    assert len(table.ranges) == 17
    assert serialize_comment_qcd(table, template=raw) == raw
    assert table.comments[0] == DeviceComment("X0", "B1")
    assert DeviceComment("T230", "REF_P2_UP") in table.comments
    assert DeviceComment("D0", "STATE") in table.comments


def test_variable_length_comment_project_write():
    path = Path(__file__).with_name("estampadora.gxw")
    if not path.exists():
        return
    p = GXWProject(path)
    comments = p.device_comments()
    comments[0] = DeviceComment("X0", "B1_TEST_LONG")
    out = GXWProject(p.replace_device_comments(comments))
    assert out.validate()["ok"]
    assert out.device_comments()[0] == DeviceComment("X0", "B1_TEST_LONG")
    for name in p.by_name:
        if name != "COMMENT.qcd":
            assert out.logical_bytes(name) == p.logical_bytes(name)
