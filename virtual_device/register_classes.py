from labscript_devices import register_classes

register_classes(
    'VirtualDevice',
    BLACS_tab='user_devices.virtual_device.blacs_tabs.VirtualDeviceTab',
    runviewer_parser=None,
)
