"""
Rawform Audio Engine
=====================
Independent, framework-agnostic DSP engine for electronic music mix analysis.
Focused on Techno and Psytrance. No FastAPI or web dependencies live here —
this package can be reused by a future VST3/AU plugin, desktop app, or CLI.

Every function returns plain dict/JSON-serializable structures with explicit
`confidence` values. Nothing here fabricates results: if a measurement can't
be computed reliably, the function returns None / "not_available" rather than
a guessed number.
"""

__version__ = "0.1.0"
