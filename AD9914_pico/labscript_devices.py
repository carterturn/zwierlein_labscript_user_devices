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
        # List of command tuples in the form
        #     (t, start freq, stop freq, start amp, stop amp, sweep, sweep time, triger)
        self.commands = []

    def generate_code(self, hdf5_file):
        TriggerableDevice.generate_code(self, hdf5_file)

        # Sort commands by start time
        self.commands.sort(key=lambda c: c[0])

        # Check for overlapping ramps
        for cl in self.commands:
            t_start = cl[0]
            if cl[5]:
                t_end = cl[0] + cl[6]
            else:
                t_end = cl[0] + 2e-6
            for cl_ in self.commands:
                if cl_[0] > t_start + 1e-9 and cl_[0] < t_end - 1e-9:
                    # Add 1e-9 (smaller than possible resolution) to mitigate floating point errors.
                    raise LabscriptError('%s requires trigger at %s, overlapping with a ramp from t = %s to %s' % (self.name, str(cl_[0]), str(t_start), str(t_end)))

        command_array = np.array(self.commands,
                                 dtype=[('t', float),
                                        ('start freq', float),
                                        ('stop freq', float),
                                        ('start amp', float),
                                        ('stop amp', float),
                                        ('sweep', bool),
                                        ('sweep time', float),
                                        ('trigger', bool)])

        # Check amplitudes
        if np.any(command_array['start amp'] < 0):
            bad_idx = np.where(command_array['start amp'] < 0)
            sys.stderr.write('WARNING: %s has commands with start_amp < 0 at times %s. Bounding to 0.\n'
                             % (self.name, str(command_array['t'][bad_idx])))
            command_array['start amp'][bad_idx] = 0
        if np.any(command_array['start amp'] > 1):
            bad_idx = np.where(command_array['start amp'] > 1)
            sys.stderr.write('WARNING: %s has commands with start_amp > 1 at times %s. Bounding to 1.\n'
                             % (self.name, str(command_array['t'][bad_idx])))
            command_array['start amp'][bad_idx] = 1
        if np.any(command_array['stop amp'] < 0):
            bad_idx = np.where(command_array['stop amp'] < 0)
            sys.stderr.write('WARNING: %s has commands with stop_amp < 0 at times %s. Bounding to 0.\n'
                             % (self.name, str(command_array['t'][bad_idx])))
            command_array['stop amp'][bad_idx] = 0
        if np.any(command_array['stop amp'] > 1):
            bad_idx = np.where(command_array['stop amp'] > 1)
            sys.stderr.write('WARNING: %s has commands with stop_amp > 1 at times %s. Bounding to 1.\n'
                             % (self.name, str(command_array['t'][bad_idx])))
            command_array['stop amp'][bad_idx] = 1

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
        self.commands.append((t, start_freq, stop_freq, start_amp, stop_amp, True, duration, True))
        self.trigger(t=t, duration=duration/2.)

    def constant(self, t, freq, amp):
        '''
        Set frequency and amplitude to constant values at time t

        Args:
        t: Time to set at
        freq: Frequency to set, Hz
        amp: Amplitude to set, arbitrary units from 1.0 to 0.0
        '''
        self.commands.append((t, freq, freq, amp, amp, False, 0.0, True))
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
                                  [True] * len(sample_times),
                                  [t_step] * (len(sample_times) - 1) + [duration - sample_times[-1]],
                                  [True] + [False] * (len(sample_times) - 1)])
        self.commands += [tuple(ca) for ca in command_array.T]
        self.trigger(t=t, duration=duration/2.)
