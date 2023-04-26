Pi Pico and AD9914 RF Generator
===============================

Overview
--------

`AD9914_pico` provides an interface to the Pi Pico controlled AD9914 based RF generator.
This device is designed to provide amplitude and frequency swept RF output.
The hardware only supports constant output and linear ramps,
but can perform up to `4096` ramps with a minimum ramp duration of `10 us`,
so the `customramp` function can be used to emulate more complex functions with high precision.
Due to serial port limitations, programming each ramp takes `1 ms`,
so the number of ramps should be limited to avoid excessive sequence programming times.
The hardware is triggered by a rising edge, which should be provided by a digital output.
An enable or gate digital line is not currently integrated into the device,
and may be provided by an additional digital output.

The Pi Pico code is available at <https://github.mit.edu/Zwierleingroup/pico_ad9914>.

Example Connection Table Entry
------------------------------

	DigitalOut(name='switch_main_rf', parent_device=dev_3, connection='port3/line7',
	           default_value=0)
	Trigger(name='trig_main_rf', parent_device=dev_6, connection='port2/line7',
	        trigger_edge_type='rising', default_value=0)
	# AD9914 RF generator
	AD9914Pico(name='main_rf', parent_device=trig_main_rf, com_port='COM4')
