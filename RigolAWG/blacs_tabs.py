from blacs.device_base_class import DeviceTab
from blacs.output_classes import AO
from labscript_utils.qtwidgets import EnumOutput, AnalogOutput
from enums import *

class Rigol4162Tab(DeviceTab):
    def initialise_GUI(self):
        device = self.settings['connection_table'].find_by_name(self.device_name)
        properties = device.properties
        self.access_mode = device.BLACS_connection.split(',').pop(0)
        self.resource_str = device.BLACS_connection.split(',').pop(1)

        self._output_sets = {}

        for channel in [1, 2]:
            outputs = {}
            outputs['state'] = DO('state', device.name, self.device_name,
                                  self.program_device, self.settings)
            outputs['mode'] = EO('mode', device.name, self.device_name,
                                 self.program_device, self.settings, RigolDG4162EnumMode)
            outputs['freq'] = AO('freq', device.name, self.device_name,
                                 self.program_device, self.settings,
                                 None, None, 'Hz', 0, 1e10, 1e3, 5)
            outputs['amplitude'] = AO('amplitude', device.name, self.device_name,
                                      self.program_device, self.settings,
                                      None, None, 'dBm', -30, 30, 1, 2)

            widgets = {}
            widgets['state'] = outputs['state'].create_widget()
            widgets['mode'] = outputs['mode'].create_widget()
            widgets['freq'] = outputs['freq'].create_widget()
            widgets['amplitude'] = outputs['amplitude'].create_widget()

            self.auto_place_widgets(('Channel {}'.format(channel), widgets))

            self._output_sets.append({'channel {}'.format(channel): outputs})

        return

    def initialise_workers(self):
        self.create_worker(
            'main_worker',
            'user_devices.RigolAWG.blacs_workers.Rigol4162Worker',
            {
                'resource_str': self.resource_str,
                'access_mode': self.access_mode,
                'initial_front_panel_values': self.get_front_panel_values()
            },
            )
        self.primary_worker = 'main_worker'
        return

    def get_front_panel_values(self):
        fpv = {}
        for channel in [1, 2]:
            chan_str = 'channel {}'.format(channel)
            fpv[chan_str] = {name:item.value for name,item in self._output_sets[chan_str]}
        return fpv
