'''
Copyright 2023-2024, MIT

This file is part of Zwierlein group labscript_user_devices,
and is licensed under the 3-clause BSD License.
See the license.txt file for the full license.
'''

from labscript_devices import register_classes

register_classes(
    'AD9959EvalDDS',
    BLACS_tab='user_devices.AD9959EvalDDS.blacs_tabs.AD9959EvalDDSTab',
    runviewer_parser='user_devices.AD9959EvalDDS.runviewer_parser.AD9959EvalDDSParser',
)
