#ifndef RIEMANN_H
#define RIEMANN_H
#include <AMReX.H>
#include <AMReX_Math.H>
#include "Constants.H"
#include <iostream>
#include "PelePhysics.H"

AMREX_GPU_DEVICE
AMREX_FORCE_INLINE
void
riemann(
  const amrex::Real rl,
  const amrex::Real ul,
  const amrex::Real vl,
  const amrex::Real v2l,
  const amrex::Real pl,
  const amrex::Real spl[NUM_SPECIES],
  const amrex::Real rr,
  const amrex::Real ur,
  const amrex::Real vr,
  const amrex::Real v2r,
  const amrex::Real pr,
  const amrex::Real spr[NUM_SPECIES],
  const int bc_test_val,
  const amrex::Real cav,
  amrex::Real& ustar,
  amrex::Real& uflx_rho,
  amrex::Real uflx_rhoY[NUM_SPECIES],
  amrex::Real& uflx_u,
  amrex::Real& uflx_v,
  amrex::Real& uflx_w,
  amrex::Real& uflx_eden,
  amrex::Real& uflx_eint,
  amrex::Real& qint_iu,
  amrex::Real& qint_iv1,
  amrex::Real& qint_iv2,
  amrex::Real& qint_gdpres,
  amrex::Real& qint_gdgame,
  amrex::Real omegal = 0.0,
  amrex::Real radl = 0.0,
  amrex::Real omegar = 0.0,
  amrex::Real radr = 0.0)
{
  const amrex::Real wsmall = std::numeric_limits<amrex::Real>::min();

  auto eos = pele::physics::PhysicsType::eos();

  amrex::Real gdnv_state_massfrac[NUM_SPECIES];
  for (int n = 0; n < NUM_SPECIES; n++) {
    gdnv_state_massfrac[n] = spl[n];
  }
  amrex::Real cl = 0.0;
  eos.RPY2Cs(rl, pl, gdnv_state_massfrac, cl);

  for (int n = 0; n < NUM_SPECIES; n++) {
    gdnv_state_massfrac[n] = spr[n];
  }
  amrex::Real cr = 0.0;
  eos.RPY2Cs(rr, pr, gdnv_state_massfrac, cr);

  const amrex::Real wl = amrex::max<amrex::Real>(wsmall, cl * rl);
  const amrex::Real wr = amrex::max<amrex::Real>(wsmall, cr * rr);
  const amrex::Real pstar = amrex::max<amrex::Real>(
    std::numeric_limits<amrex::Real>::min(),
    ((wr * pl + wl * pr) + wl * wr * (ul - ur)) / (wl + wr));
  ustar = ((wl * ul + wr * ur) + (pl - pr)) / (wl + wr);

  // The acoustic star estimate can approach numerical vacuum in a strong
  // expansion. Evaluating NASA thermochemistry at DBL_MIN pressure produces
  // 0*Inf in the polynomial energy. Use a conservative local Lax-Friedrichs
  // flux from the admissible input states before evaluating such a star EOS.
  // This fallback is deliberately dissipative and does not impose a pressure
  // floor on the evolved conservative state.
  if (pstar < 1.0e-8 * amrex::min(pl, pr)) {
    amrex::Real el, er;
    eos.RYP2E(rl, spl, pl, el);
    eos.RYP2E(rr, spr, pr, er);
    const amrex::Real speed = amrex::max(std::abs(ul) + cl, std::abs(ur) + cr);
    const amrex::Real EL = rl * (el + 0.5 *
      (ul*ul + vl*vl + v2l*v2l - omegal*omegal*radl*radl));
    const amrex::Real ER = rr * (er + 0.5 *
      (ur*ur + vr*vr + v2r*v2r - omegar*omegar*radr*radr));
    uflx_rho = 0.5 * (rl*ul + rr*ur - speed*(rr-rl));
    for (int n = 0; n < NUM_SPECIES; ++n) {
      uflx_rhoY[n] = 0.5 * (rl*spl[n]*ul + rr*spr[n]*ur
                           - speed*(rr*spr[n]-rl*spl[n]));
    }
    uflx_u = 0.5 * (rl*ul*ul + pl + rr*ur*ur + pr
                    - speed*(rr*ur-rl*ul));
    uflx_v = 0.5 * (rl*ul*vl + rr*ur*vr - speed*(rr*vr-rl*vl));
    uflx_w = 0.5 * (rl*ul*v2l + rr*ur*v2r - speed*(rr*v2r-rl*v2l));
    uflx_eden = 0.5 * ((EL+pl)*ul + (ER+pr)*ur - speed*(ER-EL));
    uflx_eint = 0.5 * (rl*el*ul + rr*er*ur - speed*(rr*er-rl*el));
    qint_iu = ustar = (rl*ul + rr*ur)/(rl+rr);
    qint_iv1 = (rl*vl + rr*vr)/(rl+rr);
    qint_iv2 = (rl*v2l + rr*v2r)/(rl+rr);
    qint_gdpres = 0.5*(pl+pr);
    qint_gdgame = 1.0 + (pl+pr)/(rl*el+rr*er);
    if (bc_test_val == 0) {
      qint_iu = ustar = 0.0;
      uflx_rho = uflx_v = uflx_w = uflx_eden = uflx_eint = 0.0;
      for (int n = 0; n < NUM_SPECIES; ++n) { uflx_rhoY[n] = 0.0; }
    }
    return;
  }

  bool mask = ustar > 0.0;
  amrex::Real ro = 0.0;
  amrex::Real rspo[NUM_SPECIES];
  for (int n = 0; n < NUM_SPECIES; n++) {
    rspo[n] = mask ? rl * spl[n] : rr * spr[n];
    ro += rspo[n];
  }
  amrex::Real uo = mask ? ul : ur;
  amrex::Real po = mask ? pl : pr;

  mask = std::abs(ustar) <
           constants::smallu() * 0.5 * (std::abs(ul) + std::abs(ur)) ||
         ustar == 0.0;
  ustar = mask ? 0.0 : ustar;
  ro = 0.0;
  for (int n = 0; n < NUM_SPECIES; n++) {
    rspo[n] = mask ? 0.5 * (rl * spl[n] + rr * spr[n]) : rspo[n];
    ro += rspo[n];
  }
  uo = mask ? 0.5 * (ul + ur) : uo;
  po = mask ? 0.5 * (pl + pr) : po;

  amrex::Real gdnv_state_rho = ro;
  amrex::Real gdnv_state_p = po;
  for (int n = 0; n < NUM_SPECIES; n++) {
    gdnv_state_massfrac[n] = rspo[n] / ro;
  }
  amrex::Real gdnv_state_e;
  eos.RYP2E(gdnv_state_rho, gdnv_state_massfrac, gdnv_state_p, gdnv_state_e);
  amrex::Real co;
  eos.RPY2Cs(gdnv_state_rho, gdnv_state_p, gdnv_state_massfrac, co);

  const amrex::Real drho = (pstar - po) / (co * co);
  amrex::Real rstar = 0.0;
  amrex::Real rspstar[NUM_SPECIES];
  for (int n = 0; n < NUM_SPECIES; n++) {
    const amrex::Real spon = rspo[n] / ro;
    rspstar[n] = amrex::max<amrex::Real>(0.0, rspo[n] + drho * spon);
    rstar += rspstar[n];
  }
  gdnv_state_rho = rstar;
  gdnv_state_p = pstar;
  for (int n = 0; n < NUM_SPECIES; n++) {
    gdnv_state_massfrac[n] = rspstar[n] / rstar;
  }
  eos.RYP2E(gdnv_state_rho, gdnv_state_massfrac, gdnv_state_p, gdnv_state_e);
  amrex::Real cstar;
  eos.RPY2Cs(gdnv_state_rho, gdnv_state_p, gdnv_state_massfrac, cstar);

  const amrex::Real sgnm = std::copysign(1.0, ustar);

  amrex::Real spout = co - sgnm * uo;
  amrex::Real spin = cstar - sgnm * ustar;
  const amrex::Real ushock = 0.5 * (spin + spout);

  mask = pstar < po;
  spout = mask ? spout : ushock;
  spin = mask ? spin : ushock;

  const amrex::Real scr = (std::abs(spout - spin) < constants::very_small_num())
                            ? constants::small_num() * cav
                            : spout - spin;
  const amrex::Real frac = amrex::max<amrex::Real>(
    0.0, amrex::min<amrex::Real>(1.0, (1.0 + (spout + spin) / scr) * 0.5));

  mask = ustar > 0.0;
  qint_iv1 = mask ? vl : vr;
  qint_iv2 = mask ? v2l : v2r;
  amrex::Real omega = mask ? omegal : omegar;
  amrex::Real rad = mask ? radl : radr;

  mask = (ustar == 0.0);
  qint_iv1 = mask ? 0.5 * (vl + vr) : qint_iv1;
  qint_iv2 = mask ? 0.5 * (v2l + v2r) : qint_iv2;
  amrex::Real rgd = 0.0;
  amrex::Real rspgd[NUM_SPECIES];
  for (int n = 0; n < NUM_SPECIES; n++) {
    rspgd[n] = frac * rspstar[n] + (1.0 - frac) * rspo[n];
    rgd += rspgd[n];
  }
  qint_iu = frac * ustar + (1.0 - frac) * uo;
  qint_gdpres = frac * pstar + (1.0 - frac) * po;
  gdnv_state_rho = rgd;
  gdnv_state_p = qint_gdpres;
  for (int n = 0; n < NUM_SPECIES; n++) {
    gdnv_state_massfrac[n] = rspgd[n] / rgd;
  }
  eos.RYP2E(gdnv_state_rho, gdnv_state_massfrac, gdnv_state_p, gdnv_state_e);

  mask = (spout < 0.0);
  rgd = 0.0;
  for (int n = 0; n < NUM_SPECIES; n++) {
    rspgd[n] = mask ? rspo[n] : rspgd[n];
    rgd += rspgd[n];
  }
  qint_iu = mask ? uo : qint_iu;
  qint_gdpres = mask ? po : qint_gdpres;

  mask = (spin >= 0.0);
  rgd = 0.0;
  for (int n = 0; n < NUM_SPECIES; n++) {
    rspgd[n] = mask ? rspstar[n] : rspgd[n];
    rgd += rspgd[n];
  }
  qint_iu = mask ? ustar : qint_iu;
  qint_gdpres = mask ? pstar : qint_gdpres;

  gdnv_state_rho = rgd;
  gdnv_state_p = qint_gdpres;
  for (int n = 0; n < NUM_SPECIES; n++) {
    gdnv_state_massfrac[n] = rspgd[n] / rgd;
  }
  eos.RYP2E(gdnv_state_rho, gdnv_state_massfrac, gdnv_state_p, gdnv_state_e);
  amrex::Real regd = gdnv_state_rho * gdnv_state_e;

  qint_gdgame = qint_gdpres / regd + 1.0;
  qint_iu = bc_test_val * qint_iu;
  uflx_rho = rgd * qint_iu;
  for (int n = 0; n < NUM_SPECIES; n++) {
    uflx_rhoY[n] = rspgd[n] * qint_iu;
  }
  uflx_u = uflx_rho * qint_iu + qint_gdpres;
  uflx_v = uflx_rho * qint_iv1;
  uflx_w = uflx_rho * qint_iv2;
  // Hari S: see Blazek's textbook,
  // Computational fluid dynamics: principles and applications
  // Appendix A3, Navier-Stokes in rotating frame of reference
  const amrex::Real rhoetot =
    regd +
    0.5 * rgd * (qint_iu * qint_iu + qint_iv1 * qint_iv1 + qint_iv2 * qint_iv2)
    // rotational frame energy
    - 0.5 * rgd * omega * omega * rad * rad;
  uflx_eden = qint_iu * (rhoetot + qint_gdpres);
  uflx_eint = qint_iu * regd;
}

AMREX_GPU_DEVICE
AMREX_FORCE_INLINE
void
laxfriedrich_flux(
  const amrex::Real rl,
  const amrex::Real ul,
  const amrex::Real vl,
  const amrex::Real v2l,
  const amrex::Real pl,
  const amrex::Real spl[NUM_SPECIES],
  const amrex::Real rr,
  const amrex::Real ur,
  const amrex::Real vr,
  const amrex::Real v2r,
  const amrex::Real pr,
  const amrex::Real spr[NUM_SPECIES],
  const int /*unused*/,
  const amrex::Real /*unused*/,
  amrex::Real& ustar,
  amrex::Real& maxeigval,
  amrex::Real& uflx_rho,
  amrex::Real uflx_rhoY[NUM_SPECIES],
  amrex::Real& uflx_u,
  amrex::Real& uflx_v,
  amrex::Real& uflx_w,
  amrex::Real& uflx_eden,
  amrex::Real& uflx_eint,
  amrex::Real omegal = 0.0,
  amrex::Real radl = 0.0,
  amrex::Real omegar = 0.0,
  amrex::Real radr = 0.0)
{

  const amrex::Real wsmall = std::numeric_limits<amrex::Real>::min();

  auto eos = pele::physics::PhysicsType::eos();

  amrex::Real cl = 0.0;
  amrex::Real mfrac_l[NUM_SPECIES];
  amrex::Real mfrac_r[NUM_SPECIES];
  for (int n = 0; n < NUM_SPECIES; n++) {
    mfrac_l[n] = spl[n];
    mfrac_r[n] = spr[n];
  }
  eos.RPY2Cs(rl, pl, mfrac_l, cl);

  amrex::Real cr = 0.0;
  eos.RPY2Cs(rr, pr, mfrac_r, cr);

  amrex::Real el = 0.0;
  eos.RYP2E(rl, mfrac_l, pl, el);

  amrex::Real er = 0.0;
  eos.RYP2E(rr, mfrac_r, pr, er);

  // rho e total
  // Hari S: see Blazek's textbook,
  // Computational fluid dynamics: principles and applications
  // Appendix A3, Navier-Stokes in rotating frame of reference
  amrex::Real r_elt = rl * (el +
                            0.5 * (ul * ul + vl * vl + v2l * v2l)
                            // rotational frame energy
                            - 0.5 * omegal * omegal * radl * radl);
  amrex::Real r_ert = rr * (er +
                            0.5 * (ur * ur + vr * vr + v2r * v2r)
                            // rotational frame energy
                            - 0.5 * omegar * omegar * radr * radr);

  const amrex::Real wl = amrex::max<amrex::Real>(wsmall, cl * rl);
  const amrex::Real wr = amrex::max<amrex::Real>(wsmall, cr * rr);
  ustar = ((wl * ul + wr * ur) + (pl - pr)) / (wl + wr);

  bool mask = std::abs(ustar) <
                constants::smallu() * 0.5 * (std::abs(ul) + std::abs(ur)) ||
              ustar == 0.0;
  ustar = mask ? 0.0 : ustar;

  amrex::Real chalf = 0.5 * (cr + cl);
  amrex::Real max_wavespd = std::abs(ustar) + chalf;

  maxeigval = max_wavespd;

  // density and mass frac eqn
  uflx_rho = 0.0;
  for (int n = 0; n < NUM_SPECIES; n++) {
    uflx_rhoY[n] = 0.5 * ((rl * ul * spl[n] + rr * ur * spr[n]) -
                          max_wavespd * (rr * spr[n] - rl * spl[n]));
    uflx_rho += uflx_rhoY[n];
  }

  // three momentum eqns
  uflx_u = 0.5 * ((rl * ul * ul + pl + rr * ur * ur + pr) -
                  max_wavespd * (rr * ur - rl * ul));
  uflx_v =
    0.5 * ((rl * vl * ul + rr * vr * ur) - max_wavespd * (rr * vr - rl * vl));
  uflx_w = 0.5 * ((rl * v2l * ul + rr * v2r * ur) -
                  max_wavespd * (rr * v2r - rl * v2l));

  // total energy eqn
  uflx_eden = 0.5 * (((r_elt + pl) * ul + (r_ert + pr) * ur) -
                     max_wavespd * (r_ert - r_elt));

  // not really used
  uflx_eint =
    0.5 * ((rl * el * ul + rr * er * ur) - max_wavespd * (rr * er - rl * el));
}
#endif
 
int main() {
 double y[NUM_SPECIES]={};y[H2O_ID]=1.;auto eos=pele::physics::PhysicsType::eos();
 for(double vel: {0.,100000.,284000.,500000.}) {
  double rho=.00176155,p=1.8e7,c;eos.RPY2Cs(rho,p,y,c);
  double us,fr,fy[NUM_SPECIES],fu,fv,fw,fe,fi,qu,qv,qw,qp,qg;
  riemann(rho,-vel,0,0,p,y,rho,vel,0,0,p,y,1,c,us,fr,fy,fu,fv,fw,fe,fi,qu,qv,qw,qp,qg);
  for(double value:{us,fr,fu,fv,fw,fe,fi,qu,qv,qw,qp,qg}) if(!std::isfinite(value)) return 1;
  if(fr!=0. || fe!=0.)return 2;
 }
 // Unequal reconstructed compositions must never create wall mass/energy flow.
 double yl[NUM_SPECIES]={};yl[H2_ID]=.1;yl[O2_ID]=.9;
 double us,fr,fy[NUM_SPECIES],fu,fv,fw,fe,fi,qu,qv,qw,qp,qg;
 riemann(.001,10000,0,0,1e6,yl,.001,-10000,0,0,1e6,y,0,1e5,us,fr,fy,fu,fv,fw,fe,fi,qu,qv,qw,qp,qg);
 if(fr!=0. || fe!=0. || fi!=0. || qu!=0.)return 3;
 for(double f:fy)if(f!=0.)return 4;
 std::cout<<"PASS actual Fuego/Riemann: finite expansion fluxes and impermeable wall fluxes\n";
}
