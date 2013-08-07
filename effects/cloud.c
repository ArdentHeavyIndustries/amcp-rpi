/*
 * Cloud lighting effect core.
 *
 * This is like a low-level shader for our LED array. Takes parameters from our
 * high-level Python code, and generates a raw RGB pixel array ready to send via
 * Open Pixel Control.
 *
 * Our "cloud" effect is based on a 4-dimensional field of simplex perlin noise,
 * sampled at the location of each LED. The noise field can be rotated/translated
 * with an arbitrary 4x4 matrix, allowing "wind" effects as well as "turbulence"
 * caused by translating along the W axis. This noise field is mapped to color using
 * provided color vectors, and a list of optional in-cloud lightning points are
 * blended with the noise field.
 *
 *********************************************************************************
 *
 * Copyright (c) 2013 Micah Elizabeth Scott
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

#include <Python.h>
#include "noise.h"

static PyObject* py_render(PyObject* self, PyObject* args)
{
	const float *model;
	int modelBytes;
	float mat[16];
	float baseColor[3];
	float noiseColor[3];
	PyObject *lightningObj;
	char *pixels;
	int numPixels;
	PyObject *result;

	/*
	 * Parse and validate arguments
	 */

	if (!PyArg_ParseTuple(args, "t#(ffffffffffffffff)(fff)(fff)O:render",
		&model, &modelBytes,
		&mat[0], &mat[1], &mat[2],  &mat[3],  &mat[4],  &mat[5],  &mat[6],  &mat[7],
		&mat[8], &mat[9], &mat[10], &mat[11], &mat[12], &mat[13], &mat[14], &mat[15],
		&baseColor[0], &baseColor[1], &baseColor[2],
		&noiseColor[0], &noiseColor[1], &noiseColor[2],
		&lightningObj)) {
		return NULL;
	}

	if (!PySequence_Check(lightningObj)) {
		PyErr_SetString(PyExc_TypeError, "Lightning is not a sequence object");
		return NULL;
	}

	if (modelBytes % 12) {
		PyErr_SetString(PyExc_ValueError, "Model string is not a multiple of 12 bytes long");
		return NULL;
	}
	numPixels = modelBytes / 12;

	/*
	 * Allocate and fill pixel array
	 */

	pixels = PyMem_Malloc(numPixels * 3);
	if (!pixels) {
		return PyErr_NoMemory();
	}

	/*
	 * Return results
	 */

	result = PyString_FromStringAndSize(pixels, numPixels * 3);
	PyMem_Free(pixels);

	return result;
}

static PyMethodDef cloud_functions[] = {
	{ "render", (PyCFunction)py_render, METH_VARARGS,
		"render(model, matrix, baseColor, noiseColor, lightning) -- return rendered RGB pixels, as a string\n\n"
		"model -- (x,y,z) coordinates for each LED, represented as a string of packed 32-bit floats\n"
		"matrix -- List of 16 floats; a column-major 4x4 matrix which model coordinates are multiplied by\n"
		"baseColor -- (r,g,b) tuple for the base color to which other colors are added\n"
		"noiseColor -- (r,g,b) tuple which is multiplied by the noise field and added to the bsae color\n"
		"lightning -- List of lightning points, in model space. Each one is an (x, y, z, r, g, b, falloff) tuple\n"
	},
	{NULL}
};

PyDoc_STRVAR(module_doc, "Native-code cloud lighting effect core");

void initcloud(void)
{
	Py_InitModule3("cloud", cloud_functions, module_doc);
}