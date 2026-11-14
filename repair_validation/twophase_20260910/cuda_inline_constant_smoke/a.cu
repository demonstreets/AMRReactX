inline __constant__ const double weights[88]={1.0};
__global__ void a(double* p){p[threadIdx.x]=weights[threadIdx.x];}
