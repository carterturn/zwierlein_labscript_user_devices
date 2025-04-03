'''
Copyright 2023-2024, MIT

This file is part of Zwierlein group labscript_user_devices,
and is licensed under the 3-clause BSD License.
See the license.txt file for the full license.
'''

import labscript_utils.h5_lock  
import h5py
import numpy as np

import labscript_utils.properties as properties

class AD9914RP2350Parser(object):
    def __init__(self, path, device):
        self.path = path
        self.name = device.name
        self.device = device

    def get_traces(self, add_trace, clock=None):
        with h5py.File(self.path, "r") as f:
            group = f['devices/' + self.name]
            dds_data = group['dds_data'][()]

            ticks = []
            freq_values = []
            amp_values = []

            for entry in dds_data:
                if not entry[5]:
                    ticks += [entry[0]]
                    freq_values += [entry[1]]
                    amp_values += [entry[3]]
                else:
                    sweep_times = np.hstack([np.arange(0, entry[6], 1. / 250e3), [entry[6]*1e-3]])
                    sweep_freq = np.interp(sweep_times, [0, entry[6]], [entry[1], entry[2]])
                    sweep_amp = np.interp(sweep_times, [0, entry[6]], [entry[3], entry[4]])

                    ticks += list(sweep_times + entry[0])
                    freq_values += list(sweep_freq)
                    amp_values += list(sweep_amp)

            add_trace(self.name + '_freq', (ticks, freq_values), self.name, 'freq')
            add_trace(self.name + '_amp', (ticks, amp_values), self.name, 'amp')
            
        return {}
