'''
Copyright 2023-2024, MIT

This file is part of Zwierlein group labscript_user_devices,
and is licensed under the 3-clause BSD License.
See the license.txt file for the full license.
'''

from blacs.device_base_class import DeviceTab

class RedPitayaSDDSTab(DeviceTab):
    def initialise_GUI(self):
        dds_prop = {'A': {}, 'B': {}}
        dds_prop['A']['freq'] = {'base_unit': 'Hz',
                                 'min': 0.0, 'max': 50e6,
                                 'step': 1e6, 'decimals': 2}
        dds_prop['A']['amp'] = {'base_unit': 'Arb',
                                'min': 0.0, 'max': 1.0,
                                'step': 1./100., 'decimals': 4}
        dds_prop['B']['freq'] = {'base_unit': 'Hz',
                                 'min': 0.0, 'max': 50e6,
                                 'step': 1e6, 'decimals': 2}
        dds_prop['B']['amp'] = {'base_unit': 'Arb',
                                'min': 0.0, 'max': 1.0,
                                'step': 1./100., 'decimals': 4}

        self.create_dds_outputs(dds_prop)
        dds_widgets, _, _ = self.auto_create_widgets()
        self.auto_place_widgets(dds_widgets)

        device = self.settings['connection_table'].find_by_name(self.device_name)

        self.ip = device.properties['ip']

        self.supports_remote_value_check(False)
        self.supports_smart_programming(False)

    def initialise_workers(self):
        self.create_worker(
            "main_worker",
            "user_devices.red_pitaya_sdds.blacs_workers.RedPitayaSDDSWorker",
            {
                'ip': self.ip,
            },
        )
        self.primary_worker = "main_worker"
