from __future__ import annotations

from typing import Protocol, Iterable, Any, runtime_checkable


# ---------------------------------------------------------------------
# Symbolic aliases (do not over-constrain)
# ---------------------------------------------------------------------

MicroSlice = Any
TimeIndex = Any        # may be int, float, datetime, opaque token
Duration = float      # external duration supplied by instrument


# ---------------------------------------------------------------------
# StreamProtocol
# ---------------------------------------------------------------------

@runtime_checkable
class StreamProtocol(Protocol):
    """
    Contract for time-indexed data sources usable by HIL.

    A Stream is the sole authority on:
    - which time anchors are admissible
    - how durations map to slices
    - what constitutes a valid time index

    The instrument must never infer these implicitly.
    """

    def times(self, dt: Duration) -> Iterable[TimeIndex]:
        """
        Return an iterable of candidate time anchors t such that
        probing with duration dt may be meaningful.

        Requirements:
        - Deterministic ordering
        - No requirement of completeness or contiguity
        - dt is a duration, not an index
        """
        ...

    def slice(self, t: TimeIndex, dt: Duration) -> MicroSlice:
        """
        Return the microstate slice corresponding to the interval
        [t, t + dt).

        Preconditions (instrument responsibility):
        - is_valid_time(t) is True
        - is_valid_time(t + dt) is True (or equivalent domain logic)

        Behavior is undefined if preconditions are violated.
        """
        ...

    def is_valid_time(self, t: TimeIndex) -> bool:
        """
        Return True iff t is a valid time anchor for this stream.

        This method is the *only* authority on time validity.
        """
        ...
