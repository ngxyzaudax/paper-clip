import pytest

from common.device_error import DeviceError
from common.ipp_codec import (
    attr_bool,
    attr_integer,
    attr_resolution,
    attr_text,
    begin_collection,
    end_collection,
    group,
    member,
    pack_message,
    unpack_message,
)


def test_device_error_is_a_runtime_error() -> None:
    error = DeviceError("printer refused the ticket")
    assert isinstance(error, RuntimeError)
    assert str(error) == "printer refused the ticket"


def test_scalars_collections_and_unsupported_round_trip() -> None:
    body = b"".join((
        group(0x01),
        attr_text(0x47, "attributes-charset", "utf-8"),
        attr_bool("ipp-attribute-fidelity", True),
        attr_integer(0x23, "print-quality", 5),
        attr_resolution("printer-resolution", 360, 360),
        group(0x02),
        begin_collection("media-col"),
        member("media-size"),
        begin_collection(""),
        member("x-dimension"),
        attr_integer(0x21, "", 21000),
        member("y-dimension"),
        attr_integer(0x21, "", 29700),
        end_collection(),
        end_collection(),
        group(0x05),
        attr_text(0x44, "print-scaling", "fit"),
    ))
    message = unpack_message(pack_message(0x0001, 9, body))
    assert message.status == 0x0001
    assert message.request_id == 9
    assert message.attributes["ipp-attribute-fidelity"] == [True]
    assert message.attributes["print-quality"] == [5]
    assert message.attributes["printer-resolution"] == [(360, 360, 3)]
    size = message.attributes["media-col"][0]["media-size"][0]
    assert size["x-dimension"] == [21000]
    assert size["y-dimension"] == [29700]
    assert message.unsupported == ("print-scaling",)


def test_short_payload_is_rejected() -> None:
    with pytest.raises(ValueError, match="too short"):
        unpack_message(b"\x02\x00")
