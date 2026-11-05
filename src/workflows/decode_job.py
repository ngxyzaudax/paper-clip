from pathlib import Path
from typing import NamedTuple

from common.decode_output import job_destination, write_recovered
from health.check import HealthCheck, run_check
from serialization.decode.decode_passes import OnDecodeProgress


class DecodeOutcome(NamedTuple):
    check: HealthCheck
    path: Path | None


def decode_source(
    source: Path,
    label: str,
    passphrase: str | None,
    track: bool,
    save: bool,
    on_page: OnDecodeProgress | None = None,
) -> DecodeOutcome:
    check = run_check(source, passphrase, track=track, on_page=on_page)
    if not save or check.decoded is None:
        return DecodeOutcome(check, None)
    target = write_recovered(job_destination(label, check.decoded.filename), check.decoded.raw)
    return DecodeOutcome(check, target)
