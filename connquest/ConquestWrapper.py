import random
import yaml
import logging
import os
from vizdoom import (
    DoomGame, GameVariable, Button, Mode,
    ScreenResolution, ScreenFormat
)

logging.basicConfig(level=logging.INFO, format="%(message)s")

class ConNquestEnv:
    def __init__(self, cfg_path="../configs/conquest.yaml"):
        cfg_path = os.path.abspath(cfg_path)
        with open(cfg_path) as f:
            self.cfg = yaml.safe_load(f)

        cfg_dir = os.path.dirname(cfg_path)  # ← путь до папки с yaml

        C = self.cfg['game']
        wad_path = os.path.join(cfg_dir, C['wad'])  # ← абсолютный путь
        self.game = DoomGame()
        self.game.set_doom_scenario_path(wad_path)

        self.game.set_doom_scenario_path(C['wad'])
        self.game.set_doom_map(C.get('map', "MAP01"))
        self.game.set_window_visible(C.get('window_visible', False))
        self.game.set_screen_resolution(getattr(ScreenResolution, C['screen_resolution']))
        self.game.set_screen_format(getattr(ScreenFormat, C['screen_format']))
        self.game.set_render_hud(C['render_hud'])
        self.game.set_render_crosshair(C['render_crosshair'])
        self.game.set_render_weapon(C['render_weapon'])
        self.game.set_render_decals(C['render_decals'])
        self.game.set_render_particles(C['render_particles'])
        self.game.set_episode_start_time(C['episode_start_time'])
        self.game.set_episode_timeout(C['episode_timeout'])
        self.game.set_mode(getattr(Mode, C['mode']))
        self.game.set_living_reward(self.cfg['rewards']['living_reward'])
        self.game.set_death_penalty(self.cfg['rewards']['death_penalty'])
        self.game.set_available_buttons([getattr(Button, b) for b in C['available_buttons']])
        self.game.set_available_game_variables([getattr(GameVariable, v) for v in C['available_game_variables']])
        self.game.init()

        random.seed(C.get('seed', None))
        self._reset_state()

    def _reset_state(self):
        self.wave = 1
        self.prev_kills = 0
        self.prev_items = 0
        self.prev_health = self.cfg['game']['start_health']
        self.prev_ammo = {a: 0 for a in self.cfg['ammo'].keys()}

    def reset(self):
        self.game.new_episode()
        self.game.send_game_command("removeall")
        self._reset_state()
        logging.info("=== Новый эпизод начат ===")
        return self.game.get_state().screen_buffer

    def _pick_spots(self, zone, n):
        spots = self.cfg['spots'][zone]
        return random.sample(spots, min(n, len(spots)))

    def spawn_wave(self):
        w, C = self.wave, self.cfg
        tier = min(w // C['wave']['waves_per_tier'] + 1, len(C['monsters']))
        max_mobs = min(C['wave']['init_mobs'] + w * 3, C['wave']['max_mobs'])

        template = []
        for t in range(1, tier + 1):
            moblist = C['monsters'][f"tier{t}"]
            count = int(max_mobs * (0.2 if t < tier else 0.4))
            template += random.choices(moblist, k=count)
        template = template[:max_mobs]
        mobs = template or ["Zombieman"]
        logging.info(f"[Волна {w}] Призыв врагов: {mobs}")

        total_hp = sum(C['monster_hp'][m] for m in mobs)
        ammo_potential = 0
        wtier = min((w + 1) // C['wave']['weap_step'], tier)
        new_weaps = C['weapons'][f"tier{wtier}"]
        for wp in new_weaps:
            ainfo = C['ammo'].get(wp)
            if ainfo and ainfo['type']:
                ammo_potential += ainfo['packs'] * ainfo['min_damage']
        logging.info(f"[Волна {w}] HP врагов: {total_hp}, потенциальный урон: {ammo_potential}")

        if ammo_potential < total_hp:
            deficit = total_hp - ammo_potential
            packs = max(1, deficit // C['wave']['extra_pack_damage'])
            for _ in range(packs):
                spot = self._pick_spots("ring", 1)[0]
                self.game.send_game_command(f"give {C['wave']['extra_ammo_type']} {spot}")
                logging.info(f"[Волна {w}] Добавлен экстренный патрон в точку {spot}")

        zones = (["near"] * (len(mobs) // 2 + 1) +
                 ["ring"] * (len(mobs) // 3) +
                 ["far"] * (len(mobs) - len(mobs) // 2 - len(mobs) // 3))
        random.shuffle(zones)
        for m, z in zip(mobs, zones):
            s = self._pick_spots(z, 1)[0]
            self.game.send_game_command(f"summon {m} {s}")
            logging.info(f"[Волна {w}] {m} в точке {z}: {s}")

        # Оружие и патроны в зоне near
        near_weap_spots = self._pick_spots("near", len(new_weaps))
        for wp, s in zip(new_weaps, near_weap_spots):
            self.game.send_game_command(f"give {wp} {s}")
            logging.info(f"[Волна {w}] Выдано оружие {wp} в точке near: {s}")

        ammo = []
        for wp in new_weaps:
            ainfo = C['ammo'].get(wp)
            if ainfo and ainfo['type']:
                ammo += [ainfo['type']] * ainfo['packs']
        for a, s in zip(ammo, self._pick_spots("near", len(ammo))):
            self.game.send_game_command(f"give {a} {s}")
            logging.info(f"[Волна {w}] Патрон {a} в точке near: {s}")

        if w % C['wave']['health_interval'] == 0:
            H = random.sample(C['health'], C['wave']['health_count'])
            A = random.sample(C['armor'], C['wave']['armor_count'])
            for it, s in zip(H + A, self._pick_spots("far", len(H + A))):
                self.game.send_game_command(f"give {it} {s}")
                logging.info(f"[Волна {w}] Выдано {it} в точке {s}")

        if w % C['wave']['backpack_interval'] == 0:
            s = self._pick_spots("ring", 1)[0]
            self.game.send_game_command(f"give Backpack {s}")
            logging.info(f"[Волна {w}] Выдан рюкзак в точке {s}")

        self.wave += 1


    def step(self, action):
        self.game.make_action(action, self.cfg['game']['frame_repeat'])
        reward = self.game.get_last_reward()

        k = self.game.get_game_variable(GameVariable.KILLCOUNT)
        reward += (k - self.prev_kills) * self.cfg['rewards']['kill']
        self.prev_kills = k

        it = self.game.get_game_variable(GameVariable.ITEMCOUNT)
        reward += (it - self.prev_items) * self.cfg['rewards']['item']
        self.prev_items = it

        h = self.game.get_game_variable(GameVariable.HEALTH)
        if h > self.prev_health:
            reward += (h - self.prev_health) * self.cfg['rewards']['health']
        self.prev_health = h

        done = self.game.is_episode_finished()
        if done and not self.game.is_player_dead():
            reward += self.cfg['rewards']['wave']

        obs = None if done else self.game.get_state().screen_buffer

        info = {
            "wave": self.wave,
            "kills": self.prev_kills,
            "items": self.prev_items,
            "health": self.prev_health
        }

        return obs, reward, done, info
