#include "CublasBatchedLU.H"
#include <algorithm>
#include <cmath>
#include <iostream>
#include <stdexcept>
using pele::physics::reactions::cvode::CublasBatchedLU;
void check(bool valid,const char* why) { if(!valid) throw std::runtime_error(why); }
template<class T> T* device(const std::vector<T>& host) {
  T* p=nullptr; check(cudaMalloc(&p,host.size()*sizeof(T))==cudaSuccess,"allocation");
  check(cudaMemcpy(p,host.data(),host.size()*sizeof(T),cudaMemcpyHostToDevice)==cudaSuccess,"copy");
  return p;
}
int main() {
  double worst=0.; int tested=0;
  for(int n:{3,17,89}) for(int batch:{1,7,128}) {
    std::vector<int> rows(n+1),cols;
    for(int i=0;i<n;++i) {
      rows[i]=cols.size();
      for(int j=0;j<n;++j) if(i==j || std::abs(i-j)==1 || j==(i+5)%n) cols.push_back(j);
    }
    rows[n]=cols.size(); const int nnz=cols.size();
    std::vector<double> a(batch*nnz),dense(batch*n*n,0.),rhs(batch*n),expected(batch*n);
    for(int k=0;k<batch;++k) for(int i=0;i<n;++i) for(int q=rows[i];q<rows[i+1];++q) {
      int j=cols[q]; double v=i==j ? n+1.+k*.01 : .2*std::sin(i+2*j+k+.3);
      // An invertible leading block that requires a row interchange.
      if(i==0 && j==0) v=0.;
      if(i==0 && j==1) v=2.;
      if(i==1 && j==0) v=3.;
      a[k*nnz+q]=v; dense[(k*n+i)*n+j]=v;
    }
    auto* dr=device(rows);auto* dc=device(cols);auto* da=device(a);
    auto* dx=device(rhs);auto* db=device(rhs);
    {
      CublasBatchedLU lu(n,batch,nnz,nullptr);check(lu.initialized(),"initialize");
      check(lu.solve(dx,db)<0,"unfactored solve must fail");
      check(lu.factor(dr,dc,da)==0,"pivoted factorization");
      for(int trial=0;trial<3;++trial) {
        for(int k=0;k<batch;++k) for(int j=0;j<n;++j) expected[k*n+j]=std::sin(.1*j+k+trial)+.2;
        for(int k=0;k<batch;++k) for(int i=0;i<n;++i) {
          long double sum=0.;for(int j=0;j<n;++j)sum+=static_cast<long double>(dense[(k*n+i)*n+j])*expected[k*n+j];
          rhs[k*n+i]=sum;
        }
        check(cudaMemcpy(db,rhs.data(),rhs.size()*sizeof(double),cudaMemcpyHostToDevice)==cudaSuccess,"rhs copy");
        double* answer=trial==2 ? db : dx;
        check(lu.solve(answer,db)==0,"solve and factor reuse");
        std::vector<double> result(rhs.size());
        check(cudaMemcpy(result.data(),answer,result.size()*sizeof(double),cudaMemcpyDeviceToHost)==cudaSuccess,"answer copy");
        for(int k=0;k<batch;++k) for(int i=0;i<n;++i) {
          long double ax=0.,scale=std::abs(rhs[k*n+i]);
          for(int j=0;j<n;++j) {const double v=dense[(k*n+i)*n+j];ax+=static_cast<long double>(v)*result[k*n+j];scale+=std::abs(v*result[k*n+j]);}
          const double residual=std::abs(ax-rhs[k*n+i])/std::max(1.L,scale);
          worst=std::max(worst,residual);
          check(residual<2.e-13,"linear residual");
          check(std::abs(result[k*n+i]-expected[k*n+i])<2.e-11,"known solution");
        }
      }
      std::vector<double> after(a.size());cudaMemcpy(after.data(),da,after.size()*sizeof(double),cudaMemcpyDeviceToHost);
      check(after==a,"factor must preserve caller matrix");
      std::fill(a.begin(),a.begin()+nnz,0.);cudaMemcpy(da,a.data(),a.size()*sizeof(double),cudaMemcpyHostToDevice);
      check(lu.factor(dr,dc,da)==1,"singular batch must fail");
      check(lu.solve(dx,db)<0,"failed factor must invalidate old LU");
    }
    cudaFree(dr);cudaFree(dc);cudaFree(da);cudaFree(dx);cudaFree(db);tested+=batch;
  }
  std::cout<<"PASS "<<tested<<" systems, pivoting, reused factors, in-place RHS, singular rejection; worst residual "<<worst<<"\n";
}
