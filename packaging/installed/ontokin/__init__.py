"""Expose the reference modules with their adjacent numerical basis resources."""

from _ontokin_reference_payload import ontokin as _implementation

__version__ = _implementation.__version__
__path__[:] = _implementation.__path__
