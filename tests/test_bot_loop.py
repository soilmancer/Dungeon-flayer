import unittest

from dungeonflayer import Bot
from dungeonflayer.agent import SurvivalPolicy, run_agent
from dungeonflayer.capture import make_source
from dungeonflayer.mock_env import MockController, MockEnv
from dungeonflayer.perception import blob_detector


def build_bot():
    env = MockEnv()
    bot = Bot(make_source("mock", env=env), MockController(env), detector=blob_detector())
    return bot, env


class LoopTests(unittest.TestCase):
    def test_agent_kills_enemies_and_survives(self):
        bot, env = build_bot()
        log = run_agent(bot, SurvivalPolicy(), steps=80)
        self.assertEqual(len(log), 80)
        self.assertGreaterEqual(env.kills, 1)
        self.assertIn("attack", [row["action"] for row in log])
        self.assertFalse(env.dead)

    def test_low_health_triggers_potion(self):
        bot, env = build_bot()
        env.player_health = 0.30
        state = bot.observe()
        action = SurvivalPolicy().act(bot, state)
        self.assertEqual(action, "potion")
        self.assertGreater(env.player_health, 0.8)

    def test_death_event_and_respawn(self):
        bot, env = build_bot()
        deaths = []
        bot.on("death", lambda state: deaths.append(state))
        env.player_health = 0.01
        env.enemy_dist = 30.0  # point blank: next tick drains the last health
        state = bot.observe()
        self.assertEqual(state.screen, "dead")
        self.assertEqual(len(deaths), 1)
        action = SurvivalPolicy().act(bot, state)
        self.assertEqual(action, "respawn")
        self.assertFalse(env.dead)
        self.assertEqual(env.player_health, 1.0)

    def test_view_shape(self):
        bot, _ = build_bot()
        bot.observe()
        self.assertEqual(bot.view(128).shape, (128, 128, 3))


if __name__ == "__main__":
    unittest.main()
