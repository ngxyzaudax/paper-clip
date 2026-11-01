from calibration.sheet_limits import AxisLimit, ChosenProfile

_PASSED_WIDTH = 40


def format_limits(axes: tuple[AxisLimit, ...], chosen: ChosenProfile) -> str:
    lines = [f"{'Aspect':<13} {'Chosen':<8} {'Passed':<{_PASSED_WIDTH}} Failed"]
    lines += [_axis_line(axis) for axis in axes]
    lines.append(
        f"A4 one side   {chosen.bytes_per_side:,} bytes at {chosen.cell_size_px} px, "
        f"{chosen.num_symbols} symbols, {chosen.tag_size_mm:g} mm tags, "
        f"pitch {chosen.tag_pitch_mm:g} mm, QR {chosen.qr_module_mm:g} mm, dot {chosen.dot_ratio:g}"
    )
    return "\n".join(lines)


def _axis_line(axis: AxisLimit) -> str:
    passed = ", ".join(axis.passed) or "-"
    return f"{axis.name:<13} {axis.chosen:<8} {passed:<{_PASSED_WIDTH}} {', '.join(axis.failed) or '-'}"
