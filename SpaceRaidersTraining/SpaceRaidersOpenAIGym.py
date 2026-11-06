import gymnasium as gym
from gymnasium import spaces
import numpy as np

def glmdistance2(posx1, posx2, posy1, posy2):
    return (pow(posx1 - posx2, 2) + pow(posy1 - posy2, 2))


class SPEFNNTEnv(gym.Env):
    """Space Raider Engine For Neural Network Training - Gymnasium Wrapper"""
    
    metadata = {"render_modes": []}

    def __init__(self, noBalls=50):
        super().__init__()
        
        self.noBalls = noBalls 
        self.FB_radius = 0.06 
        self.player_radius = 0.04 
        self.player_speed = 1.0 

        self.score = 0
        self.GAMEOVER = False 

        self.FB_position = np.ones((noBalls, 2), dtype=np.float32) 
        self.FB_velocity = np.zeros((noBalls, 2), dtype=np.float32)  
        self.FB_acceleration = np.zeros((noBalls,), dtype=np.float32) 
        self.player_position = np.array([0.0, 0.0], dtype=np.float32) 

        # Define Action Space: 16 discrete actions (bitmask for Up, Down, Left, Right)
        self.action_space = spaces.Discrete(16)

        # Define Observation Space with explicit finite bounds to remove warnings
        # Observation layout: [player_x, player_y, fb_0_x, fb_0_y, ..., fb_n_vx, fb_n_vy]
        obs_dim = 2 + (noBalls * 2) + (noBalls * 2)
        
        low = np.full((obs_dim,), -10.0, dtype=np.float32)
        high = np.full((obs_dim,), 10.0, dtype=np.float32)
        
        # Tighter bounds for positions (approx -1.0 to 1.0 with a little buffer for falling past -1.0)
        low[:2] = -1.0  # Player X, Y
        high[:2] = 1.0
        
        fb_pos_start = 2
        fb_pos_end = 2 + (noBalls * 2)
        low[fb_pos_start:fb_pos_end:2] = -1.0  # FB X positions
        high[fb_pos_start:fb_pos_end:2] = 1.0
        low[fb_pos_start+1:fb_pos_end:2] = -1.2  # FB Y positions (can drop slightly below -1 before reset)
        high[fb_pos_start+1:fb_pos_end:2] = 1.1

        self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)

    def NN1D(self):
        '''Returns a 1D array for the neural network that consists of player pos, FB pos, and FB vel'''
        return np.concatenate([
            self.player_position, 
            self.FB_position.flatten(), 
            self.FB_velocity.flatten()
        ]).astype(np.float32)
    
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        self.score = 0 
        self.GAMEOVER = False
        self.player_position = np.zeros((2,), dtype=np.float32)

        for i in range(self.noBalls):
            # Fixed line breaks
            self.FB_position[i, 0] = self.np_random.uniform(-1.0 + self.FB_radius, 1.0 - self.FB_radius) 
            self.FB_position[i, 1] = 1.0  
            self.FB_velocity[i, 1] = 0.0 
            self.FB_acceleration[i] = self.np_random.uniform(low=0.5, high=1.0 + (self.score/1000)) 

        return self.NN1D(), {} 

    def step(self, action):
        '''Takes an action and steps the environment forward by one frame'''
        if self.GAMEOVER:
            return self.NN1D(), 0.0, True, False, {} 

        dt = 1/40 
        reward = 1.0 
        self.score += 1 

        NN_Move_vec2 = np.array([0.0, 0.0], dtype=np.float32) 

        if action & 1: NN_Move_vec2[0] += 1.0  # Right bit is 1 (0001)
        if action & 2: NN_Move_vec2[0] -= 1.0  # Left bit is 1  (0010)
        if action & 4: NN_Move_vec2[1] += 1.0  # Up bit is 1    (0100)
        if action & 8: NN_Move_vec2[1] -= 1.0  # Down bit is 1  (1000)         

        self.player_position += NN_Move_vec2 * self.player_speed * dt 

        # Fixed clip line wrap
        self.player_position = np.clip(
            self.player_position, 
            -1.0 + self.player_radius, 
            1.0 - self.player_radius
        ) 

        self.FB_velocity[:, 1] -= self.FB_acceleration * dt
        self.FB_position[:, 1] += self.FB_velocity[:, 1] * dt 

        for i in range(self.noBalls):
            if self.FB_position[i, 1] < -1.0:
                self.FB_position[i, 1] = 1.0
                self.FB_position[i, 0] = self.np_random.uniform(-1.0 + self.FB_radius, 1.0 - self.FB_radius)  
                self.FB_velocity[i, 1] = 0.0  

            dist = glmdistance2(
                self.FB_position[i, 0], self.player_position[0], 
                self.FB_position[i, 1], self.player_position[1]
            ) 
            twoR2 = pow(self.FB_radius + self.player_radius, 2)  

            if dist < twoR2:
                self.GAMEOVER = True 
                reward = -100.0 
                break 

        # Gymnasium standard returns: observation, reward, terminated, truncated, info
        terminated = self.GAMEOVER
        truncated = False
        return self.NN1D(), reward, terminated, truncated, {}


# --- Example Usage for Testing or Training (e.g. Stable-Baselines3) ---
if __name__ == "__main__":
    env = SPEFNNTEnv()
    
    # Optional: Use Gymnasium's built-in environment checker to ensure compliance
    from gymnasium.utils.env_checker import check_env
    check_env(env)
    print("Gymnasium environment check passed successfully!")

    obs, info = env.reset()
    for _ in range(1000):
        action = env.action_space.sample() # Random action placeholder for DQN
        obs, reward, terminated, truncated, info = env.step(action)
        
        if terminated or truncated:
            obs, info = env.reset()