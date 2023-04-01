from labscript_devices import register_classes

register_classes(
    'AD9914Pico',
    BLACS_tab='user_devices.AD9914_pico.blacs_tabs.AD9914PicoTab',
    runviewer_parser=None,
)
