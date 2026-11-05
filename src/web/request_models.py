from pydantic import BaseModel, ConfigDict


class PrintRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    printer: str = ""
    duplex: bool | None = None
    confirm: bool = False


class DeviceSelection(BaseModel):
    model_config = ConfigDict(strict=True)
    printer_uri: str | None = None
    scanner_id: str | None = None


class HealthCheck(BaseModel):
    model_config = ConfigDict(strict=True)
    scan_job_id: str


class CalibrateAction(BaseModel):
    model_config = ConfigDict(strict=True)
    confirm: bool = False
