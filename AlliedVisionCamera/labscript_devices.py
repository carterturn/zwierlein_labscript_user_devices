from labscript import TriggerableDevice, set_passed_properties

from labscript_devices.IMAQdxCamera.labscript_devices import IMAQdxCamera

class AlliedVisionCamera(IMAQdxCamera):
    description = 'Allied Vision Camera'

    @set_passed_properties(
        property_names={
            "connection_table_properties": [
                "legacy_save_folder",
            ],
        }
    )

    def __init__(
            self,
            name,
            parent_device,
            connection,
            serial_number,
            legacy_save_folder=None,
            orientation=None,
            pixel_size=[1.0,1.0],
            magnification=1.0,
            trigger_edge_type='rising',
            trigger_duration=None,
            minimum_recovery_time=0.0,
            camera_attributes=None,
            manual_mode_camera_attributes=None,
            stop_acquisition_timeout=5.0,
            exception_on_failed_shot=True,
            saved_attribute_visibility_level='intermediate',
            mock=False,
            **kwargs
    ):
        IMAQdxCamera.__init__(self, name, parent_device, connection, serial_number, orientation,
                              pixel_size, magnification, trigger_edge_type, trigger_duration,
                              minimum_recovery_time, camera_attributes, manual_mode_camera_attributes,
                              stop_acquisition_timeout, exception_on_failed_shot,
                              saved_attribute_visibility_level, mock, **kwargs)
