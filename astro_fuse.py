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

from sys import exit, stdin, stdout, stderr, argv
import numpy as np
import argparse as ap
import pyfits
import re

par = ap.ArgumentParser(prog="astro_fuse",
                        description=("Combine different frames into a single "
                                     "image."))
par.add_argument("filenames", nargs='+', help="Files to be processed")
par.add_argument("-a", "--average", default=True, action="store_true",
                 help=("Average together the input frames "
                       "(this is the default behaviour)."))
par.add_argument("-m", "--median", default=False, action="store_true",
                 help="Median of the input frames.")
par.add_argument("-r", '--rows', type=int, default=None,
                 help="Average this many rows at a time. (Default: optimise)")
par.add_argument("-v", '--verbose', default=False, action='store_true',
                 help="Print verbose output.")
par.add_argument("-o", "--output-file", default="output.fits",
                 help="Output file name.")


def median(frames, args):
    output = np.zeros(frames[0].shape)
    Nframes = len(frames)
    shape = frames[0].shape
    
    chunks = shape[0] // args.rows
    remainder = shape[0] % args.rows

    for i in range(chunks):
        start_row =       i * args.rows
        end_row   = (i + 1) * args.rows
        output[start_row:end_row, ...] = \
                np.median([f.data[start_row:end_row, ...] for f in frames],
                          axis=0)
        if args.verbose:
            msg = "approximately {:.1%} done.\r"
            stderr.write(msg.format(end_row/shape[0]))
    if remainder != 0:
        output[end_row:, ...] = \
                np.median([f.data[end_row:, ...] for f in frames],
                          axis=0)
    return output


if __name__ == "__main__":
    args = par.parse_args()
    
    input_frames = []
    # Read files
    for fname in args.filenames:
        # open the FITS file. We assume a single HDU, and add it to the 
        # input_frames list.
        frame_hdulist = pyfits.open(fname, memmap=True, mode='readonly')
        input_frames.append(frame_hdulist[0])

    # determine number of input files
    N_frames = len(input_frames)

    # Check the size of the first frame, and use it as output frame size.
    # If not all the frames share the same size, something bad is going to 
    # happen by the time numpy comes into play. Hence, we do not worry about it
    # here, and instead wait for an exception to be raised somewhere.
    size = input_frames[0].data.shape
    
    # create the output array
    out_frame = np.zeros(shape=size, dtype=np.float64)
   
    # if not provided by user, optimise the number of rows to average at once.
    # TODO: write an optimiser that automatically calculates the optimal number
    #       of rows to compute at once. Also, double check the actual working
    #       of the FITS buffering: chances are that this is overkill and 
    #       automatic FITS buffering already takes care of not crashing the 
    #       machine.
    if args.rows == None:
        args.rows = 100
    
    if args.median:
        out_frame = median(input_frames, args=args)
        args.average = False
    elif args.average:
        # average the input frames
        for n, frame in enumerate(input_frames):
            if args.verbose:
                stderr.write("Averaging frame {}/{}\n".format(n, N_frames))
            out_frame += frame.data
        out_frame /= N_frames

    # write output FITS
    hdu = pyfits.PrimaryHDU(out_frame)
    hdu.header = input_frames[0].header
    if not re.search("\.fits$", args.output_file):
        args.output += ".fits"
    hdu.writeto(args.output_file, clobber=True)
        
    exit(0)
