'''
Copyright 2023-2024, MIT

This file is part of Zwierlein group labscript_user_devices,
and is licensed under the 3-clause BSD License.
See the license.txt file for the full license.
'''

from blacs.device_base_class import DeviceTab

class RPiDMDTab(DeviceTab):
    def initialise_GUI(self):
        device = self.settings['connection_table'].find_by_name(self.device_name)

        self.com_port = device.properties['com_port']

        self.supports_remote_value_check(False)
        self.supports_smart_programming(False)

    def initialise_workers(self):
        self.create_worker(
            "main_worker",
            "user_devices.rpi_dmd.blacs_workers.RPiDMDWorker",
            {
                'com_port': self.com_port,
            },
        )
        self.primary_worker = "main_worker"
