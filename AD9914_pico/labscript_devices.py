from labscript import TriggerableDevice, IntermediateDevice, set_passed_properties

import numpy as np

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
        command_array = np.empty(len(self.command_list),
                                 dtype=[('start freq', float),
                                        ('start amp', float),
                                        ('stop freq', float),
                                        ('stop amp', float),
                                        ('sweep', bool),
                                        ('sweep time', float),
                                        ('trigger', bool)])
        for cl, ca in zip(self.command_list, command_array):
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
        self.command_list.append({'t': t,
                                  'start_freq': freq,
                                  'stop_freq': freq,
                                  'start_amp': amp,
                                  'stop_amp': amp,
                                  'sweep': False,
                                  'trigger': True,
                                  })
        self.trigger(t=t, duration=1e-6)

    def customramp(self, t, duration, freq_function, amp_function, **kwargs):
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
