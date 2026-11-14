#ifndef PELE_CUBLAS_BATCHED_LU_H
#define PELE_CUBLAS_BATCHED_LU_H

#include <cuda_runtime.h>
#include <cublas_v2.h>
#include <vector>
#include <cstddef>

namespace pele::physics::reactions::cvode {
namespace batched_lu_detail {
static __global__ void expand_csr(int n, int nnz, int batch,
  const int* rows, const int* cols, const double* values,
  double* dense, double** matrices) {
  for (int k=blockIdx.x*blockDim.x+threadIdx.x; k<batch*n;
       k+=blockDim.x*gridDim.x) {
    const int cell=k/n, row=k%n;
    double* matrix=dense+static_cast<std::size_t>(cell)*n*n;
    if(row==0) matrices[cell]=matrix;
    for(int col=0;col<n;++col) matrix[row+col*n]=0.;
    for(int q=rows[row];q<rows[row+1];++q)
      matrix[row+cols[q]*n]=values[static_cast<std::size_t>(cell)*nnz+q];
  }
}
static __global__ void rhs_pointers(int n,int batch,double* x,double** rhs) {
  for(int cell=blockIdx.x*blockDim.x+threadIdx.x;cell<batch;
      cell+=blockDim.x*gridDim.x) rhs[cell]=x+static_cast<std::size_t>(cell)*n;
}
}

// One independent double-precision system per cell, with partial pivoting.
// Factorization preserves the caller's CSR matrix and is reused by solve().
// Return 0 on success, 1 for singular LU, and -1 for a library/runtime error.
class CublasBatchedLU {
  int n_, batch_, nnz_;
  cudaStream_t stream_;
  cublasHandle_t handle_=nullptr;
  double* factors_=nullptr;
  double** matrices_=nullptr;
  double** rhs_=nullptr;
  int* pivots_=nullptr;
  int* info_=nullptr;
  std::vector<int> host_info_;
  bool initialized_=false, factored_=false;
public:
  CublasBatchedLU(int n,int batch,int nnz,cudaStream_t stream)
    : n_(n),batch_(batch),nnz_(nnz),stream_(stream),host_info_(batch) {
    if(n<=0 || batch<=0 || nnz<=0) return;
    if(cublasCreate(&handle_)!=CUBLAS_STATUS_SUCCESS) return;
    if(cublasSetStream(handle_,stream_)!=CUBLAS_STATUS_SUCCESS) return;
    if(cudaMalloc(&factors_,sizeof(double)*static_cast<std::size_t>(batch)*n*n)!=cudaSuccess ||
       cudaMalloc(&matrices_,sizeof(double*)*batch)!=cudaSuccess ||
       cudaMalloc(&rhs_,sizeof(double*)*batch)!=cudaSuccess ||
       cudaMalloc(&pivots_,sizeof(int)*static_cast<std::size_t>(batch)*n)!=cudaSuccess ||
       cudaMalloc(&info_,sizeof(int)*batch)!=cudaSuccess) return;
    initialized_=true;
  }
  CublasBatchedLU(const CublasBatchedLU&)=delete;
  CublasBatchedLU& operator=(const CublasBatchedLU&)=delete;
  ~CublasBatchedLU() {
    if(handle_) cublasDestroy(handle_);
    cudaFree(factors_); cudaFree(matrices_); cudaFree(rhs_);
    cudaFree(pivots_); cudaFree(info_);
  }
  bool initialized() const { return initialized_; }
  int factor(const int* rows,const int* cols,const double* values) {
    factored_=false;
    if(!initialized_ || !rows || !cols || !values) return -1;
    batched_lu_detail::expand_csr<<<(batch_*n_+127)/128,128,0,stream_>>>
      (n_,nnz_,batch_,rows,cols,values,factors_,matrices_);
    if(cudaGetLastError()!=cudaSuccess) return -1;
    if(cublasDgetrfBatched(handle_,n_,matrices_,n_,pivots_,info_,batch_)!=CUBLAS_STATUS_SUCCESS)
      return -1;
    if(cudaMemcpyAsync(host_info_.data(),info_,sizeof(int)*batch_,cudaMemcpyDeviceToHost,stream_)!=cudaSuccess ||
       cudaStreamSynchronize(stream_)!=cudaSuccess) return -1;
    for(int info:host_info_) {
      if(info<0) return -1;
      if(info>0) return 1;
    }
    factored_=true;
    return 0;
  }
  int solve(double* x,const double* b) {
    if(!factored_ || !x || !b) return -1;
    if(x!=b && cudaMemcpyAsync(x,b,sizeof(double)*static_cast<std::size_t>(batch_)*n_,
                              cudaMemcpyDeviceToDevice,stream_)!=cudaSuccess) return -1;
    batched_lu_detail::rhs_pointers<<<(batch_+127)/128,128,0,stream_>>>(n_,batch_,x,rhs_);
    if(cudaGetLastError()!=cudaSuccess) return -1;
    int info=0; // getrs reports argument validity to HOST; getrf has DEVICE info per cell.
    if(cublasDgetrsBatched(handle_,CUBLAS_OP_N,n_,1,
        const_cast<const double* const*>(matrices_),n_,pivots_,rhs_,n_,&info,batch_)!=CUBLAS_STATUS_SUCCESS || info!=0)
      return -1;
    return cudaStreamSynchronize(stream_)==cudaSuccess ? 0 : -1;
  }
};
}
#endif
