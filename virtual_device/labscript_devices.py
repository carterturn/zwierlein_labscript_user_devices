from labscript import IntermediateDevice, compiler, set_passed_properties

import numpy as np

def serialize_digital_output_list(digital_output_list):
    if digital_output_list:
        return [(c.parent_device.name, c.connection, c.name, c.inverted) for c in output_list]
    else:
        return []

def serialize_analog_output_list(analog_output_list):
    if analog_output_list:
        return [(c.parent_device.name, c.connection, c.name) for c in output_list]
    else:
        return []

class VirtualDevice(IntermediateDevice):
    @set_passed_properties(
        property_names={
            'connection_table_properties': [
                'name',
                'analog_channels',
                'digital_channels',
            ]
        }
    )

    def __init__(self, name, parent_device, analog_channels=None, digital_channels=None):
        IntermediateDevice.__init__(self, name, parent_device)
        self.BLACS_connection = 'Virtual: {}'.format(name)

        self.analog_channels = serialize_analog_output_list(analog_channels)
        self.digital_channels = serialize_digital_output_list(digital_channels)

    def generate_code(self, hdf5_file):
        # Ensure that no code is generated.
        pass
