# DungeonFlayer — design

## The one-sentence version

Give an AI agent the same programming interface for Minecraft Dungeons that
Mineflayer gives it for Minecraft Java — knowing that underneath, every value
is estimated from screenshots and every action is a button press.

## Why not "real" Mineflayer

| | Minecraft Java + Mineflayer | Minecraft Dungeons + DungeonFlayer |
|---|---|---|
| Channel | Network protocol (bot is a client) | Screen pixels + virtual controller |
| Position | Exact block coordinates | Estimated (screen-relative, map overlay) |
| Health | Exact value from server | Read off the HUD bar by CV (± a few %) |
| Entities | Full entity list with IDs | Whatever a detector finds in frame |
| Latency | Milliseconds, synchronous | ~100 ms pipeline, asynchronous |
| Deaths/state | Server events | Inferred from screen classification |

The gap between the two columns is not an embarrassment to hide — measuring
how much it costs an agent *is* the research question.

## Architecture

```
            +------------------+        +-------------------+
 frames --> | capture          | -----> | perception        |
            | (dxcam/mss/mock) |        | HUD, classify,    |
            +------------------+        | detect, downscale |
                                        +---------+---------+
                                                  | GameState
                                        +---------v---------+
                                        | Bot API           |
   actions <--------------------------- | health, enemies,  |
            +------------------+        | events, view()    |
            | control          |        +---------+---------+
            | (gamepad/kb/dry) |                  |
            +------------------+        +---------v---------+
                                        | Agent / policy    |
                                        | rules today,      |
                                        | VLM tomorrow      |
                                        +-------------------+
```

## API contract (v0)

```python
bot = Bot(source, controller)
state = bot.observe()          # -> GameState(health, screen, enemies, ...)
bot.health                     # last observed health fraction or None
bot.screen                     # 'in_game' | 'loading' | 'dead' | 'menu'
bot.nearest_enemy()            # -> Enemy | None (screen coords, 0..1)
bot.view(size=128)             # downscaled frame for a VLM
bot.move(x, y, duration=0.25)  # stick direction, screen coords: x right, y down
bot.attack(); bot.roll(); bot.use_artifact(1); bot.use_potion(); bot.interact()
bot.on('damage', fn); bot.on('death', fn); bot.on('respawn', fn)
```

Rules:
- Every perception value may be `None`/empty when unreadable. Agents must
  cope; the API never fabricates state.
- Actions are fire-and-forget at the controller level; the *agent loop* is
  responsible for re-observing.
- Backends are swappable: the same agent code runs against the mock
  environment (CI, laptops), or the real game (Windows).

## Perception plan

1. **HUD (done, v0):** health bar = column-fill fraction of the red bar in the
   bottom-left HUD region. Robust, cheap, no ML.
2. **Screen classification (done, v0 heuristics):** near-black → loading;
   full-frame red wash (excluding HUD band) → dead; else in-game.
3. **Blob detector (done, toy):** color-threshold centroid finder — used by
   the mock environment and as a sanity baseline.
4. **Learned detector (Phase 2):** YOLO-style model fine-tuned on recorded,
   hand-labelled gameplay frames: classes = mob, player, drop, door, NPC.
   Training data comes from the same capture pipeline.
5. **VLM scene reads (Phase 3):** downscaled frames to a vision model for
   slow, semantic questions only (which screen is this, am I stuck, where is
   the exit arrow pointing). Never in the combat loop — latency.

## Control plan

- Primary: **virtual Xbox controller** (ViGEmBus via `vgamepad`). Dungeons is
  controller-native; analog stick movement is continuous, which suits an API.
  Button mapping lives in one dict in `control.py` and must be verified
  against the in-game settings screen on first live run.
- Fallback: keyboard/mouse (`pydirectinput`), click-to-move.
- Safety: a global stop hotkey and a max-runtime in every example script.
  The dry-run controller logs actions and touches nothing — it is the default
  everywhere except the explicit live entry point.

## Evaluation plan (the research layer)

- **Ladder:** campaign levels in order, Default difficulty, fresh character,
  fixed attempt budget per level.
- **Scoring:** VideoGameBench-style checkpoints per level (entered level,
  first objective, mid-boss, level complete), plus deaths, time, potions used.
- **Conditions:** (a) rule-based policy, (b) VLM policy at ~1 Hz decisions,
  (c) VLM + scripted combat reflexes (scaffold ablation).
- **Comparison anchor:** the imitation-learning paper's Arch Haven result —
  run our ladder's Arch Haven under each condition.

## Known gaps (honest list)

- No world coordinates; navigation is screen-relative until the map-overlay
  reader exists.
- Detector will miss mobs (occlusion, effects); agent must handle partial
  observability — that is the point, but it caps early performance.
- State is ~100 ms stale; fast boss mechanics will punish that.
- Windows-only for live runs (the game does not ship on macOS/Linux).
