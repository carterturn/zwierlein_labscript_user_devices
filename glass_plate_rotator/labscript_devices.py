from labscript import Device, set_passed_properties

import numpy as np

class GlassPlateRotator(Device):

    @set_passed_properties(
        property_names={
            'connection_table_properties': [
                'com_port',
                'channel_names',
                'inverted',
                'angle_min',
                'angle_max',
            ]
        }
    )

    def __init__(self, name, com_port, channel_names, inverted=None,
                 angle_min=-60, angle_max=60, **kwargs):
        Device.__init__(self, name, None, connection=com_port)
        self.BLACS_connection = 'Glass Plate Rotator: {}'.format(name)
        self.positions = {}
        for channel_name in channel_names:
            self.positions[channel_name] = [0, 0]

    def generate_code(self, hdf5_file):
        Device.generate_code(self, hdf5_file)

        dtypes = ([('{} upper'.format(cn), int) for cn in self.positions.keys()]
                  + [('{} lower'.format(cn), int) for cn in self.positions.keys()])
        positions_array = np.empty(1, dtype=dtypes)
        for channel_name in self.positions.keys():
            positions_array['{} upper'.format(channel_name)] = self.positions[channel_name][0]
            positions_array['{} lower'.format(channel_name)] = self.positions[channel_name][1]

        group = hdf5_file['devices'].require_group(self.name)
        group.create_dataset('rotator_data', data=positions_array)

    def set_upper(self, channel_name, angle):
        if channel_name not in self.positions.keys():
            raise NameError('{} is not a valid channel name for GlassPlateRotator {}'
                            .format(channel_name, self.name))

        self.positions[channel_name][0] = angle

    def set_lower(self, channel_name, angle):
        if channel_name not in self.positions.keys():
            raise NameError('{} is not a valid channel name for GlassPlateRotator {}'
                            .format(channel_name, self.name))

        self.positions[channel_name][1] = angle
