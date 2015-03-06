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

import rawpy as rp
import exiftool            #git://github.com/smarnach/pyexiftool.git
import pyfits

import numpy as np

par = ap.ArgumentParser(prog="rawtofits",
                        description="Convert RAW image files to FITS.")
par.add_argument("filenames", nargs='+', help="Files to be processed.")


DCRAW_DEFAULT_PARAMS = rp.Params(demosaic_algorithm=rp.DemosaicAlgorithm.LMMSE,
                                 use_camera_wb=True,
                                 output_color=rp.ColorSpace.sRGB,
                                 output_bps=16)



def raw_to_nparray(fname):
    '''
    Handles the demosaicing of the raw image, returned as 16-bit RGB numpy 
    array.
    '''
    # read RAW file
    raw_img = rp.imread(fname)
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

def pack_FITS(fname, img_data, img_exif, channel=[0, 1, 2]):    
    '''
    Creates the actual FITS.
    channels contains one or more of 0, 1, 2 in a list, representing RGB, resp.
    '''
    for ch in channel:
        hdu = pyfits.PrimaryHDU(img_data[:, :, ch])
        hdu.header.set("OBSTIME", img_exif['EXIF:CreateDate'])
        hdu.header.set('EXPTIME', img_exif['EXIF:ExposureTime'])
        hdu.header.set('APERTUR', img_exif['EXIF:FNumber'])
        hdu.header.set('ISO',     img_exif['EXIF:ISO'])
        hdu.header.set('FOCAL',   img_exif['EXIF:FocalLength'])
        hdu.header.set('ORIGIN',  fname)
        hdu.header.set('FILTER',  ch)
        hdu.header.set('CAMERA',  img_exif['EXIF:Model'])

        hdu.header.add_comment('EXPTIME is in seconds.')
        hdu.header.add_comment('APERTUR is the ratio as in f/APERTUR')
        hdu.header.add_comment('FOCAL is in mm')

        basename = fname.split('.')[0]
        hdu.writeto("{}_{}.fits".format(basename, ch))



def process_file(fname):
    '''
    Convenience function that wraps the whole postprocessing from RAW to FITS.
    '''
    img_array = raw_to_nparray(fname)
    img_exif = extract_exif(fname)
    pack_FITS(fname, img_array, img_exif)



if __name__ == "__main__":
    args = par.parse_args()

    with Pool() as pool:
        pool.map(process_file, args.filenames)

    exit(0)
