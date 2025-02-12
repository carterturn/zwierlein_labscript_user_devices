'''
Copyright 2025, MIT

This file is part of Zwierlein group labscript_user_devices,
and is licensed under the 3-clause BSD License.
See the license.txt file for the full license.
'''

from labscript_devices.IMAQdxCamera.blacs_tabs import IMAQdxCameraTab

class PixelflyCameraTab(IMAQdxCameraTab):
	# attempt to override the worker class
	worker_class = 'user_devices.PixelflyCamera.blacs_workers.PixelflyCameraWorker'
