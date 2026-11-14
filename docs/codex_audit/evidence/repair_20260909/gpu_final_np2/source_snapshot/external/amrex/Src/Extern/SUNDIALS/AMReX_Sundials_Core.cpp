#include <AMReX_Print.H>
#include <AMReX_Sundials_Core.H>
#include <AMReX_SUNMemory.H>
#include <AMReX_Vector.H>
#include <AMReX_ParallelDescriptor.H>

namespace amrex::sundials {

namespace {
    amrex::Vector<int> initialized;
    amrex::Vector<::sundials::Context*> the_sundials_context;
}

void Initialize(int nthreads)
{
    amrex::Print() << "Initializing SUNDIALS with " << nthreads << " threads...\n";

    // Initialize the sundials context
    if (initialized.empty()) {
        initialized.resize(nthreads);
        std::fill(initialized.begin(), initialized.end(), 0);
        the_sundials_context.resize(nthreads);
        std::fill(the_sundials_context.begin(), the_sundials_context.end(), nullptr);
    }
#ifdef BL_USE_MPI
    int mpi_rank, mpi_size;
    MPI_Comm_rank(ParallelDescriptor::Communicator(), &mpi_rank);
    MPI_Comm_size(ParallelDescriptor::Communicator(), &mpi_size);
    for (int serial_rank = 0; serial_rank < mpi_size; ++serial_rank) {
        if (serial_rank == mpi_rank) {
#endif
            for (int i = 0; i < nthreads; i++) {
                if (initialized[i]) { continue; }
                initialized[i] = 1;
                BL_ASSERT(the_sundials_context[i] == nullptr);
                the_sundials_context[i] = new ::sundials::Context();
            }
#ifdef BL_USE_MPI
        }
        MPI_Barrier(ParallelDescriptor::Communicator());
    }
#endif

    // Initialize the memory helper
    MemoryHelper::Initialize(nthreads);

    amrex::Print() << "SUNDIALS initialized.\n";
}

void Finalize()
{
    // Cleanup the memory helpers
    MemoryHelper::Finalize();

    // Clean up the sundials contexts
    for (int i = 0; i < initialized.size(); i++) {
        initialized[i] = 0;
        delete the_sundials_context[i];
        the_sundials_context[i] = nullptr;
    }
}

::sundials::Context* The_Sundials_Context(int i)
{
    BL_ASSERT(the_sundials_context[i] != nullptr);
    return the_sundials_context[i];
}

}//amrex::sundials
