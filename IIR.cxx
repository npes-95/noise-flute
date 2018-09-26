//IIR IIR class

#include "IIR.h"


IIR::IIR(double* a, std::size_t a_size,
             double* b, std::size_t b_size):
  a(a),
  b(b),
  a_size(a_size),
  b_size(b_size),
  process_buf(a_size,0)
{}

IIR::~IIR(){}

void IIR::process(double sig)
{
  //delay buffer is defined by order of IIR, so is the same size as the number of coefficients
  for (std::size_t(i) = {a_size-1}; i>0; i--)
  {
    process_buf[i] = process_buf[i-1];
  }

  process_buf[0] = sig;

}

void IIR::updatecoef(double* a, std::size_t a_size,
                     double* b, std::size_t b_size)
{
  this->a = a;
  this->b = b;
  this->a_size = a_size;
  this->b_size = b_size;
  this->process_buf.resize(a_size);
}

double IIR::iir_s(double sample)
{
  //iir IIR stuff
  double input_acc = sample;

  for (std::size_t(i) = {1}; i<a_size; i++)
  {
    input_acc -= a[i]*process_buf[i-1];
  }

  double output_acc = input_acc*b[0];

  for (std::size_t(i) = {1}; i<b_size; i++)
  {
    output_acc += b[i]*process_buf[i-1];
  }

  IIR::process(input_acc);

  return output_acc;

}

void IIR::iir_a(double* smp_in, const std::size_t smp_size)
{
  for (std::size_t(i) = {0}; i<smp_size; i++)
  {
    smp_in[i] = IIR::iir_s(smp_in[i]);
  }
}
