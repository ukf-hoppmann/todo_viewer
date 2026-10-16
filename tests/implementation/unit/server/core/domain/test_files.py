import pytest
from viewer.core.domain.errors import InvalidInput
from viewer.core.domain.files import (
    check_relative_path,
    decode_text,
    encode_text,
    file_version,
    has_merge_markers,
    is_temp_name,
)


def test_version_is_sha256_hex() -> None:
    assert file_version(b"") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_decode_normalizes_to_lf_and_reports_the_dominant_line_ending() -> None:
    assert decode_text(b"a\r\nb\r\n") == ("a\nb\n", "\r\n")
    assert decode_text(b"a\nb\n") == ("a\nb\n", "\n")
    assert decode_text(b"a\r\nb\nc\nd\n") == ("a\nb\nc\nd\n", "\n")  # gemischt: die Mehrheit gewinnt
    assert decode_text(b"") == ("", "\n")


def test_decode_is_strict_utf8() -> None:
    with pytest.raises(UnicodeDecodeError):
        decode_text(b"\xff\xfe")


def test_encode_follows_the_existing_file() -> None:
    assert encode_text("a\nb\n", None) == b"a\nb\n"
    assert encode_text("a\nb\n", b"x\n") == b"a\nb\n"
    assert encode_text("a\nb\n", b"x\r\ny\r\n") == b"a\r\nb\r\n"
    assert encode_text("a\r\nb\n", b"x\r\n") == b"a\r\nb\r\n"  # schon CRLF im Text wird nicht verdoppelt
    assert encode_text("ä\n", b"\xff") == "ä\n".encode()  # unlesbare Vorlage: LF


def test_merge_markers_need_start_and_end_at_line_start() -> None:
    assert has_merge_markers("a\n<<<<<<< HEAD\nx\n=======\ny\n>>>>>>> b\n")
    assert has_merge_markers("<<<<<<<\n>>>>>>>")
    assert not has_merge_markers("<<<<<<< nur Anfang\n")
    assert not has_merge_markers("  <<<<<<< eingerückt\n  >>>>>>> auch\n")
    assert not has_merge_markers("<<<<<<<<< acht\n>>>>>>>>> acht\n")


def test_temp_names() -> None:
    assert is_temp_name(".TODO.md.ab12cd.tmp")
    assert not is_temp_name("TODO.md") and not is_temp_name("x.tmp")


@pytest.mark.parametrize("path", ["TODO.md", "items/STORY-1/a.md", "notes/ä.md"])
def test_valid_paths(path: str) -> None:
    assert check_relative_path(path) == path


@pytest.mark.parametrize("path", ["", "/a", "../a", "a/../b", "a//b", "./a", "a/.", ".git/x", "a\\b"])
def test_invalid_paths(path: str) -> None:
    with pytest.raises(InvalidInput):
        check_relative_path(path)
