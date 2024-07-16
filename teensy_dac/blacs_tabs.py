'''
Copyright 2023-2024, MIT

This file is part of Zwierlein group labscript_user_devices,
and is licensed under the 3-clause BSD License.
See the license.txt file for the full license.
'''

from blacs.device_base_class import DeviceTab

class TeensyDACTab(DeviceTab):
    def initialise_GUI(self):
        ao_prop = {}
        ao_prop['output'] = {'base_unit': 'V',
                             'min': 0.0,
                             'max': 10.0,
                             'step': 0.01,
                             'decimals': 4,
                             }

        self.create_analog_outputs(ao_prop)
        _, ao_widgets, _ = self.auto_create_widgets()
        self.auto_place_widgets(ao_widgets)

        device = self.settings['connection_table'].find_by_name(self.device_name)

        self.serial_number = device.properties['serial_number']

        self.supports_remote_value_check(False)
        self.supports_smart_programming(False)

    def initialise_workers(self):
        self.create_worker(
            "main_worker",
            "user_devices.teensy_dac.blacs_workers.TeensyDACWorker",
            {
                'serial_number': self.serial_number,
            },
        )
        self.primary_worker = "main_worker"
