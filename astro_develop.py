#!/usr/bin/python3

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
    # read RAW file
    raw_img = rp.imread(fname)
    # demosaic and stuff...aka dcraw develop
    raw_img.dcraw_process(DCRAW_DEFAULT_PARAMS)
    return raw_img.dcraw_make_mem_image()

def extract_exif(fname):
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
    img_array = raw_to_nparray(fname)
    img_exif = extract_exif(fname)
    pack_FITS(fname, img_array, img_exif)



if __name__ == "__main__":
    args = par.parse_args()

    with Pool() as pool:
        pool.map(process_file, args.filenames)

    exit(0)
