from user_devices.RigolAWG.rigol_awg_enums import *
from user_devices.RigolAWG.labscript_devices import RigolDG4162

trigger_device = None # TODO: setup a trigger
RigolDG4162(name='test_rf', channel_1_trigger=trigger_device, channel_2_trigger=None,
            resource_str='USB0::0x1AB1::0x0641::DG4E160800425::INSTR', access_mode='usb')

start()
t = 0

t = t + 0.1

test_rf.channel_1.sweep_output(t, 1.0, 2000., 10000., 0.01)

t = t + 0.2

stop(t=t)
