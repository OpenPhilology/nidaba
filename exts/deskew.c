#include <leptonica/allheaders.h>
#include <Python.h>
#include <stdio.h>

int deskew(char *in, char *out) {
	printf("%s %s\n", in, out);
	PIX* pix = pixRead(in);
	if(!pix) {
		return -1;
	}
	PIX *r;
	l_float32 skew;
	if((r = pixFindSkewAndDeskew(pix, 4, &skew, NULL)) == NULL) {
		return -1;
	}
	printf("Found skew %f\n", skew);
	pixWriteImpliedFormat(out, r, 100, 0);
	pixDestroy(&pix);
	return 0;
}

static PyObject *deskew_deskew(PyObject *self, PyObject *args) {
	char *in, *out;
	if(!PyArg_ParseTuple(args, "ss", &in, &out)) {
		return NULL;
	}
	int r = deskew(in, out);
	PyObject *ret = Py_BuildValue("i", r);
	return ret;
}

static char module_docstring[] = "This module provides an interface to leptonica's image deskewing.";
static char deskew_docstring[] = "Deskews an image.";

static PyMethodDef module_methods[] = {
	{"deskew", deskew_deskew, METH_VARARGS, deskew_docstring},
	{NULL, NULL, 0, NULL},
};

PyMODINIT_FUNC initdeskew(void) {
	PyObject *m = Py_InitModule3("deskew", module_methods, module_docstring);
	if(m == NULL) { return; }
}


