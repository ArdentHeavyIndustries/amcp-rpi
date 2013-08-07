#!/usr/bin/env python

from distutils.core import setup, Extension

setup(
    packages=['effects'],
    py_modules=[
    	'server', 'fastopc',
    ],
	ext_modules=[
		Extension('effects.cloud', ['effects/cloud.c'], 
			extra_compile_args=['-Os', '-funroll-loops', '-ffast-math'],
		),
	],
)
