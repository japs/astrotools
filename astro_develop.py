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
from multiprocessing import Pool
import argparse as ap
from functools import partial

import rawpy as rp
import exiftool            #git://github.com/smarnach/pyexiftool.git
import pyfits

import numpy as np

par = ap.ArgumentParser(prog="astro_develop",
                        description="Convert RAW image files to FITS.")
par.add_argument("filenames", nargs='+', help="Files to be processed.")
par.add_argument("--no-demosaic", default=False, action="store_true", 
                 help="Use raw sensor data, without demosaicing..")


DCRAW_DEFAULT_PARAMS = rp.Params(demosaic_algorithm=rp.DemosaicAlgorithm.LMMSE,
                                 use_camera_wb=True,
                                 output_color=rp.ColorSpace.sRGB,
                                 output_bps=16)


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
    raw_img.dcraw_process(DCRAW_DEFAULT_PARAMS)
    return raw_img.dcraw_make_mem_image()

def extract_exif(fname):
    '''
    Extracts the EXIF metadata, returned as a dictionary.
    '''
    with exiftool.ExifTool() as et:
        metadata = et.get_metadata(fname)
    return metadata

def FITS_header(fname, img_exif):
    hdu_header = pyfits.Header()
    hdu_header.set("OBSTIME", img_exif['EXIF:CreateDate'])
    hdu_header.set('EXPTIME', img_exif['EXIF:ExposureTime'])
    hdu_header.set('APERTUR', img_exif['EXIF:FNumber'])
    hdu_header.set('ISO',     img_exif['EXIF:ISO'])
    hdu_header.set('FOCAL',   img_exif['EXIF:FocalLength'])
    hdu_header.set('ORIGIN',  fname)
    hdu_header.set('CAMERA',  img_exif['EXIF:Model'])

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
    hdu.writeto("{}_{}.fits".format(basename, channel))



def process_file(fname, args):
    '''
    Convenience function that wraps the whole postprocessing from RAW to FITS.
    '''
    raw_img = open_raw_image(fname)
    img_exif = extract_exif(fname)
    fits_header = FITS_header(fname, img_exif)
    if args.no_demosaic:
        img_array = raw_img.raw_image
        pack_FITS(fname, img_array, fits_header, 4)
    else:
        img_array = raw_to_nparray(raw_img)
        for channel in [0, 1, 2]:
            pack_FITS(fname, img_array[:, :, channel], fits_header, channel)



if __name__ == "__main__":
    args = par.parse_args()

    with Pool() as pool:
        partial_process_file = partial(process_file, args=args)
        pool.map(partial_process_file, args.filenames)

    exit(0)
