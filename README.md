User Devices
============

Clone in the userlib of your labscript installation and rename to user_devices.

Current Devices
===============

Pi Pico and AD9914 RF Generator
-------------------------------

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

Rigol AWG
---------

`RigolAWG` provides a labscript interface to the Rigol DG4162 AWG (and similar models).

Tested so far with
-Rigol DG4162
-Rigol DG4102

PrawnDO
-------

`PrawnDO` is a cheap way to have 16 buffered (in the sequence sense) digital outputs using a Raspberry Pi Pico running custom software.

The Pi Pico code is available at <https://github.mit.edu/Zwierleingroup/prawn_do>.
