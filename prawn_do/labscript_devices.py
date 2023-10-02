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

        bits = [0] * 16 # Start with a list of 16 zeros
        for line in self.child_devices:
            # Replace each zero with the list for each output
            bits[int(line.connection, 16)] = line.raw_output
        # Merge list of lists into an array with a single 16 bit integer column
        do_table = np.array(bitfield(bits, dtype=np.uint16))

        group = hdf5_file['devices'].require_group(self.name)
        group.create_dataset('do_data', data=do_table)
