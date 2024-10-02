'''
Copyright 2023-2024, MIT

This file is part of Zwierlein group labscript_user_devices,
and is licensed under the 3-clause BSD License.
See the license.txt file for the full license.
'''

from labscript import DDS, StaticDDS, IntermediateDevice, TriggerableDevice, set_passed_properties, LabscriptError, config, Trigger
from labscript_utils.unitconversions import NovaTechDDS9mFreqConversion, NovaTechDDS9mAmpConversion


import numpy as np
import sys

class AD9959EvalDDS(TriggerableDevice):
    description = 'Pi Pico AD9959 Eval Board DDS device'

    # default specs assuming 125MHz system clock
    clock_resolution = 8e-9
    "Minimum resolvable unit of time, corresponsd to system clock period."
    minimum_duration = 10e-6
    "Minimum time between updates on the outputs."
    wait_delay = 50e-9
    "Minimum required length of wait before a retrigger can be detected."
    input_response_time = 50e-9
    "Time between hardware trigger and output starting."
    trigger_delay = 50e-9
    trigger_minimum_duration = 160e-9
    "Minimum required duration of hardware trigger. A fairly large over-estimate."

    allowed_children = [DDS, StaticDDS]

    max_instructions = 4032
    """Maximum number of instructions. Set by zmq timeout when sending the commands."""

    @set_passed_properties(
        property_names={
            'connection_table_properties': [
                'name',
                'com_port',
            ]
        }
    )

    def __init__(self, name, trigger_device=None, trigger_connection=None, clock_line=None,
                 com_port='COM1', **kwargs):
        '''Labscript device class for AD9959 eval board controlled by a Raspberry Pi Pico.
        '''
        if clock_line is not None and trigger_device is not None:
            raise LabscriptError("Provide only a trigger_device or a clock_line, not both")
        if clock_line is not None:
            # make internal Intermediate device and trigger to connect it
            self.__intermediate = _AD9959EvalDDSIntermediateDevice(f'{name:s}__intermediate',
                                                                   clock_line)
            TriggerableDevice.__init__(self, name, self.__intermediate, 'internal')
        else:
            # normal device triggering
            TriggerableDevice.__init__(self, name, trigger_device, trigger_connection)

        self.BLACS_connection = '%s' % com_port

        self.clk_scale = 2**32

        self._initial_trigger_time = 0

    # following three defs ensure initial_trigger_time is not modified
    # when directly triggered from a clockline using an internal IntermediateDevice
    @property
    def initial_trigger_time(self):
        return self._initial_trigger_time

    @initial_trigger_time.setter
    def initial_trigger_time(self, value):
        if value != 0 and hasattr(self, "__intermediate"):
            raise LabscriptError("You cannot set the initial trigger time when the AD9959EvalDDS is directly triggered by a clockline")
        self._initial_trigger_time = value

    def set_initial_trigger_time(self, *args, **kwargs):
        if hasattr(self, "__intermediate"):
            raise LabscriptError("You cannot set the initial trigger time when the AD9959EvalDDS is directly triggered by a clockline")
        return super().set_initial_trigger_time(*args, **kwargs)

    def get_default_unit_conversion_classes(self, device):
        """Child devices call this during their __init__ (with themselves
        as the argument) to check if there are certain unit calibration
        classes that they should apply to their outputs, if the user has
        not otherwise specified a calibration class"""
        if device.connection in ['channel 0', 'channel 1', 'channel 2', 'channel 3']:
            # Default calibration classes for the non-static channels:
            return NovaTechDDS9mFreqConversion, NovaTechDDS9mAmpConversion, None
        else:
            return None, None, None

    def quantise_freq(self, data, device):
        """Provides bounds error checking and scales input values to instrument
        units (0.1 Hz) before ensuring uint32 integer type."""
        if not isinstance(data, np.ndarray):
            data = np.array(data)
        # Ensure that frequencies are within bounds:
        if np.any(data > 250e6) or np.any(data < 0.0):
            raise LabscriptError('%s %s ' % (device.description, device.name) +
                              'can only have frequencies between 0.0Hz and 250MHz, ' + 
                              'the limit imposed by %s.' % self.name)
        scale_factor = self.clk_scale # Need to multiply by clk scale factor

        # It's faster to add 0.5 then typecast than to round to integers first:
        data = np.array((scale_factor*data)+0.5,dtype=np.uint32)
        return data, scale_factor
        
    def quantise_phase(self, data, device):
        """Ensures phase is wrapped about 360 degrees and scales to instrument
        units before type casting to uint16."""
        if not isinstance(data, np.ndarray):
            data = np.array(data)
        # ensure that phase wraps around:
        data %= 360
        # It's faster to add 0.5 then typecast than to round to integers first:
        scale_factor = 16384/360.0
        data = np.array((scale_factor*data)+0.5,dtype=np.uint16)
        return data, scale_factor
        
    def quantise_amp(self,data,device):
        """Ensures amplitude is within bounds and scales to instrument units
        (between 0 and 1023) before typecasting to uint16"""
        if not isinstance(data, np.ndarray):
            data = np.array(data)
        # ensure that amplitudes are within bounds:
        if np.any(data > 1 )  or np.any(data < 0):
            raise LabscriptError('%s %s ' % (device.description, device.name) +
                              'can only have amplitudes between 0 and 1 (Volts peak to peak approx), ' + 
                              'the limit imposed by %s.' % self.name)
        # It's faster to add 0.5 then typecast than to round to integers first:
        data = np.array((1023*data)+0.5,dtype=np.uint16)
        scale_factor = 1023
        return data, scale_factor

    def generate_code(self, hdf5_file):
        # Find times at which something occurs
        all_change_times = []
        for dds in self.child_devices:
            for output in dds.child_devices:
                all_change_times.extend(output.get_change_times())
        if len(all_change_times) == 0:
            # No outputs, skip
            return
        all_change_times.extend(self.pseudoclock_device.trigger_times)
        all_change_times.append(self.pseudoclock_device.stop_time)
        all_change_times = sorted(list(set(all_change_times)))

        DDSs = {}
        for dds in self.child_devices:
            # Since we are using internal timing, expand timeseries here
            for output in dds.child_devices:
                output.make_timeseries(all_change_times)
                output.expand_timeseries(all_change_times, len(all_change_times))
           # Check that the instructions will fit into RAM:
            if isinstance(dds, DDS) and len(dds.frequency.raw_output) > self.max_instructions - 2: # -2 to include space for dummy instructions
                raise LabscriptError('%s can only support 4030 instructions. ' % self.name +
                                     'Please decrease the sample rates of devices on the same clock, ' + 
                                     'or connect %s to a different pseudoclock.' % self.name)
            try:
                prefix, channel = dds.connection.split()
                channel = int(channel)
            except:
                raise LabscriptError('%s %s has invalid connection string: \'%s\'. ' % (dds.description,dds.name,str(dds.connection)) + 
                                     'Format must be \'channel n\' with n from 0 to 4.')
            DDSs[channel] = dds

        if not DDSs:
            # if no channels are being used, no need to continue
            return            

        for connection in DDSs:
            if connection in range(4):
                dds = DDSs[connection]   
                dds.frequency.raw_output, dds.frequency.scale_factor = self.quantise_freq(dds.frequency.raw_output, dds)
                dds.phase.raw_output, dds.phase.scale_factor = self.quantise_phase(dds.phase.raw_output, dds)
                dds.amplitude.raw_output, dds.amplitude.scale_factor = self.quantise_amp(dds.amplitude.raw_output, dds)
            else:
                raise LabscriptError('%s %s has invalid connection string: \'%s\'. ' % (dds.description,dds.name,str(dds.connection)) + 
                                     'Format must be \'channel n\' with n from 0 to 4.')

        dtypes = {'names':['freq%d' % i for i in DDSs] +
                  ['amp%d' % i for i in DDSs] +
                  ['phase%d' % i for i in DDSs] +
                  ['duration'],
                  'formats':[np.float for i in DDSs] +
                  [np.float for i in DDSs] +
                  [np.float for i in DDSs] +
                  [np.float]}

        out_table = np.zeros(len(all_change_times), dtype=dtypes)

        for i, dds in DDSs.items():
            out_table['freq%d' % i][:] = dds.frequency.raw_output
            out_table['amp%d' % i][:] = dds.amplitude.raw_output
            out_table['phase%d' % i][:] = dds.phase.raw_output

        all_change_times = np.array(all_change_times)
        # Setup trigger waits
        durations = np.rint(np.diff(all_change_times)/self.clock_resolution).astype(np.uint32)
        durations = np.concatenate([durations, [0]]) # Add final wait (as stop)
        for trigger_time in self.pseudoclock_device.trigger_times:
            if trigger_time == 0:
                # Already wait for trigger at start
                continue
            durations[all_change_times == trigger_time] = 0
        out_table['duration'][:] = durations

        print(out_table)
        # write out data tables
        grp = self.init_device_group(hdf5_file)
        grp.create_dataset('dds_data', compression=config.compression, data=out_table)
        self.set_property('frequency_scale_factor', dds.frequency.scale_factor, location='device_properties')
        self.set_property('amplitude_scale_factor', dds.amplitude.scale_factor, location='device_properties')
        self.set_property('phase_scale_factor', dds.phase.scale_factor, location='device_properties')

class _AD9959EvalDDSIntermediateDevice(IntermediateDevice):
    description = "AD9959EvalDDS Internal Intermediate Device"

    allowed_children = [Trigger]
