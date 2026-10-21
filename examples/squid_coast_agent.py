"""Run the rule-based SurvivalPolicy.

Mock mode (any machine, no game):
    python examples/squid_coast_agent.py --mock --steps 120

Live mode (Windows, Minecraft Dungeons running, single player):
    pip install -r requirements.txt
    python examples/squid_coast_agent.py --steps 600
Live mode uses mss capture + the virtual gamepad. VERIFY the button
mapping in dungeonflayer/control.py against the in-game settings first,
and keep a hand on the real controller — you are the safety stop.
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dungeonflayer import Bot
from dungeonflayer.agent import SurvivalPolicy, run_agent
from dungeonflayer.perception import blob_detector


def build_mock_bot():
    from dungeonflayer.capture import make_source
    from dungeonflayer.mock_env import MockController, MockEnv

    env = MockEnv()
    bot = Bot(make_source("mock", env=env), MockController(env), detector=blob_detector())
    return bot, env


def build_live_bot():
    from dungeonflayer.capture import make_source
    from dungeonflayer.control import GamepadController

    bot = Bot(make_source("mss"), GamepadController(), detector=None)
    return bot, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true", help="run against the mock env")
    ap.add_argument("--steps", type=int, default=120)
    args = ap.parse_args()

    if args.mock:
        bot, env = build_mock_bot()
    else:
        try:
            bot, env = build_live_bot()
        except ImportError as e:
            print(f"Live backends unavailable ({e}). Install requirements.txt "
                  f"on Windows, or use --mock.")
            return 2

    deaths = []
    bot.on("death", lambda state: deaths.append(state.timestamp))
    log = run_agent(bot, SurvivalPolicy(), steps=args.steps)
    actions = {}
    for row in log:
        actions[row["action"]] = actions.get(row["action"], 0) + 1
    print(f"steps={len(log)} actions={actions} deaths={len(deaths)}")
    if env is not None:
        print(f"mock world: kills={env.kills} final_health={env.player_health:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
