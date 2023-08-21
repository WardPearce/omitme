from typing import TYPE_CHECKING

from omitme.platforms.discord import Discord
from omitme.platforms.element import Element
from omitme.platforms.matrix import Matrix
from omitme.platforms.reddit import Reddit

if TYPE_CHECKING:
    from omitme.util.platform import Platform

PLATFORMS: list[type["Platform"]] = [Discord, Matrix, Element, Reddit]

__all__ = ["PLATFORMS"]
