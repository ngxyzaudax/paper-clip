CALIBRATE_CSS = """
CalibrateScreen {
    width: 100%;
    height: 100%;
    padding: 0 1;
}
CalibrateScreen #cal-body {
    height: 1fr;
}
CalibrateScreen #cal-left {
    width: 52;
    padding-right: 1;
}
CalibrateScreen #cal-right {
    width: 1fr;
}
CalibrateScreen .cal-heading {
    text-style: bold;
    color: $accent;
    margin-top: 1;
}
CalibrateScreen #cal-next {
    border: round $warning;
    padding: 0 1;
    height: auto;
}
CalibrateScreen #cal-steps, CalibrateScreen #cal-scans {
    height: auto;
}
CalibrateScreen #cal-table {
    height: auto;
    max-height: 12;
}
CalibrateScreen #cal-summary {
    margin-top: 1;
    height: auto;
}
CalibrateScreen #cal-status-row {
    height: 1;
    margin-top: 1;
}
CalibrateScreen #cal-busy {
    width: 4;
    height: 1;
    display: none;
}
CalibrateScreen #cal-busy.busy {
    display: block;
}
CalibrateScreen #cal-status {
    width: 1fr;
    color: $text-muted;
}
CalibrateScreen #cal-actions {
    height: auto;
    margin-top: 1;
}
CalibrateScreen #cal-actions Button {
    margin-right: 1;
}
"""
