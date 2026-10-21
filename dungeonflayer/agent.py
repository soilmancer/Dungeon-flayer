"""Agent loop + a rule-based starter policy.

A policy is anything with .act(bot, state) -> str (a label for the log).
Phase 3 adds a VLM policy with the same interface; the loop doesn't care.
"""
from __future__ import annotations

from .state import SCREEN_DEAD


class Policy:
    def act(self, bot, state) -> str:
        raise NotImplementedError


class SurvivalPolicy(Policy):
    """v0 rules, in priority order:
    dead -> click through respawn; health low -> potion;
    enemy visible -> move toward it and attack; else patrol a square.
    """

    def __init__(self, potion_below: float = 0.35):
        self.potion_below = potion_below
        self._patrol = 0

    def act(self, bot, state) -> str:
        if state.screen == SCREEN_DEAD:
            bot.interact()
            return "respawn"
        if state.health is not None and state.health < self.potion_below:
            bot.use_potion()
            return "potion"
        enemy = bot.nearest_enemy()
        if enemy is not None:
            bot.move((enemy.x - 0.5) * 2, (enemy.y - 0.5) * 2, duration=0.1)
            bot.attack()
            return "attack"
        dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        x, y = dirs[self._patrol % 4]
        self._patrol += 1
        bot.move(x, y, duration=0.15)
        return "patrol"


def run_agent(bot, policy: Policy, steps: int = 50) -> list[dict]:
    log = []
    for i in range(steps):
        state = bot.observe()
        action = policy.act(bot, state)
        log.append(
            {
                "step": i,
                "screen": state.screen,
                "health": None if state.health is None else round(state.health, 3),
                "action": action,
            }
        )
    return log
