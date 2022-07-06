from blacs.device_base_class import DeviceTab

class Rigol4162Tab(DeviceTab):
    def initialize_GUI(self):
        device = self.settings['connection_table'].find_by_name(self.device_name)
        self.access_mode = device.BLACS_connection.split(',').pop(0)
        self.resource_str = device.BLACS_connection.split(',').pop(1)

        

        return

    def initialize_workers(self):

        return

