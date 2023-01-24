from labscript_devices.IMAQdxCamera.blacs_workers import MockCamera, IMAQdxCameraWorker

class AlliedVisionCamera(object):

    def __init__(self, serial_number):
        import os
        os.environ['VIMBA_HOME'] = self.vimba_home
        global Vimba
        from vimba import Vimba, VimbaCameraError

        self.camera = None
        self.attributes = self.camera.default_acquisition_attrs
        self.exception_on_failed_shot = True

        with Vimba.get_instance() as vimba:
            try:
                self.camera = vimba.get_camera_by_id(serial_number)
            except VimbaCameraError as e:
                raise RuntimeError('Failed to open camera {}'.format(serial_number), e)
        if self.camera is None:
            raise RuntimeError('Unable to get instance of Vimba')

    def set_attributes(self, attr_dict):
        for k, v in attr_dict.items():
            self.set_attribute(k, v)

    def set_attribute(self, name, value):
        with Vimba.get_instance(), self.camera:
            self.camera.get_feature_by_name(name).set(value)

    def get_attribute_names(self, visibility_level, writeable_only=True):
        with Vimba.get_instance(), self.camera:
            return [feature.get_name() for feature in self.camera.get_all_features()]

    def get_attribute(self, name):
        with Vimba.get_instance(), self.camera:
            return self.camera.get_feature_by_name(name).get()

    def snap(self):
        '''Acquire a single image and return it'''
        frame = self.camera.get_frame()
        return self._decode_image_data(frame)

    def configure_acquisition(self, continuous=False, bufferCount=None):
        self.camera.setup_acquisition(self.attributes)

    def grab(self):
        '''Grab last/single image.
        Currently just calls snap.'''
        return self.snap()

    def grab_multiple(self, n_images, images, waitForNextBuffer=True):
        '''Grab n_images into images array during buffered acquistion.'''

        printf(f"Acquiring from camera {n_images} images.")
        for image_number in range(n_images):
            image = self.camera.grab()
            print(f"    {image_number}: Acquire complete")
            images.append(image)

    def stop_acquisition(self):
        pass

    def abort_acquisition(self):
        pass

    def _decode_image_data(self, frame):
        # Assume single channel image
        return frame.as_numpy_ndarray()[:,:,0]

    def close(self):
        pass

class AlliedVisionCameraWorker(IMAQdxCameraWorker):
    # N.B. We use the camera server architecture from IMAQdxCamera,
    # but the interface is entirely based on the Allied Vision API.
    interface_class = AlliedVisionCamera
