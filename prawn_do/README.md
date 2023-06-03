Code for interfacing with a Raspberry Pi Pico used as a basic digital output.
See https://github.mit.edu/Zwierleingroup/prawn_do for the Pi Pico code.

PrawnDO is a cheap, reasonably high performance way to have 16 buffered (in the sequence sense) digital outputs.
Preliminary tests have indicated accurate pulse widths being accurate to +/-100ns (given by the PIO clock frequency, which as of writing is 10MHz).
No tests have yet been performed for trigger to output timing repeatability.
