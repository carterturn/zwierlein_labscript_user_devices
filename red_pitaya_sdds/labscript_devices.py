'''
Copyright 2023-2024, MIT

This file is part of Zwierlein group labscript_user_devices,
and is licensed under the 3-clause BSD License.
See the license.txt file for the full license.
'''

from labscript import AnalogQuantity, IntermediateDevice, TriggerableDevice, set_passed_properties, LabscriptError

import numpy as np
import sys

class RedPitayaSDDSChannel(TriggerableDevice):
    # Frequency and amplitude are added as children, though never used due to instruction encoding.
    allowed_children = [AnalogQuantity]

    FPGA_CLOCK = 125e6
    FPGA_OUT_MAX = 1.0
    FPGA_STEP_SCALE = 2**16

    FREQ_SCALE = (2**32 - 1) / FPGA_CLOCK
    AMP_SCALE = (2**14 - 1) / FPGA_OUT_MAX

    def __init__(self, parent_name, parent_device, channel=''):
        self.name = parent_name + '_' + channel
        self.trigger_edge_type = parent_device.trigger_edge_type
        TriggerableDevice.__init__(self, self.name, parent_device, connection='trigger')

        assert channel in ['A', 'B'], "RedPitayaSDDSChannel only has channel 'A' or channel 'B'"

        self.channel = channel
        self.parent_name = parent_name

        self.commands = []

    def generate_code(self, hdf5_file):
        cmd_arr_float = np.array(self.commands,
                                 dtype=[('t', float),
                                        ('freq_start', float),
                                        ('freq_stop', float),
                                        ('amp_start', float),
                                        ('amp_stop', float),
                                        ('duration', float),
                                        ('trigger', '<i1')])

        # Check for overlapping ramps
        cmd_arr_float.sort(order='t')
        end_ts = cmd_arr_float['t'] + cmd_arr_float['duration']
        if np.any(end_ts[1:] < cmd_arr_float['t'][:-1]): # Quick check
            for cl in self.commands: # Figure out where the problem is
                t_start = cl[0]
                t_end = cl[0] + cl[5]
                for cl_ in self.commands:
                    if cl_[0] > t_start and cl_[0] < t_end:
                        raise LabscriptError('%s requires trigger at %s, overlapping with a ramp from t = %s to %s' % (self.name, str(cl_[0]), str(t_start), str(t_end)))

        cmd_arr_float_step = np.empty(cmd_arr_float.shape,
                                      dtype=[('freq_start', float),
                                             ('freq_step', float),
                                             ('amp_start', float),
                                             ('amp_step', float),
                                             ('step_total', float),
                                             ('trigger', '<i1'),
                                             ('step_scale', '<i1')])

        cmd_arr_float_step['step_total'] = cmd_arr_float['duration'] * self.FPGA_CLOCK
        cmd_arr_float_step['freq_start'] = cmd_arr_float['freq_start']*self.FREQ_SCALE
        cmd_arr_float_step['freq_step'] = ((cmd_arr_float['freq_stop'] - cmd_arr_float['freq_start'])
                                           * self.FREQ_SCALE / cmd_arr_float_step['step_total'])
        cmd_arr_float_step['amp_start'] = cmd_arr_float['amp_start'] * self.AMP_SCALE
        cmd_arr_float_step['amp_step'] = ((cmd_arr_float['amp_stop'] - cmd_arr_float['amp_start'])
                                          * 2*self.AMP_SCALE / cmd_arr_float_step['step_total'])
        cmd_arr_float_step['trigger'] = cmd_arr_float['trigger']
        # Check if we need to disable step scaling
        cmd_arr_float_step['step_scale'] = np.logical_or(
            np.logical_or(cmd_arr_float_step['freq_step']*2**16 > 2**31-1,
                          cmd_arr_float_step['freq_step']*2**16 < -2**31),
            np.logical_or(cmd_arr_float_step['amp_step']*2**16 > 2**15-1,
                          cmd_arr_float_step['amp_step']*2**16 < -2**15))
        # If we do, apply step scaling
        cmd_arr_float_step['freq_step'] = (cmd_arr_float_step['freq_step']
                                           * (2**16)**(cmd_arr_float_step['step_scale']==0))
        cmd_arr_float_step['amp_step'] = (cmd_arr_float_step['amp_step']
                                          * (2**16)**(cmd_arr_float_step['step_scale']==0))

        cmd_arr_int = np.empty(cmd_arr_float_step.shape,
                               dtype=[('freq_start', '<u4'),
                                      ('freq_step', '<i4'),
                                      ('amp_start', '<u2'),
                                      ('amp_step', '<i2'),
                                      ('step_total', '<u4')])

        cmd_arr_int['freq_start'] = cmd_arr_float_step['freq_start']
        cmd_arr_int['freq_step'] = cmd_arr_float_step['freq_step']
        cmd_arr_int['amp_start'] = (cmd_arr_float_step['amp_start'].astype('<u2')
                                   | 0x8000 * (cmd_arr_float_step['trigger']==0)
                                   | 0x4000 * (cmd_arr_float_step['step_scale']==1))
        cmd_arr_int['amp_step'] = cmd_arr_float_step['amp_step']
        cmd_arr_int['step_total'] = cmd_arr_float_step['step_total']

        group = hdf5_file['devices'].require_group(self.parent_name)
        group.create_dataset(self.channel, data=cmd_arr_int)

    def ramp(self, t, duration, start_freq, stop_freq, start_amp, stop_amp, trigger=True):
        '''
        Ramp frequency and amplitude from start values to end values over some time.
        Resolution is always hardware maximum (~1 MHz)

        Args:
        t: Time to start ramp at
        duration: Duration of ramp
        start_freq: Frequency to start at, Hz
        stop_freq: Frequency to stop at, Hz
        start_amp: Amplitude to start at, arbitrary units from 1.0 to 0.0
        stop_amp: Amplitude to stop at, arbitrary units from 1.0 to 0.0
        '''
        self.commands.append((t, start_freq, stop_freq, start_amp, stop_amp, duration, trigger))
        if trigger:
            self.trigger(t=t, duration=duration/2.)

    def constant(self, t, freq, amp):
        '''
        Set frequency and amplitude to constant values at time t

        Args:
        t: Time to set at
        freq: Frequency to set, Hz
        amp: Amplitude to set, arbitrary units from 1.0 to 0.0
        '''
        self.commands.append((t, freq, freq, amp, amp, 2e-6, True))
        self.trigger(t=t, duration=2e-6) # Need to be >1e-6s for safe triggering with NI card

    def customramp(self, t, duration, freq_function, amp_function, **kwargs):
        '''
        Ramp frequency and amplitude according to custom functions.
        kwargs should include samplerate,
        which instructs Labscript how many linear ramps to divide the functions into.
        A trigger is set at the start of the ramps, but not for the intermediate ones.

        Args:
        t: Time to start ramps at
        duration: Total ramp time
        freq_function: Function describing frequency versus time.
        	Should be a function with one argument: the time relative to the ramp start time.
        	Output should be a frequency in Hz.
        amp_function: Function describing amplitude versus time.
        	Should be a function with one argument: the time relative to the ramp start time.
        	Output should be a amplitude between 0.0 and 1.0.
        '''
        t_step = 1. / kwargs.pop('samplerate')
        sample_times = np.arange(0, duration, t_step)
        freqs = list(freq_function(sample_times))
        amps = list(amp_function(sample_times))

        command_array = np.array([sample_times + t,
                                  freqs, freqs[1:] + [freq_function(duration)],
                                  amps, amps[1:] + [amp_function(duration)],
                                  [t_step] * (len(sample_times) - 1) + [duration - sample_times[-1]],
                                  [True] + [False] * (len(sample_times) - 1)])
        self.commands += [tuple(ca) for ca in command_array.T]
        self.trigger(t=t, duration=duration/2.)

class RedPitayaSDDS(IntermediateDevice):
    allowed_children = [RedPitayaSDDSChannel]

    """A labscript_device for a Red Pitaya Scriptable DDS
        connection_table_properties (set once)
        ip: IP address
    """
    description = 'Red Pitaya Scriptable DDS'

    @set_passed_properties(
        property_names={
            'connection_table_properties': [
                'name',
                'ip',
            ]
        }
    )

    def __init__(self, name, channel_A_trigger, channel_B_trigger, ip, **kwargs):
        IntermediateDevice.__init__(self, name, None, **kwargs)
        self.name = name

        self.BLACS_connection = ':RedPitayaSDDS: {}'.format(name)

        if channel_A_trigger is not None:
            self.channel_A = RedPitayaSDDSChannel(name, channel_A_trigger, 'A')
            self.child_devices.append(self.channel_A)
        else:
            self.channel_A = None

        if channel_B_trigger is not None:
            self.channel_B = RedPitayaSDDSChannel(name, channel_B_trigger, 'B')
            self.child_devices.append(self.channel_B)
        else:
            self.channel_B = None

    def generate_code(self, hdf5_file):
        pass
