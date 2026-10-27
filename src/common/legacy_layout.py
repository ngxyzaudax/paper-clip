TIMING_TRACK_WIDTH = 1
DOWNSCALE_MAX_DIM = 4000
APRILTAG_FAMILY = "tag36h11"
LAYOUT_CLEARANCE_DIVISOR = 200
FIDUCIAL_DPI = 300
APRILTAG_MESH_N = 5
APRILTAG_EDGE_CELLS = 9
APRILTAG_36H11_ID_COUNT = 587
QR_MODULE_PX = 12
QR_BORDER_MODULES = 2
QR_VERSION = 5


def layout_clearance_px(print_dpi: int) -> int:
    return max(3, print_dpi // LAYOUT_CLEARANCE_DIVISOR)


def center_sample_half(cell_size_px: int) -> int:
    return max(1, cell_size_px // 8)


def qr_image_size_px() -> int:
    modules_per_side = 17 + 4 * QR_VERSION
    return (modules_per_side + 2 * QR_BORDER_MODULES) * QR_MODULE_PX
