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
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>

/* leper is Iris' wrapper around leptonica doing miscellaneous image processing
 * work that is too cumbersome or slow for python. */

int exists(char *path) {
	struct stat sb;
	if(stat(path, &sb) || !S_ISREG(sb.st_mode)) {
		return -1;
	}
	return 0;
}

/* Dewarps a single page. TODO: Create a function to build a dewarp model for a
 * whole codex and apply to all pages. */
char *dewarp(char *in, char *out) {
	
	if(exists(in)) {
		return NULL;
	}
	PIX *pix = pixRead(in);
	if(!pix) {
		return NULL;
	}
	if(pix->d != 1) {
		pixDestroy(&pix);
		return NULL;
	}
	PIX *ret;
	if(dewarpSinglePage(pix, 0, 0, 1, &ret, NULL, 0) == 1) {
		pixDestroy(&pix);
		return NULL;
	}
	pixWriteImpliedFormat(out, ret, 100, 0);
	pixDestroy(&pix);
	pixDestroy(&ret);
	return out;
}

static PyObject *leper_dewarp(PyObject *self, PyObject *args) {
	PyUnicodeObject *uin, *uout;
	if(!PyArg_ParseTuple(args, "UU", &uin, &uout)) {
		return NULL;
	}
	char *in = PyString_AsString(PyUnicode_AsUTF8String((PyObject *)uin));
	char *out = PyString_AsString(PyUnicode_AsUTF8String((PyObject *)uout));
	char *r = dewarp(in, out);
	if(r == NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}
	PyObject *ret = PyUnicode_FromString(r);
	return ret;
}


/* Converts a 32bpp input image to an 8bpp grayscale one. */
char *rgb_to_gray(char *in, char *out) {

	if(exists(in)) {
		return NULL;
	}

	PIX *pix = pixRead(in);
	if(!pix) {
		return NULL;
	}
        PIX *r;
	if((r = pixConvertRGBToGray(pix, 0.0, 0.0, 0.0)) == NULL) {
		return NULL;
	}
	pixWriteImpliedFormat(out, r, 100, 0);
	pixDestroy(&pix);
	pixDestroy(&r);
	return out;
}

static PyObject *leper_rgb_to_gray(PyObject *self, PyObject *args) {
	PyUnicodeObject *uin, *uout;
	if(!PyArg_ParseTuple(args, "UU", &uin, &uout)) {
		return NULL;
	}
	char *in = PyString_AsString(PyUnicode_AsUTF8String((PyObject *)uin));
	char *out = PyString_AsString(PyUnicode_AsUTF8String((PyObject *)uout));
	char *r = rgb_to_gray(in, out);
	if(r == NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}
	PyObject *ret = PyUnicode_FromString(r);
	return ret;
}

/* Runs a tiled localized binarization of the input images */
char *sauvola_binarize(char *in, char *out, l_int32 thresh, l_float32 factor) {

	if(exists(in)) {
		return NULL;
	}

	PIX* pix = pixRead(in);
	if(!pix) {
		return NULL;
	}
	if(pix->d != 8) {
		pixDestroy(&pix);
		return NULL;
	}
	PIX *r = NULL;
	if(pixSauvolaBinarize(pix, thresh, factor, 0, NULL, NULL, NULL, &r) == 1) {
		pixDestroy(&pix);
		return NULL;
	}
	pixWriteImpliedFormat(out, r, 100, 0);
	pixDestroy(&r);
	pixDestroy(&pix);
	return out;
}

static PyObject *leper_sauvola_binarize(PyObject *self, PyObject *args) {
	PyUnicodeObject *uin, *uout;
	l_int32 thresh = 10;
	l_float32 factor = 0.3;
	if(!PyArg_ParseTuple(args, "UU|if", &uin, &uout, &thresh, &factor)) {
		return NULL;
	}
	char *in = PyString_AsString(PyUnicode_AsUTF8String((PyObject *)uin));
	char *out = PyString_AsString(PyUnicode_AsUTF8String((PyObject *)uout));
	char *r = sauvola_binarize(in, out, thresh, factor);
	if(r == NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}
	PyObject *ret = PyUnicode_FromString(r);
	return ret;
}

char *otsu_binarize(char *in, char *out, l_int32 thresh, l_int32 mincount,
		  l_int32 bgval, l_int32 smoothx, l_int32 smoothy) {

	if(exists(in)) {
		return NULL;
	}
	PIX* pix = pixRead(in);
	if(!pix) {
		return NULL;
	}
	if(pix->d != 8) {
		pixDestroy(&pix);
		return NULL;
	}

	l_int32 sx = 10, sy = 15;
	/* Normalizes the background followd by Otsu thresholding. Refer to the
	 * leptonica documentation for further details. */
	PIX *r;
	if((r = pixOtsuThreshOnBackgroundNorm(pix, NULL, sx, sy, thresh,
					mincount, bgval, smoothx,
					smoothy, 0.1, NULL)) == NULL) {
		pixDestroy(&pix);
		return NULL;
	}
	pixWriteImpliedFormat(out, r, 100, 0);
	pixDestroy(&r);
	pixDestroy(&pix);
	return out;
}

static PyObject *leper_otsu_binarize(PyObject *self, PyObject *args) {
	PyUnicodeObject *uin, *uout;
	l_int32 thresh = 100;
	l_int32 mincount = 50;
	l_int32 bgval = 255;
	l_int32 smoothx = 2;
	l_int32 smoothy = 2;
	if(!PyArg_ParseTuple(args, "UU|iiiii", &uin, &uout, &thresh,
				&mincount, &bgval, &smoothx, &smoothy)) {
		return NULL;
	}
	char *in = PyString_AsString(PyUnicode_AsUTF8String((PyObject *)uin));
	char *out = PyString_AsString(PyUnicode_AsUTF8String((PyObject *)uout));
	char *r = otsu_binarize(in, out, thresh, mincount, bgval, smoothx,
			smoothy);
	if(r == NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}
	PyObject *ret = PyUnicode_FromString(r);
	return ret;
}

char *deskew(char *in, char *out) {

	if(exists(in)) {
		return NULL;
	}

	PIX* pix = pixRead(in);
	if(!pix) {
		return NULL;
	}

	PIX *r;
	l_float32 skew;
	if((r = pixFindSkewAndDeskew(pix, 4, &skew, NULL)) == NULL) {
		return NULL;
	}
	pixWriteImpliedFormat(out, r, 100, 0);
	pixDestroy(&pix);
	pixDestroy(&r);
	return out;
}

static PyObject *leper_deskew(PyObject *self, PyObject *args) {
	PyUnicodeObject *uin, *uout;
	if(!PyArg_ParseTuple(args, "UU", &uin, &uout)) {
		return NULL;
	}
	char *in = PyString_AsString(PyUnicode_AsUTF8String((PyObject *)uin));
	char *out = PyString_AsString(PyUnicode_AsUTF8String((PyObject *)uout));
	char *r = deskew(in, out);
	if(r == NULL) {
		r =  Py_BuildValue("s", "");
	}
	PyObject *ret = PyUnicode_FromString(r);
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


