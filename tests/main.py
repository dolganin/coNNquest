import os
import sys
import random
import unittest

# подключаем env
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from connquest.ConquestWrapper import ConNquestEnv

# Fake-реализация для DoomGame
class FakeState:
    def __init__(self):
        self.screen_buffer = b'DUMMY'

class FakeGame:
    def __init__(self):
        self.commands = []
        self._health = 0
        self.inited = False
    def set_doom_scenario_path(self, path): self.scenario = path
    def set_doom_map(self, m): pass
    def set_window_visible(self, v): pass
    def set_screen_resolution(self, r): pass
    def set_screen_format(self, f): pass
    def set_render_hud(self, v): pass
    def set_render_crosshair(self, v): pass
    def set_render_weapon(self, v): pass
    def set_render_decals(self, v): pass
    def set_render_particles(self, v): pass
    def set_episode_start_time(self, t): pass
    def set_episode_timeout(self, t): pass
    def set_mode(self, m): pass
    def set_living_reward(self, r): pass
    def set_death_penalty(self, p): pass
    def set_available_buttons(self, b): pass
    def set_available_game_variables(self, v): pass
    def init(self): self.inited = True
    def new_episode(self): self.episode_started = True
    def send_game_command(self, cmd): self.commands.append(cmd)
    def get_state(self): return FakeState()
    def is_episode_finished(self): return True
    def make_action(self, action, frame_repeat): pass
    def get_last_reward(self): return 1.0
    def get_game_variable(self, var):
        name = getattr(var, 'name', '')
        if name == 'KILLCOUNT': return 2
        if name == 'ITEMCOUNT': return 1
        if name == 'HEALTH':    return self._health + 20
        return 0
    def is_player_dead(self): return False
    def get_total_reward(self): return 5.0

class TestConNquestEnv(unittest.TestCase):

    def setUp(self):
        self.cfg = {
            'game': {
                'wad': 'maps/CoNNquest.wad',
                'map': 'MAP01',
                'window_visible': False,
                'screen_resolution': 'RES_320X240',
                'screen_format': 'CRCGCB',
                'render_hud': True,
                'render_crosshair': True,
                'render_weapon': True,
                'render_decals': False,
                'render_particles': False,
                'episode_start_time': 0,
                'episode_timeout': 100,
                'mode': 'PLAYER',
                'seed': 42,
                'start_health': 100,
                'frame_repeat': 1
            },
            'ammo': {
                'Fist':   {'type': None, 'packs': 0, 'min_damage': 0},
                'Pistol': {'type': 'Clip', 'packs': 4, 'min_damage': 5}
            },
            'spots': {'near': [1,2,3], 'ring': [4,5], 'far': [6]},
            'monsters': {
                'tier1': ['Zombieman'],
                'tier2': ['Imp'],
                'tier3': ['Demon'],
                'tier4': ['Cacodemon'],
                'tier5': ['Mancubus'],
                'tier6': ['Archvile'],
                'tier7': ['MarineShotgun']
            },
            'monster_hp': {
                'Zombieman': 20,
                'Imp': 60,
                'Demon': 150,
                'Cacodemon': 400,
                'Mancubus': 600,
                'Archvile': 700,
                'MarineShotgun': 200
            },
            'weapons': {
                'tier1': ['Pistol']
            },
            'health': ['Stimpack'],
            'armor': ['GreenArmor'],
            'wave': {
                'waves_per_tier': 1,
                'init_mobs': 1,
                'max_mobs': 5,
                'weap_step': 1,
                'health_interval': 1,
                'health_count': 1,
                'armor_count': 1,
                'backpack_interval': 1,
                'extra_ammo_type': 'Clip',
                'extra_pack_damage': 10
            },
            'bots': {
                'start_wave': 1,
                'interval': 1,
                'skill_base': 1,
                'skill_step': 1,
                'max_skill': 5,
                'classes': ['MarineShotgun']
            },
            'rewards': {
                'kill': 0.9, 'item': 0.5, 'health': 0.1,
                'wave': 10.0, 'living_reward': 0.0,
                'death_penalty': 0.0
            }
        }

        self.env = ConNquestEnv.__new__(ConNquestEnv)
        self.env.cfg = self.cfg
        self.env.bots = self.cfg['bots']
        self.env.disable_monsters = False
        self.env.game = FakeGame()
        self.env.game._health = self.cfg['game']['start_health']
        self.env._reset_state()

    def test_spawn_all_monsters_and_items(self):
        seen_monsters = set()
        seen_items    = set()
        self.env.wave = 1
        for _ in range(120):
            self.env.game.commands.clear()
            self.env.spawn_wave()
            for cmd in self.env.game.commands:
                parts = cmd.split()
                if parts[0] == 'summon':
                    seen_monsters.add(parts[1])
                elif parts[0] == 'give':
                    seen_items.add(parts[1])
        # проверяем что каждый монстр и бот был замечен
        all_expected_monsters = set(sum(self.cfg['monsters'].values(), []))
        missing_monsters = all_expected_monsters - seen_monsters
        self.assertTrue(len(missing_monsters) == 0,
                        msg=f"Не заспаунились: {sorted(missing_monsters)}")
        self.assertIn('Pistol', seen_items)
        self.assertIn('Clip', seen_items)
        self.assertIn('Stimpack', seen_items)
        self.assertIn('GreenArmor', seen_items)


if __name__ == '__main__':
    unittest.main()
