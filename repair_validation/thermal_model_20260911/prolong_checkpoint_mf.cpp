#include <AMReX.H>
#include <AMReX_MultiFab.H>
#include <AMReX_MultiFabUtil.H>
#include <AMReX_ParmParse.H>
#include <AMReX_VisMF.H>
#include <filesystem>
#include <iomanip>

// Conservative piecewise-constant prolongation of native cell-average data.
// This utility does not evolve chemistry, modify thermodynamics or create particles.
int main(int argc, char* argv[]) {
  amrex::Initialize(argc, argv);
  {
    amrex::ParmParse pp;
    std::string source, destination;
    int ratio = 1;
    pp.get("source", source); pp.get("destination", destination); pp.get("ratio", ratio);
    AMREX_ALWAYS_ASSERT(ratio == 1 || ratio == 2);
    AMREX_ALWAYS_ASSERT(!std::filesystem::exists(destination+"_H"));
    amrex::MultiFab coarse;
    amrex::VisMF::Read(coarse, source);
    AMREX_ALWAYS_ASSERT(coarse.nGrow() == 0);
    AMREX_ALWAYS_ASSERT(coarse.ixType().cellCentered());
    amrex::BoxArray fine_boxes(coarse.boxArray());
    fine_boxes.refine(ratio);
    amrex::MultiFab fine(fine_boxes, coarse.DistributionMap(), coarse.nComp(), 0);
    for (amrex::MFIter mfi(fine); mfi.isValid(); ++mfi) {
      auto old = coarse.const_array(mfi);
      auto next = fine.array(mfi);
      amrex::ParallelFor(mfi.validbox(), coarse.nComp(),
        [=] AMREX_GPU_DEVICE(int i, int j, int k, int n) noexcept {
          next(i,j,k,n) = old(i/ratio,j/ratio,k,n);
        });
    }
    amrex::MultiFab recovered(coarse.boxArray(), coarse.DistributionMap(), coarse.nComp(), 0);
    amrex::average_down(fine, recovered, 0, coarse.nComp(), ratio);
    amrex::MultiFab::Subtract(recovered, coarse, 0, 0, coarse.nComp(), 0);
    amrex::Vector<amrex::Real> errors(coarse.nComp()), sums(coarse.nComp()), refined_sums(coarse.nComp());
    for (int n=0; n<coarse.nComp(); ++n) {
      errors[n]=recovered.norm0(n);
      sums[n]=coarse.sum(n);
      refined_sums[n]=fine.sum(n)/(ratio*ratio);
      AMREX_ALWAYS_ASSERT(errors[n] == 0.);
    }
    amrex::VisMF::Write(fine, destination);
    amrex::Print()<<std::setprecision(17)<<"PROLONGATION_RESULT {\"ratio\":"<<ratio
      <<",\"components\":"<<coarse.nComp()<<",\"coarse_cells\":"<<coarse.boxArray().numPts()
      <<",\"fine_cells\":"<<fine.boxArray().numPts()<<",\"components_audit\":[";
    for (int n=0; n<coarse.nComp(); ++n) {
      if(n)amrex::Print()<<",";
      amrex::Print()<<"{\"component\":"<<n<<",\"coarse_sum\":"<<sums[n]
        <<",\"fine_sum_divided_by_ratio_squared\":"<<refined_sums[n]
        <<",\"restriction_max_abs_error\":"<<errors[n]<<"}";
    }
    amrex::Print()<<"]}\n";
  }
  amrex::Finalize();
}
