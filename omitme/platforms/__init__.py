from omitme.platforms.discord import Discord
from omitme.platforms.matrix import Matrix
from omitme.util.platform import Platform

PLATFORMS: list[type[Platform]] = [Discord, Matrix]

__all__ = ["PLATFORMS"]
