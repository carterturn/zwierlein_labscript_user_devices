'''
Copyright 2023-2024, MIT

This file is part of Zwierlein group labscript_user_devices,
and is licensed under the 3-clause BSD License.
See the license.txt file for the full license.
'''

from labscript import AnalogQuantity, TriggerableDevice, set_passed_properties, LabscriptError

import numpy as np
import sys

class RPiDMD(TriggerableDevice):
    allowed_children = []

    @set_passed_properties(
        property_names={
            'connection_table_properties': [
                'name',
                'width',
                'height',
                'host',
                'port',
            ]
        }
    )

    def __init__(self, name, parent_trigger, strobe_gate,
                 width, height, host, port, **kwargs):
        self.trigger_edge_type = parent_trigger.trigger_edge_type
        TriggerableDevice.__init__(self, name, parent_trigger, connection='trigger', **kwargs)
        self.BLACS_connection = 'RPiDMD: {}'.format(name)
        self.strobe_gate = strobe_gate

        self.width = width
        self.height = height
        # List of images
        self.images = []

    def generate_code(self, hdf5_file):
        TriggerableDevice.do_checks(self)

        group = hdf5_file['devices'].require_group(self.name)
        group.create_dataset('dmd_image_data', data=command_array)

    def display_image(self, t, duration, image):
        '''
        Display an image starting at time t.
        DMD will be allowed to flicker from t-20us to t in order for image to update.
        Raspberry Pi will be triggered to update the image at t-30ms to provide time for HDMI

        Args:
        t: Time to switch to new image
        duration: Duration to stop DMD strobe
        image: the image to display. Should be DMD width cols by DMD height rows,
            type uint8 with 0 for an off pixel, 255 for an on pixel.
        '''
        assert (image.shape[0] == self.height and image.shape[1] == self.width), 'Image shape does not match DMD shape'
        assert image.dtype == np.uint8, 'Image type not uint8'
        assert (np.all((image == 0) + (image == 255))), 'Image contains non-binary values'

        self.images.append(image)

        self.trigger(t=t-30e-3, duration=duration/2.)
        self.strobe_gate.go_low(t-20e-6)
        self.strobe_gate.go_high(t)
