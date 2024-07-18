'''
Copyright 2023-2024, MIT

This file is part of Zwierlein group labscript_user_devices,
and is licensed under the 3-clause BSD License.
See the license.txt file for the full license.
'''

from blacs.tab_base_classes import Worker
import labscript_utils.h5_lock, h5py

class RPiDMDWorker(Worker):
    def init(self):
        global zmq; import zmq
        global zlib; import zlib

        self.z_context = zmq.Context()
        self.z_socket = self.z_context.socket(zmq.REQ)
        self.z_socket.connect('tcp://{}:{}'.format(self.host, self.port))

    def program_manual(self, image):
        self.z_socket.send('ABORT'.encode())
        assert self.z_socket.recv().decode() == 'STOPPED'

        assert (image.shape[0] == self.height and image.shape[1] == self.width), 'Image shape does not match DMD shape'
        assert image.dtype == np.uint8, 'Image type not uint8'
        assert (np.all((image == 0) + (image == 255))), 'Image contains non-binary values'

        self.z_socket.send_multipart(['MANUAL'.encode(),
                                      zlib.compress(image.tobytes())])

    def transition_to_buffered(self, device_name, h5file, initial_values, fresh):
        self.z_socket.send('ABORT'.encode())
        assert self.z_socket.recv().decode() == 'STOPPED'

        with h5py.File(h5file, 'r') as hdf5_file:
            group = hdf5_file['devices'][device_name]
            images = group['dmd_image_data']
            for i, image in enumerate(images):
                self.z_socket.send_multipart(['SET'.encode(),
                                              zlib.compress(image.tobytes()),
                                              str(i).encode()])
                assert self.z_socket.recv().decode() == 'SET'

        self.z_socket.send('RUN'.encode())
        assert self.z_socket.recv().decode() == 'RUNNING'

        return {}

    def transition_to_manual(self):
        return True

    def abort_buffered(self):
        self.z_socket.send('ABORT'.encode())
        assert self.z_socket.recv().decode() == 'STOPPED'
        return True

    def abort_transition_to_buffered(self):
        self.z_socket.send('ABORT'.encode())
        assert self.z_socket.recv().decode() == 'STOPPED'
        return True

    def shutdown(self):
        self.z_socket.send('SHUTDOWN'.encode())
        assert self.z_socket.recv().decode() == 'SHUTDOWN'
