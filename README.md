# astrotools
Some tools to process astrophotography images.

Project
=======
The idea is to have a full toolchain to process astrophotographic images from 
the RAW files of any modern DSLR camera to final product.

The toolchain I have in mind is the following:  
1. Produce a master dark frame, a master bias frame and a master flat frame.  
2. Develop the RAW files.  
4. Apply dark, bias and flat frame corrections.  
5. Apply lens distortion correction.  
6. Align the frames.  
7. Fuse the frames together.  

As I'm still very new to astrophotography, any comment is very welcome.
The target system is any modern Linux distribution, although my code might 
also run on some other OSs.

What's included
===============
* 'astro_develop.py'  
  Raw development into fits files (one per channel). 
  Inspired by M. Emre Aydin's [cr2fits](https://github.com/eaydin/cr2fits).

* 'astro_align.py'  
  Alignement of multiple frames.

* 'astro_fuse.py'  
  Takes the aligned frames and output the combined frame.

* 'astro_fitspreview.py'  
  A very dumb, matplotlib-based fits previewer.

To do
=====
* 'Frame calibration'  
  Also check if it is possible to apply dark subtraction 'before' demosaicing.

* 'pyIRAF alignement with distortion correction'
  This only really requires a line of code in astro_align and the installation 
  of the dependencies (see alipy docs).

* 'Multiple HDU fits file'  
  Check if feasable to keep RGB channels in the same file, using multiple HDUs.

A word on lincensing
====================
A good part of the code was blatantly copied from tutorials and documentation 
pages throughout the web. I'm assuming that the documentation of free software 
is free itself, and can be redistributed here under the terms of the GPL.
This should be true for GPL as well as MIT/BSD code.
However, when looking for code that would help this project, it is sometimes 
not clear under which terms one can a code snippet. To the best of my 
knowledge, the code I used falls into allowed categories.


Third party libraries
=====================
These tools would not work without the a decent number of third party 
libraries, as well as people who wrote code and released it public.
I'm going to list them here, for convenience and future study, and to credit 
the authors for their job.

## Libraries
* [**Alipy**](http://obswww.unige.ch/~tewes/alipy/) (GPLv3)
  Alignement of multiple frames. At the present stage the tool 
  'astro_align.py' is basically a copy of 
  [Alipy's tutorial](http://obswww.unige.ch/~tewes/alipy/tutorial.html).

* [**Lensfunpy**](https://warehouse.python.org/project/lensfunpy/)
  [doc](http://pythonhosted.org/lensfunpy/)  
  Lens distortion correction. See in particular the example code on the 
  project's page.

* [**PyFITS**](http://www.stsci.edu/institute/software_hardware/pyfits/)
  [doc](http://pythonhosted.org/pyfits/index.html)
  Python library for FITS i/o. (Fits is the standard file format for 
  astronomical data).

* [**Rawpy**](http://pythonhosted.org//rawpy/api/index.html) (MIT)
  ([Code](https://github.com/neothemachine/rawpy))
  A Python wrapper around [libraw](http://www.libraw.org/) (LGPLv2.1 with
  GPLv2 and GPLv3 demosaicing code).

## Other code
* ['cr2fits'](https://github.com/eaydin/cr2fits)
  M. Emre Aydin's raw development script. See also 
  [Kelsey's version](https://github.com/kjordahl/cr2fits).


Sources of inspiration and further reading
==========================================
Definitely, [Kelsey's weblog](http://kjordahl.net/blog/) contains all one 
needs to bootstrap a project like this.

[Using Image Calibration to Reduce Noise in Digital 
Images](http://photo.net/learn/dark_noise/) looks like a good place to start
implementing the dark/bias/flat frame processing.
