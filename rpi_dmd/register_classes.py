'''
Copyright 2023-2024, MIT

This file is part of Zwierlein group labscript_user_devices,
and is licensed under the 3-clause BSD License.
See the license.txt file for the full license.
'''

from labscript_devices import register_classes

register_classes(
    'RPiDMD',
    BLACS_tab='user_devices.rpi_dmd.blacs_tabs.RPiDMDTab',
    runviewer_parser=None,
)
