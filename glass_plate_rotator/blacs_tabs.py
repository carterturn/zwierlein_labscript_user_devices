from blacs.device_base_class import DeviceTab
from blacs.output_classes import AO, DO
from user_devices import EO

from enum import Enum

GlassPlateRotatorEnumMode = Enum('Mode', ['static', 'motion', 'calibration'])
GlassPlateRotatorEnumFirst = Enum('First', ['upper', 'lower'])

class GlassPlateRotatorTab(DeviceTab):
    def initialise_GUI(self):
        device = self.settings['connection_table'].find_by_name(self.device_name)

        self.com_port = device.properties['com_port']
        self.channel_names = device.properties['channel_names']
        angle_min = device.properties['angle_min']
        angle_max = device.properties['angle_max']

        self._output_sets = {}

        for channel_name in self.channel_names:
            outputs = {}
            outputs['mode'] = EO('mode', device.name, self.device_name,
                                 self.program_device, self.settings, GlassPlateRotatorEnumMode)
            outputs['first'] = EO('first', device.name, self.device_name,
                                  self.program_device, self.settings, GlassPlateRotatorEnumFirst)
            outputs['pos_upper'] = AO('pos_upper', device.name, self.device_name,
                                      self.program_device, self.settings,
                                      None, None, 'deg', angle_min, angle_max, 1, 0)
            outputs['pos_lower'] = AO('pos_upper', device.name, self.device_name,
                                      self.program_device, self.settings,
                                      None, None, 'deg', angle_min, angle_max, 1, 0)
            widgets = {}
            for name, output in outputs.items():
                widgets[name] = output.create_widget()
            self.auto_place_widgets((channel_name, widgets))

            self._output_sets[channel_name] = outputs

        self.supports_remote_value_check(False)
        self.supports_smart_programming(False)

    def initialise_workers(self):
        self.create_worker(
            "main_worker",
            "user_devices.glass_plate_rotator.blacs_workers.GlassPlateRotatorWorker",
            {
                'com_port': self.com_port,
                'channel_names': self.channel_names,
            },
        )
        self.primary_worker = "main_worker"

    def get_front_panel_values(self):
        '''Get values from BLACS tab interface.

        We override this function so that we can return separate arrays for each channel,
        which cleans up the front panel channel names a bit.
        '''
        fpv = {}
        for channel_name in self.channel_names:
            fpv[channel_name] = {name:item.value for name,item
                                 in self._output_sets[channel_name].items()}
        return fpv
