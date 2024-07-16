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

class TeensyDACParser(object):
    def __init__(self, path, device):
        self.path = path
        self.name = device.name
        self.device = device

    def get_traces(self, add_trace, clock=None):
        times, clock_value = clock[0], clock[1]

        clock_indices = np.where((clock_value[1:] - clock_value[:-1]) == 1)[0] + 1
        # If initial clock value is 1, then this counts as a rising edge (clock should
        # be 0 before experiment) but this is not picked up by the above code. So we
        # insert it!
        if clock_value[0] == 1:
            clock_indices = np.insert(clock_indices, 0, 0)
        clock_ticks = times[clock_indices]

        with h5py.File(self.path, "r") as f:
            props = properties.get(f, self.name, 'connection_table_properties')

            group = f['devices/' + self.name]
            dac_data = group['dac_data'][()]

            if 'dac_cmd_scale' in props.keys():
                dac_cmd_scale = props['dac_cmd_scale']
            else:
                dac_cmd_scale = 1.0

            values = dac_data.astype(float) / dac_cmd_scale

            add_trace(self.name, (clock_ticks, values), self.name, self.name)

        return {}
