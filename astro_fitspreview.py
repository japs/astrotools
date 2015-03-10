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
import argparse as ap
from matplotlib import pyplot as plt
import pyfits

par = ap.ArgumentParser(prog="astro_fitspreview",
                        description="Convert RAW image files to FITS.")
par.add_argument("filenames", nargs='+', help="Files to be processed")

if __name__ == "__main__":
    args = par.parse_args()
    
    for fname in args.filenames:
        frame_hdulist = pyfits.open(fname, memmap=True, mode='readonly')
        frame = frame_hdulist[0]
        imgplot = plt.imshow(1 - frame.data)
        imgplot.set_cmap('Greys')
        plt.show()
    exit(0)
