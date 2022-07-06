from labscript import Device, LabscriptError, set_passed_properties

class RigolDG4162Static(Device):
    def __init__(self, name, parent_device, **kwargs):
        Device.__init__(self, name, parent_device, connection,
                        call_parents_add_device=false, **kwargs)

        self.freq = StaticAnalogQuantity(self.name+'_freq', self, 'freq')
        self.amplitude = StaticAnalogQuantity(self.name+'_amplitude', self, 'amplitude')

        self.parent_device.add(self)

        return

class RigolDG4162Sweep(Device):
    def __init__(self, name, parent_device):
        Device.__init__(self, name, parent_device, connection,
                        call_parents_add_device=false, **kwargs)

        self.freq_start = StaticAnalogQuantity(self.name+'_freq_start', self, 'freq_start')
        self.freq_stop = StaticAnalogQuantity(self.name+'_freq_stop', self, 'freq_stop')
        self.amplitude = StaticAnalogQuantity(self.name+'_amplitude', self, 'amplitude')
        self.time = StaticAnalogQuantity(self.name+'_time', self, 'time')
        self.time_hold_start = StaticAnalogQuantity(self.name+'_time_hold_start', self, 'time_hold_start')
        self.time_hold_stop = StaticAnalogQuantity(self.name+'_time_hold_stop', self, 'time_hold_stop')
        self.time_return = StaticAnalogQuantity(self.name+'_time_return', self, 'time_return')
        self.spacing = StaticStrQuantity(self.name+'_spacing', self, 'spacing', values=['LIN', 'LOG', 'STE'])
        self.steps = StaticAnalogQuantity(self.name+'_steps', self, 'steps')
        self.trigger_slope = StaticStrQuantity(self.name+'_trigger_slope', self, 'trigger_slope', values=['POS', 'NEG'])
        self.trigger_source = StaticStrQuantity(self.name+'_trigger_source', self, 'trigger_source', values=['EXT', 'INT', 'MAN'])
        self.trigger_out = StaticStrQuantity(self.name+'_trigger_out', self, 'trigger_out', values=['OFF', 'POS', 'NEG'])

        self.parent_device.add(self)

class RigolDG4162(IntermediateDevice):
    """A labscript_device for the Rigol DG4162 arbitrary waveform generator
          connection_table_properties (set once)
          termination: character signalling end of response
          resource_str: IP address or USBTMC name
          access_mode: 'eth' or 'usb'

          device_properties (set per shot)
          timeout: in seconds for response to queries over visa interface
    """
    description = 'Rigol DG4162 arbitrary waveform generator'

    @set_passed_properties(
        property_names = {
            'connection_table_properties': ['termination', 'resource_str', 'access_mode'],
            'device_properties': ['timeout']}
        )
    def __init__(self, name, addr, 
                 termination='\n', resource_str=None, access_mode=None,
                 timeout=5,
                 **kwargs):
        Device.__init__(self, name, None, **kwargs)
        self.name = name
        self.BLACS_connection = access_mode + ',' + resource_str
        self.termination = termination
        assert access_mode in ['eth', 'usb'], "Access mode must be one of 'eth' (Ethernet) or 'usb' (USB)"

    def generate_code(self, hdf5_file):
        # group = self.init_device_name(hdf5_file)
        IntermediateDevice.generate_code(self, hdf5_file)
        group = self.init_device_group(hdf5_file)
        for channel in self.child_devices:
            
