#include "mechanism.H"
const int rmap[NUM_REACTIONS] = {24,8,13,14,15,34,0,1,2,3,4,5,6,7,9,10,11,12,16,17,18,19,20,21,22,23,25,26,27,28,29,30,31,32,33,35,36};

// Returns 0-based map of reaction order
void GET_RMAP
(int * _rmap)
{
for (int j=0; j<NUM_REACTIONS; ++j)
{
_rmap[j] = rmap[j];
}
}

// Returns a count of gas species in a gas reaction, and their indices
// and stoichiometric coefficients. (Eq 50)
void CKINU(const int i, int& nspec, int ki[], int nu[])
{
const int ns[NUM_GAS_REACTIONS] =
     {5,4,4,4,4,4,3,3,3,3,4,4,3,2,3,3,4,4,4,4,4,4,4,4,3,4,4,4,4,4,4,3,4,4,3,4,4};
const int kiv[NUM_GAS_REACTIONS*5] =
     {0,1,3,2,1,0,4,2,5,0,6,1,5,4,0,5,4,6,1,0,7,4,6,8,0,6,8,7,4,0,8,5,4,0,0,4,8,5,0,0,6,1,12,0,0,6,12,4,0,0,6,12,7,1,0,12,4,8,1,0,12,9,1,0,0,9,4,0,0,0,6,4,8,0,0,8,6,4,0,0,10,4,11,6,0,11,6,10,4,0,2,1,3,12,0,2,4,3,8,0,2,5,13,6,0,2,5,14,19,0,2,12,3,9,0,2,6,3,7,0,2,6,16,0,0,3,6,17,7,0,3,1,18,19,0,3,1,13,5,0,14,1,18,4,0,14,5,18,6,0,16,1,2,12,0,13,20,6,0,0,20,6,14,10,0,18,4,8,19,0,19,10,6,0,0,19,1,10,12,0,17,4,20,6,0};
const int nuv[NUM_GAS_REACTIONS*5] =
     {-1,-1,1,5,1,-1,-1,6,1,0,-1,-1,1,1,0,-1,-1,1,1,0,-1,-1,1,1,0,-1,-1,1,1,0,-1,-1,2,0,0,-2,1,1,0,0,-1,-1,1,0,0,-1,-1,2,0,0,-1,-1,1,1,0,-1,-1,1,1,0,-2,1,1,0,0,-1,2,0,0,0,-1,-1,1,0,0,-1,1,1,0,0,-1,-1,1,1,0,-1,-1,1,1,0,-1,-1,1,1,0,-1,-1,1,1,0,-1,-1,1,1,0,-1,-1,1,1,0,-1,-1,1,1,0,-1,-1,1,1,0,-1,-1,1,0,0,-1,-1,1,1,0,-1,-1,1,1,0,-1,-1,1,1,0,-1,-1,1,1,0,-1,-1,1,1,0,-1,-1,1,1,0,-1,1,1,0,0,-1,-1,1,1,0,-1,-1,1,1,0,-1,1,1,0,0,-1,-1,1,1,0,-1,-1,1,1,0};
if (i < 1) {
// Return max num species per reaction
nspec = 5;
} else {
if (i > NUM_GAS_REACTIONS) {
nspec = -1;
} else {
nspec = ns[i-1];
for (int j=0; j<nspec; ++j) {
ki[j] = kiv[(i-1)*5 + j] + 1;
nu[j] = nuv[(i-1)*5 + j];
}
}
}
}

// Returns the progress rates of each reactions
// Given P, T, and mole fractions
void CKKFKR(const amrex::Real P, const amrex::Real T, const amrex::Real x[], amrex::Real q_f[], amrex::Real q_r[])
{
amrex::Real c[21]; // temporary storage
amrex::Real PORT = 1e6 * P/(8.31446261815324e+07 * T); // 1e6 * P/RT so c goes to SI units

// Compute conversion, see Eq 10
for (int id = 0; id < 21; ++id) {
c[id] = x[id]*PORT;
}

// convert to chemkin units
progressRateFR(q_f, q_r, c, T);

// convert to chemkin units
for (int id = 0; id < 37; ++id) {
q_f[id] *= 1.0e-6;
q_r[id] *= 1.0e-6;
}
}

// compute the progress rate for each reaction
// USES progressRate : todo switch to GPU
void progressRateFR(amrex::Real *  q_f, amrex::Real *  q_r, amrex::Real *  sc, amrex::Real T)
{
const amrex::Real invT = 1.0 / T;
const amrex::Real logT = log(T);
// compute the Gibbs free energy
amrex::Real g_RT[21];
gibbs(g_RT, T);

amrex::Real sc_qss[1];
comp_qfqr(q_f, q_r, sc, sc_qss, T, invT, logT);

}

// Returns the vector of strings of element names
void CKSYME_STR(amrex::Vector<std::string>& ename)
{
ename.resize(4);
ename[0] = "H";
ename[1] = "O";
ename[2] = "C";
ename[3] = "N";
}

// Returns the vector of strings of species names
void CKSYMS_STR(amrex::Vector<std::string>& kname)
{
kname.resize(21);
kname[0] = "C12H23";
kname[1] = "O2";
kname[2] = "C2H4";
kname[3] = "C2H3";
kname[4] = "OH";
kname[5] = "O";
kname[6] = "H";
kname[7] = "H2";
kname[8] = "H2O";
kname[9] = "H2O2";
kname[10] = "CO";
kname[11] = "CO2";
kname[12] = "HO2";
kname[13] = "CH2CHO";
kname[14] = "CH3";
kname[15] = "N2";
kname[16] = "C2H5";
kname[17] = "C2H2";
kname[18] = "CH2O";
kname[19] = "HCO";
kname[20] = "CH2CO";
}

// compute the sparsity pattern of the chemistry Jacobian
void SPARSITY_INFO( int * nJdata, const int * consP, int NCELLS)
{
amrex::GpuArray<amrex::Real,484> Jac = {0.0};
amrex::GpuArray<amrex::Real,21> conc = {0.0};
for (int n=0; n<21; n++) {
    conc[n] = 1.0/ 21.000000 ;
}
aJacobian(Jac.data(), conc.data(), 1500.0, *consP);

int nJdata_tmp = 0;
for (int k=0; k<22; k++) {
for (int l=0; l<22; l++) {
if(Jac[ 22 * k + l] != 0.0){
nJdata_tmp = nJdata_tmp + 1;
}
}
}

*nJdata = NCELLS * nJdata_tmp;
}



// compute the sparsity pattern of the system Jacobian
void SPARSITY_INFO_SYST( int * nJdata, const int * consP, int NCELLS)
{
amrex::GpuArray<amrex::Real,484> Jac = {0.0};
amrex::GpuArray<amrex::Real,21> conc = {0.0};
for (int n=0; n<21; n++) {
    conc[n] = 1.0/ 21.000000 ;
}
aJacobian(Jac.data(), conc.data(), 1500.0, *consP);

int nJdata_tmp = 0;
for (int k=0; k<22; k++) {
for (int l=0; l<22; l++) {
if(k == l){
nJdata_tmp = nJdata_tmp + 1;
} else {
if(Jac[ 22 * k + l] != 0.0){
nJdata_tmp = nJdata_tmp + 1;
}
}
}
}

*nJdata = NCELLS * nJdata_tmp;
}



// compute the sparsity pattern of the simplified (for preconditioning) system Jacobian
void SPARSITY_INFO_SYST_SIMPLIFIED( int * nJdata, const int * consP)
{
amrex::GpuArray<amrex::Real,484> Jac = {0.0};
amrex::GpuArray<amrex::Real,21> conc = {0.0};
for (int n=0; n<21; n++) {
    conc[n] = 1.0/ 21.000000 ;
}
aJacobian_precond(Jac.data(), conc.data(), 1500.0, *consP);

int nJdata_tmp = 0;
for (int k=0; k<22; k++) {
for (int l=0; l<22; l++) {
if(k == l){
nJdata_tmp = nJdata_tmp + 1;
} else {
if(Jac[ 22 * k + l] != 0.0){
nJdata_tmp = nJdata_tmp + 1;
}
}
}
}

nJdata[0] = nJdata_tmp;
}


// compute the sparsity pattern of the chemistry Jacobian in CSC format -- base 0
void SPARSITY_PREPROC_CSC(int *  rowVals, int *  colPtrs, const int * consP, int NCELLS)
{
amrex::GpuArray<amrex::Real,484> Jac = {0.0};
amrex::GpuArray<amrex::Real,21> conc = {0.0};
for (int n=0; n<21; n++) {
    conc[n] = 1.0/ 21.000000 ;
}
aJacobian(Jac.data(), conc.data(), 1500.0, *consP);

colPtrs[0] = 0;
int nJdata_tmp = 0;
for (int nc=0; nc<NCELLS; nc++) {
int offset_row = nc * 22;
int offset_col = nc * 22;
for (int k=0; k<22; k++) {
for (int l=0; l<22; l++) {
if(Jac[22*k + l] != 0.0) {
rowVals[nJdata_tmp] = l + offset_row; 
nJdata_tmp = nJdata_tmp + 1; 
}
}
colPtrs[offset_col + (k + 1)] = nJdata_tmp;
}
}
}

// compute the sparsity pattern of the chemistry Jacobian in CSR format -- base 0
void SPARSITY_PREPROC_CSR(int * colVals, int * rowPtrs, const int * consP, int NCELLS, int base)
{
amrex::GpuArray<amrex::Real,484> Jac = {0.0};
amrex::GpuArray<amrex::Real,21> conc = {0.0};
for (int n=0; n<21; n++) {
    conc[n] = 1.0/ 21.000000 ;
}
aJacobian(Jac.data(), conc.data(), 1500.0, *consP);

if (base == 1) {
rowPtrs[0] = 1;
int nJdata_tmp = 1;
for (int nc=0; nc<NCELLS; nc++) {
int offset = nc * 22;
for (int l=0; l<22; l++) {
for (int k=0; k<22; k++) {
if(Jac[22*k + l] != 0.0) {
colVals[nJdata_tmp-1] = k+1 + offset; 
nJdata_tmp = nJdata_tmp + 1; 
}
}
rowPtrs[offset + (l + 1)] = nJdata_tmp;
}
}
} else {
rowPtrs[0] = 0;
int nJdata_tmp = 0;
for (int nc=0; nc<NCELLS; nc++) {
int offset = nc * 22;
for (int l=0; l<22; l++) {
for (int k=0; k<22; k++) {
if(Jac[22*k + l] != 0.0) {
colVals[nJdata_tmp] = k + offset; 
nJdata_tmp = nJdata_tmp + 1; 
}
}
rowPtrs[offset + (l + 1)] = nJdata_tmp;
}
}
}
}

// compute the sparsity pattern of the system Jacobian
// CSR format BASE is user choice
void SPARSITY_PREPROC_SYST_CSR(int * colVals, int * rowPtr, const int * consP, int NCELLS, int base)
{
amrex::GpuArray<amrex::Real,484> Jac = {0.0};
amrex::GpuArray<amrex::Real,21> conc = {0.0};
for (int n=0; n<21; n++) {
    conc[n] = 1.0/ 21.000000 ;
}
aJacobian(Jac.data(), conc.data(), 1500.0, *consP);

if (base == 1) {
rowPtr[0] = 1;
int nJdata_tmp = 1;
for (int nc=0; nc<NCELLS; nc++) {
int offset = nc * 22;
for (int l=0; l<22; l++) {
for (int k=0; k<22; k++) {
if (k == l) {
colVals[nJdata_tmp-1] = l+1 + offset; 
nJdata_tmp = nJdata_tmp + 1; 
} else {
if(Jac[22*k + l] != 0.0) {
colVals[nJdata_tmp-1] = k+1 + offset; 
nJdata_tmp = nJdata_tmp + 1; 
}
}
}
rowPtr[offset + (l + 1)] = nJdata_tmp;
}
}
} else {
rowPtr[0] = 0;
int nJdata_tmp = 0;
for (int nc=0; nc<NCELLS; nc++) {
int offset = nc * 22;
for (int l=0; l<22; l++) {
for (int k=0; k<22; k++) {
if (k == l) {
colVals[nJdata_tmp] = l + offset; 
nJdata_tmp = nJdata_tmp + 1; 
} else {
if(Jac[22*k + l] != 0.0) {
colVals[nJdata_tmp] = k + offset; 
nJdata_tmp = nJdata_tmp + 1; 
}
}
}
rowPtr[offset + (l + 1)] = nJdata_tmp;
}
}
}
}

// compute the sparsity pattern of the simplified (for precond) system Jacobian on CPU
// BASE 0
void SPARSITY_PREPROC_SYST_SIMPLIFIED_CSC(int * rowVals, int * colPtrs, int * indx, const int * consP)
{
amrex::GpuArray<amrex::Real,484> Jac = {0.0};
amrex::GpuArray<amrex::Real,21> conc = {0.0};
for (int n=0; n<21; n++) {
    conc[n] = 1.0/ 21.000000 ;
}
aJacobian_precond(Jac.data(), conc.data(), 1500.0, *consP);

colPtrs[0] = 0;
int nJdata_tmp = 0;
for (int k=0; k<22; k++) {
for (int l=0; l<22; l++) {
if (k == l) {
rowVals[nJdata_tmp] = l; 
indx[nJdata_tmp] = 22*k + l;
nJdata_tmp = nJdata_tmp + 1; 
} else {
if(Jac[22*k + l] != 0.0) {
rowVals[nJdata_tmp] = l; 
indx[nJdata_tmp] = 22*k + l;
nJdata_tmp = nJdata_tmp + 1; 
}
}
}
colPtrs[k+1] = nJdata_tmp;
}
}

// compute the sparsity pattern of the simplified (for precond) system Jacobian
// CSR format BASE is under choice
void SPARSITY_PREPROC_SYST_SIMPLIFIED_CSR(int * colVals, int * rowPtr, const int * consP, int base)
{
amrex::GpuArray<amrex::Real,484> Jac = {0.0};
amrex::GpuArray<amrex::Real,21> conc = {0.0};
for (int n=0; n<21; n++) {
    conc[n] = 1.0/ 21.000000 ;
}
aJacobian_precond(Jac.data(), conc.data(), 1500.0, *consP);

if (base == 1) {
rowPtr[0] = 1;
int nJdata_tmp = 1;
for (int l=0; l<22; l++) {
for (int k=0; k<22; k++) {
if (k == l) {
colVals[nJdata_tmp-1] = l+1; 
nJdata_tmp = nJdata_tmp + 1; 
} else {
if(Jac[22*k + l] != 0.0) {
colVals[nJdata_tmp-1] = k+1; 
nJdata_tmp = nJdata_tmp + 1; 
}
}
}
rowPtr[l+1] = nJdata_tmp;
}
} else {
rowPtr[0] = 0;
int nJdata_tmp = 0;
for (int l=0; l<22; l++) {
for (int k=0; k<22; k++) {
if (k == l) {
colVals[nJdata_tmp] = l; 
nJdata_tmp = nJdata_tmp + 1; 
} else {
if(Jac[22*k + l] != 0.0) {
colVals[nJdata_tmp] = k; 
nJdata_tmp = nJdata_tmp + 1; 
}
}
}
rowPtr[l+1] = nJdata_tmp;
}
}
}
