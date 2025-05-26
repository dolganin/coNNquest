import random
import yaml
import logging
import os
import sys
from vizdoom import (
    DoomGame, GameVariable, Button, Mode,
    ScreenResolution, ScreenFormat
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

MON_SCRIPTS = {
    "ZombieMan":        101, "ShotgunGuy":     102, "ChaingunGuy":   103,
    "DoomImp":          104, "Demon":           105, "Spectre":       106,
    "LostSoul":         107, "Cacodemon":       108, "HellKnight":    109,
    "BaronOfHell":      110, "Revenant":        111, "Arachnotron":   112,
    "Mancubus":         113, "PainElemental":   114, "Archvile":      115,
    "SpiderMastermind": 116, "Cyberdemon":      117, "WolfensteinSS": 118,
    "Keen":             119,
    "MarineFist":       120, "MarinePistol":    121, "MarineShotgun": 122,
    "MarineSSG":        123, "MarineChaingun":  124, "MarineRocket":  125,
    "MarinePlasma":     126, "MarineBFG":       127, "MarineChainsaw":128,
    "MarineRailgun":    129,
}

class ConNquestEnv:
    def __init__(self, cfg_path=None, disable_monsters=False, extra_args: str = ""):
        cfg_path = os.path.abspath(cfg_path or os.path.join(BASE_DIR, "../configs/conquest.yaml"))
        with open(cfg_path) as f:
            self.cfg = yaml.safe_load(f)

        cfg_dir = os.path.dirname(cfg_path)
        wad_rel = self.cfg['game']['wad']
        wad_path = os.path.join(cfg_dir + "/../", wad_rel)

        self.game = DoomGame()
        self.game.set_doom_scenario_path(wad_path)
        self.disable_monsters = disable_monsters
        self.active_enemies = 0
        C = self.cfg['game']
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
        self.bots = self.cfg.get("bots", {})
        if extra_args:
            self.game.add_game_args(extra_args)
        self.game.add_game_args("+skill 4")
        self.game.init()

        random.seed(C.get('seed', None))
        self.wave = 1
        self._reset_state()

    def _reset_state(self):
        self.prev_kills = 0
        self.prev_items = 0
        self.prev_health = self.cfg['game']['start_health']
        self.prev_ammo = {a: 0 for a in self.cfg['ammo'].keys()}

    def reset_waves(self):
        self.wave = 1

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
        if self.game.is_player_dead():
            logging.warning(f"[Волна {self.wave}] Игрок мёртв — волна не будет запущена.")
            return
    
        w, cfg, B = self.wave, self.cfg, self.bots
        self.game.send_game_command("removeall")
        used_spots = set()
        self.wave_kill_start = self.game.get_game_variable(GameVariable.KILLCOUNT)
    
        # выдача оружия без мобов
        wtier = min((w + 1)//cfg['wave']['weap_step'], len(cfg['weapons']))
        new_weaps = cfg['weapons'].get(f"tier{wtier}", [])
        all_monsters = [m for tier in cfg.get('monsters',{}).values() for m in tier]
        if self.disable_monsters or not all_monsters:
            for wp in new_weaps:
                spot = random.choice(cfg['spots']['near'])
                self.game.send_game_command(f"give {wp} {spot}")
                logging.info(f"[Волна {w}] Выдано оружие {wp} (без монстров)")
            for wp in new_weaps:
                ainfo = cfg['ammo'].get(wp,{})
                for _ in range(ainfo.get('packs',0)):
                    spot = random.choice(cfg['spots']['near'])
                    self.game.send_game_command(f"give {ainfo.get('type')} {spot}")
                    logging.info(f"[Волна {w}] Выдан патрон {ainfo.get('type')}")
            self.active_enemies = 0
            self.wave += 1
            return
    
        # формируем список мобов
        tier = min(w//cfg['wave']['waves_per_tier']+1, len(cfg['monsters']))
        max_mobs = min(cfg['wave']['init_mobs']+w*10, cfg['wave']['max_mobs'])
        template = []
        for t in range(1, tier+1):
            moblist = cfg['monsters'].get(f"tier{t}", [])
            if moblist:
                cnt = int(max_mobs*(0.2 if t<tier else 0.4))
                template += random.choices(moblist, k=cnt)
        mobs = template[:max_mobs]
        self.active_enemies = len(mobs)
        logging.info(f"[Волна {w}] Призыв врагов: {mobs or 'нет'}")
    
        # расчёт HP vs боеприпасы
        pistol_ammo   = 50
        pistol_type   = cfg['wave'].get('default_weapon_type','Clip')
        pistol_dmg    = cfg['ammo'].get(pistol_type,{}).get('min_damage',5)
        base_ammo_pot = pistol_ammo * pistol_dmg
        bonus_ammo_pot= sum(cfg['ammo'].get(wp,{}).get('packs',0) *
                            cfg['ammo'].get(wp,{}).get('min_damage',0)
                            for wp in new_weaps)
        total_hp = sum(cfg['monster_hp'].get(m,0) for m in mobs)
        ammo_pot  = base_ammo_pot + bonus_ammo_pot
        logging.info(f"[Волна {w}] HP врагов: {total_hp}, урон боеприпасов: {ammo_pot}")
    
        # спавн бота
        if B and w>=B['start_wave'] and (w-B['start_wave'])%B['interval']==0:
            skill  = min(B['skill_base']+((w-B['start_wave'])//B['interval'])*B['skill_step'],
                         B['max_skill'])
            bot    = random.choice(B['classes'])
            spot   = random.choice(cfg['spots']['ring'])
            self.game.send_game_command(f"skill {skill}")
            sid = MON_SCRIPTS.get(bot)
            cmd = f"puke {sid} {spot}" if sid else f"summon {bot} {spot}"
            self.game.send_game_command(cmd)
            mobs.append(bot)
            self.active_enemies += 1
            logging.info(f"[Волна {w}] Бот {bot} skill={skill} в точке {spot}")
    
        # экстренные боеприпасы
        if ammo_pot < total_hp:
            deficit = total_hp - ammo_pot
            extra = cfg['wave']['extra_ammo_type']
            is_list = isinstance(extra, list)
            added = 0
            while added < deficit:
                spot = random.choice(cfg['spots']['ring'])
                if is_list:
                    choice = random.choice(extra)
                    ammo_type, dmg = choice['type'], choice['min_damage']
                else:
                    ammo_type = extra
                    dmg = cfg['wave'].get('extra_pack_damage',100)
                self.game.send_game_command(f"give {ammo_type} {spot}")
                logging.info(f"[Волна {w}] Экстренно {ammo_type} (+~{dmg} урона)")
                added += dmg
    
        # распределение far/near/ring
        tier_map = {m:int(t.replace('tier',''))
                    for t,ml in cfg['monsters'].items() for m in ml}
        max_t = max(tier_map.values())
        n, cnt_far = len(mobs), max(1,int(len(mobs)*0.2))
        high = [m for m in mobs if tier_map.get(m,0)==max_t]
        far = (random.sample(high,cnt_far) if len(high)>=cnt_far
               else high+random.sample([m for m in mobs if m not in high],
                                       cnt_far-len(high)))
        low = [m for m in mobs if m not in far]
    
        for m in far:
            spots = [s for s in cfg['spots']['far'] if s not in used_spots]
            if not spots:
                logging.warning(f"[Волна {w}] Нет точек в far для {m}")
                continue
            spot = random.choice(spots); used_spots.add(spot)
            sid = MON_SCRIPTS.get(m)
            cmd = f"puke {sid} {spot}" if sid else f"summon {m} {spot}"
            self.game.send_game_command(cmd)
            logging.info(f"[Волна {w}] {m} (far) в {spot}")
    
        for m in low:
            zone = 'near' if random.random()<0.8 else 'ring'
            spots = [s for s in cfg['spots'][zone] if s not in used_spots]
            if not spots:
                logging.warning(f"[Волна {w}] Нет точек в {zone} для {m}")
                continue
            spot = random.choice(spots); used_spots.add(spot)
            sid = MON_SCRIPTS.get(m)
            cmd = f"puke {sid} {spot}" if sid else f"summon {m} {spot}"
            self.game.send_game_command(cmd)
            logging.info(f"[Волна {w}] {m} ({zone}) в {spot}")
    
        # выдача оружия и аптечек
        for wp in new_weaps:
            spot = random.choice(cfg['spots']['near'])
            self.game.send_game_command(f"give {wp} {spot}")
            logging.info(f"[Волна {w}] Выдано оружие {wp}")
        for wp in new_weaps:
            packs = cfg['ammo'].get(wp,{}).get('packs',0)
            ammo_type = cfg['ammo'].get(wp,{}).get('type')
            for _ in range(packs):
                spot = random.choice(cfg['spots']['near'])
                self.game.send_game_command(f"give {ammo_type} {spot}")
                logging.info(f"[Волна {w}] Выдан патрон {ammo_type}")
    
        if w % cfg['wave']['health_interval']==0:
            items = (random.sample(cfg['health'],cfg['wave']['health_count']) +
                     random.sample(cfg['armor'], cfg['wave']['armor_count']))
            for it in items:
                spot = random.choice(cfg['spots']['far'])
                self.game.send_game_command(f"give {it} {spot}")
                logging.info(f"[Волна {w}] Выдано {it}")
        if w % cfg['wave']['backpack_interval']==0:
            spot = random.choice(cfg['spots']['ring'])
            self.game.send_game_command(f"give Backpack {spot}")
            logging.info(f"[Волна {w}] Выдан рюкзак")
    
        self.wave += 1
    
    
    # ОБНОВИ step:
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
    
        if not self.game.is_player_dead() and (k - getattr(self, 'wave_kill_start', 0)) >= self.active_enemies and self.active_enemies > 0:
            logging.info(f"[STEP] Все {self.active_enemies} врагов убиты — запускаем следующую волну.")
            self.spawn_wave()
    
        done = self.game.is_episode_finished()
        if done and not self.game.is_player_dead():
            reward += self.cfg['rewards']['wave']
    
        # ограничение реворда
        if reward > 200:
            logging.warning(f"[STEP] reward слишком большой: {reward:.2f} → обрезан до 200")
            reward = 200.0
        elif reward < -200:
            logging.warning(f"[STEP] reward слишком маленький: {reward:.2f} → обрезан до -200")
            reward = -200.0
    
        obs = None if done else self.game.get_state().screen_buffer
    
        info = {
            "wave": self.wave,
            "kills": self.prev_kills,
            "items": self.prev_items,
            "health": self.prev_health
        }
    
        return obs, reward, done, info


    def new_episode(self):
        return self.reset()

    def get_state(self):
        return self.game.get_state()

    def make_action(self, action, frame_repeat):
        return self.game.make_action(action, frame_repeat)

    def is_episode_finished(self):
        return self.game.is_episode_finished()

    def get_total_reward(self):
        return self.game.get_total_reward()

    def close(self):
        return self.game.close()

    def reset_stats(self):
        """Сброс статистик без перезапуска эпизода"""
        self.prev_kills = self.game.get_game_variable(GameVariable.KILLCOUNT)
        self.prev_items = self.game.get_game_variable(GameVariable.ITEMCOUNT)
        self.prev_health = self.game.get_game_variable(GameVariable.HEALTH)
        self.prev_ammo = {a: 0 for a in self.cfg['ammo'].keys()}
        logging.info(f"[STATS] Статистика сброшена: kills={self.prev_kills}, items={self.prev_items}, health={self.prev_health}")
        self.game.new_episode()
        return self.game.get_state().screen_buffer
