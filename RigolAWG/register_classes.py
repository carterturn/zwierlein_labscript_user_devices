from labscript_devices import register_classes

register_classes(
    'Rigol4162Controller',
    BLACS_tab='user_devices.RigolAWG.blacs_tabs.Rigol4162Tab',
    runviewer_parser=None,
)
