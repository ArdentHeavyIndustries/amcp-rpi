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

#define ALWAYS_INLINE __attribute__((always_inline))


// We may expose these parameters to Python if needed, but so far there's no demand
static const int NUM_OCTAVES = 4;
static const float PERSISTENCE = 0.5;
static const float LACUNARITY = 2.0;


typedef struct {
    float center[3];
    float color[3];
    float falloff;
} Lightning_t;

typedef struct {
    const float *model;
    float mat[16];
    float baseColor[3];
    float noiseColor[3];
    int pixelCount;
    int lightningCount; 
    Lightning_t *lightning;
} CloudArgs_t;


inline static char ALWAYS_INLINE packChannel(float c)
{
    /*
     * Clamp, scale, and pack a floating point channel value as an 8-bit integer.
     */

    int value = (int) ((c * 255.0f) + 0.5f);
    if (value < 0) value = 0;
    if (value > 255) value = 255;
    return value;
}


inline static void ALWAYS_INLINE render(CloudArgs_t args, char *pixels)
{
    /*
     * Low-level rendering core. Uses parameters in 'args' (inlined), places results
     * in the provided pixel buffer.
     */

    while (args.pixelCount--) {
        float x0, y0, z0, x, y, z, w, r, g, b, n;
        int ltCount = args.lightningCount;
        Lightning_t *ltPtr = args.lightning;

        // Model-space vector. (w0 assumed to be 1)
        x0 = args.model[0];
        y0 = args.model[1];
        z0 = args.model[2];
        args.model += 3;

        // Matrix multiply
        x = args.mat[0] * x0 + args.mat[4] * y0 + args.mat[8] * z0 + args.mat[12];
        y = args.mat[1] * x0 + args.mat[5] * y0 + args.mat[9] * z0 + args.mat[13];
        z = args.mat[2] * x0 + args.mat[6] * y0 + args.mat[10] * z0 + args.mat[14];
        w = args.mat[3] * x0 + args.mat[7] * y0 + args.mat[11] * z0 + args.mat[15];

        // Fractional brownian motion
        n = fbm_noise4(x, y, z, w, NUM_OCTAVES, PERSISTENCE, LACUNARITY);

        // Color interpolation
        r = args.baseColor[0] + n * args.noiseColor[0];
        g = args.baseColor[1] + n * args.noiseColor[1];
        b = args.baseColor[2] + n * args.noiseColor[2];

        // Sum the effects of each lightning object
        while (ltCount--) {

            // Squared distance from lightning center
            float xd = ltPtr->center[0] - x0;
            float yd = ltPtr->center[1] - y0;
            float zd = ltPtr->center[2] - z0;
            float dist2 = xd*xd + yd*yd + zd*zd;

            // Falloff calculation
            float intensity = 1.0f / (1.0f + ltPtr->falloff * dist2);

            r += intensity * ltPtr->color[0];
            g += intensity * ltPtr->color[1];
            b += intensity * ltPtr->color[2];

            ltPtr++;
        }

        pixels[0] = packChannel(r);
        pixels[1] = packChannel(g);
        pixels[2] = packChannel(b);
        pixels += 3;
    }
}


static PyObject* py_render(PyObject* self, PyObject* args)
{
    /*
     * Python argument parsing and return formatting for render()
     */

    CloudArgs_t ca;
    int i, modelBytes;
    Py_ssize_t tmp;
    PyObject *lightningObj;
    char *pixels;
    PyObject *result = NULL;

    if (!PyArg_ParseTuple(args, "t#(ffffffffffffffff)(fff)(fff)O:render",
        &ca.model, &modelBytes,
        &ca.mat[0],  &ca.mat[1],  &ca.mat[2],  &ca.mat[3],  
        &ca.mat[4],  &ca.mat[5],  &ca.mat[6],  &ca.mat[7],
        &ca.mat[8],  &ca.mat[9],  &ca.mat[10], &ca.mat[11], 
        &ca.mat[12], &ca.mat[13], &ca.mat[14], &ca.mat[15],
        &ca.baseColor[0], &ca.baseColor[1], &ca.baseColor[2],
        &ca.noiseColor[0], &ca.noiseColor[1], &ca.noiseColor[2],
        &lightningObj)) {
        return NULL;
    }

    if (modelBytes % 12) {
        PyErr_SetString(PyExc_ValueError, "Model string is not a multiple of 12 bytes long");
        return NULL;
    }
    ca.pixelCount = modelBytes / 12;

    if (!PySequence_Check(lightningObj)) {
        PyErr_SetString(PyExc_TypeError, "Lightning is not a sequence object");
        return NULL;
    }
    ca.lightningCount = (int) PySequence_Length(lightningObj);

    ca.lightning = PyMem_Malloc(ca.lightningCount * sizeof ca.lightning[0]);
    if (!ca.lightning) {
        return PyErr_NoMemory();
    }

    for (i = 0; i < ca.lightningCount; ++i) {
        PyObject *item = PySequence_GetItem(lightningObj, i);
        Lightning_t *lt = &ca.lightning[i];

        if (!PyArg_Parse(item, "(fffffff)",
            &lt->center[0], &lt->center[1], &lt->center[2],
            &lt->color[0], &lt->color[1], &lt->color[2],
            &lt->falloff)) {
            Py_DECREF(item);
            PyMem_Free(ca.lightning);
            return NULL;
        }
        Py_DECREF(item);
    }

    result = PyBuffer_New(ca.pixelCount * 3);
    if (result) {
        PyObject_AsWriteBuffer(result, (void**) &pixels, &tmp);
        render(ca, pixels);
    }

    PyMem_Free(ca.lightning);
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