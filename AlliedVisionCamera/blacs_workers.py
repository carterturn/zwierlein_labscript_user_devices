from labscript_devices.IMAQdxCamera.blacs_workers import MockCamera, IMAQdxCameraWorker

class AlliedVisionCamera(object):

    def __init__(self, serial_number):
        global Vimba
        from vimba import Vimba, VimbaCameraError

        self.camera = None
        self.exception_on_failed_shot = True

        with Vimba.get_instance() as vimba:
            try:
                self.camera = vimba.get_camera_by_id('DEV_' + hex(serial_number).upper())
            except VimbaCameraError as e:
                try:
                    self.camera = vimba.get_camera_by_id('DEV_' + hex(serial_number)[2:].upper())
                except VimbaCameraError as e:
                    raise RuntimeError('Failed to open camera {}'.format(serial_number), e)
        if self.camera is None:
            raise RuntimeError('Unable to get instance of Vimba')

    def set_attributes(self, attr_dict):
        with Vimba.get_instance(), self.camera:
            for k, v in attr_dict.items():
                print('get_feature_by_name({}).set({})'.format(k, v))
                self.camera.get_feature_by_name(k).set(v)

    def set_attribute(self, name, value):
        with Vimba.get_instance(), self.camera:
            print('get_feature_by_name(name).set(value)')
            self.camera.get_feature_by_name(name).set(value)

    def get_attribute_names(self, visibility_level, writeable_only=True):
        from vimba.feature import CommandFeature
        with Vimba.get_instance(), self.camera:
            print('self.camera.get_all_features()')
            return [f.get_name() for f in self.camera.get_all_features()
                    if (1 in f.get_flags()) and (2 in f.get_flags())]

    def get_attribute(self, name):
        with Vimba.get_instance(), self.camera:
            print('get_feature_by_name(name).get()')
            return str(self.camera.get_feature_by_name(name).get())

    def snap(self):
        '''Acquire a single image in manual mode and return it'''
        return self.grab()

    def configure_acquisition(self, continuous=True, bufferCount=None):
        pass

    def grab(self):
        '''Acquire a single image and return it'''
        with Vimba.get_instance(), self.camera:
            print('get_frame()')
            frame = self.camera.get_frame()
        return self._decode_image_data(frame)

    def grab_multiple(self, n_images, images, waitForNextBuffer=True):
        '''Grab n_images into images array during buffered acquistion.'''

        print(f"Acquiring from camera {n_images} images.")
        with Vimba.get_instance(), self.camera:
            image_number = 0
            print('get_frame_generator(limit=n_images, timeout_ms=60*60*1000):')
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
    def get_camera(self):
        # Allied Vision firewire cameras do not reliably set attributes,
        # so we will hide the manual mode attributes and only apply them
        # when actually using the camera in manual mode.
        self._manual_mode_attributes = self.manual_mode_camera_attributes
        self.manual_mode_camera_attributes = self.camera_attributes

        return AlliedVisionCamera(self.serial_number)

    def snap(self):
        self.set_attributes_smart(self._manual_mode_attributes)
        super().snap()

    def start_continuous(self, dt):
        self.set_attributes_smart(self._manual_mode_attributes)
        super().start_continuous(dt)
