from blacs.tab_base_classes import Worker
import numpy as np
from labscript_utils import dedent
import labscript_utils.h5_lock
import h5py
import labscript_utils.properties
import zmq
import os
from labscript_utils.shared_drive import path_to_local

from labscript_utils.ls_zprocess import Context

class AlliedVisionCameraWorker(Worker):
    '''
    Worker for an Allied Vision camera, using the Vimba API.

    Compatible with the IMAQdxCamera BLACS tab.
    
    The Vimba API works quite well with callbacks, and thus does not require separate threads.
    Furthermore, we can avoid acquiring the camera when it is not used,
    which allows other programs (such as Vimba Viewer to use cameras that we are not capturing from).
    '''

    def init(self):
        global Vimba
        from vimba import Vimba, VimbaCameraError

        if self.legacy_save_folder is not None:
            global fits
            from astropy.io import fits
            global datetime
            import datetime

        self.camera = None

        self.vimba = Vimba.get_instance()
        self.vimba.__enter__()

        try:
            self.camera = self.vimba.get_camera_by_id('DEV_' + hex(self.serial_number).upper())
        except VimbaCameraError as e:
            try:
                self.camera = self.vimba.get_camera_by_id('DEV_' + hex(self.serial_number)[2:].upper())
            except VimbaCameraError as e:
                raise RuntimeError('Failed to open camera {}'.format(self.serial_number), e)
        if self.camera is None:
            raise RuntimeError('Unable to get instance of Vimba')

        self.camera.active = False

        print("Setting attributes...")
        self.smart_cache = {}
        with self.camera:
            self.camera.active = True
            self.set_attributes_smart(self.camera_attributes)
            self.set_attributes_smart(self.manual_mode_camera_attributes)
        self.camera.active = False
        print("Initialisation complete")
        self.images = None
        self.n_images = None
        self.exposures = None
        self.acquisition_thread = None
        self.h5_filepath = None
        self.stop_acquisition_timeout = None
        self.image_socket = Context().socket(zmq.REQ)
        self.image_socket.connect(
            f'tcp://{self.parent_host}:{self.image_receiver_port}'
        )

    def set_attributes_smart(self, attributes):
        '''Call self.camera.set_attributes() to set the given attributes, only setting
        those that differ from their value in, or are absent from self.smart_cache.
        Update self.smart_cache with the newly-set values'''
        if not self.camera.active:
            raise RuntimeError('Camera not active, can not set_attributes_smart')
        uncached_attributes = {}
        for name, value in attributes.items():
            if name not in self.smart_cache or self.smart_cache[name] != value:
                uncached_attributes[name] = value
                self.smart_cache[name] = value
        for k, v in uncached_attributes.items():
            self.camera.get_feature_by_name(k).set(v)

    def get_attributes_as_dict(self, visibility_level):
        '''Return a dict of the attributes of the camera for the given visibility
        level'''
        if not self.camera.active:
            raise RuntimeError('Camera not active, can not get_attributes_as_dict')
        names = [f.get_name() for f in self.camera.get_all_features()
                 if (1 in f.get_flags()) and (2 in f.get_flags())]
        attributes_dict = {name: str(self.camera.get_feature_by_name(name).get()) for name in names}
        return attributes_dict

    def get_attributes_as_text(self, visibility_level):
        '''Return a string representation of the attributes of the camera for
        the given visibility level'''
        attrs = self.get_attributes_as_dict(visibility_level)
        # Format it nicely:
        lines = [f'    {repr(key)}: {repr(value)},' for key, value in attrs.items()]
        dict_repr = '\n'.join(['{'] + lines + ['}'])
        return self.device_name + '_camera_attributes = ' + dict_repr

    def _decode_image_data(self, frame):
        # Assume single channel image
        return frame.as_numpy_ndarray()[:,:,0]

    def _send_image_to_parent(self, image):
        '''Send the image to the GUI to display. This will block if the parent process
        is lagging behind in displaying frames, in order to avoid a backlog.'''
        metadata = dict(dtype=str(image.dtype), shape=image.shape)
        self.image_socket.send_json(metadata, zmq.SNDMORE)
        self.image_socket.send(image, copy=False)
        response = self.image_socket.recv()
        assert response == b'ok', response

    def snap(self):
        '''Acquire one frame in manual mode. Send it to the parent via
        self.image_socket. Wait for a response from the parent.'''
        self.camera.__enter__()
        self.camera.active = True
        self.set_attributes_smart(self.manual_mode_camera_attributes)
        self.camera.AcquisitionMode.set('SingleFrame')
        frame = self.camera.get_frame()
        self.camera.__exit__(None, None, None)
        self.camera.active = False
        self._send_image_to_parent(self._decode_image_data(frame))

    def _handle_send_frame_to_parent(self, camera, frame):
        image = self._decode_image_data(frame)
        camera.queue_frame(frame)
        self._send_image_to_parent(image)

    def start_continuous(self, dt):
        '''Begin continuous acquisition through asynchronous streaming'''
        self.camera.__enter__()
        self.camera.active = True
        self.set_attributes_smart(self.manual_mode_camera_attributes)
        self.camera.AcquisitionMode.set('Continuous')
        if self.camera.is_streaming():
            raise RuntimeError('Camera already streaming, can not start_continuous')
        self.camera.start_streaming(handler=self._handle_send_frame_to_parent, buffer_count=10)

    def stop_continuous(self, pause=False):
        '''Stop the continuous acquisition'''
        if self.camera.is_streaming():
            self.camera.stop_streaming()
        if self.camera.active:
            self.camera.__exit__(None, None, None)
            self.camera.active = False

    def _handle_add_frame_to_images(self, camera, frame):
        self.images.append(self._decode_image_data(frame))
        camera.queue_frame(frame)

    def transition_to_buffered(self, device_name, h5_filepath, initial_values, fresh):
        if getattr(self, 'is_remote', False):
            h5_filepath = path_to_local(h5_filepath)
        if self.camera.active:
            if self.camera.is_streaming():
                self.camera.stop_streaming()
        with h5py.File(h5_filepath, 'r') as f:
            group = f['devices'][self.device_name]
            if not 'EXPOSURES' in group:
                return {}
            self.h5_filepath = h5_filepath
            self.exposures = group['EXPOSURES'][:]
            self.n_images = len(self.exposures)

            # Get the camera_attributes from the device_properties
            properties = labscript_utils.properties.get(
                f, self.device_name, 'device_properties'
            )
            camera_attributes = properties['camera_attributes']
            self.stop_acquisition_timeout = properties['stop_acquisition_timeout']
        # Only reprogram attributes that differ from those last programmed in, or all of
        # them if a fresh reprogramming was requested:
        if fresh:
            self.smart_cache = {}
        if self.n_images > 0: # Only acquire and lock camera if it will be used this shot
            self.camera.__enter__()
            self.camera.active = True
            self.set_attributes_smart(camera_attributes)
            print(f"Configuring camera for {self.n_images} images.")
            self.camera.AcquisitionMode.set('MultiFrame')
            self.camera.AcquisitionFrameCount.set(self.n_images)
            self.images = []
            print(f"Camera armed.")
            self.camera.start_streaming(handler=self._handle_add_frame_to_images,
                                        buffer_count=self.n_images)
        return {}

    def transition_to_manual(self):
        if self.h5_filepath is None:
            print('No camera exposures in this shot.\n')
            return True

        print("Stopping acquisition.")
        if self.camera.active:
            if self.camera.is_streaming():
                self.camera.stop_streaming()
            self.camera.__exit__(None, None, None)
            self.camera.active = False

        print(f"Saving {len(self.images)}/{len(self.exposures)} images.")

        with h5py.File(self.h5_filepath, 'r+') as f:
            # Use orientation for image path, device_name if orientation unspecified
            if self.orientation is not None:
                image_path = 'images/' + self.orientation
            else:
                image_path = 'images/' + self.device_name
            image_group = f.require_group(image_path)
            image_group.attrs['camera'] = self.device_name

            # Whether we failed to get all the expected exposures:
            image_group.attrs['failed_shot'] = len(self.images) != len(self.exposures)

            # key the images by name and frametype. Allow for the case of there being
            # multiple images with the same name and frametype. In this case we will
            # save an array of images in a single dataset.
            images = {
                (exposure['name'], exposure['frametype']): []
                for exposure in self.exposures
            }

            # Iterate over expected exposures, sorted by acquisition time, to match them
            # up with the acquired images:
            self.exposures.sort(order='t')
            for image, exposure in zip(self.images, self.exposures):
                images[(exposure['name'], exposure['frametype'])].append(image)

            # Save images to the HDF5 file:
            for (name, frametype), imagelist in images.items():
                data = imagelist[0] if len(imagelist) == 1 else np.array(imagelist)
                print(f"Saving frame(s) {name}/{frametype}.")
                group = image_group.require_group(name)
                dset = group.create_dataset(
                    frametype, data=data, dtype='uint16', compression='gzip'
                )
                # Specify this dataset should be viewed as an image
                dset.attrs['CLASS'] = np.string_('IMAGE')
                dset.attrs['IMAGE_VERSION'] = np.string_('1.2')
                dset.attrs['IMAGE_SUBCLASS'] = np.string_('IMAGE_GRAYSCALE')
                dset.attrs['IMAGE_WHITE_IS_ZERO'] = np.uint8(0)

        # If the images are all the same shape, send them to the GUI for display:
        try:
            image_block = np.stack(self.images)
        except ValueError:
            print("Cannot display images in the GUI, they are not all the same shape")
        else:
            self._send_image_to_parent(image_block)

        if self.legacy_save_folder is not None:
            filename = datetime.datetime.now().strftime('%Y-%m-%d-%H;%M;%S') + '.fits'
            fits.PrimaryHDU(self.images).writeto(os.path.join(self.legacy_save_folder, filename))

        self.images = None
        self.n_images = None
        self.exposures = None
        self.h5_filepath = None
        self.stop_acquisition_timeout = None
        return True

    def abort(self):
        if self.camera.active:
            if self.camera.is_streaming():
                self.camera.stop_streaming()
        self.images = None
        self.n_images = None
        self.exposures = None
        self.h5_filepath = None
        self.stop_acquisition_timeout = None
        return True

    def abort_buffered(self):
        return self.abort()

    def abort_transition_to_buffered(self):
        return self.abort()

    def program_manual(self, values):
        return {}

    def shutdown(self):
        if self.camera.active:
            if self.camera.is_streaming():
                self.camera.stop_streaming()
            self.camera.__exit__(None, None, None)
            self.camera.active = False
        self.vimba.__exit__(None, None, None)
