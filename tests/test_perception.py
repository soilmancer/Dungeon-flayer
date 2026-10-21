import unittest

import numpy as np

from dungeonflayer import perception
from dungeonflayer.mock_env import MockEnv
from dungeonflayer.state import SCREEN_DEAD, SCREEN_IN_GAME, SCREEN_LOADING


def frame_with_health(value):
    env = MockEnv()
    env.player_health = value
    return env.render()


class HealthBarTests(unittest.TestCase):
    def test_full_bar(self):
        self.assertAlmostEqual(perception.health_fraction(frame_with_health(1.0)), 1.0, delta=0.03)

    def test_empty_bar(self):
        self.assertAlmostEqual(perception.health_fraction(frame_with_health(0.0)), 0.0, delta=0.03)

    def test_half_bar(self):
        self.assertAlmostEqual(perception.health_fraction(frame_with_health(0.5)), 0.5, delta=0.04)

    def test_quarter_bar(self):
        self.assertAlmostEqual(perception.health_fraction(frame_with_health(0.25)), 0.25, delta=0.04)

    def test_none_frame(self):
        self.assertIsNone(perception.health_fraction(None))


class ClassifyTests(unittest.TestCase):
    def test_black_frame_is_loading(self):
        black = np.zeros((360, 640, 3), dtype=np.uint8)
        self.assertEqual(perception.classify_screen(black), SCREEN_LOADING)

    def test_normal_frame_is_in_game(self):
        self.assertEqual(perception.classify_screen(frame_with_health(0.9)), SCREEN_IN_GAME)

    def test_dead_frame(self):
        env = MockEnv()
        env.dead = True
        self.assertEqual(perception.classify_screen(env.render()), SCREEN_DEAD)


class DetectorAndViewTests(unittest.TestCase):
    def test_blob_detector_finds_enemy(self):
        env = MockEnv()
        frame = env.render()
        enemies = perception.blob_detector()(frame)
        self.assertEqual(len(enemies), 1)
        self.assertTrue(0.8 < enemies[0].x < 0.97)
        self.assertAlmostEqual(enemies[0].y, 0.5, delta=0.06)

    def test_downscale_shape(self):
        small = perception.downscale(frame_with_health(1.0), size=128)
        self.assertEqual(small.shape, (128, 128, 3))


if __name__ == "__main__":
    unittest.main()
