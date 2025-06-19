from utils.logger import log  # assuming you have a logger set up

def refresh_all(app):
    """
    Refresh all relevant frames in the app after DB changes.
    Expects `app` to have a `frames` dict with frame instances.
    """
    if not hasattr(app, "frames"):
        log.warning("App has no frames attribute; skipping refresh_all")
        return

    frames_to_refresh = {
        "Customers": "refresh_customers",
        "Products": "refresh_products",
        "Reports": "refresh_report",
        "Billing": "refresh_cart",
        "Settings": None,  # Add method name if needed
    }

    for frame_name, refresh_method in frames_to_refresh.items():
        frame = app.frames.get(frame_name)
        if frame and refresh_method and hasattr(frame, refresh_method):
            try:
                getattr(frame, refresh_method)()
            except Exception as e:
                log.error(f"Failed to refresh {frame_name} frame: {e}")
