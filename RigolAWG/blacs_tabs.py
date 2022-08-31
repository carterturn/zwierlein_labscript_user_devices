from blacs.device_base_class import DeviceTab
from blacs.output_classes import AO, DO
from labscript_utils.qtwidgets.enumoutput import EnumOutput
from labscript_utils.qtwidgets.analogoutput import AnalogOutput

from user_devices import EO
from user_devices.RigolAWG.rigol_awg_enums import *

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
            outputs['freq_stop'] = AO('freq_stop', device.name, self.device_name,
                                      self.program_device, self.settings,
                                      None, None, 'Hz', 0, 1e10, 1e3, 5)
            outputs['time'] = AO('time', device.name, self.device_name,
                                 self.program_device, self.settings,
                                 None, None, 's', 0, 30, 0.01, 3)
            outputs['time_hold_start'] = AO('time_hold_start', device.name, self.device_name,
                                            self.program_device, self.settings,
                                            None, None, 's', 0, 30, 0.01, 3)
            outputs['time_hold_stop'] = AO('time_hold_stop', device.name, self.device_name,
                                           self.program_device, self.settings,
                                           None, None, 's', 0, 30, 0.01, 3)
            outputs['time_return'] = AO('time_return', device.name, self.device_name,
                                        self.program_device, self.settings,
                                        None, None, 's', 0, 30, 0.01, 3)
            outputs['spacing'] = EO('spacing', device.name, self.device_name,
                                    self.program_device, self.settings,
                                    RigolDG4162EnumSpacing)
            outputs['steps'] = AO('steps', device.name, self.device_name,
                                  self.program_device, self.settings,
                                  None, None, '#', 0, 100, 1, 0)
            outputs['trigger_slope'] = EO('trigger_slope', device.name, self.device_name,
                                          self.program_device, self.settings,
                                          RigolDG4162EnumTriggerSlope)
            outputs['trigger_source'] = EO('trigger_source', device.name, self.device_name,
                                           self.program_device, self.settings,
                                           RigolDG4162EnumTriggerSource)
            outputs['trigger_out'] = EO('trigger_out', device.name, self.device_name,
                                        self.program_device, self.settings,
                                        RigolDG4162EnumTriggerOut)

            widgets = {}
            for name, output in outputs.items():
                widgets[name] = output.create_widget()
            self.auto_place_widgets(('Channel {}'.format(channel), widgets))

            self._output_sets['channel {}'.format(channel)] = outputs

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
            fpv[chan_str] = {name:item.value for name,item in self._output_sets[chan_str].items()}
        return fpv
