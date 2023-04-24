from user_devices.RigolAWG.rigol_awg_enums import *
from user_devices.RigolAWG.labscript_devices import RigolDG4162

trigger_device = None # TODO: setup a trigger
RigolDG4162(name='test_rf', parent_device=trigger_device,
            resource_str='USB0::0x1AB1::0x0641::DG4E160800425::INSTR', access_mode='usb')

start()
t = 0

test_rf.channels[0]['state'].go_high()
test_rf.channels[0]['mode'].constant(RigolDG4162EnumMode.sweep)
test_rf.channels[0]['freq'].constant(2000.)
test_rf.channels[0]['freq_stop'].constant(10000.)
test_rf.channels[0]['spacing'].constant(RigolDG4162EnumSpacing.LIN)
test_rf.channels[0]['steps'].constant(100)
test_rf.channels[0]['time'].constant(0.01)
test_rf.channels[0]['trigger_slope'].constant(RigolDG4162EnumTriggerSlope.POS)
test_rf.channels[0]['trigger_source'].constant(RigolDG4162EnumTriggerSource.EXT)

t = t + 0.1
test_rf.trigger(t, 1e-4)

t = t + 0.2

stop(t=t)
