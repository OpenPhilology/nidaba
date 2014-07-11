/**
 * Copyright (C) 2014 University of Leipzig
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to
 * deal in the Software without restriction, including without limitation the
 * rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
 * sell copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 * IN THE SOFTWARE.
 */

#define _GNU_SOURCE

#include <string.h>
#include <leptonica/allheaders.h>
#include <Python.h>
#include <stdio.h>
#include <libgen.h>

/* leper is Iris' wrapper around leptonica doing miscellaneous image processing
 * work that is too cumbersome or slow for python. */

/* inserts val into a file name just before the extension, e.g.
 * /foo/bar/baz.jpg -> /foo/bar/baz_10.jpg. Run multiple times for more than
 * one value. */
char *param_path(char *path, int val) {
        char *dirc, *basec, *d, *f;

        if((dirc = strdup(path)) == NULL) {
                return NULL;
        }
        if((basec = strdup(path)) == NULL) {
                free(dirc);
                return NULL;
        }
        d = dirname(dirc);
        f = basename(basec);
        char *ext;
        char *dot = strrchr(f, '.');
        if((ext = strdup(dot)) == NULL) {
                free(dirc);
                free(basec);
                return NULL;
        }
        *dot = 0;
        char *res;
        if(asprintf(&res, "%s/%s_%d%s", d, f, val, ext) == -1) {
                return NULL;
        }
	return res;
}

/* Dewarps a single page. TODO: Create a function to build a dewarp model for a
 * whole codex and apply to all pages. */
int dewarp(char *in, char *out) {
	PIX *pix = pixRead(in);
	if(!pix) {
		return -1;
	}
	if(pix->d != 1) {
		pixDestroy(&pix);
		return -1;
	}
	PIX *ret;
	dewarpSinglePage(pix, 0, 0, 1, &ret, NULL, 0);
	pixWriteImpliedFormat(out, ret, 100, 0);
	pixDestroy(&pix);
	pixDestroy(&ret);
	return 0;
}

static PyObject *leper_dewarp(PyObject *self, PyObject *args) {
	char *in, *out;
	if(!PyArg_ParseTuple(args, "ss", &in, &out)) {
		return NULL;
	}
	int r = dewarp(in, out);
	PyObject *ret = Py_BuildValue("i", r);
	return ret;
}


/* Converts a 32bpp input image to an 8bpp grayscale one. */
int rgb_to_gray(char *in, char *out) {
	PIX *pix = pixRead(in);
	if(!pix) {
		return -1;
	}
        PIX *r;
	if((r = pixConvertRGBToGray(pix, 0.0, 0.0, 0.0)) == NULL) {
		return -1;
	}
	pixWriteImpliedFormat(out, r, 100, 0);
	pixDestroy(&pix);
	pixDestroy(&r);
	return 0;
}

static PyObject *leper_rgb_to_gray(PyObject *self, PyObject *args) {
	char *in, *out;
	if(!PyArg_ParseTuple(args, "ss", &in, &out)) {
		return NULL;
	}
	int r = rgb_to_gray(in, out);
	PyObject *ret = Py_BuildValue("i", r);
	return ret;
}

/* Runs a tiled localized binarization of the input images */
int sauvola_binarize(char *in, char *out, l_int32 bins, l_int32 min_wsize, l_int32 max_wsize, l_float32 factor) {

	PIX* pix = pixRead(in);
	if(!pix) {
		return -1;
	}
	if(pix->d != 8) {
		pixDestroy(&pix);
		return -1;
	}
	/* Different binarizations are produced by manipulating the window size
	 * of the local threshold calculation. */
	l_int32 t = min_wsize;
	do {
		PIX *r = NULL;
		if(pixSauvolaBinarize(pix, t, factor, 0, NULL, NULL, NULL, &r) == 1) {
			pixDestroy(&pix);
			return -1;
		}
		char *res;
		if((res = param_path(out, t)) == NULL) {
			pixDestroy(&pix);
			pixDestroy(&r);
			return -1;
		}
		pixWriteImpliedFormat(res, r, 100, 0);
		pixDestroy(&r);
		free(res);
		t += (max_wsize - min_wsize)/bins;
	} while(t < max_wsize);
	pixDestroy(&pix);
	return 0;
}

static PyObject *leper_sauvola_binarize(PyObject *self, PyObject *args) {
	char *in, *out;
	l_int32 bins = 1;
	l_int32 min_wsize = 10;
	l_int32 max_wsize = 10;
	l_float32 factor = 0.3;
	if(!PyArg_ParseTuple(args, "ss|iiif", &in, &out, &bins, &min_wsize, &max_wsize, &factor)) {
		return NULL;
	}
	int r = sauvola_binarize(in, out, bins, min_wsize, max_wsize, factor);
	PyObject *ret = Py_BuildValue("i", r);
	return ret;
}

/* Runs a tiled global binarization of the input image. Different binarizations
 * of the same input are created by manipulating the threshold of the
 * background normalization. */
int otsu_binarize(char *in, char *out, l_int32 bins, l_int32 tiles, 
		  l_int32 min_thresh, l_int32 max_thresh, l_int32 mincount,
		  l_int32 bgval, l_int32 smoothx, l_int32 smoothy) {

	if(min_thresh > max_thresh) { 
		return -1;
	}

	PIX* pix = pixRead(in);
	if(!pix) {
		return -1;
	}
	if(pix->d != 8) {
		pixDestroy(&pix);
		return -1;
	}

	l_int32 sx, sy;
	if(tiles > 0) {
		sx = pix->w / tiles;
		sy = pix->h / tiles;
	} else {
		sx = 10;
		sy = 15;
	}

	/* thresholds are spaced out equally between min_thresh and max_thresh */
	l_int32 t = min_thresh;
	do {
		/* Normalizes the background followd by Otsu thresholding. Refer to the
		 * leptonica documentation for further details. */
		PIX *r;
		if((r = pixOtsuThreshOnBackgroundNorm(pix, NULL, sx, sy, t,
						mincount, bgval, smoothx,
						smoothy, 0.1, NULL)) == NULL) {
			pixDestroy(&pix);
			return -1;
		}
		char *res;
		if((res = param_path(out, t)) == NULL) {
			pixDestroy(&pix);
			pixDestroy(&r);
			return -1;
		}
		pixWriteImpliedFormat(res, pixConvert1To8(NULL, r, 255, 0), 100, 0);
		pixDestroy(&r);
		free(res);
		t += (max_thresh - min_thresh)/bins;
	} while(t < max_thresh);
	pixDestroy(&pix);
	return 0;
}

static PyObject *leper_otsu_binarize(PyObject *self, PyObject *args) {
	char *in, *out;
	l_int32 bins = 1;
	l_int32 tiles = 0;
	l_int32 min_thresh = 100;
	l_int32 max_thresh = 100;
	l_int32 mincount = 50;
	l_int32 bgval = 255;
	l_int32 smoothx = 2;
	l_int32 smoothy = 2;
	if(!PyArg_ParseTuple(args, "ss|iiiiiiii", &in, &out, &bins, &tiles,
				&min_thresh, &max_thresh, &mincount, &bgval,
				&smoothx, &smoothy)) {
		return NULL;
	}
	int r = otsu_binarize(in, out, bins, tiles, min_thresh, max_thresh,
			mincount, bgval, smoothx, smoothy);
	PyObject *ret = Py_BuildValue("i", r);
	return ret;
}

int deskew(char *in, char *out) {
	PIX* pix = pixRead(in);
	if(!pix) {
		return -1;
	}

	PIX *r;
	l_float32 skew;
	if((r = pixFindSkewAndDeskew(pix, 4, &skew, NULL)) == NULL) {
		return -1;
	}
	pixWriteImpliedFormat(out, r, 100, 0);
	pixDestroy(&pix);
	pixDestroy(&r);
	return 0;
}

static PyObject *leper_deskew(PyObject *self, PyObject *args) {
	char *in, *out;
	if(!PyArg_ParseTuple(args, "ss", &in, &out)) {
		return NULL;
	}
	int r = deskew(in, out);
	PyObject *ret = Py_BuildValue("i", r);
	return ret;
}

static char module_docstring[] = "This module provides an interface to useful functions from leptonica.";
static char deskew_docstring[] = "Deskews an image. Accepts input of arbitrary depth.";
static char dewarp_docstring[] = "Dewarps (removing optical distortion) an\
				  image. Accepts 1 bpp (binarized) input images.";
static char otsu_binarize_docstring[] = "Creates one or more binarizations of\
					 an input image using Otsu\
					 thresholding. Accepts 8 bpp\
					 (grayscale) input images. Use an image\
					 format capable of 1 bpp.";
static char sauvola_binarize_docstring[] = "Creates one or more binarizations\
					    of an input image using Sauvola\
					    thresholding. Accepts 8 bpp\
					    (grayscale) input images. Use an\
					    image format capable of 1 bpp.";
static char rgb_to_gray_docstring[] = "Converts an 24bpp image to a gray-scaled 8bpp one.";

static PyMethodDef module_methods[] = {
	{"deskew", leper_deskew, METH_VARARGS, deskew_docstring},
	{"dewarp", leper_dewarp, METH_VARARGS, dewarp_docstring},
	{"otsu_binarize", leper_otsu_binarize, METH_VARARGS, otsu_binarize_docstring},
	{"sauvola_binarize", leper_sauvola_binarize, METH_VARARGS, sauvola_binarize_docstring},
	{"rgb_to_gray", leper_rgb_to_gray, METH_VARARGS, rgb_to_gray_docstring},
	{NULL, NULL, 0, NULL},
};

PyMODINIT_FUNC initleper(void) {
	PyObject *m = Py_InitModule3("leper", module_methods, module_docstring);
	if(m == NULL) { return; }
}


