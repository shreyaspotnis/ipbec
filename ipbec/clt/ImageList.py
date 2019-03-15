import os
import re


class ImageList(object):
    """Lists absorption and reference images in a directory"""

    def __init__(self, path_to_dir=None):
        self.path_to_dir = path_to_dir
        self.updateFileList()

    def updateFileList(self, path_to_new_dir=None):
        """Updates files to reflect contents of current directory.

        Call this function whenever contents of current directory have
        changed.

        If current directory has changed, then pass path to new directory as
        an argument.
        """

        if path_to_new_dir is not None:
            self.path_to_dir = path_to_new_dir

        if self.path_to_dir is None:
            return

        # list everything in path_to_dir but only add files which have .tif to
        # the list of files
        self.files = sorted([f for f in os.listdir(self.path_to_dir)
                             if (os.path.isfile(os.path.join(self.path_to_dir, f))
                                 and f[-4:] == '.tif')])
        if len(self.files) is 0:
            raise ImageListError('No .tif files in this directory.')

        # check if there are two absorption images per reference image
        # find all files that end in Abs2.tif
        # abs2_files = [f for f in self.files if f[-8:]=='Abs2.tif']
        abs2_files = [f for f in self.files if f[-11:]=='Frame-3.tif']

        if(len(abs2_files) > 0):
            # we have 2 absorption images per ref image
            if len(self.files) % 3 is not 0:
                raise ImageListError('2 Aborption files per ref detected.'
                                     ' Yet total number of files is not'
                                     ' divisible by 3. Something is wrong.')
            self.abs0 = [os.path.join(self.path_to_dir, f)
                         for f in self.files[::3]]
            self.abs1 = [os.path.join(self.path_to_dir, f)
                         for f in self.files[1:][::3]]
            self.ref = [os.path.join(self.path_to_dir, f)
                         for f in self.files[2:][::3]]
            # interleave self.abs0 and self.abs1
            self.absorption_files = [x for t in zip(self.abs0, self.abs1)
                                     for x in t]
            self.reference_files = [x for t in zip(self.ref, self.ref)
                                     for x in t]
            short_names1 = [f[:-6]+' 1' for f in self.files[::3]]
            short_names2 = [f[:-6]+' 2' for f in self.files[1:][::3]]
            self.short_names = [x for t in zip(short_names1, short_names2)
                                     for x in t]
        else:
            # we have 1 absorption image per ref image
            if len(self.files) % 2 is not 0:
                raise ImageListError('Odd number of files in the directory.'
                                     ' Something is wrong.')
            self.absorption_files = [os.path.join(self.path_to_dir, f)
                                     for f in self.files[::2]]  # even entries
            self.reference_files = [os.path.join(self.path_to_dir, f)
                                    for f in self.files[1:][::2]]  # odd entries
            self.short_names = [f[:-11] for f in self.files[::2]]
            for a, r in zip(self.absorption_files, self.reference_files):
                # abs_name = re.split('Abs.tif', a)[0]
                # ref_name = re.split('Ref.tif', r)[0]
                abs_name = re.split('Frame-1.tif', a)[0]
                ref_name = re.split('Frame-2.tif', r)[0]
                if abs_name != ref_name:
                    # TODO: handle this error
                    raise ImageListError('Absorption and Reference image names do'
                                         'not match. Check for missing files.')

        self.n_images = len(self.absorption_files)


class ImageListError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value
