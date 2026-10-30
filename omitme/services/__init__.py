"""Built-in services.

Importing this package registers every bundled service.  To add your own,
create a module next to this one and import it below.
"""

from omitme.core.registry import create_services, service_classes
from omitme.services import mock  # noqa: F401  (registration side effects)
from omitme.services import discord  # noqa: F401  (registration side effects)

__all__ = ["create_services", "service_classes"]
