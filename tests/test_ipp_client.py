import pytest

from common.device_error import DeviceError
from common.ipp_codec import attr_integer, attr_text, group, pack_message
from common.ipp_client import printer_attributes, submit_document, validate_ticket, wait_for_job
from common.ipp_media import MEDIA_SIZES
from common.ipp_options import PrintTicket

_URI = "ipp://printer.example:631/ipp/print"


def test_printer_attributes_returns_the_merged_map(monkeypatch) -> None:
    body = b"".join((
        group(0x01),
        attr_text(0x47, "attributes-charset", "utf-8"),
        group(0x04),
        attr_text(0x44, "print-scaling-supported", "none"),
        attr_text(0x44, "", "fit"),
    ))
    monkeypatch.setattr("common.ipp_client.post_ipp", lambda uri, request, timeout: pack_message(0, 1, body))
    assert printer_attributes(_URI)["print-scaling-supported"] == ["none", "fit"]


def test_exchange_rejects_an_ignored_safety_attribute(monkeypatch) -> None:
    body = b"".join((
        group(0x05),
        attr_text(0x44, "print-scaling", "none"),
    ))
    monkeypatch.setattr("common.ipp_client.post_ipp", lambda uri, request, timeout: pack_message(0, 1, body))
    with pytest.raises(DeviceError, match="print-scaling"):
        validate_ticket(_URI, _ticket())


def test_submit_returns_the_job_id(monkeypatch) -> None:
    body = group(0x02) + attr_integer(0x21, "job-id", 4)
    monkeypatch.setattr("common.ipp_client.post_ipp", lambda uri, request, timeout: pack_message(0, 2, body))
    assert submit_document(_URI, _ticket(), b"pwg", "page") == 4


def test_submit_requires_a_job_id(monkeypatch) -> None:
    monkeypatch.setattr("common.ipp_client.post_ipp", lambda uri, request, timeout: pack_message(0, 2, b""))
    with pytest.raises(DeviceError, match="job id"):
        submit_document(_URI, _ticket(), b"pwg", "page")


def test_wait_for_job_returns_when_the_printer_completes(monkeypatch) -> None:
    states = iter((5, 9))

    def fake_post(uri: str, request: bytes, timeout: float) -> bytes:
        state = next(states)
        body = group(0x02) + attr_integer(0x23, "job-state", state)
        return pack_message(0, 3, body)

    monkeypatch.setattr("common.ipp_client.post_ipp", fake_post)
    monkeypatch.setattr("common.ipp_client.time.sleep", lambda _seconds: None)
    assert wait_for_job(_URI, 4, timeout=5) == "completed"


def test_wait_for_job_fails_when_the_job_is_aborted(monkeypatch) -> None:
    body = group(0x02) + attr_integer(0x23, "job-state", 8)
    monkeypatch.setattr("common.ipp_client.post_ipp", lambda uri, request, timeout: pack_message(0, 3, body))
    with pytest.raises(DeviceError, match="state 8"):
        wait_for_job(_URI, 4, timeout=5)


def test_wait_for_job_times_out(monkeypatch) -> None:
    monkeypatch.setattr("common.ipp_client.time.sleep", lambda _seconds: None)
    monkeypatch.setattr(
        "common.ipp_client.post_ipp",
        lambda uri, request, timeout: (_ for _ in ()).throw(AssertionError("timed-out wait must not query")),
    )
    with pytest.raises(DeviceError, match="did not finish"):
        wait_for_job(_URI, 4, timeout=0)


def _ticket() -> PrintTicket:
    return PrintTicket(
        media=MEDIA_SIZES["A4"],
        source="main",
        margin=300,
        color="color",
        quality=5,
        scaling="none",
        sides="one-sided",
        dpi=360,
        document_format="image/pwg-raster",
    )
