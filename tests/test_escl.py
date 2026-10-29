from common.escl_caps import SCAN, PWG, choose_dpi, parse_capabilities, scan_settings
from common.escl_scan import _submit_job, scan_jpeg


def test_capabilities_and_settings_request_color_jpeg() -> None:
    caps = parse_capabilities(_CAPS.encode())
    assert caps.max_width == 2550
    assert caps.max_height == 3510
    assert caps.resolutions == (100, 1200)
    assert caps.color_modes == ("RGB24",)
    assert caps.formats == ("image/jpeg",)
    assert caps.source == "Platen"
    assert choose_dpi(caps.resolutions, 150) == 100
    settings = scan_settings(caps, 1200).decode()
    assert "<pwg:ColorMode>RGB24</pwg:ColorMode>" in settings
    assert "<scan:XResolution>1200</scan:XResolution>" in settings
    assert "<pwg:DocumentFormat>image/jpeg</pwg:DocumentFormat>" in settings
    assert "<pwg:Width>2550</pwg:Width>" in settings
    assert "<pwg:InputSource>Platen</pwg:InputSource>" in settings


def test_submit_job_retries_while_the_scanner_is_busy(monkeypatch) -> None:
    calls: list[int] = []

    def fake_request(
        uri: str,
        method: str,
        path: str,
        body: bytes | None = None,
        timeout: float = 60,
        content_type: str = "",
    ) -> tuple[int, str, bytes]:
        calls.append(1)
        if len(calls) < 3:
            return 503, "", b"busy"
        return 201, "/eSCL/ScanJobs/1", b""

    monkeypatch.setattr("common.escl_scan.request_escl", fake_request)
    monkeypatch.setattr("common.escl_scan.time.sleep", lambda _seconds: None)
    status, location, _payload = _submit_job("https://scanner.local", b"<settings/>")
    assert (status, location) == (201, "/eSCL/ScanJobs/1")
    assert len(calls) == 3


def test_scan_jpeg_reads_the_document_and_deletes_the_job(monkeypatch) -> None:
    jpeg = b"\xff\xd8\xff\xd9"
    calls: list[tuple[str, str]] = []

    def fake_request(
        uri: str,
        method: str,
        path: str,
        body: bytes | None = None,
        timeout: float = 60,
        content_type: str = "",
    ) -> tuple[int, str, bytes]:
        calls.append((method, path))
        if path.endswith("ScannerCapabilities"):
            return 200, "", _CAPS.encode()
        if method == "POST":
            return 201, "/eSCL/ScanJobs/9", b""
        if path.endswith("NextDocument"):
            return 200, "", jpeg
        return 200, "", b""

    monkeypatch.setattr("common.escl_scan.request_escl", fake_request)
    monkeypatch.setattr("common.escl_scan.time.sleep", lambda _seconds: None)
    payload, dpi = scan_jpeg("https://scanner.local", 1200, timeout=5)
    assert payload == jpeg
    assert dpi == 1200
    assert ("DELETE", "/eSCL/ScanJobs/9") in calls


_CAPS = f"""<?xml version="1.0" encoding="UTF-8"?>
<scan:ScannerCapabilities xmlns:scan="{SCAN}" xmlns:pwg="{PWG}">
  <pwg:MakeAndModel>EPSON ET-8500 Series</pwg:MakeAndModel>
  <scan:Platen>
    <scan:PlatenInputCaps>
      <scan:MaxWidth>2550</scan:MaxWidth>
      <scan:MaxHeight>3510</scan:MaxHeight>
      <scan:SettingProfiles>
        <scan:SettingProfile>
          <scan:ColorModes><scan:ColorMode>RGB24</scan:ColorMode></scan:ColorModes>
          <scan:DocumentFormats><pwg:DocumentFormat>image/jpeg</pwg:DocumentFormat></scan:DocumentFormats>
          <scan:SupportedResolutions>
            <scan:DiscreteResolutions>
              <scan:DiscreteResolution>
                <scan:XResolution>100</scan:XResolution>
                <scan:YResolution>100</scan:YResolution>
              </scan:DiscreteResolution>
              <scan:DiscreteResolution>
                <scan:XResolution>1200</scan:XResolution>
                <scan:YResolution>1200</scan:YResolution>
              </scan:DiscreteResolution>
            </scan:DiscreteResolutions>
          </scan:SupportedResolutions>
        </scan:SettingProfile>
      </scan:SettingProfiles>
    </scan:PlatenInputCaps>
  </scan:Platen>
</scan:ScannerCapabilities>
"""
