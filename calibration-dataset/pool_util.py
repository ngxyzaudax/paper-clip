import os


def max_cpu_workers() -> int:
    env = os.environ.get("CALIBRATION_MAX_WORKERS")
    if env is not None and env.strip() != "":
        return max(1, int(env))
    try:
        return max(1, len(os.sched_getaffinity(0)))
    except AttributeError:
        return max(1, os.cpu_count() or 1)
