from connquest import ConNquestEnv

env = ConNquestEnv("configs/conquest.yaml")
obs = env.reset()
env.spawn_wave()

# Получаем индекс кнопки MOVE_FORWARD
move_forward_idx = env.game.get_available_buttons().index(env.game.get_button("MOVE_FORWARD"))

done = False
while not done:
    action = [0] * env.game.get_available_buttons_size()
    action[move_forward_idx] = 1
    obs, reward, done, info = env.step(action)
    print(f"Wave: {info['wave']}  Reward: {reward}")
