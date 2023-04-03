from qtutils.qt.QtWidgets import QWidget, QSpacerItem, QSizePolicy

from blacs.tab_base_classes import Tab
from labscript_utils.qtwidgets.digitaloutput import DigitalOutput, InvertedDigitalOutput
from labscript_utils.qtwidgets.toolpalette import ToolPaletteGroup

class VirtualDeviceTab(Tab):
    def __init__(self, notebook, settings, restart=False):
        Tab.__init__(self, notebook, settings, restart)
        self.connection_table = settings['connection_table']

        self.initialise_GUI()

    def initialise_GUI(self):
        properties = self.connection_table.find_by_name(self.device_name).properties

        self.create_do_widgets(properties['digital_channels'])
        self.create_ao_widgets(properties['analog_channels'])
        self.place_widget_group('Digital Outputs', self.do_widgets)
        self.place_widget_group('Analog Outputs', self.ao_widgets)

    def place_widget_group(self, name, widgets):
        widget = QWidget()
        toolpalettegroup = ToolPaletteGroup(widget)

        if toolpalettegroup.has_palette(name):
            toolpalette = toolpalettegroup.get_palette(name)
        else:
            toolpalette = toolpalettegroup.append_new_palette(name)

        for _, do_widget in self.do_widgets.items():
            toolpalette.addWidget(do_widget, True)

        self.get_tab_layout().addWidget(widget)
        self.get_tab_layout().addItem(QSpacerItem(0,0,QSizePolicy.Minimum,QSizePolicy.MinimumExpanding))

    def create_do_widgets(self, digital_channels):
        self.do_widgets = {}
        for device_name, connection_name, name in digital_channels:
            full_conn_name = '%s.%s' % (device_name, connection_name)
            self.do_widgets[full_conn_name] =  DigitalOutput('%s\n%s' % (name, full_conn_name))
            self.do_widgets[full_conn_name].last_DO = None
            self.do_widgets[full_conn_name].closing = False

    def create_ao_widgets(self, analog_channels):
        self.ao_widgets = {}
        for device_name, connection_name, name in analog_channels:
            full_conn_name = '%s.%s' % (device_name, connection_name)
            self.ao_widgets[full_conn_name] =  AnalogOutput('%s\n%s' % (name, full_conn_name))
            self.ao_widgets[full_conn_name].last_AO = None
            self.ao_widgets[full_conn_name].closing = False
