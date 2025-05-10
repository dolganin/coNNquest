import random
import yaml
import logging
from vizdoom import (
    DoomGame, GameVariable, Button, Mode,
    ScreenResolution, ScreenFormat
)

logging.basicConfig(level=logging.INFO, format="%(message)s")

class ConNquestEnv:
    def __init__(self, cfg_path):
        with open(cfg_path) as f:
            self.cfg = yaml.safe_load(f)

        C = self.cfg['game']
        self.game = DoomGame()
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

    def _pick_spots(self, ring, n):
        spots = self.cfg['spots']['ring'] if ring else self.cfg['spots']['far']
        if not ring:
            init = self.cfg['wave']['initial_far']
            extra = (self.wave // self.cfg['wave']['waves_per_tier']) * self.cfg['wave']['extra_far']
            avail = min(init + extra, len(spots))
            spots = spots[:avail]
        return random.sample(spots, min(n, len(spots)))

    def _weighted_sample(self, pool, weights, k):
        pick = []
        for _ in range(min(k, len(pool))):
            s = sum(weights)
            r = random.uniform(0, s)
            for i, w in enumerate(weights):
                r -= w
                if r <= 0:
                    pick.append(pool.pop(i))
                    weights.pop(i)
                    break
        return pick

    def spawn_wave(self):
        w, C = self.wave, self.cfg
        tier = min(w // C['wave']['waves_per_tier'] + 1, len(C['monsters']))
        max_mobs = min(C['wave']['init_mobs'] + w * C['wave']['mobs_per_wave'], C['wave']['max_mobs'])

        dist_type = self.cfg.get("distribution", {}).get("type", "weighted")
        pool = []
        for t in range(1, tier + 1):
            pool += C['monsters'][f"tier{t}"]

        if dist_type == "uniform":
            mobs = random.sample(pool, min(max_mobs, len(pool)))
        else:
            weights = [1 + (i // len(pool) + 1 == tier) * C['wave']['tier_bonus'] for i in range(len(pool))]
            mobs = self._weighted_sample(pool, weights, max_mobs)

        logging.info(f"[Волна {w}] Призыв врагов: {mobs}")

        total_hp = sum(C['monster_hp'][m] for m in mobs)
        ammo_potential = 0
        wtier = min((w + 1) // C['wave']['weap_step'], tier)
        new_weaps = C['weapons'][f"tier{wtier}"]
        for wp in new_weaps:
            ainfo = C['ammo'].get(wp)
            if ainfo and ainfo['type']:
                ammo_potential += ainfo['packs'] * ainfo['min_damage']
        logging.info(f"[Волна {w}] Всего HP врагов: {total_hp}, потенциальный урон из боезапаса: {ammo_potential}")
        if ammo_potential < total_hp:
            deficit = total_hp - ammo_potential
            packs = max(1, deficit // C['wave']['extra_pack_damage'])
            for _ in range(packs):
                spot = self._pick_spots(True, 1)[0]
                self.game.send_game_command(f"give {C['wave']['extra_ammo_type']} {spot}")
                logging.info(f"[Волна {w}] Добавлен экстренный патрон в точку {spot}")

        for m, s in zip(mobs, self._pick_spots(False, len(mobs))):
            self.game.send_game_command(f"summon {m} {s}")
            logging.info(f"[Волна {w}] Призван {m} в точку {s}")

        for wp, s in zip(new_weaps, self._pick_spots(True, len(new_weaps))):
            self.game.send_game_command(f"give {wp} {s}")
            logging.info(f"[Волна {w}] Выдано оружие {wp} в точку {s}")

        ammo = []
        for wp in new_weaps:
            ainfo = C['ammo'].get(wp)
            if ainfo and ainfo['type']:
                ammo += [ainfo['type']] * ainfo['packs']
        for a, s in zip(ammo, self._pick_spots(True, len(ammo))):
            self.game.send_game_command(f"give {a} {s}")
            logging.info(f"[Волна {w}] Патрон {a} в точку {s}")

        if w % C['wave']['health_interval'] == 0:
            H = random.sample(C['health'], C['wave']['health_count'])
            A = random.sample(C['armor'], C['wave']['armor_count'])
            for it, s in zip(H + A, self._pick_spots(False, len(H + A))):
                self.game.send_game_command(f"give {it} {s}")
                logging.info(f"[Волна {w}] Выдано {it} в точку {s}")

        if w % C['wave']['backpack_interval'] == 0:
            s = self._pick_spots(True, 1)[0]
            self.game.send_game_command(f"give Backpack {s}")
            logging.info(f"[Волна {w}] Выдан рюкзак в точку {s}")

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
