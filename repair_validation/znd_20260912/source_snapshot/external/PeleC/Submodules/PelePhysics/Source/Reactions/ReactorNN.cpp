#include "AMReX_Reduce.H"
#include "ReactorNN.H"
#include <cstdio>
#include <cmath>
#include <cstdlib>
#include <string>

// ═══════════════════════════════════════
// Architecture: 12 -> 384 -> 384 -> 384 -> 384 -> 384 -> 10 (SiLU after each hidden)
// Output: signed-log rate → delta = dt * rate
// ═══════════════════════════════════════
#define RNN_N_HIDDEN 5
#define RNN_WIDTH 384

namespace pele::physics::reactions {

enum class RNNMode { PURE_NN, DIAGNOSTIC_ONLY, HYBRID };

// ── Weights (host) ──
static float *h_W[6], *h_B[6];
static const int W_sizes[6] = {4608, 147456, 147456, 147456, 147456, 3840}; // W0..W4
static const int B_sizes[6] = {384, 384, 384, 384, 384, 10};
// ── Normalization (loaded from file) ──
static float X_mean[12], X_std[12], X_std_ood[12], Z_mean[10], Z_std[10], RateScale[10];

// ── CPU NN forward ──
void rnn_forward_v3(const float* xn, float* z_out)
{
    float h[RNN_WIDTH], h_next[RNN_WIDTH];

    // Layer 0: input → hidden
    for (int i = 0; i < RNN_WIDTH; i++) {
        float sum = h_B[0][i];
        for (int j = 0; j < 12; j++) sum += h_W[0][i*12+j] * xn[j];
        h[i] = sum / (1.0f + expf(-sum));
    }

    // Layers 1-3: hidden → hidden
    for (int layer = 1; layer < RNN_N_HIDDEN; layer++) {
        for (int i = 0; i < RNN_WIDTH; i++) {
            float sum = h_B[layer][i];
            for (int j = 0; j < RNN_WIDTH; j++) sum += h_W[layer][i*RNN_WIDTH+j] * h[j];
            h_next[i] = sum / (1.0f + expf(-sum));
        }
        for (int i = 0; i < RNN_WIDTH; i++) h[i] = h_next[i];
    }

    // Output layer: hidden -> output (z_norm, 10 values)
    for (int i = 0; i < 10; i++) {
        float sum = h_B[5][i];
        for (int j = 0; j < RNN_WIDTH; j++) sum += h_W[5][i*RNN_WIDTH+j] * h[j];
        z_out[i] = sum;
    }
}

// ── Signed-log rate → delta ──
void slograte_to_delta(const float* z_norm, amrex::Real dt, amrex::Real* delta)
{
    for (int i = 0; i < 10; i++) {
        float z = z_norm[i] * Z_std[i] + Z_mean[i];
        float rate = (z >= 0.0f ? 1.0f : -1.0f) * RateScale[i] * (powf(10.0f, fabsf(z)) - 1.0f);
        delta[i] = (amrex::Real)(dt * rate);
    }
}

// ═══════════════════════════════════════
// ReactorNN class
// ═══════════════════════════════════════

int
ReactorNN::init(int reactor_type, int /*ncells*/)
{
    BL_PROFILE("Pele::ReactorNN::init()");
    m_reactor_type = reactor_type;
    ReactorTypes::check_reactor_type(m_reactor_type);

    amrex::ParmParse pp("ode");
    pp.query("verbose", verbose);

    std::string mode_str = "pure_nn";
    amrex::ParmParse ppr("reactornn");
    ppr.query("mode", mode_str);
    if (mode_str == "diagnostic_only")      m_mode = RNNMode::DIAGNOSTIC_ONLY;
    else if (mode_str == "hybrid")          m_mode = RNNMode::HYBRID;
    else                                    m_mode = RNNMode::PURE_NN;

    ppr.query("ood_threshold", m_ood_threshold);
    ppr.query("low_temp_threshold", m_low_temp_threshold);
    ppr.query("write_diagnostics", m_write_diagnostics);
    ppr.query("enable_fallback", m_enable_fallback);

    amrex::Print() << "ReactorNN v4.2: mode=" << mode_str
                   << " ood=" << m_ood_threshold
                   << " Tmin=" << m_low_temp_threshold << "\n";

    // ── Load weights ──
    std::string weights_path;
    std::string norm_path;
    ppr.query("weights_path", weights_path);
    ppr.query("norm_path", norm_path);
    if (weights_path.empty()) {
        if (const char* env = std::getenv("REACTORNN_WEIGHTS_PATH")) weights_path = env;
    }
    if (norm_path.empty()) {
        if (const char* env = std::getenv("REACTORNN_NORM_PATH")) norm_path = env;
    }
    if (weights_path.empty() || norm_path.empty()) {
        amrex::Print() << "ReactorNN: missing model paths; set reactornn.weights_path/reactornn.norm_path "
                       << "or REACTORNN_WEIGHTS_PATH/REACTORNN_NORM_PATH\n";
        return 1;
    }

    const char* wpath = weights_path.c_str();
    const char* npath = norm_path.c_str();
    FILE* fp = fopen(wpath, "rb");
    if (!fp) { amrex::Print() << "ReactorNN: cannot open " << wpath << "\n"; return 1; }
    fseek(fp, 0, SEEK_END); long wsz = ftell(fp); rewind(fp);
    float* wbuf = new float[wsz/4];
    fread(wbuf, sizeof(float), wsz/4, fp); fclose(fp);

    for (int l = 0; l < 6; l++) {
        h_W[l] = new float[W_sizes[l]];
        h_B[l] = new float[B_sizes[l]];
    }

    // Sequential offsets: W0=3072 B0=256 W1=65536 B1=256 W2=65536 B2=256 W3=65536 B3=256 W4=2560 B4=10
    int off = 0;
    memcpy(h_W[0], wbuf + off, 4608*4); off += 4608;
    memcpy(h_B[0], wbuf + off, 384*4);  off += 384;
    memcpy(h_W[1], wbuf + off, 147456*4); off += 147456;
    memcpy(h_B[1], wbuf + off, 384*4);  off += 384;
    memcpy(h_W[2], wbuf + off, 147456*4); off += 147456;
    memcpy(h_B[2], wbuf + off, 384*4);  off += 384;
    memcpy(h_W[3], wbuf + off, 147456*4); off += 147456;
    memcpy(h_B[3], wbuf + off, 384*4);  off += 384;
    memcpy(h_W[4], wbuf + off, 147456*4); off += 147456;
    memcpy(h_B[4], wbuf + off, 384*4);  off += 384;
    memcpy(h_W[5], wbuf + off, 3840*4); off += 3840;
    memcpy(h_B[5], wbuf + off, 10*4);

    delete[] wbuf;
    amrex::Print() << "ReactorNN: loaded " << off << " weight floats\n";

    // ── Load normalization ──
    fp = fopen(npath, "rb");
    if (!fp) { amrex::Print() << "ReactorNN: cannot open " << npath << "\n"; return 1; }
    float nbuf[54];
    fread(nbuf, sizeof(float), 54, fp); fclose(fp);
    memcpy(X_mean, nbuf, 12*4);
    memcpy(X_std, nbuf+12, 12*4);
    memcpy(Z_mean, nbuf+24, 10*4);
    memcpy(Z_std, nbuf+34, 10*4);
    memcpy(RateScale, nbuf+44, 10*4);

    // Keep training normalization for inference, but use a wider physical
    // scale for OOD gating so tiny radical std values do not reject burned gas.
    memcpy(X_std_ood, X_std, 12*4);

    // The v4 dataset uses a fixed chemistry dt, so logdt has near-zero std.
    // Restore the trained-export compatibility floor for NN inference.
    for (int j = 0; j < 12; j++) if (X_std[j] < 1.0e-4f) X_std[j] = 1.0f;

    const float ood_floor[12] = {0.18f, 0.10f, 0.020f, 0.080f, 0.080f,
                                 0.002f, 0.010f, 0.010f, 2.0e-4f, 2.0e-5f,
                                 0.002f, 0.10f};
    for (int j = 0; j < 12; j++) if (X_std_ood[j] < ood_floor[j]) X_std_ood[j] = ood_floor[j];

    // ── Create fallback ──
    if (m_mode == RNNMode::DIAGNOSTIC_ONLY || (m_mode == RNNMode::HYBRID && m_enable_fallback)) {
        m_fallback = ReactorBase::create("ReactorRK64");
        if (m_fallback) {
            m_fallback->init(m_reactor_type, 0);
            amrex::Print() << "ReactorNN: fallback ReactorRK64 ready\n";
        }
    }
    return 0;
}

void ReactorNN::close()
{
    for (int l = 0; l < 6; l++) { delete[] h_W[l]; delete[] h_B[l]; }
    if (m_fallback) { m_fallback->close(); m_fallback.reset(); }
}

// Stub
int ReactorNN::react(amrex::Real*,amrex::Real*,amrex::Real*,amrex::Real*,amrex::Real&,amrex::Real&,int
#ifdef AMREX_USE_GPU
,amrex::gpuStream_t
#endif
) { return 0; }

// ── Main Array4 react ──
int ReactorNN::react(
    const amrex::Box& box,
    amrex::Array4<amrex::Real> const& rY_in,
    amrex::Array4<amrex::Real> const& rYsrc_in,
    amrex::Array4<amrex::Real> const& T_in,
    amrex::Array4<amrex::Real> const& rEner_in,
    amrex::Array4<amrex::Real> const& rEner_src_in,
    amrex::Array4<amrex::Real> const& FC_in,
    amrex::Array4<int> const&,
    amrex::Real& dt_react, amrex::Real& time
#ifdef AMREX_USE_GPU
    ,amrex::gpuStream_t stream
#endif
)
{
    BL_PROFILE("Pele::ReactorNN::react()");
    int ncells = static_cast<int>(box.numPts());
    if (ncells == 0) return 0;
    auto len = amrex::length(box), lo = amrex::lbound(box);
    int nx = len.x, ny = len.y;
    auto* leosparm = m_d_eosparm;

    // LiDryer molwt: H2=2.016 O2=32 H2O=18.016 H=1.008 O=16 OH=17.008 HO2=33.008 H2O2=34.016 N2=28.013
    const amrex::Real molwt[9] = {2.016, 32.0, 18.016, 1.008, 16.0, 17.008, 33.008, 34.016, 28.013};

    // ── Phase 1: Pack ──
    amrex::Gpu::DeviceVector<amrex::Real> d_rhoY(ncells*NUM_SPECIES,0), d_T(ncells,0), d_rho(ncells,0);
    amrex::Real *p_rhoY=d_rhoY.data(), *p_T=d_T.data(), *p_rho=d_rho.data();

    amrex::ParallelFor(box, [=] AMREX_GPU_DEVICE(int i,int j,int k) noexcept {
        int ic=(k-lo.z)*nx*ny+(j-lo.y)*nx+(i-lo.x);
        auto eos=pele::physics::PhysicsType::eos(leosparm);
        amrex::Real tmp[NUM_SPECIES],mf[NUM_SPECIES],rho=0,ri=0;
        for(int s=0;s<NUM_SPECIES;s++)tmp[s]=rY_in(i,j,k,s);
        eos.RY2RRinvY(tmp,rho,ri,mf);
        p_rho[ic]=rho; p_T[ic]=T_in(i,j,k,0);
        for(int s=0;s<NUM_SPECIES;s++)p_rhoY[ic*NUM_SPECIES+s]=rY_in(i,j,k,s);
    });

    // ── Phase 2: dtoh ──
    amrex::Vector<amrex::Real> h_rhoY(ncells*NUM_SPECIES), h_T(ncells), h_rho(ncells);
    amrex::Gpu::dtoh_memcpy(h_rhoY.data(),p_rhoY,ncells*NUM_SPECIES*sizeof(amrex::Real));
    amrex::Gpu::dtoh_memcpy(h_T.data(),p_T,ncells*sizeof(amrex::Real));
    amrex::Gpu::dtoh_memcpy(h_rho.data(),p_rho,ncells*sizeof(amrex::Real));

    int nn_ok=0, nn_skip=0, nn_bad=0;
    float max_xn=0;
    amrex::Real dT_abs_sum=0.0, dT_abs_max=0.0, dY_abs_max=0.0;
    int err_count=0;

    // ═══════════════════════════════════
    // DIAGNOSTIC_ONLY / HYBRID: fallback first
    // ═══════════════════════════════════
    if ((m_mode == RNNMode::DIAGNOSTIC_ONLY || m_mode == RNNMode::HYBRID) && m_fallback) {
        m_fallback->set_eos_parm(m_h_eosparm, m_d_eosparm);
        m_fallback->react(box,rY_in,rYsrc_in,T_in,rEner_in,rEner_src_in,FC_in,
                          amrex::Array4<int>{},dt_react,time
#ifdef AMREX_USE_GPU
                          ,stream
#endif
        );

        // Read back after-state
        amrex::Gpu::DeviceVector<amrex::Real> d_ryA(ncells*NUM_SPECIES,0), d_TA(ncells,0);
        amrex::Real *p_ryA=d_ryA.data(), *p_TA=d_TA.data();
        amrex::ParallelFor(box,[=]AMREX_GPU_DEVICE(int i,int j,int k)noexcept{
            int ic=(k-lo.z)*nx*ny+(j-lo.y)*nx+(i-lo.x);
            for(int s=0;s<NUM_SPECIES;s++)p_ryA[ic*NUM_SPECIES+s]=rY_in(i,j,k,s);
            p_TA[ic]=T_in(i,j,k,0);
        });
        amrex::Vector<amrex::Real> h_ryA(ncells*NUM_SPECIES), h_TA(ncells);
        amrex::Gpu::dtoh_memcpy(h_ryA.data(),p_ryA,ncells*NUM_SPECIES*sizeof(amrex::Real));
        amrex::Gpu::dtoh_memcpy(h_TA.data(),p_TA,ncells*sizeof(amrex::Real));

        // NN diagnostic
        for (int ic=0; ic<ncells; ic++) {
            amrex::Real Tb=h_T[ic], rhob=h_rho[ic];
            if (Tb < m_low_temp_threshold) continue;

            amrex::Real Y[9]={0}, sY=0;
            for(int s=0;s<9;s++) {Y[s]=(rhob>1e-50)?h_rhoY[ic*NUM_SPECIES+s]/rhob:0; if(Y[s]<0)Y[s]=0; if(Y[s]>1)Y[s]=1; sY+=Y[s];}
            if(sY>1e-50) for(int s=0;s<9;s++) Y[s]/=sY;

            amrex::Real iW=0; for(int s=0;s<9;s++) if(molwt[s]>0)iW+=Y[s]/molwt[s];
            amrex::Real Rs=(iW>1e-50)?8.314462618e7*iW:2.87e6;
            amrex::Real Pa=rhob*Rs*Tb/1.01325e6;

            // NN input
            float xraw[12], xn[12], xood[12];
            xraw[0]=log10f(fmaxf(Tb,1.f));
            xraw[1]=log10f(fmaxf(Pa,1e-10f));
            for(int s=0;s<9;s++)xraw[2+s]=(float)Y[s];
            xraw[11]=log10f(fmaxf(dt_react,1e-20f));
            for(int j=0;j<12;j++){
                xn[j]=(xraw[j]-X_mean[j])/X_std[j];
                xood[j]=(xraw[j]-X_mean[j])/X_std_ood[j];
            }

            float mxn=0; for(int j=0;j<12;j++){float a=fabsf(xood[j]); if(a>mxn)mxn=a;}
            if(mxn>max_xn)max_xn=mxn;
            if(mxn>m_ood_threshold){nn_skip++; continue;}

            float zn[10]; rnn_forward_v3(xn,zn);
            amrex::Real delta[10]; slograte_to_delta(zn,dt_react,delta);
            bool delta_ok=true;
            for(int q=0;q<10;q++) if(!std::isfinite((double)delta[q])) delta_ok=false;
            if(fabs(delta[9]) > 50.0) delta_ok=false;
            for(int q=0;q<9;q++) if(fabs(delta[q]) > 0.05) delta_ok=false;
            if(!delta_ok){ nn_bad++; nn_skip++; continue; }
            nn_ok++;

            amrex::Real Ta=h_TA[ic], dT_rk=Ta-Tb;
            amrex::Real dT_err=fabs(delta[9]-dT_rk);
            dT_abs_sum += dT_err;
            if(dT_err>dT_abs_max) dT_abs_max=dT_err;
            for(int s=0;s<9;s++){
                amrex::Real dY_rk=(rhob>1e-50)?h_ryA[ic*NUM_SPECIES+s]/rhob-Y[s]:0.0;
                amrex::Real e=fabs(delta[s]-dY_rk);
                if(e>dY_abs_max) dY_abs_max=e;
            }
            err_count++;

            static int sct=0;
            if(sct<3 && m_write_diagnostics){
                printf("[NNv3 cell=%d] Tb=%.1f T_nn=%.1f T_rk=%.1f dT_nn=%.4e dT_rk=%.4e dY_nn=%.2e\n",
                       ic,Tb,Tb+delta[9],Ta,delta[9],dT_rk,delta[0]);
                sct++;
            }
        }
        if(m_write_diagnostics) {
            amrex::Print()<<"[ReactorNN v4.2 DIAG] cells="<<ncells<<" nn_ok="<<nn_ok
                          <<" skip="<<nn_skip<<" bad="<<nn_bad<<" max_xn_ood="<<max_xn;
            if(err_count>0) {
                amrex::Print()<<" dT_abs_mean="<<(dT_abs_sum/err_count)
                              <<" dT_abs_max="<<dT_abs_max
                              <<" dY_abs_max="<<dY_abs_max;
            }
            amrex::Print()<<"\n";
        }
        return 0;
    }

    // ═══════════════════════════════════
    // PURE_NN mode
    // ═══════════════════════════════════
    for (int ic=0; ic<ncells; ic++) {
        amrex::Real Tb=h_T[ic], rhob=h_rho[ic];
        if (Tb < m_low_temp_threshold) continue;

        amrex::Real Y[9]={0}, sY=0;
        for(int s=0;s<9;s++){Y[s]=(rhob>1e-50)?h_rhoY[ic*NUM_SPECIES+s]/rhob:0; if(Y[s]<0)Y[s]=0;if(Y[s]>1)Y[s]=1;sY+=Y[s];}
        if(sY>1e-50) for(int s=0;s<9;s++)Y[s]/=sY;

        amrex::Real iW=0; for(int s=0;s<9;s++)if(molwt[s]>0)iW+=Y[s]/molwt[s];
        amrex::Real Rs=(iW>1e-50)?8.314462618e7*iW:2.87e6, Pa=rhob*Rs*Tb/1.01325e6;

        float xraw[12], xn[12], xood[12];
        xraw[0]=log10f(fmaxf(Tb,1.f));
        xraw[1]=log10f(fmaxf(Pa,1e-10f));
        for(int s=0;s<9;s++)xraw[2+s]=(float)Y[s];
        xraw[11]=log10f(fmaxf(dt_react,1e-20f));
        for(int j=0;j<12;j++){
            xn[j]=(xraw[j]-X_mean[j])/X_std[j];
            xood[j]=(xraw[j]-X_mean[j])/X_std_ood[j];
        }

        float mxn=0; for(int j=0;j<12;j++){float a=fabsf(xood[j]);if(a>mxn)mxn=a;}
        if(mxn>m_ood_threshold) continue;

        float zn[10]; rnn_forward_v3(xn,zn);
        amrex::Real delta[10]; slograte_to_delta(zn,dt_react,delta);
        bool delta_ok=true;
        for(int q=0;q<10;q++) if(!std::isfinite((double)delta[q])) delta_ok=false;
        if(fabs(delta[9]) > 50.0) delta_ok=false;
        for(int q=0;q<9;q++) if(fabs(delta[q]) > 0.05) delta_ok=false;
        if(!delta_ok) continue;

        for(int s=0;s<9;s++){
            amrex::Real nv=h_rhoY[ic*NUM_SPECIES+s]+rhob*delta[s];
            if(nv<0)nv=0; h_rhoY[ic*NUM_SPECIES+s]=nv;
        }
        amrex::Real nT=Tb+delta[9]; if(nT<1)nT=1; h_T[ic]=nT;
        nn_ok++;
    }

    // Write back
    amrex::Gpu::htod_memcpy(p_rhoY,h_rhoY.data(),ncells*NUM_SPECIES*sizeof(amrex::Real));
    amrex::Gpu::htod_memcpy(p_T,h_T.data(),ncells*sizeof(amrex::Real));
    amrex::ParallelFor(box,[=]AMREX_GPU_DEVICE(int i,int j,int k)noexcept{
        int ic=(k-lo.z)*nx*ny+(j-lo.y)*nx+(i-lo.x);
        for(int s=0;s<NUM_SPECIES;s++)rY_in(i,j,k,s)=p_rhoY[ic*NUM_SPECIES+s];
        T_in(i,j,k,0)=p_T[ic];
    });

    return 0;
}

} // namespace pele::physics::reactions
