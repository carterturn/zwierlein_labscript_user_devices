from blacs.device_base_class import DeviceTab

class AD9914PicoTab(DeviceTab):
    def initialise_GUI(self):
        dds_prop = {'output': {}}
        dds_prop['output']['freq'] = {'base_unit': 'Hz',
                                      'min': 0.0, 'max': 1.2e9,
                                      'step': 1e5, 'decimals': 2}
        dds_prop['output']['amp'] = {'base_unit': 'Arb',
                                     'min': 0.0, 'max': 1.0,
                                     'step': 1./1024., 'decimals': 4}

        self.create_dds_outputs(dds_prop)
        dds_widgets, _, _ = self.auto_create_widgets()
        self.auto_place_widgets(dds_widgets)

        device = self.settings['connection_table'].find_by_name(self.device_name)

        self.com_port = device.properties['com_port']

        self.supports_remote_value_check(False)
        self.supports_smart_programming(False)

    def initialise_workers(self):
        self.create_worker(
            "main_worker",
            "user_devices.AD9914_pico.blacs_workers.AD9914PicoWorker",
            {
                'com_port': self.com_port,
            },
        )
        self.primary_worker = "main_worker"
