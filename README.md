# DungeonFlayer

A Mineflayer-style API for **Minecraft Dungeons** — built from pixels.

Mineflayer works because Minecraft (Java) lets a program connect as a client and
read game state directly from the network protocol. Minecraft Dungeons has no
protocol API and no modding API: it is a closed Unreal Engine game. So
DungeonFlayer rebuilds the same *shape* of library on top of the only two
channels available:

- **Eyes:** screen capture + computer vision (HUD parsing, blob/template
  detection, optional vision-language models)
- **Hands:** a virtual Xbox controller (ViGEm) or synthetic mouse/keyboard

An agent program then talks to a familiar bot object — `bot.health`,
`bot.nearest_enemy()`, `bot.attack()` — and never has to care that the state
underneath is estimated from pixels instead of read from packets.

## Why

Faldor, Singh & Raileanu (arXiv:2610.22319) beat vanilla Minecraft with a team
of Gemini agents acting through Mineflayer, and noted in their limitations
that perception through an API is far easier than perception from pixels.
Minecraft Dungeons is the pixels-only case, and it is almost untouched as a
research benchmark: the one published study (imitation learning, ICLR 2024
submission) covers a single level, Arch Haven, with behavioral cloning.

DungeonFlayer is the harness that makes the follow-up question askable:
*how far can an AI agent get through the Dungeons campaign ladder when it can
only see screenshots and press buttons?*

## Status

Phase 0/1 scaffold (October 2026):

- [x] Project layout, design doc, API skeleton
- [x] Screen-state model + HUD health-bar reader (numpy, no game needed)
- [x] Capture backends: mock, mss (cross-platform), dxcam (Windows)
- [x] Control backends: dry-run logger, virtual gamepad (Windows), kb/mouse
- [x] Bot API with events (`damage`, `death`, `respawn`)
- [x] Mock environment + rule-based survival agent — full loop runs headless
- [x] Unit tests for perception and the agent loop
- [ ] Enemy detector trained on real gameplay (YOLO-style, Phase 2)
- [ ] Live run against the real game on Windows (needs a Windows PC)
- [ ] VLM policy (Gemini) + campaign-ladder evaluation (Phase 3)

## Quick start (no game required)

```bash
cd dungeonflayer
python -m unittest discover -s tests -v
python examples/squid_coast_agent.py --mock
```

## Quick start (Windows, real game)

```bash
pip install -r requirements.txt   # numpy, mss, dxcam, vgamepad, pydirectinput
# Launch Minecraft Dungeons (single player, offline), then:
python examples/squid_coast_agent.py
```

## Layout

```
dungeonflayer/
  state.py       GameState / Enemy dataclasses
  perception.py  health-bar reader, screen classifier, blob detector, downscale
  capture.py     frame sources: mock / mss / dxcam
  control.py     controllers: dry-run / virtual gamepad / keyboard+mouse
  bot.py         the Mineflayer-style Bot API + events
  mock_env.py    synthetic game used for development and tests
  agent.py       policy interface + rule-based SurvivalPolicy
examples/
  squid_coast_agent.py
tests/
```

See `DESIGN.md` for the API contract, the Mineflayer comparison, and the
honest list of what pixels cannot give us.

## Scope and ethics

Single-player, offline, on a copy of the game you own, for research. No online
play, no leaderboards, no memory reading, no packet interception.
