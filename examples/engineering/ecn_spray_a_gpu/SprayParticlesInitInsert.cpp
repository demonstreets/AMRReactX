#include "SprayParticles.H"
#include "SprayInjection.H"
#include "pelelmex_prob.H"

class ECNJet : public SprayJet
{
public:
  ECNJet(const std::string jet_name, const amrex::Geometry& geom)
    : SprayJet(jet_name, geom)
  {
  }

  bool get_new_particle(
    const amrex::Real time,
    const amrex::Real& phi_radial,
    const amrex::Real& cur_radius,
    amrex::Real& umag,
    amrex::Real& theta_spread,
    amrex::Real& phi_swirl,
    amrex::Real& dia_part,
    amrex::Real& T_part,
    amrex::Real* Y_part) override;
};

bool
ECNJet::get_new_particle(
  const amrex::Real time,
  const amrex::Real& phi_radial,
  const amrex::Real& cur_radius,
  amrex::Real& umag,
  amrex::Real& theta_spread,
  amrex::Real& phi_swirl,
  amrex::Real& dia_part,
  amrex::Real& T_part,
  amrex::Real* Y_part)
{
  umag = m_jetVel;
  T_part = m_jetT;
  dia_part = m_dropDist->get_dia();
  phi_swirl = 0.0;
  theta_spread = 0.0;  // No spread angle
  for (int sp = 0; sp < SPRAY_FUEL_NUM; ++sp) {
    Y_part[sp] = 0.0;
  }
  Y_part[0] = 1.0;  // Pure C12H23 fuel
  return true;
}

bool
SprayParticleContainer::injectParticles(
  amrex::Real time, amrex::Real dt, int nstep, int lev, int finest_level)
{
  if (lev != 0) {
    return false;
  }
  SprayJet* js = m_sprayJets[0].get();
  if (!js->jet_active(time)) {
    return false;
  }
  sprayInjection(time, js, dt, lev);
  return true;
}

void
SprayParticleContainer::InitSprayParticles(const bool init_parts)
{
  m_sprayJets.resize(1);
  std::string jet_name = "jet1";
  m_sprayJets[0] = std::make_unique<ECNJet>(jet_name, Geom(0));
  m_sprayJets[0]->set_inj_proc(0);
  return;
}
