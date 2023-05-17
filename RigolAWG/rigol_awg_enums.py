from enum import Enum

RigolDG4162EnumMode = Enum('Mode', ['static', 'sweep', 'fm_mod'])
RigolDG4162EnumSpacing = Enum('Spacing', ['LIN', 'LOG', 'STE'])
RigolDG4162EnumTriggerSlope = Enum('TriggerSlope', ['POS', 'NEG'])
RigolDG4162EnumTriggerSource = Enum('TriggerSource', ['EXT', 'INT', 'MAN'])
RigolDG4162EnumTriggerOut = Enum('TriggerOut', ['OFF', 'POS', 'NEG'])
RigolDG4162EnumModShape = Enum('ModShape', ['SIN', 'SQU', 'TRI', 'RAMP', 'NRAMP'])
