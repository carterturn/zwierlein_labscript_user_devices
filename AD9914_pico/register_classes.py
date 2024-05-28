'''
Copyright 2023-2024, MIT

This file is part of Zwierlein group labscript_user_devices,
and is licensed under the 3-clause BSD License.
See the license.txt file for the full license.
'''

from labscript_devices import register_classes

register_classes(
    'AD9914Pico',
    BLACS_tab='user_devices.AD9914_pico.blacs_tabs.AD9914PicoTab',
    runviewer_parser='user_devices.AD9914_pico.runviewer_parser.AD9914PicoParser',
)
