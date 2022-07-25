from labscript import Device, IntermediateDevice, LabscriptError, set_passed_properties, StaticAnalogQuantity
from enum import *

from user_devices import StaticEnumQuantity

class RigolDG4162Static(Device):
    def __init__(self, name, parent_device, connection, **kwargs):
        Device.__init__(self, name, parent_device, connection, **kwargs)

        self.freq = StaticAnalogQuantity(self.name+'_freq', self, 'freq')
        self.amplitude = StaticAnalogQuantity(self.name+'_amplitude', self, 'amplitude')

        self.parent_device.add_device(self)

        return

class RigolDG4162Sweep(Device):
    def __init__(self, name, parent_device, connection, **kwargs):
        Device.__init__(self, name, parent_device, connection, **kwargs)

        self.freq_start = StaticAnalogQuantity(self.name+'_freq_start', self, 'freq_start')
        self.freq_stop = StaticAnalogQuantity(self.name+'_freq_stop', self, 'freq_stop')
        self.amplitude = StaticAnalogQuantity(self.name+'_amplitude', self, 'amplitude')
        self.time = StaticAnalogQuantity(self.name+'_time', self, 'time')
        self.time_hold_start = StaticAnalogQuantity(self.name+'_time_hold_start', self, 'time_hold_start')
        self.time_hold_stop = StaticAnalogQuantity(self.name+'_time_hold_stop', self, 'time_hold_stop')
        self.time_return = StaticAnalogQuantity(self.name+'_time_return', self, 'time_return')
        self.spacing = StaticEnumQuantity(self.name+'_spacing', self, 'spacing', RigolDG4162EnumSpacing)
        self.steps = StaticAnalogQuantity(self.name+'_steps', self, 'steps')
        self.trigger_slope = StaticEnumQuantity(self.name+'_trigger_slope', self, 'trigger_slope', RigolDG4162EnumTriggerSlope)
        self.trigger_source = StaticEnumQuantity(self.name+'_trigger_source', self, 'trigger_source', RigolDG4162EnumTriggerSource)
        self.trigger_out = StaticEnumQuantity(self.name+'_trigger_out', self, 'trigger_out', RigolDG4162EnumTriggerSource)

        self.parent_device.add_device(self)

        return

class RigolDG4162(IntermediateDevice):
    """A labscript_device for the Rigol DG4162 arbitrary waveform generator
          connection_table_properties (set once)
          termination: character signalling end of response
          resource_str: IP address or USBTMC name
          access_mode: 'eth' or 'usb'
          frequency_limits: minimum and maximum output frequency
          amplitude_limits: minimum and maximum output amplitude
    """
    description = 'Rigol DG4162 arbitrary waveform generator'

    @set_passed_properties(
        property_names = {
            'connection_table_properties': ['termination', 'resource_str', 'access_mode',
                                            'frequency_limits', 'amplitude_limits'],
        }
    )
    def __init__(self, name, termination='\n', resource_str=None, access_mode=None,
                 frequency_limits=None, amplitude_limits=None, timeout=5, **kwargs):
        Device.__init__(self, name, None, None, **kwargs)
        self.name = name
        assert access_mode in ['eth', 'usb'], "Access mode must be one of 'eth' (Ethernet) or 'usb' (USB)"
        self.BLACS_connection = access_mode + ',' + resource_str
        self.termination = termination

        self.frequency_limits = frequency_limits
        self.amplitude_limits = amplitude_limits

    def generate_code(self, hdf5_file):
        # group = self.init_device_name(hdf5_file)
        IntermediateDevice.generate_code(self, hdf5_file)
        group = self.init_device_group(hdf5_file)
        for channel in self.child_devices:
            print(channel.connection)
