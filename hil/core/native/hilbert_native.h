#ifndef HILBERT_NATIVE_H
#define HILBERT_NATIVE_H

/*
 * hilbert_native.h
 *
 * Numerical epistemic primitives for the Hilbert Information Lab (HIL).
 *
 * This header declares the deterministic, theory-witnessing numerical
 * operations used to compute structural diagnostics over Hilbert Epistemic
 * Fields and their induced graphs.
 *
 * This file defines WHAT can be computed, not HOW it is orchestrated.
 *
 * Epistemic constraints:
 *  - No semantics or interpretation
 *  - No orchestration or control flow
 *  - No persistence, identity, or provenance
 *  - No optimisation objectives
 *  - Deterministic numerical behaviour only
 */

#include <stddef.h>   /* size_t */
#include <stdint.h>   /* uint32_t, uint64_t */

#ifdef __cplusplus
extern "C" {
#endif

/* ============================================================================
 * Core Numeric Types
 * ============================================================================
 */

/*
 * Dense vector representation.
 * Used for field coordinates and derived scalar quantities.
 */
typedef struct {
    double *data;
    size_t  length;
} hil_vector_t;

/*
 * Dense matrix representation.
 * Row-major, contiguous memory.
 */
typedef struct {
    double *data;
    size_t  rows;
    size_t  cols;
} hil_matrix_t;

/*
 * Graph representation.
 *
 * Nodes are implicit (0 .. num_nodes-1).
 * Edges are represented in compressed form.
 *
 * No semantic meaning is attached to nodes or edges.
 */
typedef struct {
    size_t   num_nodes;
    size_t   num_edges;

    /* Edge list representation */
    uint32_t *src;     /* source node indices */
    uint32_t *dst;     /* destination node indices */
    double   *weight;  /* edge weights (structural strength) */
} hil_graph_t;

/*
 * Hilbert Epistemic Field representation.
 *
 * Each row corresponds to an informational element embedded
 * in a shared vector space.
 */
typedef struct {
    hil_matrix_t coordinates;   /* element embeddings */
} hil_field_t;


/* ============================================================================
 * Graph Integrity & Basic Structure
 * ============================================================================
 */

/*
 * Validate structural consistency of a graph.
 *
 * Returns 1 if valid, 0 otherwise.
 * Does not mutate the graph.
 */
int hil_graph_validate(const hil_graph_t *graph);

/*
 * Compute node degree sequence.
 *
 * Output array must be preallocated with length = num_nodes.
 */
void hil_graph_degree(
    const hil_graph_t *graph,
    double *out_degree
);


/* ============================================================================
 * Structural Diagnostics (Graph-Theoretic)
 * ============================================================================
 */

/*
 * Compute structural density of a graph.
 *
 * Returns a scalar in [0, 1].
 */
double hil_graph_density(const hil_graph_t *graph);

/*
 * Compute structural entropy of a graph.
 *
 * Entropy is defined over degree or weight distributions.
 * No semantic interpretation is applied.
 */
double hil_graph_entropy(const hil_graph_t *graph);

/*
 * Compute connected component count.
 */
size_t hil_graph_connected_components(const hil_graph_t *graph);


/* ============================================================================
 * Field Diagnostics (Geometric)
 * ============================================================================
 */

/*
 * Compute mean field norm.
 */
double hil_field_mean_norm(const hil_field_t *field);

/*
 * Compute field coherence.
 *
 * Coherence is a geometric quantity derived from pairwise
 * relations in the embedding space.
 */
double hil_field_coherence(const hil_field_t *field);


/* ============================================================================
 * Epistemic Stability
 * ============================================================================
 */

/*
 * Compute structural stability of a field-graph pair.
 *
 * Stability is a diagnostic quantity describing sensitivity
 * to perturbation, not a control signal.
 */
double hil_epistemic_stability(
    const hil_field_t *field,
    const hil_graph_t *graph
);


/* ============================================================================
 * Structural Perturbation (Counterfactual)
 * ============================================================================
 */

/*
 * Apply a bounded perturbation to a field.
 *
 * This function mutates the field in-place.
 * The perturbation is purely numerical and deterministic
 * given the same epsilon.
 */
void hil_field_perturb(
    hil_field_t *field,
    double epsilon
);


/* ============================================================================
 * Memory Management Helpers
 * ============================================================================
 */

/*
 * Free helpers for structures allocated externally.
 * These functions do NOT allocate memory.
 */
void hil_vector_free(hil_vector_t *vec);
void hil_matrix_free(hil_matrix_t *mat);
void hil_graph_free(hil_graph_t *graph);
void hil_field_free(hil_field_t *field);


#ifdef __cplusplus
}
#endif

#endif /* HILBERT_NATIVE_H */
