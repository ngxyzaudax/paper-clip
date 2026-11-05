from pydantic import BaseModel


class SessionCreate(BaseModel):
    duplex: bool | None = None
    print_job_id: str | None = None


class SessionSetup(BaseModel):
    duplex: bool | None = None
    print_job_id: str | None = None


class DecodeRequest(BaseModel):
    passphrase: str | None = None
    track: bool | None = None
    save: bool | None = None
