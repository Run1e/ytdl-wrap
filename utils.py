import os


def subfolders(folder):
	for subfolder in os.listdir(folder):
		if not os.path.isfile(os.path.join(folder, subfolder)):
			yield subfolder


def ensure_folder(folder):
	if not os.path.isdir(folder):
		os.mkdir(folder)
