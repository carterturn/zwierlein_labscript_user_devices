from labscript_devices import register_classes

register_classes(
    labscript_device_name='RigolDG4162',
    BLACS_tab='user_devices.RigolAWG.blacs_tabs.Rigol4162Tab',
    runviewer_parser=None,
)
