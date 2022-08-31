from labscript import Device, DigitalOut, IntermediateDevice, LabscriptError, set_passed_properties, StaticAnalogQuantity, StaticDigitalQuantity, TriggerableDevice
from user_devices.RigolAWG.rigol_awg_enums import *
import numpy as np

from user_devices import StaticEnumQuantity

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
    def __init__(self, name, parent_device, termination='\n', resource_str=None, access_mode=None,
                 frequency_limits=None, amplitude_limits=None, timeout=5,
                 connection_1=None, connection_2=None, **kwargs):
        IntermediateDevice.__init__(self, name, parent_device, **kwargs)
        self.name = name
        assert access_mode in ['eth', 'usb'], "Access mode must be one of 'eth' (Ethernet) or 'usb' (USB)"
        self.BLACS_connection = access_mode + ',' + resource_str
        self.termination = termination

        self.frequency_limits = frequency_limits
        self.amplitude_limits = amplitude_limits

        self.channels = []

        for channel in [1, 2]:
            channel_props = {'channel': channel}
            channel_props['state'] = StaticDigitalQuantity(self.name+'_channel_{:d}_state'.format(channel), self, None)
            channel_props['mode'] = StaticEnumQuantity(self.name+'_channel_{:d}_mode'.format(channel), self, None, RigolDG4162EnumMode, RigolDG4162EnumMode.static)
            channel_props['freq'] = StaticAnalogQuantity(self.name+'_channel_{:d}_freq'.format(channel), self, None)
            channel_props['freq_stop'] = StaticAnalogQuantity(self.name+'_channel_{:d}_freq_stop'.format(channel), self, None)
            channel_props['amplitude'] = StaticAnalogQuantity(self.name+'_channel_{:d}_amplitude'.format(channel), self, None)
            channel_props['time'] = StaticAnalogQuantity(self.name+'_channel_{:d}_time'.format(channel), self, None)
            channel_props['time_hold_start'] = StaticAnalogQuantity(self.name+'_channel_{:d}_time_hold_start'.format(channel), self, None)
            channel_props['time_hold_stop'] = StaticAnalogQuantity(self.name+'_channel_{:d}_time_hold_stop'.format(channel), self, None)
            channel_props['time_return'] = StaticAnalogQuantity(self.name+'_channel_{:d}_time_return'.format(channel), self, None)
            channel_props['spacing'] = StaticEnumQuantity(self.name+'_channel_{:d}_spacing'.format(channel), self, None, RigolDG4162EnumSpacing, RigolDG4162EnumSpacing.LIN)
            channel_props['steps'] = StaticAnalogQuantity(self.name+'_channel_{:d}_steps'.format(channel), self, None)
            channel_props['trigger_slope'] = StaticEnumQuantity(self.name+'_channel_{:d}_trigger_slope'.format(channel), self, None, RigolDG4162EnumTriggerSlope, RigolDG4162EnumTriggerSlope.POS)
            channel_props['trigger_source'] = StaticEnumQuantity(self.name+'_channel_{:d}_trigger_source'.format(channel), self, None, RigolDG4162EnumTriggerSource, RigolDG4162EnumTriggerSource.EXT)
            channel_props['trigger_out'] = StaticEnumQuantity(self.name+'_channel_{:d}_trigger_out'.format(channel), self, None, RigolDG4162EnumTriggerOut, RigolDG4162EnumTriggerOut.OFF)
            channel_props['trigger'] = DigitalOut(self.name+'_channel_{:d}_trigger'.format(channel), self, locals()['connection_{:d}'.format(channel)])
            self.channels.append(channel_props)

    def generate_code(self, hdf5_file):
        Device.generate_code(self, hdf5_file)
        group = self.init_device_group(hdf5_file)
        for channel in [1, 2]:
            params = np.empty(1, dtype=[('state', bool),
                                        ('mode', '<S8'),
                                        ('freq', float),
                                        ('freq_stop', float),
                                        ('amplitude', float),
                                        ('time', float),
                                        ('time_hold_start', float),
                                        ('time_hold_stop', float),
                                        ('time_return', float),
                                        ('spacing', '<S3'),
                                        ('steps', int),
                                        ('trigger_slope', '<S3'),
                                        ('trigger_source', '<S3'),
                                        ('trigger_out', '<S3'),
                                        ])
            params['state'] = self.channels[channel-1]['state'].static_value
            params['mode'] = self.channels[channel-1]['mode'].static_value.name
            params['freq'] = self.channels[channel-1]['freq'].static_value
            params['freq_stop'] = self.channels[channel-1]['freq_stop'].static_value
            params['amplitude'] = self.channels[channel-1]['amplitude'].static_value
            params['time'] = self.channels[channel-1]['time'].static_value
            params['time_hold_start'] = self.channels[channel-1]['time_hold_start'].static_value
            params['time_hold_stop'] = self.channels[channel-1]['time_hold_stop'].static_value
            params['time_return'] = self.channels[channel-1]['time_return'].static_value
            params['spacing'] = self.channels[channel-1]['spacing'].static_value.name
            params['steps'] = self.channels[channel-1]['steps'].static_value
            params['trigger_slope'] = self.channels[channel-1]['trigger_slope'].static_value.name
            params['trigger_source'] = self.channels[channel-1]['trigger_source'].static_value.name
            params['trigger_out'] = self.channels[channel-1]['trigger_out'].static_value.name
            group.create_dataset('channel {:d}'.format(channel), data=params)
