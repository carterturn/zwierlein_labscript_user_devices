'''
Copyright 2023-2024, MIT

This file is part of Zwierlein group labscript_user_devices,
and is licensed under the 3-clause BSD License.
See the license.txt file for the full license.
'''

from enum import Enum

RigolDG4162EnumMode = Enum('Mode', ['static', 'sweep', 'fm_mod'])
RigolDG4162EnumSpacing = Enum('Spacing', ['LIN', 'LOG', 'STE'])
RigolDG4162EnumTriggerSlope = Enum('TriggerSlope', ['POS', 'NEG'])
RigolDG4162EnumTriggerSource = Enum('TriggerSource', ['EXT', 'INT', 'MAN'])
RigolDG4162EnumTriggerOut = Enum('TriggerOut', ['OFF', 'POS', 'NEG'])
RigolDG4162EnumModSource = Enum('ModSource', ['INT', 'EXT'])
RigolDG4162EnumModShape = Enum('ModShape', ['SIN', 'SQU', 'TRI', 'RAMP', 'NRAMP'])
