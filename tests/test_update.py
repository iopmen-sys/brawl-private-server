import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server import apply_rewards, player_profile
from updates.season_update import UpdateConfig, open_box


def run_test() -> None:
    start_coins = player_profile["coins"]
    start_gems = player_profile["gems"]
    start_pp = player_profile["power_points"]

    cfg = UpdateConfig()
    box = open_box(cfg)
    apply_rewards(box["rewards"])

    assert isinstance(box["rewards"], list) and len(box["rewards"]) >= 2
    assert player_profile["coins"] >= start_coins
    assert player_profile["gems"] >= start_gems
    assert player_profile["power_points"] >= start_pp

    print("TEST PASSED:", box)
    print("UPDATED PROFILE:", player_profile)


if __name__ == "__main__":
    run_test()
  
