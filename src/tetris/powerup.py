"""Power-up system for special blocks."""

import time
from dataclasses import dataclass
from typing import Optional, Callable
from .constants import PowerUpType


@dataclass
class PowerUp:
    """Represents a power-up item."""
    type: PowerUpType
    icon: str  # Emoji icon for display
    description: str
    duration: float = 0.0  # Duration in seconds (0 = instant)
    is_active: bool = False
    activation_time: float = 0.0

    def activate(self) -> None:
        """Activate this power-up."""
        self.is_active = True
        self.activation_time = time.time()

    def is_expired(self) -> bool:
        """Check if power-up effect has expired.

        Returns:
            True if expired or instant effect
        """
        if self.duration == 0:
            return True
        return time.time() - self.activation_time >= self.duration

    def get_remaining_time(self) -> float:
        """Get remaining time for power-up effect.

        Returns:
            Remaining seconds, or 0 if expired/instant
        """
        if self.duration == 0 or not self.is_active:
            return 0.0
        remaining = self.duration - (time.time() - self.activation_time)
        return max(0.0, remaining)


# Power-up definitions
POWERUP_DEFINITIONS = {
    PowerUpType.BOMB: PowerUp(
        type=PowerUpType.BOMB,
        icon="💣",
        description="Clear 3×3 area",
        duration=0.0,  # Instant effect
    ),
    PowerUpType.MAGNET: PowerUp(
        type=PowerUpType.MAGNET,
        icon="🧲",
        description="Drop all floating blocks down",
        duration=0.0,
    ),
    PowerUpType.TIME_FREEZE: PowerUp(
        type=PowerUpType.TIME_FREEZE,
        icon="⏸️",
        description="Freeze falling for 5 seconds",
        duration=5.0,
    ),
    PowerUpType.GRAVITY_REVERSE: PowerUp(
        type=PowerUpType.GRAVITY_REVERSE,
        icon="🔄",
        description="Blocks fall upward for 8 seconds",
        duration=8.0,
    ),
    PowerUpType.LINE_ERASER: PowerUp(
        type=PowerUpType.LINE_ERASER,
        icon="⚡",
        description="Clear bottom 2 rows instantly",
        duration=0.0,
    ),
    PowerUpType.GHOST_MODE: PowerUp(
        type=PowerUpType.GHOST_MODE,
        icon="👻",
        description="Next 3 blocks can overlap",
        duration=0.0,  # Handled by block counter
    ),
}


class PowerUpManager:
    """Manages power-up inventory and effects."""

    def __init__(self, max_inventory: int = 2):
        """Initialize power-up manager.

        Args:
            max_inventory: Maximum number of power-ups that can be held
        """
        self.max_inventory = max_inventory
        self.inventory: list[PowerUp] = []
        self.active_effects: list[PowerUp] = []
        self.ghost_mode_blocks_remaining = 0

    def add_powerup(self, powerup_type: PowerUpType) -> bool:
        """Add a power-up to inventory.

        Args:
            powerup_type: Type of power-up to add

        Returns:
            True if added successfully, False if inventory full
        """
        if len(self.inventory) >= self.max_inventory:
            return False

        # Create a copy of the power-up definition
        powerup = PowerUp(
            type=powerup_type,
            icon=POWERUP_DEFINITIONS[powerup_type].icon,
            description=POWERUP_DEFINITIONS[powerup_type].description,
            duration=POWERUP_DEFINITIONS[powerup_type].duration,
        )
        self.inventory.append(powerup)
        return True

    def use_powerup(self) -> Optional[PowerUp]:
        """Use the oldest power-up in inventory.

        Returns:
            PowerUp that was used, or None if inventory empty
        """
        if not self.inventory:
            return None

        powerup = self.inventory.pop(0)  # FIFO - use oldest first
        powerup.activate()

        # Special handling for ghost mode
        if powerup.type == PowerUpType.GHOST_MODE:
            self.ghost_mode_blocks_remaining = 3

        # Add to active effects if has duration
        if powerup.duration > 0:
            self.active_effects.append(powerup)

        return powerup

    def update(self, dt: float) -> None:
        """Update active effects and remove expired ones.

        Args:
            dt: Delta time in seconds
        """
        # Remove expired effects
        self.active_effects = [
            effect for effect in self.active_effects
            if not effect.is_expired()
        ]

    def is_effect_active(self, powerup_type: PowerUpType) -> bool:
        """Check if a specific power-up effect is currently active.

        Args:
            powerup_type: Type to check

        Returns:
            True if active, False otherwise
        """
        if powerup_type == PowerUpType.GHOST_MODE:
            return self.ghost_mode_blocks_remaining > 0

        return any(
            effect.type == powerup_type and effect.is_active
            for effect in self.active_effects
        )

    def get_active_effect(self, powerup_type: PowerUpType) -> Optional[PowerUp]:
        """Get active power-up effect of specific type.

        Args:
            powerup_type: Type to get

        Returns:
            PowerUp instance or None
        """
        for effect in self.active_effects:
            if effect.type == powerup_type and effect.is_active:
                return effect
        return None

    def decrement_ghost_mode(self) -> None:
        """Decrement ghost mode block counter (call when block placed)."""
        if self.ghost_mode_blocks_remaining > 0:
            self.ghost_mode_blocks_remaining -= 1

    def clear(self) -> None:
        """Clear all power-ups and effects."""
        self.inventory.clear()
        self.active_effects.clear()
        self.ghost_mode_blocks_remaining = 0

    def get_inventory_display(self) -> list[str]:
        """Get list of power-up icons for display.

        Returns:
            List of emoji icons
        """
        return [p.icon for p in self.inventory]

    def get_active_effects_display(self) -> list[tuple[str, float]]:
        """Get active effects for display.

        Returns:
            List of (icon, remaining_time) tuples
        """
        effects = []
        for effect in self.active_effects:
            if effect.is_active:
                effects.append((effect.icon, effect.get_remaining_time()))

        # Add ghost mode if active
        if self.ghost_mode_blocks_remaining > 0:
            ghost = POWERUP_DEFINITIONS[PowerUpType.GHOST_MODE]
            effects.append((ghost.icon, float(self.ghost_mode_blocks_remaining)))

        return effects


def get_random_powerup() -> PowerUpType:
    """Get a random power-up type.

    Returns:
        Random PowerUpType
    """
    import random
    return random.choice(list(PowerUpType))
