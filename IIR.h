#include <vector>
#include <cmath>
#include <iostream>


class IIR {

public:

  IIR(double* a, std::size_t a_size,
        double* b, std::size_t b_size);

  virtual ~IIR();

  void iir_a(double* smp_in, const std::size_t smp_size);

  void updatecoef(double* a, std::size_t a_size, double* b, std::size_t b_size);

private:

  void process(double in);

  double iir_s(double sample);

protected:

  double* a;
  double* b;
  std::size_t a_size;
  std::size_t b_size;
  std::vector<double> process_buf;


};
