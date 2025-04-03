'''
Copyright 2023-2024, MIT

This file is part of Zwierlein group labscript_user_devices,
and is licensed under the 3-clause BSD License.
See the license.txt file for the full license.
'''

from labscript_devices import register_classes

register_classes(
    'AD9914RP2350',
    BLACS_tab='user_devices.AD9914_RP2350.blacs_tabs.AD9914RP2350Tab',
    runviewer_parser='user_devices.AD9914_RP2350.runviewer_parser.AD9914RP3250Parser',
)
