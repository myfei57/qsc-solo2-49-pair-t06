"""Process control core for a continuous strip treatment line.

The package is organised by equipment area. Each area owns its own state and
exposes a narrow public surface; cross-area reactions are carried by the
in-process event bus instead of direct access to another area's internals.
"""

from .domain.phase import Phase

__all__ = ["Phase"]

__version__ = "1.0.0"
