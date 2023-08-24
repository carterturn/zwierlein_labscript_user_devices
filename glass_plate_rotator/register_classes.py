from labscript_devices import register_classes

register_classes(
    'GlassPlateRotator',
    BLACS_tab='user_devices.glass_plate_rotator.blacs_tabs.GlassPlateRotatorTab',
    runviewer_parser=None,
)
