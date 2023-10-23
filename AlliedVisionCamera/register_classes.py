from labscript_devices import register_classes

register_classes(
    'AlliedVisionCamera',
    BLACS_tab='user_devices.AlliedVisionCamera.blacs_tabs.AlliedVisionCameraTab',
    runviewer_parser=None,
)
