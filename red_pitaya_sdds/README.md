Red Pitaya Scriptable DDS
=========================

Overview
--------

`red_pitaya_sdds` provides an interface to (Carter's) Red Pitaya Scriptable DDS.
This device provides two channels of swept RF output (up to `50 MHz`).
It can perform up to `1048576` ramps (per channel). A `1 us` minimum ramp duration is recommended.
The hardware only supports constant output and linear ramps;
the `customramp` function can be used to emulate more complex functions with high precision.

Communication is over Ethernet via an SCPI-like protocol.
Setting a static IP address for the Red Pitaya is recommended.

Trigger is on rising edge. Channels can be independently triggered.

The Red Pitaya code (FPGA hardware design and SCPI-like server) is available at <https://gitlab.com/carterturn/red_pitaya_scriptable_dds>.

Example Connection Table Entry
------------------------------

	Trigger(name='trig_rp_sdds, parent_device=dev_6, connection='port2/line7',
	        trigger_edge_type='rising', default_value=0)
	# Red Pitaya Scriptable DDS
	RedPitayaSDDS(name=rp_sdds_0', parent_device=trig_rp_sdds, ip='192.168.1.174')
