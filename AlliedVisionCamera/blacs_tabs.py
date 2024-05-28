'''
Copyright 2023-2024, MIT

This file is part of Zwierlein group labscript_user_devices,
and is licensed under the 3-clause BSD License.
See the license.txt file for the full license.
'''

from labscript_devices.IMAQdxCamera.blacs_tabs import IMAQdxCameraTab

class AlliedVisionCameraTab(IMAQdxCameraTab):
	# attempt to override the worker class (hopefully with more success than Starbucks)
	worker_class = 'user_devices.AlliedVisionCamera.blacs_workers.AlliedVisionCameraWorker'
