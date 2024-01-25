from labscript import TriggerableDevice, IntermediateDevice, set_passed_properties, LabscriptError

import numpy as np
import sys

class AD9914Pico(TriggerableDevice):

    @set_passed_properties(
        property_names={
            'connection_table_properties': [
                'name',
                'com_port',
            ]
        }
    )

    def __init__(self, name, parent_device, com_port, **kwargs):
        self.trigger_edge_type = parent_device.trigger_edge_type
        TriggerableDevice.__init__(self, name, parent_device, connection='trigger', **kwargs)
        self.BLACS_connection = 'AD9914Pico: {}'.format(name)
        self.command_list = []

    def generate_code(self, hdf5_file):
        TriggerableDevice.generate_code(self, hdf5_file)

        self.command_list.sort(key=lambda cl: cl['t'])

        # Check for overlapping ramps
        for cl in self.command_list:
            t_start = cl['t']
            if cl['sweep']:
                t_end = cl['t'] + cl['sweep_time']
            else:
                t_end = cl['t'] + 2e-6
            for cl_ in self.command_list:
                if cl_['t'] > t_start and cl_['t'] < t_end:
                    raise LabscriptError('%s requires trigger at %s, overlapping with a ramp from t = %s to %s' % (self.name, str(cl_['t']), str(t_start), str(t_end)))

        command_array = np.empty(len(self.command_list),
                                 dtype=[('start freq', float),
                                        ('start amp', float),
                                        ('stop freq', float),
                                        ('stop amp', float),
                                        ('sweep', bool),
                                        ('sweep time', float),
                                        ('trigger', bool)])
        for cl, ca in zip(self.command_list, command_array):
            # Bound amplitude to avoid unexpected results
            if cl['start_amp'] < 0:
                cl['start_amp'] = 0
                sys.stderr.write('WARNING: %s has a command with start_amp < 0 at time %s. Bounding to 0.\n'
                                 % (self.name, str(cl['t'])))
            if cl['start_amp'] > 1:
                cl['start_amp'] = 1
                sys.stderr.write('WARNING: %s has a command with start_amp > 1 at time %s. Bounding to 1.\n'
                                 % (self.name, str(cl['t'])))
            if cl['stop_amp'] < 0:
                cl['stop_amp'] = 0
                sys.stderr.write('WARNING: %s has a command with stop_amp < 0 at time %s. Bounding to 0.\n'
                                 % (self.name, str(cl['t'])))
            if cl['stop_amp'] > 1:
                cl['stop_amp'] = 1
                sys.stderr.write('WARNING: %s has a command with stop_amp > 1 at time %s. Bounding to 1.\n'
                                 % (self.name, str(cl['t'])))

            ca['start freq'] = cl['start_freq']
            ca['stop freq'] = cl['stop_freq']
            ca['start amp'] = cl['start_amp']
            ca['stop amp'] = cl['stop_amp']
            ca['sweep'] = cl['sweep']
            if cl['sweep']:
                ca['sweep time'] = cl['sweep_time']
            ca['trigger'] = cl['trigger']

        group = hdf5_file['devices'].require_group(self.name)
        group.create_dataset('dds_data', data=command_array)

    def ramp(self, t, duration, start_freq, stop_freq, start_amp, stop_amp):
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
        self.command_list.append({'t': t,
                                  'start_freq': start_freq,
                                  'stop_freq': stop_freq,
                                  'start_amp': start_amp,
                                  'stop_amp': stop_amp,
                                  'sweep': True,
                                  'sweep_time': duration,
                                  'trigger': True,
                                  })
        self.trigger(t=t, duration=duration/2.)

    def constant(self, t, freq, amp):
        '''
        Set frequency and amplitude to constant values at time t

        Args:
        t: Time to set at
        freq: Frequency to set, Hz
        amp: Amplitude to set, arbitrary units from 1.0 to 0.0
        '''
        self.command_list.append({'t': t,
                                  'start_freq': freq,
                                  'stop_freq': freq,
                                  'start_amp': amp,
                                  'stop_amp': amp,
                                  'sweep': False,
                                  'trigger': True,
                                  })
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

        first_linear = True
        t_rel = 0
        next_freq = freq_function(0)
        next_amp = amp_function(0)

        while t_rel < duration - t_step:
            start_freq = next_freq
            start_amp = next_amp
            t_rel = t_rel + t_step
            next_freq = freq_function(t_rel)
            next_amp = amp_function(t_rel)

            self.command_list.append({'t': t + t_rel - t_step,
                                      'start_freq': start_freq,
                                      'stop_freq': next_freq,
                                      'start_amp': start_amp,
                                      'stop_amp': next_amp,
                                      'sweep': True,
                                      'sweep_time': t_step,
                                      'trigger': first_linear
                                      })

            first_linear = False

        start_freq = next_freq
        start_amp = next_amp
        next_freq = freq_function(duration)
        next_amp = amp_function(duration)

        self.command_list.append({'t': t + t_rel - t_step,
                                  'start_freq': start_freq,
                                  'stop_freq': next_freq,
                                  'start_amp': start_amp,
                                  'stop_amp': next_amp,
                                  'sweep': True,
                                  'sweep_time': duration + t_step - (t + t_rel),
                                  'trigger': False
                                  })
        self.trigger(t=t, duration=duration/2.)
