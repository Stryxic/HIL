/*
 * hilbert_native.c
 *
 * First-pass implementation of the numerical epistemic primitives declared in
 * hilbert_native.h.
 *
 * Design intent:
 *  - Deterministic, theory-witnessing numerical computation only
 *  - No orchestration, no persistence, no semantics, no labels
 *
 * NOTE:
 *  This file is a conservative “reference kernel” implementation:
 *   - graph entropy is structural (degree-weight distribution)
 *   - field coherence is geometric (mean cosine to centroid)
 *   - epistemic stability is a sensitivity diagnostic (coherence sensitivity
 *     under bounded deterministic perturbation)
 *
 * If the thesis defines alternative exact forms, swap the internals while
 * preserving signatures and constraints.
 */

#include "hilbert_native.h"
#include "hilbert_math.h"


#include <stdlib.h>   /* malloc, free */
#include <string.h>   /* memcpy */
#include <math.h>     /* sqrt, log */


/* ============================================================================
 * Graph Integrity & Basic Structure
 * ============================================================================
 */

int hil_graph_validate(const hil_graph_t *graph) {
    if (!graph) return 0;
    if (graph->num_nodes == 0) return 0;

    /* Edge arrays can be NULL if num_edges == 0 */
    if (graph->num_edges > 0) {
        if (!graph->src || !graph->dst || !graph->weight) return 0;
    }

    /* Validate indices and finite weights */
    for (size_t e = 0; e < graph->num_edges; e++) {
        uint32_t s = graph->src[e];
        uint32_t d = graph->dst[e];
        if ((size_t)s >= graph->num_nodes) return 0;
        if ((size_t)d >= graph->num_nodes) return 0;

        double w = graph->weight[e];
        /* weights must be finite and non-negative for structural metrics */
        if (!isfinite(w)) return 0;
        if (w < 0.0) return 0;
    }

    return 1;
}

void hil_graph_degree(const hil_graph_t *graph, double *out_degree) {
    if (!graph || !out_degree) return;
    const size_t n = graph->num_nodes;

    for (size_t i = 0; i < n; i++) out_degree[i] = 0.0;

    for (size_t e = 0; e < graph->num_edges; e++) {
        const uint32_t s = graph->src[e];
        const uint32_t d = graph->dst[e];
        const double   w = graph->weight[e];

        /* Weighted degree accumulation */
        out_degree[s] += w;
        out_degree[d] += w;
    }
}

/* ============================================================================
 * Structural Diagnostics (Graph-Theoretic)
 * ============================================================================
 */

double hil_graph_density(const hil_graph_t *graph) {
    if (!graph) return 0.0;
    const double n = (double)graph->num_nodes;

    if (n <= 1.0) return 0.0;

    /* For a simple undirected graph, max edges = n*(n-1)/2.
       We do not enforce simple-graph constraints; this is a structural proxy. */
    const double max_e = (n * (n - 1.0)) / 2.0;
    const double e = (double)graph->num_edges;

    if (max_e <= 0.0) return 0.0;
    double d = e / max_e;

    if (d < 0.0) d = 0.0;
    if (d > 1.0) d = 1.0;
    return d;
}

double hil_graph_entropy(const hil_graph_t *graph) {
    if (!graph) return 0.0;
    if (graph->num_nodes == 0) return 0.0;

    /* Structural entropy computed over weighted degree distribution:
       p_i = deg_i / sum(deg), H = -sum p_i log p_i
       This is purely structural (no semantics). */

    double *deg = (double*)malloc(sizeof(double) * graph->num_nodes);
    if (!deg) return 0.0;

    hil_graph_degree(graph, deg);

    double sum_deg = 0.0;
    for (size_t i = 0; i < graph->num_nodes; i++) sum_deg += deg[i];

    if (sum_deg <= HIL_EPS) {
        free(deg);
        return 0.0;
    }

    double H = 0.0;
    for (size_t i = 0; i < graph->num_nodes; i++) {
        double p = deg[i] / sum_deg;
        if (p > HIL_EPS) {
            H -= p * hil_safe_log(p);
        }
    }

    free(deg);
    return H;
}

size_t hil_graph_connected_components(const hil_graph_t *graph) {
    if (!graph) return 0;
    const size_t n = graph->num_nodes;
    const size_t m = graph->num_edges;
    if (n == 0) return 0;

    /* Build adjacency lists (undirected) */
    size_t *deg = (size_t*)calloc(n, sizeof(size_t));
    if (!deg) return 0;

    for (size_t e = 0; e < m; e++) {
        uint32_t s = graph->src[e], d = graph->dst[e];
        if ((size_t)s < n && (size_t)d < n) {
            deg[s]++; deg[d]++;
        }
    }

    size_t *offset = (size_t*)malloc(sizeof(size_t) * (n + 1));
    if (!offset) { free(deg); return 0; }

    offset[0] = 0;
    for (size_t i = 0; i < n; i++) offset[i + 1] = offset[i] + deg[i];

    uint32_t *adj = (uint32_t*)malloc(sizeof(uint32_t) * offset[n]);
    if (!adj) { free(offset); free(deg); return 0; }

    /* temp counters */
    size_t *cur = (size_t*)calloc(n, sizeof(size_t));
    if (!cur) { free(adj); free(offset); free(deg); return 0; }

    for (size_t e = 0; e < m; e++) {
        uint32_t s = graph->src[e], d = graph->dst[e];
        if ((size_t)s < n && (size_t)d < n) {
            adj[offset[s] + cur[s]++] = d;
            adj[offset[d] + cur[d]++] = s;
        }
    }

    free(cur);

    /* BFS over components */
    uint8_t *seen = (uint8_t*)calloc(n, sizeof(uint8_t));
    uint32_t *queue = (uint32_t*)malloc(sizeof(uint32_t) * n);
    if (!seen || !queue) {
        free(queue); free(seen); free(adj); free(offset); free(deg);
        return 0;
    }

    size_t comps = 0;

    for (size_t i = 0; i < n; i++) {
        if (seen[i]) continue;

        comps++;
        /* BFS from i */
        size_t qh = 0, qt = 0;
        queue[qt++] = (uint32_t)i;
        seen[i] = 1;

        while (qh < qt) {
            uint32_t v = queue[qh++];
            for (size_t k = offset[v]; k < offset[v + 1]; k++) {
                uint32_t u = adj[k];
                if (!seen[u]) {
                    seen[u] = 1;
                    queue[qt++] = u;
                }
            }
        }
    }

    free(queue);
    free(seen);
    free(adj);
    free(offset);
    free(deg);

    return comps;
}

/* ============================================================================
 * Field Diagnostics (Geometric)
 * ============================================================================
 */

double hil_field_mean_norm(const hil_field_t *field) {
    if (!field) return 0.0;
    const hil_matrix_t M = field->coordinates;
    if (!M.data || M.rows == 0 || M.cols == 0) return 0.0;

    double sum = 0.0;
    for (size_t r = 0; r < M.rows; r++) {
        const double *row = M.data + (r * M.cols);
        sum += hil_vec_norm(row, M.cols);
    }

    return sum / (double)M.rows;
}

double hil_field_coherence(const hil_field_t *field) {
    if (!field) return 0.0;
    const hil_matrix_t M = field->coordinates;
    if (!M.data || M.rows == 0 || M.cols == 0) return 0.0;

    /* Coherence proxy: mean cosine similarity to centroid.
       Purely geometric; no semantics. */

    double *centroid = (double*)malloc(sizeof(double) * M.cols);
    if (!centroid) return 0.0;

    hil_vec_zero(centroid, M.cols);

    for (size_t r = 0; r < M.rows; r++) {
        const double *row = M.data + (r * M.cols);
        hil_vec_add_inplace(centroid, row, M.cols);
    }

    hil_vec_scale_inplace(centroid, M.cols, 1.0 / (double)M.rows);

    const double c_norm = hil_clamp_min(hil_vec_norm(centroid, M.cols), HIL_EPS);

    double sum_cos = 0.0;
    for (size_t r = 0; r < M.rows; r++) {
        const double *row = M.data + (r * M.cols);
        const double r_norm = hil_clamp_min(hil_vec_norm(row, M.cols), HIL_EPS);
        const double dot = hil_vec_dot(row, centroid, M.cols);
        sum_cos += dot / (r_norm * c_norm);
    }

    free(centroid);
    return sum_cos / (double)M.rows;
}

/* ============================================================================
 * Epistemic Stability
 * ============================================================================
 */

double hil_epistemic_stability(const hil_field_t *field, const hil_graph_t *graph) {
    (void)graph; /* reserved: stability may later incorporate graph terms */

    if (!field) return 0.0;

    /* First-pass stability as sensitivity of coherence under bounded perturbation:
         S = |C(field) - C(perturbed(field, eps))| / eps
       This yields a diagnostic “instability” magnitude.
       Interpretation is left to Python/theory layer; we only compute.
    */

    const double eps = 1e-6;

    double C0 = hil_field_coherence(field);

    /* Copy field coordinates for perturbation (do not mutate caller state) */
    const hil_matrix_t M = field->coordinates;
    if (!M.data || M.rows == 0 || M.cols == 0) return 0.0;

    hil_field_t tmp;
    tmp.coordinates.rows = M.rows;
    tmp.coordinates.cols = M.cols;
    tmp.coordinates.data = (double*)malloc(sizeof(double) * M.rows * M.cols);
    if (!tmp.coordinates.data) return 0.0;

    memcpy(tmp.coordinates.data, M.data, sizeof(double) * M.rows * M.cols);

    hil_field_perturb(&tmp, eps);

    double C1 = hil_field_coherence(&tmp);

    hil_field_free(&tmp);

    return fabs(C1 - C0) / eps;
}

/* ============================================================================
 * Structural Perturbation (Counterfactual)
 * ============================================================================
 */

void hil_field_perturb(hil_field_t *field, double epsilon) {
    if (!field) return;
    hil_matrix_t M = field->coordinates;
    if (!M.data || M.rows == 0 || M.cols == 0) return;

    /* Deterministic perturbation:
       Add +/-epsilon pattern across coordinates, then renormalize each row
       to preserve scale and avoid numerical blow-up. */

    for (size_t r = 0; r < M.rows; r++) {
        double *row = M.data + (r * M.cols);

        for (size_t c = 0; c < M.cols; c++) {
            size_t idx = r * M.cols + c;
            row[c] += epsilon * hil_det_sign(idx);
        }

        /* Optional renormalization to unit norm (numerical stability) */
        double nrm = hil_vec_norm(row, M.cols);
        if (nrm > HIL_EPS) {
            hil_vec_scale_inplace(row, M.cols, 1.0 / nrm);
        }
    }
}

/* ============================================================================
 * Memory Management Helpers
 * ============================================================================
 */

void hil_vector_free(hil_vector_t *vec) {
    if (!vec) return;
    free(vec->data);
    vec->data = NULL;
    vec->length = 0;
}

void hil_matrix_free(hil_matrix_t *mat) {
    if (!mat) return;
    free(mat->data);
    mat->data = NULL;
    mat->rows = 0;
    mat->cols = 0;
}

void hil_graph_free(hil_graph_t *graph) {
    if (!graph) return;
    free(graph->src);
    free(graph->dst);
    free(graph->weight);
    graph->src = NULL;
    graph->dst = NULL;
    graph->weight = NULL;
    graph->num_nodes = 0;
    graph->num_edges = 0;
}

void hil_field_free(hil_field_t *field) {
    if (!field) return;
    hil_matrix_free(&field->coordinates);
}
