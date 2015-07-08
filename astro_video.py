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

from sys import stdin, stderr, stdout, exit, argv
from subprocess import check_call
from skimage.io import imread, imsave
from glob import glob
import argparse as ap
import numpy as np

par = ap.ArgumentParser(prog="astro_fuse",
                        description=("Combine different frames into a single "
                                     "image."))
par.add_argument("filenames", nargs='*', help="Files to be processed.")
par.add_argument('-r', '--reference', type=str, default=None, 
                 help="Reference frame.")
par.add_argument('-e', '--video', default=False, action="store_true",
                 help="Extract frames from video(s).")
par.add_argument('-s', '--sigma', default=3, type=float,
                 help=("Average frames with distance from references "
                       "smaller than mean + sigma standard deviations."))

def extract_frames(fname, frame_rate=25, fout_root=None):
    '''
    Extracts frames from video. It requires ffmpeg to be installed.
    '''
    if fout_root is None:
        fout_root = fname
    _fout_root = fout_root + "-%5d.tif"

    cmd = ["ffmpeg", "-i", fname, "-r", str(frame_rate), _fout_root]
    check_call(cmd)
    return glob("fout_root" + "*")


def load_frame(fname, channel="To_Implement"):
    '''
    Loads a single frame.
    '''
    print("loading " + fname)
    image = imread(fname, plugin='freeimage')
    return image


def distance(reference, other_fnames):
    '''
    Computes the distance between a frame F and a reference frame R.
        d = \sum_ijk (R-F)_ijk^2
    '''
    distances = np.zeros(len(other_fnames))

    for idx, fname in enumerate(other_fnames):
        frame = load_frame(fname)
        difference = reference - frame
        distance = np.sum(difference**2)
        distances[idx] = distance
    return distances


def fuse_mean(frame_fnames, distances, sum_frac=0.25):
    '''
    Averages together the sum_frac fraction of frames with the least distance
    from the reference frame.
    '''
    #dumb but for now ok
    frame = load_frame(frame_fnames[0])
    #
    output = np.zeros(frame.shape)
    sort_idx = np.argsort(distances)
    Naveraged = 0
    for idx in sort_idx[:int(len(distances)*sum_frac)]:
        fname = frame_fnames[idx]
        distance = distances[idx]
        print("summing {}".format(fname))
        frame = load_frame(fname)
        output += frame
        Naveraged += 1
    print(Naveraged)
    output /= Naveraged
    maximum = np.max(output)
    MAX_BRIGHT = 0.85
    output *= MAX_BRIGHT * (2**16 - 1) / maximum
    return np.uint16(output)





if __name__ == "__main__":
    args = par.parse_args()

    if args.video:
        # Extract frames from video.
        for f in args.filenames:
            extract_frames(f)

    if args.reference is not None:
        # A reference frame was passed.
        # 1) load reference frame and compute distances to other frames.
        reference_frame = load_frame(args.reference)
        distances = distance(reference_frame, args.filenames)
        # 2) average together.
        image = fuse_mean(args.filenames, distances, 
                          sum_frac=0.25)
        imsave("./output.tif", image, plugin="freeimage")

    exit(0)
