import os
import re


class ImageList(object):
    """Lists absorption and reference images in a directory"""

    def __init__(self, path_to_dir):
        self.changeDirectory(path_to_dir)

    def changeDirectory(self, path_to_new_dir):
        """Updates files to reflect contents of new directory."""
        if path_to_new_dir is None:
            return
        else:
            self.path_to_dir = path_to_new_dir
            self.updateFileList()

    def updateFileList(self):
        """Updates files to reflect contents of current directory.

        Call this function whenever contents of current directory have
        changed."""

        # list everything in path_to_dir but only add files which have .tif to
        # the list of files
        self.files = sorted([f for f in os.listdir(self.path_to_dir)
                             if (os.path.isfile(os.path.join(self.path_to_dir, f))
                                 and f[-4:] == '.tif')])
        self.absorption_files = [os.path.join(self.path_to_dir, f)
                                 for f in self.files[::2]]  # even entries
        self.reference_files = [os.path.join(self.path_to_dir, f)
                                for f in self.files[1:][::2]]  # odd entries
        for a, r in zip(self.absorption_files, self.reference_files):
            abs_name = re.split('Abs.tif', a)[0]
            ref_name = re.split('Ref.tif', r)[0]
            if abs_name != ref_name:
                # TODO: handle this error
                raise ImageListError('Absorption and Reference images do'
                                     'not match. Check for missing files')

        self.n_images = len(self.absorption_files)


class ImageListError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value
