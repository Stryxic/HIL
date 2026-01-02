#include "hilbert_math.h"

#include <math.h>    /* sqrt, log, log1p, exp, fabs */
#include <float.h>   /* DBL_MAX */

/* ============================================================================
 * Scalar Helpers
 * ============================================================================
 */

double hil_clamp_min(double x, double m) {
    return (x < m) ? m : x;
}

double hil_safe_log(double x) {
    /* Caller should ensure x > 0; clamp as last resort for robustness */
    x = hil_clamp_min(x, HIL_EPS);
    return log(x);
}

double hil_safe_log1p(double x) {
    /* stable log(1+x) for small x */
    return log1p(x);
}

double hil_safe_exp(double x) {
    /* Avoid overflow when exp(x) would exceed DBL_MAX */
    /* log(DBL_MAX) ~ 709.78 for IEEE-754 doubles */
    const double LIM = 709.0;
    if (x > LIM)  x = LIM;
    if (x < -LIM) x = -LIM;
    return exp(x);
}

/* ============================================================================
 * Decay Kernels (Time / Step)
 * ============================================================================
 *
 * These are purely numerical kernels. No semantics are implied.
 */

double hil_decay_exponential(double t, double tau) {
    /* exp(-t/tau), with tau > 0 */
    tau = hil_clamp_min(tau, HIL_EPS);
    if (t <= 0.0) return 1.0;
    return hil_safe_exp(-t / tau);
}

double hil_decay_linear(double t, double t_max) {
    /* max(0, 1 - t/t_max), with t_max > 0 */
    t_max = hil_clamp_min(t_max, HIL_EPS);
    if (t <= 0.0) return 1.0;
    double v = 1.0 - (t / t_max);
    return (v < 0.0) ? 0.0 : v;
}

double hil_decay_power(double t, double alpha) {
    /* 1 / (1 + t)^alpha, alpha >= 0 */
    if (alpha < 0.0) alpha = 0.0;
    if (t <= 0.0) return 1.0;
    return pow(1.0 + t, -alpha);
}

/* ============================================================================
 * Vector Helpers
 * ============================================================================
 */

double hil_vec_dot(const double *a, const double *b, size_t n) {
    double s = 0.0;
    for (size_t i = 0; i < n; i++) s += a[i] * b[i];
    return s;
}

double hil_vec_norm(const double *a, size_t n) {
    double s = 0.0;
    for (size_t i = 0; i < n; i++) s += a[i] * a[i];
    return sqrt(s);
}

void hil_vec_zero(double *dst, size_t n) {
    for (size_t i = 0; i < n; i++) dst[i] = 0.0;
}

void hil_vec_add_inplace(double *dst, const double *src, size_t n) {
    for (size_t i = 0; i < n; i++) dst[i] += src[i];
}

void hil_vec_scale_inplace(double *dst, size_t n, double k) {
    for (size_t i = 0; i < n; i++) dst[i] *= k;
}

void hil_vec_copy(double *dst, const double *src, size_t n) {
    for (size_t i = 0; i < n; i++) dst[i] = src[i];
}

/* Deterministic sign pattern for perturbation (no RNG, no state) */
double hil_det_sign(size_t idx) {
    return (idx & 1u) ? -1.0 : 1.0;
}
