#include "SprayParticles.H"
#include "SprayInjection.H"
#include "prob.H"

bool SprayParticleContainer::injectParticles(amrex::Real, amrex::Real, int, int lev, int) {
    return (lev != 0) ? false : false;
}

void SprayParticleContainer::InitSprayParticles(const bool) {
    const int npart = 100;
    const auto plo = Geom(0).ProbLo();
    const auto phi = Geom(0).ProbHi();
    for (int i = 0; i < npart; ++i) {
        ParticleType p;
        amrex::Real r = amrex::Random();
        p.id() = ParticleType::NextID();
        p.cpu() = amrex::ParallelDescriptor::MyProc();
        p.pos(0) = plo[0] + r * (phi[0] - plo[0]);
        p.pos(1) = plo[1] + 0.5 * (phi[1] - plo[1]);
        p.pos(2) = 0.0;
        p.rdata(SprayComps::pstateVel) = 1.0;
        p.rdata(SprayComps::pstateVel + 1) = 0.0;
#if AMREX_SPACEDIM == 3
        p.rdata(SprayComps::pstateVel + 2) = 0.0;
#endif
        p.rdata(SprayComps::pstateT) = 350.0;
        p.rdata(SprayComps::pstateDia) = 1.0e-4;
        p.rdata(SprayComps::pstateY) = 1.0;
        auto& ptile = GetParticles(0)[std::make_pair(0,0)];
        ptile.push_back(p);
    }
}
