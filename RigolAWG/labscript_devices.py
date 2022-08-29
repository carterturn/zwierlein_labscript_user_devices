from labscript import Device, IntermediateDevice, LabscriptError, set_passed_properties, StaticAnalogQuantity
from enum import *
import numpy as np

from user_devices import StaticEnumQuantity

class RigolDG4162Static(IntermediateDevice):
    def __init__(self, name, host_device, parent_device, channel, **kwargs):
        IntermediateDevice.__init__(self, name, parent_device, **kwargs)

        self.channel_name = channel

        self.freq = StaticAnalogQuantity(self.name+'_freq', self, 'freq')
        self.amplitude = StaticAnalogQuantity(self.name+'_amplitude', self, 'amplitude')

        host_device.add_device(self)
        self.parent_device.add_device(self)

        return

class RigolDG4162Sweep(IntermediateDevice):
    def __init__(self, name, host_device, parent_device, channel, **kwargs):
        IntermediateDevice.__init__(self, name, parent_device, **kwargs)

        self.channel_name = channel

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

        host_device.add_device(self)
        self.parent_device.add_device(self)

        return

class RigolDG4162(Device):
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
        IntermediateDevice.generate_code(self, hdf5_file)
        group = self.init_device_group(hdf5_file)
        for channel in self.child_devices:
            if True or isinstance(channel, RigolDG4162Static):
                print('Adding static RigolDG4162 channel')
                static_params = np.empty(1, dtype=[('state', bool),
                                                   ('mode', '<S8'),
                                                   ('freq', float),
                                                   ('amplitude', float),
                                                   ])
                static_params['state'] = True
                static_params['mode'] = 'static'
                static_params['freq'] = channel.freq.static_value
                static_params['amplitude'] = channel.amplitude.static_value
                group.create_dataset(channel.channel_name, data=static_params)
            elif isinstance(channel, RigolDG4162Sweep):
                print('Adding sweep RigolDG4162 channel')
                sweep_params = np.empty(1, dtype=[('mode', '<S8'),
                                                  ('freq_start', float),
                                                  ('freq_stop', float),
                                                  ('amplitude', float),
                                                  ('time', float),
                                                  ('time_hold_start', float),
                                                  ('time_hold_stop', float),
                                                  ('time_return', float),
                                                  ('spacing', float),
                                                  ('steps', int),
                                                  ('trigger_slope', bool),
                                                  ('trigger_source', bool),
                                                  ('trigger_out', bool),
                                                  ])
                sweep_params['state'] = True
                sweep_params['mode'] = 'sweep'
                sweep_params['freq_start'] = channel.freq_start.static_value
                sweep_params['freq_stop'] = channel.freq_stop.static_value
                sweep_params['amplitude'] = channel.amplitude.static_value
                sweep_params['time'] = channel.time.static_value
                sweep_params['time_hold_start'] = channel.time_hold_start.static_value
                sweep_params['time_hold_stop'] = channel.time_hold_stop.static_value
                sweep_params['time_return'] = channel.time_return.static_value
                sweep_params['spacing'] = channel.spacing.static_value
                sweep_params['steps'] = channel.steps.static_value
                sweep_params['trigger_slope'] = channel.trigger_slope.static_value
                sweep_params['trigger_source'] = channel.trigger_source.static_value
                sweep_params['trigger_out'] = channel.trigger_out.static_value
                group.create_dataset(channel.channel_name, data=sweep_params)
            else:
                print('Invalid RigolDG4162 channel: ' + type(channel))
