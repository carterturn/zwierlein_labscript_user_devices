'''
Copyright 2023-2024, MIT

This file is part of Zwierlein group labscript_user_devices,
and is licensed under the 3-clause BSD License.
See the license.txt file for the full license.
'''

from labscript_devices import register_classes

register_classes(
    labscript_device_name='RigolDG4162',
    BLACS_tab='user_devices.RigolAWG.blacs_tabs.Rigol4162Tab',
    runviewer_parser=None,
)
