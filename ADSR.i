/* ADSR.i */

%module ADSR
%{
/* Includes the header in the wrapper code */
#define SWIG_FILE_WITH_INIT
#include "ADSR.h"
%}

/* Use the numpy interface for ndarrays. See the warning below */
%include <numpy.i>

%init %{
import_array();
%}

/* Match the arguments of our various C++ methods */
%apply (double* INPLACE_ARRAY1, int DIM1) { (double* smp_in, const std::size_t smp_size) };

/* Parse the header file to generate wrappers */
%include "ADSR.h"
