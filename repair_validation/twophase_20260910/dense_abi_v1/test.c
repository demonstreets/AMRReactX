#include <stdio.h>
#include <sunmatrix/sunmatrix_dense.h>
int main(){SUNContext c;SUNContext_Create(0,&c);SUNMatrix a=SUNDenseMatrix(3,3,c);printf("index=%zu api rows=%lld cols=%lld macro rows=%lld cols=%lld ptr=%p macro_ptr=%p\n",sizeof(sunindextype),(long long)SUNDenseMatrix_Rows(a),(long long)SUNDenseMatrix_Columns(a),(long long)SM_ROWS_D(a),(long long)SM_COLUMNS_D(a),(void*)SUNDenseMatrix_Cols(a),(void*)SM_COLS_D(a));SUNMatDestroy(a);SUNContext_Free(&c);}
