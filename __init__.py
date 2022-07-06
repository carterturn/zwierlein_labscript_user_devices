import labscript_devices

__version__ = '0.1.0'
__author__ = ['carterturn']

from labscript import Device

class StaticStrQuantity(Device):
    """Class to use internally to handle modes/other string properties on devices."""

    @set_passed_properties(property_names={})
    def __init__(self, name, parent_device, connection, values=None,
                 unit_conversion_class=None, unit_conversion_parameters=None,
                 static_value=None, **kwargs):
        Device.__init__(self, name, parent_device, connection, **kwargs)

        self.instructions = {}
        self.default_value = default_value
        self._static_value = None
        self.values = values

        return

    def constant(self, value):
        """Set the static value of the quantity

        Args:
        	value (str): value to set the quantity to

        Raises:
        	LabscriptError: If the static value has already been set,
        		or the value is not in the list of allowed values.
        """
        if self._static_value == None:
            if value not in self.values:
                raise LabscriptError('You cannot program the value %s to %s as it is not a valid value'%(str(value), self.name))
            self._static_value = value
        else:
            raise LabscriptError('%s has already been set to %s. It cannot also be set to %s.'%(self.name, str(self._static_value), str(value)))

        return

    def get_change_times(self):
        """Enforces that static value has no change times.

        Returns:
        	list: An empty list.
        """
        return []

    def make_timeseries(self, change_times):
        """Since static, does nothing."""
        return

    def expand_timeseries(self, *args, **kwargs):
        """Defines the raw_value attribute."""
        self.raw_value = array([self.static_value], dtype=str)

        return

    @property
    def static_value(self):
        """str: the static value of the quantity."""
        if self._static_value is None:
            if not config.suppress_mild_warnings and not config.suppress_all_warnings:
                sys.stderr.write(' '.join(['WARNING:', self.name, 'has no value set. It will be set to %s.\n'%self.instruction_to_string(self.default_value)]))
            self._static_value = self.default_value
        return self._static_value
