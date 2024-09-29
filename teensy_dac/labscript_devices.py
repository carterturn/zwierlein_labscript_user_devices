'''
Copyright 2023-2024, MIT

This file is part of Zwierlein group labscript_user_devices,
and is licensed under the 3-clause BSD License.
See the license.txt file for the full license.
'''

from user_devices.library.outputs import AnalogRamper
from labscript import config, IntermediateDevice, set_passed_properties

import numpy as np

class TeensyDAC(IntermediateDevice):
    allowed_children = [AnalogRamper]

    @set_passed_properties(
        property_names={
            'connection_table_properties': [
                'name',
                'serial_number',
                'dac_cmd_scale',
            ]
        }
    )

    def __init__(self, name, parent_device, serial_number, dac_cmd_scale=2**16/(4.096*2.5), **kwargs):
        IntermediateDevice.__init__(self, name, parent_device, *kwargs)
        self.BLACS_connection = 'TeensyDAC: {}'.format(name)
        self.dac_cmd_scale = dac_cmd_scale

    def add_device(self, device):
        '''Error checking for adding a child device.

        Args:
        	device (AnalogOut): Device to attach. Must be an analog output.
        		Only one allowed, connection must be "output"
        '''
        conn = device.connection

        if conn != 'output':
            raise LabscriptError(f'Invalid channel specification: {conn}')
        if len(self.child_devices) > 0:
            raise LabscriptError(f'TeensyDAC output already connected')

        super().add_device(device)

    def generate_code(self, hdf5_file):
        IntermediateDevice.generate_code(self, hdf5_file)

        clockline = self.parent_device
        times = clockline.parent_device.times[clockline]

        n_timepoints = len(times)
        raw_outputs = self.child_devices[0].raw_output
        raw_outputs = self.child_devices[0].raw_output * self.dac_cmd_scale
        raw_outputs[raw_outputs < 0] = 0
        raw_outputs[raw_outputs > 2**16 - 1] = 2**16 - 1
        output_table = raw_outputs

        group = hdf5_file['devices'].require_group(self.name)
        group.create_dataset('dac_data', data=output_table.astype('<u2'),
                             compression=config.compression)
