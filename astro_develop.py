#!/usr/bin/python3
# *********************************************************************        
# * Copyright (C) 2015 Jacopo Nespolo <j.nespolo@gmail.com>           *        
# *                                                                   *
# * For the license terms see the file LICENCE, distributed           *
# * along with this software.                                         *
# *********************************************************************
#
# This file is part of astrotools.
# 
# Astrotools is free software: you can redistribute it and/or modify it under 
# the terms of the GNU General Public License as published by the Free Software 
# Foundation, either version 3 of the License, or (at your option) any later 
# version.
# 
# Astrotools is distributed in the hope that it will be useful, but WITHOUT ANY 
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS 
# FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along 
# with astrotools.  If not, see <http://www.gnu.org/licenses/>
#

from sys import stdin, stdout, stderr, argv, exit
from multiprocessing import Pool, cpu_count, Value
from subprocess import check_output
from tempfile import NamedTemporaryFile
import argparse as ap
from functools import partial
import lensfunpy as lfp

import rawpy as rp
from skimage.io import imread
import pyfits

import numpy as np
from scipy.ndimage import map_coordinates

par = ap.ArgumentParser(prog="astro_develop",
                        description="Convert RAW image files to FITS.")
par.add_argument("filenames", nargs='+', help="Files to be processed.")
par.add_argument("--no-demosaic", default=False, action="store_true", 
                 help="Use raw sensor data, without demosaicing..")
par.add_argument("-l", '--lens-correction', default=False, action='store_true',
                 help="Apply lens distortion correction.")
par.add_argument('-c', "--output-channel", nargs="+", default=[0, 1, 2],
                 help="Select output channels. Default is [0 1 2] (RGB).")
par.add_argument("-v", '--verbose', default=False, action='store_true',
                 help="Print verbose output.")
par.add_argument('--use-libraw', default=False, action='store_true',
                 help="Use libraw for raw development.")
par.add_argument('--use-dcraw', default=True, action='store_true',
                 help="Use dcraw for raw development (default).")



DCRAW_DEFAULT_PARAMS = rp.Params(demosaic_algorithm=rp.DemosaicAlgorithm.LMMSE, 
                                 use_camera_wb=True, 
                                 use_auto_wb=False, 
                                 user_wb=None,
                                 output_color=rp.ColorSpace.sRGB, 
                                 output_bps=16, 
                                 user_flip=None, 
                                 user_black=0,
                                 user_sat=None, 
                                 no_auto_bright=True, 
                                 auto_bright_thr=None,
                                 adjust_maximum_thr=0, 
                                 exp_shift=None, 
                                 exp_preserve_highlights=0.0,
                                 gamma=None, #(1., 1.), 
                                 bad_pixels_path=None)

UNDISTORT_COORDS = {}

def open_raw_image(fname):
    '''
    Read the raw image and return the corresponding object
    '''
    raw_img = rp.imread(fname)
    return raw_img

def raw_to_nparray(raw_img):
    '''
    Handles the demosaicing of the raw image, returned as 16-bit RGB numpy 
    array.
    '''
    # demosaic and stuff...aka dcraw develop
    return raw_img.postprocess(DCRAW_DEFAULT_PARAMS)


def dcraw_develop(fname):
    '''
    Call dcraw -w -6 on the given file and extract the data.
    '''
    with NamedTemporaryFile() as tmpfile:
    #with open('/tmp/fname' + ".tiff", 'w+b') as tmpfile:
        dcraw_output = check_output(['dcraw', '-w', '-6', '-c', '-T', fname])
        tmpfile.write(dcraw_output)

        image = imread(tmpfile.name, plugin='freeimage')
    return image
    

def extract_exif(fname):
    '''
    Extracts the EXIF metadata, returned as a dictionary.
    '''
    metadata = {}
    output = check_output(["exiftool", fname]).decode('utf-8')
    for line in output.splitlines():
        tag, value = line.split(":", maxsplit=1)
        tag = tag.strip()
        if tag not in metadata:
            metadata[tag] = value.strip()
    return metadata

def FITS_header(fname, img_exif):
    hdu_header = pyfits.Header()
    hdu_header.set("OBSTIME", img_exif['Create Date'])
    hdu_header.set('EXPTIME', img_exif['Exposure Time'])
    hdu_header.set('APERTUR', img_exif['F Number'])
    hdu_header.set('ISO',     img_exif['ISO'])
    hdu_header.set('FOCAL',   img_exif['Focal Length'])
    hdu_header.set('ORIGIN',  fname)
    hdu_header.set('CAMERA',  img_exif['Camera Model Name'])

    hdu_header.add_comment('EXPTIME is in seconds.')
    hdu_header.add_comment('APERTUR is the ratio as in f/APERTUR')
    hdu_header.add_comment('FOCAL is in mm')
    return hdu_header


def pack_FITS(fname, img_data, header, channel):    
    '''
    Creates the actual FITS.
    channels contains one or more of 0, 1, 2 in a list, representing RGB, resp.
    '''
    hdu = pyfits.PrimaryHDU(data=img_data, header=header)
    hdu.header.set('FILTER',  channel)

    basename = fname.split('.')[0]
    hdu.writeto("{}_{}.fits".format(basename, channel), clobber=True)


def correct_distortion(img_array, img_exif):
    cam_maker   = img_exif["Make"]
    cam_model   = img_exif["Camera Model Name"]
    lens_id     = img_exif["Lens ID"]
    crop_factor = float(img_exif["Scale Factor To 35 mm Equivalent"])
    aperture    = float(img_exif['F Number'])
    focal       = float(img_exif['Focal Length'][:-3])
    distance    = float(img_exif["Focus Distance"][:-2])
    
    try:
        height, width, channels = img_array.shape
    except ValueError: # only one channel
        height, width = img_array.shape
        channels = 1
    
    if lens_id not in UNDISTORT_COORDS:
        db = lfp.Database()
        camera = db.find_cameras(cam_maker, cam_model)[0]
        lens   = db.find_lenses(camera, lens=lens_id)[0]
        img_shape = img_array.shape
        modifier = lfp.Modifier(lens, camera.crop_factor, 
                                img_shape[0], img_shape[1])
        modifier.initialize(focal, aperture, distance, pixel_format=np.uint16)
        undistort_coords = modifier.apply_geometry_distortion()
        undistort_coords = np.rollaxis(undistort_coords, 2)
        UNDISTORT_COORDS[lens_id] = undistort_coords
    else:
        undistort_coords = UNDISTORT_COORDS[lens_id]

    if channels == 1:
        img_undistorted = map_coordinates(img_array, undistort_coords, 
                                          order=2)
        return img_undistorted
    else:
        out_channels = []
        for c in range(channels):
            out_channels.append(map_coordinates(img_array[:, :, c], 
                                                undistort_coords, order=2))
        return np.dstack(out_channels)


def process_file(fname, args):
    '''
    Convenience function that wraps the whole postprocessing from RAW to FITS.
    '''
    img_exif = extract_exif(fname)
    fits_header = FITS_header(fname, img_exif)

    if args.use_libraw:
        raw_img = open_raw_image(fname)
        if args.no_demosaic:
            img_array = raw_img.raw_image
            args.output_channel = [4]
        else:
            img_array = raw_to_nparray(raw_img)
    elif args.use_dcraw:
        img_array = dcraw_develop(fname)

    if args.lens_correction:
        img_array = correct_distortion(img_array, img_exif)
        
    for channel in args.output_channel:
        if args.no_demosaic:
            pack_FITS(fname, img_array, fits_header, channel)
        else:
            pack_FITS(fname, img_array[:, :, channel], fits_header, channel)
    if args.verbose:
        with DONE.get_lock():
            DONE.value += 1
        stderr.write("{:.1%}\r".format(DONE.value / NFRAMES.value))



if __name__ == "__main__":
    args = par.parse_args()
    if args.verbose:
        NFRAMES = Value('i', len(args.filenames))
        DONE = Value('i', 0)

    if args.use_libraw:
        args.use_dcraw = False

    if args.lens_correction:
        nprocesses = cpu_count() // 2
    else:
        nprocesses = cpu_count()

    with Pool(nprocesses) as pool:
        partial_process_file = partial(process_file, args=args)
        pool.map(partial_process_file, args.filenames)

    exit(0)
