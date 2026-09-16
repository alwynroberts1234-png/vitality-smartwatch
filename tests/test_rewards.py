"""Daily demo reward rules, persistence and UI interactions, without a GUI."""
import sys
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "preview"))
from watch_preview import Model, Preview, Rewards


class RewardsTests(unittest.TestCase):
    def test_unique_daily_goals_and_claim(self):
        rewards=Rewards()
        self.assertFalse(rewards.claim())
        for index in range(3):
            self.assertTrue(rewards.complete(index))
            self.assertFalse(rewards.complete(index))
            self.assertEqual(rewards.points, 20*(index+1))
        self.assertTrue(rewards.claim())
        self.assertFalse(rewards.claim())
        self.assertEqual(rewards.points, 60)
        self.assertFalse(rewards.complete(-1))
        self.assertFalse(rewards.complete(3))

    def test_reopen_and_next_day(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"rewards.json"
            date=["2026-09-16"]
            today=lambda: date[0]
            rewards=Rewards(path,today)
            for i in range(3): rewards.complete(i)
            rewards.claim()
            restored=Rewards(path,today)
            self.assertEqual(restored.points,60)
            self.assertTrue(restored.claimed)
            date[0]="2026-09-17"
            restored.refresh()
            self.assertEqual(restored.points,0)
            self.assertFalse(restored.claimed)
            self.assertTrue(restored.complete(0))
            self.assertEqual(Rewards(path,today).points,20)

    def test_corrupt_storage_recovers(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"rewards.json"
            for invalid in ('not json', '{}', '{"completed": [true]}', 'null'):
                path.write_text(invalid)
                self.assertEqual(Rewards(path).points,0)

    def test_sensors_never_award_points(self):
        model=Model()
        model.measure()
        model.workout=True
        for _ in range(100): model.tick(.2)
        self.assertEqual(model.rewards.points,0)
        model.set_simulated(False)
        self.assertTrue(model.rewards.complete(0))
        self.assertEqual(model.rewards.points,20)

    def test_goal_and_theme_clicks(self):
        ui=Preview.__new__(Preview)
        ui.model=Model()
        ui.drag=None
        ui.draw=lambda: None
        click=lambda x,y: ui.click(SimpleNamespace(x=x,y=y))
        click(600,367)
        click(600,367)
        self.assertEqual(ui.model.rewards.points,20)
        click(600,406)
        click(600,445)
        click(660,493)
        self.assertTrue(ui.model.rewards.claimed)
        click(900,680)
        self.assertEqual(ui.model.theme,9)


if __name__ == "__main__":
    unittest.main()
