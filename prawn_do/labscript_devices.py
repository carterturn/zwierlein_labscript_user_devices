from labscript import IntermediateDevice, DigitalOut, bitfield, set_passed_properties

import numpy as np

class PrawnDO(IntermediateDevice):
    allowed_children = [DigitalOut]

    @set_passed_properties(
        property_names={
            'connection_table_properties': [
                'name',
                'com_port',
            ]
        }
    )

    def __init__(self, name, parent_device, com_port, **kwargs):
        IntermediateDevice.__init__(self, name, parent_device, **kwargs)
        self.BLACS_connection = 'PrawnDO: {}'.format(name)

    def generate_code(self, hdf5_file):
        IntermediateDevice.generate_code(self, hdf5_file)

        times = self.parent_device.parent_device.times[self.parent_device]
        bits = [0] * 16
        for line in self.child_devices:
            bits[int(line.connection, 16)] = line.raw_output
        do_table = np.array(bitfield(bits, dtype=np.uint16))

        group = hdf5_file['devices'].require_group(self.name)
        group.create_dataset('do_data', data=do_table)
