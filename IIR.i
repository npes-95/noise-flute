/* File: IIR.i */

/* Name our python module */
%module Filter

/* Put the literal code needed at the top of the output file */
%{
#define SWIG_FILE_WITH_INIT
#include "IIR.h"
%}

/* Use the numpy interface for ndarrays. See the warning below */
%include <numpy.i>

%init %{
import_array();
%}

/* Match the arguments of our various C++ methods */
%apply (double* IN_ARRAY1, int DIM1) { (double* a, std::size_t a_size) };
%apply (double* IN_ARRAY1, int DIM1) { (double* b, std::size_t b_size) };
%apply (double* INPLACE_ARRAY1, int DIM1) { (double* smp_in, const std::size_t smp_size) };

/* Parse the c++ header file and generate the output file */
%include "IIR.h"
