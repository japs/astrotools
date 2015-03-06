#!/usr/bin/python2
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

from sys import stdin, stderr, stdout, exit, argv
import alipy
import argparse as ap
import re
from multiprocessing import Pool
from functools import partial

par = ap.ArgumentParser(prog="rawtofits",
                        description="Convert RAW image files to FITS.")
par.add_argument("filenames", nargs='+', help="Files to be processed.")
par.add_argument('-r', '--reference-frame', default=None,
                 help=("Reference frame to align other frames to. If not "
                       "present, the first input filename will be used."))
par.add_argument("-s", "--separate-channels", default=False, 
                 action="store_true",
                 help=("Align separately each of the three RGB channels. "
                       "By default, the green channel of images with the same "
                       "root filename is aligned, and the transform is then "
                       "applied to R and B."))
par.add_argument("-V", "--img-verbose", default=False, action='store_true',
                 help=("Produce verbose image output, i.e., png files showing"
                       "identifications, quads, etc."))


def align_frames(ident, green=True, img_verbose=False):
    '''
    Take the Identification objects and carry out the actual transformation.
    :param green: bool.
        If true, it substitute the ending for the R and B channels, and aligns
        all three channels, using the same transformation as the one 
        calculated for the green channel, to which ident refers.
        If false, it only aligns the ident Identification object provided.
    '''
    if id.ok == True:
        if green:
            rgb_fnames = [ident.ukn.filepath.replace("_1.fits", "_0.fits"),
                          ident.ukn.filepath,
                          ident.ukn.filepath.replace("_1.fits", "_2.fits")]
        else:
            rgb_frames = list(ident.ukn.filepath)

        for fname in rgb_fnames:
            alipy.align.affineremap(fname, ident.trans, shape=output_shape,
                                    makepng=args.img_verbose)
    else:
        msg = "Unable to align image {}"
        raise RuntimeError(msg.format(ident.ukn.filepath))
#end def




if __name__ == "__main__":
    args = par.parse_args()
    
    if args.reference_frame is None:
        args.reference_frame = args.filenames[0]

    if args.separate_channels:
        fnames = args.filenames
    else:
        # select green channels by filename, i.e., files ending in _1.fits
        fnames = [fname for fname in args.filenames if "_1.fits" in fname]

    # Perform the actual identifications.
    # TODO: Check the code of alipy.ident.run. It shouldn't be difficult to
    #       parallelise this.
    identifications = alipy.ident.run(args.reference_frame, fnames,
                                      visu=args.img_verbose)
    
    # set output shape
    output_shape = alipy.align.shape(ref_image)
    
    # actual alignement
    if args.separate_channels:
        partial_align_frames = align_frames(ident, green=False, 
                                            img_verbose=args.img_verbose)
    else:
        partial_align_frames = align_frames(ident, green=True, 
                                            img_verbose=args.img_verbose)

    with Pool() as pool:
        pool.map(partial_align_frames, identifications)


    exit(0)
