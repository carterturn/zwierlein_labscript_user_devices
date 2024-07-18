Raspberry Pi Controlled DMD
===========================

Overview
--------

`rpi_dmd` provides an interface to the Raspberry Pi controlled DMD.
This has been tested with the DLPC900 + DLP6500 evaluation board combination.
The Pi is used to put the DMD into video mode, then provides frames to the DMD over HDMI.
The Pi should be triggered to advance images.
A separate digital line should be used to freeze the DMD strobe clock (preventing flickering and more precisely gating image changes).
Communication to the Pi is based on ZeroMQ over TCP/IP.

The Raspberry Pi code is available at <https://github.mit.edu/Zwierleingroup/fermi2_RPi_DMD_controller>.

Example Connection Table Entry
------------------------------

	DigitalOut(name='dmd_1_strobe_gate', parent_device=dev_3, connection='port3/line7',
	           default_value=0)
	Trigger(name='trig_dmd_1_pi', parent_device=dev_6, connection='port2/line7',
	        trigger_edge_type='rising', default_value=0)
	rpi_dmd(name='dmd_1_rpi', parent_trigger=trig_dmd_1_pi, strobe_gate=dmd_1_strobe_gate,
	        width=1920, height=1080, host='192.168.1.249', port=8448)
