from labscript_devices.IMAQdxCamera.blacs_tabs import IMAQdxCameraTab

class AlliedVisionCameraTab(IMAQdxCameraTab):
	# attempt to override the worker class (hopefully with more success than Starbucks)
	worker_class = 'user_devices.AlliedVisionCamera.blacs_workers.AlliedVisionCameraWorker'
