from pathlib import Path

from common.decode_output import decode_destination, free_path, safe_filename


def test_recovered_names_cannot_leave_the_output_folder() -> None:
    assert safe_filename("../../etc/passwd") == "passwd"
    assert safe_filename("..\\secret.txt") == "secret.txt"
    assert safe_filename("..") == "recovered.bin"


def test_existing_output_is_kept_unless_forced(tmp_path: Path) -> None:
    (tmp_path / "report.pdf").write_bytes(b"old")
    assert decode_destination(tmp_path, "report.pdf", force=False) == tmp_path / "report (1).pdf"
    assert decode_destination(tmp_path, "report.pdf", force=True) == tmp_path / "report.pdf"


def test_free_path_counts_past_taken_names(tmp_path: Path) -> None:
    for name in ("a.txt", "a (1).txt"):
        (tmp_path / name).write_text("x")
    assert free_path(tmp_path / "a.txt") == tmp_path / "a (2).txt"
