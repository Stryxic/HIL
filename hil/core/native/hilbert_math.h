#ifndef HILBERT_MATH_H
#define HILBERT_MATH_H

#include <stddef.h>  /* size_t */

#ifdef __cplusplus
extern "C" {
#endif

/* ============================================================================
 * Constants / Guards
 * ============================================================================
 */

#ifndef HIL_EPS
#define HIL_EPS 1e-12
#endif

/* ============================================================================
 * Scalar Helpers
 * ============================================================================
 */

double hil_clamp_min(double x, double m);
double hil_safe_log(double x);                 /* expects x > 0 */
double hil_safe_log1p(double x);               /* stable log(1+x) for small x */
double hil_safe_exp(double x);                 /* avoids overflow where possible */

/* ============================================================================
 * Decay Kernels (Time / Step)
 * ============================================================================
 */

double hil_decay_exponential(double t, double tau);
double hil_decay_linear(double t, double t_max);
double hil_decay_power(double t, double alpha);

/* ============================================================================
 * Vector Helpers
 * ============================================================================
 */

double hil_vec_dot(const double *a, const double *b, size_t n);
double hil_vec_norm(const double *a, size_t n);
void   hil_vec_zero(double *dst, size_t n);
void   hil_vec_add_inplace(double *dst, const double *src, size_t n);
void   hil_vec_scale_inplace(double *dst, size_t n, double k);
void   hil_vec_copy(double *dst, const double *src, size_t n);

/* Deterministic sign pattern (no RNG, no state) */
double hil_det_sign(size_t idx);

#ifdef __cplusplus
}
#endif

#endif /* HILBERT_MATH_H */
