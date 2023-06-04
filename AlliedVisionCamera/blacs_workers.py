from labscript_devices.IMAQdxCamera.blacs_workers import MockCamera, IMAQdxCameraWorker

class AlliedVisionCamera(object):

    def __init__(self, serial_number):
        global Vimba
        from vimba import Vimba, VimbaCameraError

        self.camera = None
        self.exception_on_failed_shot = True

        with Vimba.get_instance() as vimba:
            try:
                self.camera = vimba.get_camera_by_id('DEV_' + hex(serial_number)[2:].upper())
            except VimbaCameraError as e:
                raise RuntimeError('Failed to open camera {}'.format(serial_number), e)
        if self.camera is None:
            raise RuntimeError('Unable to get instance of Vimba')

    def set_attributes(self, attr_dict):
        with Vimba.get_instance(), self.camera:
            for k, v in attr_dict.items():
                self.camera.get_feature_by_name(k).set(v)

    def set_attribute(self, name, value):
        with Vimba.get_instance(), self.camera:
            self.camera.get_feature_by_name(name).set(value)

    def get_attribute_names(self, visibility_level, writeable_only=True):
        from vimba.feature import CommandFeature
        with Vimba.get_instance(), self.camera:
            return [f.get_name() for f in self.camera.get_all_features()
                    if (1 in f.get_flags()) and (2 in f.get_flags())]

    def get_attribute(self, name):
        with Vimba.get_instance(), self.camera:
            return str(self.camera.get_feature_by_name(name).get())

    def snap(self):
        '''Acquire a single image and return it'''
        with Vimba.get_instance(), self.camera:
            frame = self.camera.get_frame()
        return self._decode_image_data(frame)

    def configure_acquisition(self, continuous=False, bufferCount=None):
        pass

    def grab(self):
        '''Grab last/single image.
        Currently just calls snap.'''
        return self.snap()

    def grab_multiple(self, n_images, images, waitForNextBuffer=True):
        '''Grab n_images into images array during buffered acquistion.'''

        print(f"Acquiring from camera {n_images} images.")
        with Vimba.get_instance(), self.camera:
            image_number = 0
            for frame in self.camera.get_frame_generator(limit=n_images, timeout_ms=60*60*1000):
                image = self._decode_image_data(frame)
                print(f"    {image_number}: Acquire complete")
                image_number += 1
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
