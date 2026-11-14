#include "SprayParticles.H"
#include "SprayInjection.H"
#include "prob.H"

bool
SprayParticleContainer::injectParticles(
  amrex::Real /*time*/,
  amrex::Real /*dt*/,
  int /*nstep*/,
  int /*lev*/,
  int /*finest_level*/)
{
  // No injection for this case — particles initialized from file
  return false;
}

void
SprayParticleContainer::InitSprayParticles(const bool /*init_parts*/)
{
  // No spray jets — all particles initialized from init_file
  return;
}
