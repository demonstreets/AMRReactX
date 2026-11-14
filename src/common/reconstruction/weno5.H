#ifndef RECONSTRUCTION_WENO5_H
#define RECONSTRUCTION_WENO5_H

#ifndef AMREX_GPU_HOST_DEVICE
#define AMREX_GPU_HOST_DEVICE
#endif

#include <cmath>

namespace reconstruction {

enum class WENOVariant { JS, Z };

/// Smoothness indicators (Jiang-Shu 1996)
/// Computes beta0, beta1, beta2 from 5 cell-averaged values.
template <typename T>
AMREX_GPU_HOST_DEVICE
void smoothness_indicators(const T u_im2, const T u_im1, const T u_i,
                           const T u_ip1, const T u_ip2,
                           T& beta0, T& beta1, T& beta2)
{
    // beta0 = (13/12)*(u_im2 - 2*u_im1 + u_i)^2 + (1/4)*(u_im2 - 4*u_im1 + 3*u_i)^2
    // beta1 = (13/12)*(u_im1 - 2*u_i + u_ip1)^2 + (1/4)*(u_im1 - u_ip1)^2
    // beta2 = (13/12)*(u_i - 2*u_ip1 + u_ip2)^2 + (1/4)*(3*u_i - 4*u_ip1 + u_ip2)^2

    const T c13_12 = T(13) / T(12);
    const T c1_4   = T(1)  / T(4);

    beta0 = c13_12 * (u_im2 - T(2)*u_im1 + u_i) * (u_im2 - T(2)*u_im1 + u_i)
          + c1_4   * (u_im2 - T(4)*u_im1 + T(3)*u_i) * (u_im2 - T(4)*u_im1 + T(3)*u_i);

    beta1 = c13_12 * (u_im1 - T(2)*u_i + u_ip1) * (u_im1 - T(2)*u_i + u_ip1)
          + c1_4   * (u_im1 - u_ip1) * (u_im1 - u_ip1);

    beta2 = c13_12 * (u_i - T(2)*u_ip1 + u_ip2) * (u_i - T(2)*u_ip1 + u_ip2)
          + c1_4   * (T(3)*u_i - T(4)*u_ip1 + u_ip2) * (T(3)*u_i - T(4)*u_ip1 + u_ip2);
}

/// WENO5 left-biased reconstruction at face i+1/2 (scalar, 1D).
/// Returns only the left value.
template <typename T>
AMREX_GPU_HOST_DEVICE
T weno5_left(const T u_im2, const T u_im1, const T u_i, const T u_ip1, const T u_ip2,
             WENOVariant variant = WENOVariant::Z)
{
    const T eps = T(1e-6);

    // Ideal linear weights
    const T d0 = T(1) / T(10);   // 0.1
    const T d1 = T(6) / T(10);   // 0.6
    const T d2 = T(3) / T(10);   // 0.3

    // Sub-stencil interpolations (left-biased)
    // v0 = (2*u_im2 - 7*u_im1 + 11*u_i) / 6
    // v1 = (-u_im1 + 5*u_i + 2*u_ip1) / 6
    // v2 = (2*u_i + 5*u_ip1 - u_ip2) / 6
    const T inv6 = T(1) / T(6);
    const T v0 = (T(2)*u_im2 - T(7)*u_im1 + T(11)*u_i) * inv6;
    const T v1 = (-u_im1 + T(5)*u_i + T(2)*u_ip1) * inv6;
    const T v2 = (T(2)*u_i + T(5)*u_ip1 - u_ip2) * inv6;

    // Smoothness indicators
    T beta0, beta1, beta2;
    smoothness_indicators(u_im2, u_im1, u_i, u_ip1, u_ip2, beta0, beta1, beta2);

    // Nonlinear weights
    T alpha0, alpha1, alpha2;
    if (variant == WENOVariant::JS) {
        // WENO-JS: alpha_k = d_k / (beta_k + eps)^2
        const T den0 = beta0 + eps;
        const T den1 = beta1 + eps;
        const T den2 = beta2 + eps;
        alpha0 = d0 / (den0 * den0);
        alpha1 = d1 / (den1 * den1);
        alpha2 = d2 / (den2 * den2);
    } else {
        // WENO-Z: tau5 = |beta0 - beta2|
        // alpha_k = d_k * (1 + (tau5 / (beta_k + eps))^2)
        const T tau5 = (beta0 > beta2) ? (beta0 - beta2) : (beta2 - beta0);

        const T den0 = beta0 + eps;
        const T den1 = beta1 + eps;
        const T den2 = beta2 + eps;

        const T r0 = tau5 / den0;
        const T r1 = tau5 / den1;
        const T r2 = tau5 / den2;

        alpha0 = d0 * (T(1) + r0 * r0);
        alpha1 = d1 * (T(1) + r1 * r1);
        alpha2 = d2 * (T(1) + r2 * r2);
    }

    const T alpha_sum = alpha0 + alpha1 + alpha2;
    // Guard against near-zero alpha_sum (e.g. exactly zero betas in constant field)
    if (alpha_sum < T(1e-15)) {
        // Fallback: use ideal linear weights (optimal for smooth flow)
        return d0 * v0 + d1 * v1 + d2 * v2;
    }
    const T inv_sum = T(1) / alpha_sum;
    const T w0 = alpha0 * inv_sum;
    const T w1 = alpha1 * inv_sum;
    const T w2 = alpha2 * inv_sum;

    return w0 * v0 + w1 * v1 + w2 * v2;
}

/// Full WENO5 reconstruction at face i+1/2 (scalar, 1D).
/// Computes both left and right values.  Left and right use the same three
/// 3-point sub-stencils, but with reversed ideal weights and the mapping
/// from smoothness indicators to sub-stencils properly aligned.
///
/// Sub-stencil assignments:
///   v0 (left)  = sub-stencil {u_im2, u_im1, u_i}        -> beta0, weight d0=0.1
///   v1 (left)  = sub-stencil {u_im1, u_i, u_ip1}        -> beta1, weight d1=0.6
///   v2 (left)  = sub-stencil {u_i, u_ip1, u_ip2}        -> beta2, weight d2=0.3
///   v0r (right)= sub-stencil {u_i, u_ip1, u_ip2}        -> beta2, weight d2=0.3
///   v1r (right)= sub-stencil {u_im1, u_i, u_ip1}        -> beta1, weight d1=0.6
///   v2r (right)= sub-stencil {u_im2, u_im1, u_i}        -> beta0, weight d0=0.1
template <typename T>
AMREX_GPU_HOST_DEVICE
void weno5(const T u_im2, const T u_im1, const T u_i, const T u_ip1, const T u_ip2,
           T& u_left, T& u_right,
           WENOVariant variant = WENOVariant::Z)
{
    const T eps = T(1e-6);

    // Ideal linear weights
    const T d0 = T(1) / T(10);   // 0.1
    const T d1 = T(6) / T(10);   // 0.6
    const T d2 = T(3) / T(10);   // 0.3

    const T inv6 = T(1) / T(6);

    // Three 3-point sub-stencil reconstructions to face i+1/2
    const T v0 = (T(2)*u_im2 - T(7)*u_im1 + T(11)*u_i) * inv6;   // {im2,im1,i}
    const T v1 = (-u_im1 + T(5)*u_i + T(2)*u_ip1) * inv6;         // {im1,i,ip1}
    const T v2 = (T(2)*u_i + T(5)*u_ip1 - u_ip2) * inv6;          // {i,ip1,ip2}

    // Right-biased values = same 3 sub-stencils, re-ordered
    const T v0r = v2;   // {i, ip1, ip2} -> beta2, weight d2
    const T v1r = v1;   // {im1, i, ip1} -> beta1, weight d1
    const T v2r = v0;   // {im2, im1, i} -> beta0, weight d0

    // Smoothness indicators
    T beta0, beta1, beta2;
    smoothness_indicators(u_im2, u_im1, u_i, u_ip1, u_ip2, beta0, beta1, beta2);

    // Nonlinear weights — separate for left and right bias
    T alpha0_L, alpha1_L, alpha2_L;
    T alpha0_R, alpha1_R, alpha2_R;

    if (variant == WENOVariant::JS) {
        // WENO-JS: alpha_k = d_k / (beta_k + eps)^2
        const T den0 = beta0 + eps;
        const T den1 = beta1 + eps;
        const T den2 = beta2 + eps;
        const T nd0 = T(1) / (den0 * den0);
        const T nd1 = T(1) / (den1 * den1);
        const T nd2 = T(1) / (den2 * den2);

        // Left:  v0->beta0 weight d0, v1->beta1 weight d1, v2->beta2 weight d2
        alpha0_L = d0 * nd0;
        alpha1_L = d1 * nd1;
        alpha2_L = d2 * nd2;

        // Right: v0r uses {i,ip1,ip2}->beta2 weight d2,
        //        v1r uses {im1,i,ip1}->beta1 weight d1,
        //        v2r uses {im2,im1,i}->beta0 weight d0
        alpha0_R = d2 * nd2;
        alpha1_R = d1 * nd1;
        alpha2_R = d0 * nd0;
    } else {
        // WENO-Z: tau5 = |beta0 - beta2|
        // alpha_k = d_k * (1 + (tau5 / (beta_k + eps))^2)
        const T tau5 = (beta0 > beta2) ? (beta0 - beta2) : (beta2 - beta0);
        const T den0 = beta0 + eps;
        const T den1 = beta1 + eps;
        const T den2 = beta2 + eps;
        const T r0 = tau5 / den0;
        const T r1 = tau5 / den1;
        const T r2 = tau5 / den2;
        const T nr0 = T(1) + r0 * r0;
        const T nr1 = T(1) + r1 * r1;
        const T nr2 = T(1) + r2 * r2;

        // Left
        alpha0_L = d0 * nr0;
        alpha1_L = d1 * nr1;
        alpha2_L = d2 * nr2;

        // Right: reversed weight mapping, aligned with sub-stencil betas
        alpha0_R = d2 * nr2;   // v0r -> beta2 -> d2
        alpha1_R = d1 * nr1;   // v1r -> beta1 -> d1
        alpha2_R = d0 * nr0;   // v2r -> beta0 -> d0
    }

    // Normalize left weights with zero-guard
    const T alpha_sum_L = alpha0_L + alpha1_L + alpha2_L;
    T w0_L, w1_L, w2_L;
    if (alpha_sum_L < T(1e-15)) {
        w0_L = d0;
        w1_L = d1;
        w2_L = d2;
    } else {
        const T inv_sum_L = T(1) / alpha_sum_L;
        w0_L = alpha0_L * inv_sum_L;
        w1_L = alpha1_L * inv_sum_L;
        w2_L = alpha2_L * inv_sum_L;
    }

    // Normalize right weights with zero-guard
    const T alpha_sum_R = alpha0_R + alpha1_R + alpha2_R;
    T w0_R, w1_R, w2_R;
    if (alpha_sum_R < T(1e-15)) {
        w0_R = d2;
        w1_R = d1;
        w2_R = d0;
    } else {
        const T inv_sum_R = T(1) / alpha_sum_R;
        w0_R = alpha0_R * inv_sum_R;
        w1_R = alpha1_R * inv_sum_R;
        w2_R = alpha2_R * inv_sum_R;
    }

    u_left  = w0_L * v0  + w1_L * v1  + w2_L * v2;
    u_right = w0_R * v0r + w1_R * v1r + w2_R * v2r;
}

} // namespace reconstruction

#endif // RECONSTRUCTION_WENO5_H
