import logging
from collections.abc import Callable

from fastapi import APIRouter, Body, HTTPException

from common.device_error import DeviceError
from web.calibrate_view import calibrate_state
from web.request_models import CalibrateAction
from web.tasks import TaskRecord, submit
from workflows.calibrate_actions import (
    new_session,
    print_once,
    printer_for_sheet,
    render_sheet,
    run_simulation,
    save_profile,
    scan_view,
)

logger = logging.getLogger(__name__)
router = APIRouter()
_CONFIRM = frozenset({"print", "save", "new"})


@router.get("/calibrate")
def calibrate() -> dict[str, object]:
    return calibrate_state()


@router.post("/calibrate/{action}")
def calibrate_action(action: str, body: CalibrateAction | None = Body(default=None)) -> dict[str, str]:
    chosen = _actions().get(action)
    if chosen is None:
        raise HTTPException(404, "Unknown calibration step")
    if action in _CONFIRM and not _confirmed(body):
        raise HTTPException(400, "confirm is required")
    return {"task_id": submit(_task(chosen))}


def _confirmed(body: CalibrateAction | None) -> bool:
    return body is not None and body.confirm is True


def _task(action: Callable[[], str]) -> Callable[[TaskRecord], dict[str, object]]:
    def run(record: TaskRecord) -> dict[str, object]:
        return _message(action, record)
    return run


def _message(action: Callable[[], str], record: TaskRecord) -> dict[str, object]:
    logger.info("Calibration task %s started", record.id)
    return {"message": _invoke(action)}


def _invoke(action: Callable[[], str]) -> str:
    try:
        return action()
    except (DeviceError, OSError, ValueError, RuntimeError) as exc:
        raise ValueError(str(exc)) from exc


def _actions() -> dict[str, Callable[[], str]]:
    return {
        "sheet": render_sheet,
        "simulate": run_simulation,
        "print": _print_sheet,
        "scan": scan_view,
        "save": save_profile,
        "new": new_session,
    }


def _print_sheet() -> str:
    return print_once(printer_for_sheet())
