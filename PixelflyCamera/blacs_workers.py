'''
Copyright 2025, MIT

This file is part of Zwierlein group labscript_user_devices,
and is licensed under the 3-clause BSD License.
See the license.txt file for the full license.
'''

from blacs.tab_base_classes import Worker
import numpy as np
from labscript_utils import dedent
import labscript_utils.h5_lock
import h5py
import labscript_utils.properties
import zmq
import os
from time import perf_counter
import threading
from labscript_utils.shared_drive import path_to_local

from labscript_utils.ls_zprocess import Context

class PixelflyCameraWorker(Worker):
    '''
    Worker for a PCO Pixelfly camera, using the Pixelfly API.

    Compatible with the IMAQdxCamera BLACS tab.
    '''

    def init(self):
        global pco
        import pco

        if self.legacy_save_folder is not None:
            global fits
            from astropy.io import fits
            global datetime
            import datetime

        self.cam = pco.Camera(self.interface, self.serial)

        self.cam.default_configuration()

        self.smart_cache = {}
        self.set_attributes_smart(self.camera_attributes)
        self.set_attributes_smart(self.manual_mode_camera_attributes)

        self.n_images = None
        self.exposures = None
        self.acquisition_thread = None
        self.h5_filepath = None
        self.stop_acquisition_timeout = None
        self.continuous_stop = threading.Event()
        self.continuous_thread = None
        self.continuous_dt = None
        self.image_socket = Context().socket(zmq.REQ)
        self.image_socket.connect(
            f'tcp://{self.parent_host}:{self.image_receiver_port}'
        )

    def set_attributes_smart(self, attributes):
        '''Call self.cam.configuration to set the given attributes, only setting
        those that differ from their value in, or are absent from self.smart_cache.
        Update self.smart_cache with the newly-set values'''
        uncached_attributes = {}
        for name, value in attributes.items():
            if name not in self.smart_cache or self.smart_cache[name] != value:
                uncached_attributes[name] = value
                self.smart_cache[name] = value
        for k, v in uncached_attributes.items():
            self.cam.configuration[k] = v

    def get_attributes_as_dict(self):
        '''Return a dict of the attributes of the camera
        level'''
        return self.cam.configuration

    def get_attributes_as_text(self):
        '''Return a string representation of the attributes of the camera for
        the given visibility level'''
        attrs = self.get_attributes_as_dict()
        # Format it nicely:
        lines = [f'    {repr(key)}: {repr(value)},' for key, value in attrs.items()]
        dict_repr = '\n'.join(['{'] + lines + ['}'])
        return self.device_name + '_camera_attributes = ' + dict_repr

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
        if self.cam.is_recording:
            self.cam.stop()
        self.set_attributes_smart(self.manual_mode_camera_attributes)
        self.cam.configuration['trigger'] = 'software trigger'
        self.cam.record(number_of_images=1, mode='sequence')
        self._send_image_to_parent(self.cam.image())

    def continuous_loop(self, dt):
        '''Acquire continuously in a loop, with minimum repetition interval dt'''
        while True:
            if dt is not None:
                t = perf_counter()
            image = self.cam.image()
            self._send_image_to_parent(image)
            if dt is None:
                timeout = 0
            else:
                timeout = t + dt - perf_counter()
            if self.continuous_stop.wait(timeout):
                self.continuous_stop.clear()
                break

    def start_continuous(self, dt):
        '''Begin continuous acquisition in separate thread'''
        if self.cam.is_recording:
            self.cam.stop()
        self.set_attributes_smart(self.manual_mode_camera_attributes)
        self.cam.record(number_of_images=5, mode='fifo')
        self.continuous_thread = threading.Thread(
            target=self.continuous_loop, args=(dt,), daemon=True
        )
        self.continuous_thread.start()
        self.continuous_dt = dt

    def stop_continuous(self, pause=False):
        '''Stop the continuous acquisition'''
        assert self.continuous_thread is not None
        self.continuous_stop.set()
        self.continuous_thread.join()
        self.continuous_thread = None
        self.cam.stop()
        # If we're just 'pausing', then do not clear self.continuous_dt. That way
        # continuous acquisition can be resumed with the same interval by calling
        # start(self.continuous_dt), without having to get the interval from the parent
        # again, and the fact that self.continuous_dt is not None can be used to infer
        # that continuous acquisiton is paused and should be resumed after a buffered
        # run is complete:
        if not pause:
            self.continuous_dt = None 

    def transition_to_buffered(self, device_name, h5_filepath, initial_values, fresh):
        if getattr(self, 'is_remote', False):
            h5_filepath = path_to_local(h5_filepath)
        if self.cam.is_recording:
            self.cam.stop()
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
            self.set_attributes_smart(camera_attributes)
            print(f"Configuring camera for {self.n_images} images.")
            self.cam.configuration['trigger'] = 'external exposure control'
            self.cam.record(self.n_images, mode='sequence non blocking')
            print(f"Camera armed.")
        return {}

    def transition_to_manual(self):
        if self.h5_filepath is None:
            print('No camera exposures in this shot.\n')
            return True

        print("Stopping acquisition.")
        if self.cam.is_recording:
            self.cam.stop()

        cam_images = self.cam.images()
        print(f"Saving {len(cam_images)}/{len(self.exposures)} images.")

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
            for image, exposure in zip(cam_images, self.exposures):
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
            image_block = np.stack(cam_images)
        except ValueError:
            print("Cannot display images in the GUI, they are not all the same shape")
        else:
            self._send_image_to_parent(image_block)

        if self.legacy_save_folder is not None:
            filename = datetime.datetime.now().strftime('%Y-%m-%d-%H;%M;%S') + '.fits'
            fits.PrimaryHDU(cam_images).writeto(os.path.join(self.legacy_save_folder, filename))

        self.n_images = None
        self.exposures = None
        self.h5_filepath = None
        self.stop_acquisition_timeout = None
        return True

    def abort(self):
        if self.cam.is_recording:
            self.cam.stop()
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
        self.cam.close()
