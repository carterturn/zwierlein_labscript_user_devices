from labscript import IntermediateDevice, DigitalOut, LabscriptError, set_passed_properties, StaticAnalogQuantity, StaticDigitalQuantity, TriggerableDevice
from user_devices.RigolAWG.rigol_awg_enums import *
import numpy as np

class RigolDG4162Channel(TriggerableDevice):
    description = 'Rigol DG4162 arbitrary waveform generator channel'

    def __init__(self, name, parent_device, channel=0):
        self.trigger_edge_type = parent_device.trigger_edge_type
        TriggerableDevice.__init__(self, name, parent_device, connection='trigger')
        self.name = name

        assert channel in [1, 2], "RigolDG4162Channel only has channel 1 or channel 2"

        self.channel = channel
        self.state = 0
        self.mode = 'static'
        self.freq = 0.0
        self.freq_2 = 0.0
        self.amplitude = 0.0
        self.mod_amp = 0.0
        self.time = 0.0
        self.time_hold_start = 0.0
        self.time_hold_stop = 0.0
        self.time_return = 0.0
        self.spacing = 'LIN'
        self.steps = 0
        self.trigger_slope = 'POS'
        self.trigger_source = 'EXT'
        self.trigger_out = 'OFF'
        self.mod_source = 'INT'
        self.mod_shape = 'SIN'

        self.setup = False

    def static_output(self, amp, freq):
        if self.setup:
            raise LabscriptError('%s has already been setup. It can only have one output per run.' % self.name)
        self.state = 1
        self.mode = 'static'
        self.freq = freq
        self.amplitude = amp

        self.setup = True

    def sweep_output(self, t, amp, freq_start, freq_stop, ramp_time,
                     time_hold_start=0, time_hold_stop=0, time_return=0, steps=2048, trigger=True):
        if self.setup:
            raise LabscriptError('%s has already been setup. It can only have one output per run.' % self.name)
        self.state = 1
        self.mode = 'sweep'
        self.freq = freq_start
        self.freq_2 = freq_stop
        self.amplitude = amp

        self.time = ramp_time
        self.time_hold_start = time_hold_start
        self.time_hold_stop = time_hold_stop
        self.time_return = time_return
        self.steps = steps

        if trigger:
            self.parent_device.trigger(t, 1e-4)

        self.setup = True

    def fm_mod_output(self, t, amp, carrier_freq, mod_freq, mod_amp, mod_source='INT', shape='SIN'):
        if self.setup:
            raise LabscriptError('%s has already been setup. It can only have one output per run.' % self.name)
        self.state = 1
        self.mode = 'fm_mod'
        self.freq = carrier_freq
        self.freq_2 = mod_freq
        self.mod_amp = mod_amp
        self.mod_source = mod_source
        self.mod_shape = shape

        self.setup = True

    def generate_code(self, hdf5_file):
        pass

class RigolDG4162(IntermediateDevice):
    allowed_children = [RigolDG4162Channel]

    """A labscript_device for a Rigol DG4162 arbitrary waveform generator
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
    def __init__(self, name, channel_1_trigger, channel_2_trigger,
                 termination='\n', resource_str=None, access_mode=None,
                 frequency_limits=None, amplitude_limits=None, timeout=5, **kwargs):
        IntermediateDevice.__init__(self, name, None, **kwargs)

        self.name = name
        assert access_mode in ['eth', 'usb'], "Access mode must be one of 'eth' (Ethernet) or 'usb' (USB)"
        self.BLACS_connection = access_mode + ',' + resource_str
        self.termination = termination

        self.frequency_limits = frequency_limits
        self.amplitude_limits = amplitude_limits

        if channel_1_trigger is not None:
            self.channel_1 = RigolDG4162Channel(name + '_1', channel_1_trigger, 1)
            self.child_devices.append(self.channel_1)
        else:
            self.channel_1 = None

        if channel_2_trigger is not None:
            self.channel_2 = RigolDG4162Channel(name + '_2', channel_2_trigger, 2)
            self.child_devices.append(self.channel_2)
        else:
            self.channel_2 = None

    def get_channel_params(self, channel):
        params = np.empty(1, dtype=[('state', bool),
                                    ('mode', '<S8'),
                                    ('freq', float),
                                    ('freq_2', float),
                                    ('amplitude', float),
                                    ('mod_amp', float),
                                    ('time', float),
                                    ('time_hold_start', float),
                                    ('time_hold_stop', float),
                                    ('time_return', float),
                                    ('spacing', '<S3'),
                                    ('steps', int),
                                    ('trigger_slope', '<S3'),
                                    ('trigger_source', '<S3'),
                                    ('trigger_out', '<S3'),
                                    ('mod_source', '<S5'),
                                    ('mod_shape', '<S5'),
                                    ])
        params['state'] = channel.state
        params['mode'] = channel.mode
        params['freq'] = channel.freq
        params['freq_2'] = channel.freq_2
        params['amplitude'] = channel.amplitude
        params['mod_amp'] = channel.mod_amp
        params['time'] = channel.time
        params['time_hold_start'] = channel.time_hold_start
        params['time_hold_stop'] = channel.time_hold_stop
        params['time_return'] = channel.time_return
        params['spacing'] = channel.spacing
        params['steps'] = channel.steps
        params['trigger_slope'] = channel.trigger_slope
        params['trigger_source'] = channel.trigger_source
        params['trigger_out'] = channel.trigger_out
        params['mod_source'] = channel.mod_source
        params['mod_shape'] = channel.mod_shape

        return params

    def generate_code(self, hdf5_file):
        IntermediateDevice.generate_code(self, hdf5_file)
        group = self.init_device_group(hdf5_file)
        if self.channel_1:
            group.create_dataset('channel 1', data=self.get_channel_params(self.channel_1))
        if self.channel_2:
            group.create_dataset('channel 2', data=self.get_channel_params(self.channel_2))
