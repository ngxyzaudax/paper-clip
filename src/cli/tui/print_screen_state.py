from cli.tui.print_jobs import PrintJob


def find_job(jobs: list[PrintJob], job_id: str | None) -> PrintJob | None:
    return next((job for job in jobs if job.job_id == job_id), None)


def preferred_job(options: list[tuple[str, str]], wanted: str | None, fallback: str | None) -> str | None:
    """The job a handoff asked for when it exists, otherwise the newest job."""
    if wanted and any(job_id == wanted for _, job_id in options):
        return wanted
    return fallback


def print_confirm_body(job: PrintJob, printer: str, duplex: bool) -> str:
    sheets = (len(job.page_paths) + 1) // 2 if duplex else len(job.page_paths)
    sides = "both sides" if duplex else "one side"
    return (
        f"Printer: {printer}\n"
        f"Job: {job.job_id} ({job.source_file or 'unknown source'})\n"
        f"Pages: {len(job.page_paths)} on {sides}, about {sheets} sheet(s) of {job.paper_size or 'A4'}.\n\n"
        "The job is submitted once. If it fails, check the printer before printing again."
    )
