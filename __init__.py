import logging
import math
import sys

__version__ = '0.1.0'
__author__ = ['carterturn']

from qtutils.qt.QtCore import *
from qtutils.qt.QtGui import *
from qtutils.qt.QtWidgets import *

from pylab import *

from labscript import Device, config, Output, set_passed_properties
from labscript_utils.qtwidgets.enumoutput import EnumOutput
from labscript_utils.unitconversions import UnitConversion
import labscript_devices

class EO(object):
    def __init__(self, hardware_name, connection_name, device_name, program_function, settings, enum_class):
        self._connection_name = connection_name
        self._hardware_name = hardware_name
        self._device_name = device_name

        self._locked = False
        self._comboboxmodel = QStandardItemModel()
        self._widget_list = []
        self._program_device = program_function

        self._current_value = None
        self._enum_class = enum_class

        self._logger = logging.getLogger('BLACS.%s.%s'%(self._device_name,hardware_name))

        self._update_from_settings(settings)

    def _update_from_settings(self, settings):
        if not isinstance(settings, dict):
            settings = {}
        if 'front_panel_settings' not in settings or not isinstance(settings['front_panel_settings'], dict):
            settings['front_panel_settings'] = {}
        if self._hardware_name not in settings['front_panel_settings'] or not isinstance(settings['front_panel_settings'][self._hardware_name], dict):
            settings['front_panel_settings'][self._hardware_name] = {}
        # Set default values if they are not already saved in the settings dictionary
        if 'base_value' not in settings['front_panel_settings'][self._hardware_name]:
            settings['front_panel_settings'][self._hardware_name]['base_value'] = None
        if 'locked' not in settings['front_panel_settings'][self._hardware_name]:
            settings['front_panel_settings'][self._hardware_name]['locked'] = False
        if 'name' not in settings['front_panel_settings'][self._hardware_name]:
            settings['front_panel_settings'][self._hardware_name]['name'] = self._connection_name

        # only keep a reference to the part of the settings dictionary relevant to this EO
        self._settings = settings['front_panel_settings'][self._hardware_name]

        # Update the state of the button
        self.set_value(self._settings['base_value'], program=False)

        # Update the lock state
        self._update_lock(self._settings['locked'])

    def create_widget(self, *args, **kwargs):
        inverted = kwargs.pop("inverted", False)
        widget = EnumOutput('%s\n%s'%(self._hardware_name,self._connection_name),*args,**kwargs)
        self.add_widget(widget)

        model = QStandardItemModel()
        for name in self._enum_class._member_names_:
            item = QStandardItem(name)
            item.setData(item, Qt.UserRole)
            model.appendRow(item)
        widget.set_combobox_model(model)

        return widget

    def add_widget(self, widget):
        if widget in self._widget_list:
            return False

        self._widget_list.append(widget)

        widget.set_EO(self, True, False)

        widget.connect_value_change(self.set_value)

        self._update_lock(self._locked)

        return True

    def remove_widget(self, widget, call_set_EO = True, new_EO = None):
        if widget not in self._widget_list:
            # TODO: Make this error better!
            raise RuntimeError('The widget specified was not part of the EO object')
        self._widget_list.remove(widget)

        if call_set_EO:
            widget.set_EO(new_EO, True, True)

        widget.disconnect_value_change()

    @property
    def value(self):
        return self._current_state

    def lock(self):
        self._update_lock(True)

    def unlock(self):
        self._update_lock(False)

    def _update_lock(self, locked):
        self._locked = locked
        for widget in self._widget_list:
            if locked:
                widget.lock(False)
            else:
                widget.unlock(False)

        # update the settings dictionary if it exists, to maintain continuity on tab restarts
        self._settings['locked'] = locked

    def set_value(self, state, program=True):
        # We are programatically setting the state, so break the check lock function logic
        self._current_state = state

        # update the settings dictionary if it exists, to maintain continuity on tab restarts
        self._settings['base_value'] = state

        if program:
            self._logger.debug('program device called')
            self._program_device()

        for widget in self._widget_list:
            if state != widget.selected_option:
                widget.block_combobox_signals()
                widget.selected_option = state
                widget.unblock_combobox_signals()

    @property
    def name(self):
        return self._hardware_name + ' - ' + self._connection_name


class StaticEnumQuantity(Output):
    """Class to use internally to handle modes/other string properties on devices."""
    description = 'static enum quantity'

    @set_passed_properties(property_names={})
    def __init__(self, name, parent_device, connection, enum_class, default_value,
                 unit_conversion_class=None, unit_conversion_parameters=None,
                 static_value=None, **kwargs):
        Output.__init__(self, name, parent_device, connection, **kwargs)

        self.instructions = {}
        self.default_value = default_value
        self._static_value = None
        self.enum_class = enum_class

        return

    def constant(self, value):
        """Set the static value of the quantity

        Args:
        	value to set the quantity to

        Raises:
        	LabscriptError: If the static value has already been set,
        		or the value is not in the list of allowed values.
        """
        if self._static_value == None:
            if not isinstance(value, self.enum_class):
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

class integer_unit(UnitConversion):
    base_unit = '#'

    def __init__(self):
        UnitConversion.__init__(self, None)
