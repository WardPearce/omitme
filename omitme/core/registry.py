"""A tiny registry so services are discovered without UI changes."""

from __future__ import annotations

from omitme.core.service import Service

_REGISTRY: dict[str, type[Service]] = {}


def register(service_cls: type[Service]) -> type[Service]:
    """Class decorator that makes a service visible to the app."""
    service_id = service_cls.meta.id
    existing = _REGISTRY.get(service_id)
    if existing is not None and existing is not service_cls:
        raise ValueError(f"Service id {service_id!r} is already registered.")
    _REGISTRY[service_id] = service_cls
    return service_cls


def service_classes() -> list[type[Service]]:
    """Return registered service classes in registration order."""
    return list(_REGISTRY.values())


def create_services() -> list[Service]:
    """Instantiate one service object per registered class."""
    return [service_cls() for service_cls in _REGISTRY.values()]
