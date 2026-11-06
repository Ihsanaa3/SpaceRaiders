import random
from collections import deque
import gymnasium as gym
from gymnasium import spaces
import matplotlib.pyplot as np_plt
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

# ==========================================
# 1. Custom Environment with Reward Shaping
# ==========================================
def glmdistance2(posx1, posx2, posy1, posy2):
    return (pow(posx1 - posx2, 2) + pow(posy1 - posy2, 2))


class SPEFNNTEnv(gym.Env):
    """Space Raider Engine For Neural Network Training - Gymnasium Wrapper"""
    
    metadata = {"render_modes": []}

    def __init__(self, noBalls=5):
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

        # Action Space: 16 discrete bitmask actions
        self.action_space = spaces.Discrete(16)

        # Observation Space Layout
        obs_dim = 2 + (noBalls * 2) + (noBalls * 2)
        low = np.full((obs_dim,), -10.0, dtype=np.float32)
        high = np.full((obs_dim,), 10.0, dtype=np.float32)
        
        low[:2] = -1.0  
        high[:2] = 1.0
        
        fb_pos_start = 2
        fb_pos_end = 2 + (noBalls * 2)
        low[fb_pos_start:fb_pos_end:2] = -1.0  
        high[fb_pos_start:fb_pos_end:2] = 1.0
        low[fb_pos_start+1:fb_pos_end:2] = -1.2  
        high[fb_pos_start+1:fb_pos_end:2] = 1.1

        self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)

    def NN1D(self):
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
            self.FB_position[i, 0] = self.np_random.uniform(-1.0 + self.FB_radius, 1.0 - self.FB_radius) 
            self.FB_position[i, 1] = 1.0  
            self.FB_velocity[i, 1] = 0.0 
            self.FB_acceleration[i] = self.np_random.uniform(low=0.5, high=1.0 + (self.score/1000)) 

        return self.NN1D(), {} 

    def step(self, action):
        if self.GAMEOVER:
            return self.NN1D(), 0.0, True, False, {} 

        dt = 1/40 
        self.score += 1 

        NN_Move_vec2 = np.array([0.0, 0.0], dtype=np.float32) 
        if action & 1: NN_Move_vec2[0] += 1.0  
        if action & 2: NN_Move_vec2[0] -= 1.0  
        if action & 4: NN_Move_vec2[1] += 1.0  
        if action & 8: NN_Move_vec2[1] -= 1.0          

        self.player_position += NN_Move_vec2 * self.player_speed * dt 
        self.player_position = np.clip(
            self.player_position, 
            -1.0 + self.player_radius, 
            1.0 - self.player_radius
        ) 

        self.FB_velocity[:, 1] -= self.FB_acceleration * dt
        self.FB_position[:, 1] += self.FB_velocity[:, 1] * dt 

        min_dist_to_ball = float('inf')

        for i in range(self.noBalls):
            if self.FB_position[i, 1] < -1.0:
                self.FB_position[i, 1] = 1.0
                self.FB_position[i, 0] = self.np_random.uniform(-1.0 + self.FB_radius, 1.0 - self.FB_radius)  
                self.FB_velocity[i, 1] = 0.0  

            dist = glmdistance2(
                self.FB_position[i, 0], self.player_position[0], 
                self.FB_position[i, 1], self.player_position[1]
            ) 
            
            if dist < min_dist_to_ball:
                min_dist_to_ball = dist

            twoR2 = pow(self.FB_radius + self.player_radius, 2)  
            if dist < twoR2:
                self.GAMEOVER = True 
                break 

        if self.GAMEOVER:
            reward = -100.0
        else:
            # Reward Shaping: Base survival + bonus for maintaining distance from balls
            reward = 1.0 + min(min_dist_to_ball * 0.05, 0.5)

        terminated = self.GAMEOVER
        truncated = False
        return self.NN1D(), reward, terminated, truncated, {}


# ==========================================
# 2. Replay Buffer & Upgraded DQN Network
# ==========================================
class ReplayBuffer:
    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        state, action, reward, next_state, done = zip(*random.sample(self.buffer, batch_size))
        return (
            torch.FloatTensor(np.array(state)),
            torch.LongTensor(action),
            torch.FloatTensor(reward),
            torch.FloatTensor(np.array(next_state)),
            torch.FloatTensor(done)
        )

    def __len__(self):
        return len(self.buffer)


class DQN(nn.Module):
    def __init__(self, state_dim, action_dim):
        super(DQN, self).__init__()
        # Upgraded to 256 hidden units for higher capacity
        self.net = nn.Sequential(
            nn.Linear(state_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, action_dim)
        )

    def forward(self, x):
        return self.net(x)


# ==========================================
# 3. Training Setup & Double DQN Loop
# ==========================================
if __name__ == "__main__":
    env = SPEFNNTEnv(noBalls=5)
    
    state_dim = env.observation_space.shape[0] # type: ignore
    action_dim = env.action_space.n # type: ignore

    gamma = 0.99
    batch_size = 64
    lr = 5e-4  # Slightly tuned learning rate for stability
    buffer_capacity = 20000
    target_update_freq = 10  # Episodes

    epsilon = 1.0
    epsilon_min = 0.01
    epsilon_decay = 0.998  # Slower decay to allow longer exploration

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    policy_net = DQN(state_dim, action_dim).to(device)
    target_net = DQN(state_dim, action_dim).to(device)
    target_net.load_state_dict(policy_net.state_dict())
    target_net.eval()

    optimizer = optim.Adam(policy_net.parameters(), lr=lr)
    replay_buffer = ReplayBuffer(buffer_capacity)

    num_episodes = 1000  # Extended run for convergence
    episode_rewards = []

    print(f"🚀 Starting Optimized Training on device: {device} for {num_episodes} episodes...")
    
    for episode in range(num_episodes):
        state, _ = env.reset()
        episode_reward = 0
        done = False

        while not done:
            if random.random() < epsilon:
                action = env.action_space.sample()
            else:
                with torch.no_grad():
                    state_tensor = torch.FloatTensor(state).unsqueeze(0).to(device)
                    q_values = policy_net(state_tensor)
                    action = q_values.argmax().item()

            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated

            replay_buffer.push(state, action, reward, next_state, float(done))
            state = next_state
            episode_reward += reward

            if len(replay_buffer) >= batch_size:
                states, actions, rewards, next_states, dones = replay_buffer.sample(batch_size)
                states, actions = states.to(device), actions.to(device)
                rewards, next_states, dones = rewards.to(device), next_states.to(device), dones.to(device)

                current_q_values = policy_net(states).gather(1, actions.unsqueeze(1)).squeeze(1)

                # ==========================================
                # DOUBLE DQN TARGET COMPUTATION
                # ==========================================
                with torch.no_grad():
                    # Policy net selects the best action
                    best_actions = policy_net(next_states).max(1)[1].unsqueeze(1)
                    # Target net evaluates that action's value
                    max_next_q_values = target_net(next_states).gather(1, best_actions).squeeze(1)
                    target_q_values = rewards + (gamma * max_next_q_values * (1 - dones))

                loss = nn.MSELoss()(current_q_values, target_q_values)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

        epsilon = max(epsilon_min, epsilon * epsilon_decay)

        if episode % target_update_freq == 0:
            target_net.load_state_dict(policy_net.state_dict())

        episode_rewards.append(episode_reward)
        if (episode + 1) % 50 == 0:
            print(f"Episode {episode + 1}/{num_episodes} | Reward: {episode_reward:.2f} | Epsilon: {epsilon:.2f}")

    env.close()

    # Plotting Performance
    np_plt.figure(figsize=(12, 6))
    np_plt.plot(episode_rewards, label='Episode Reward', color='blue', alpha=0.4)
    
    if len(episode_rewards) >= 20:
        window_size = 20
        moving_avg = np.convolve(episode_rewards, np.ones(window_size)/window_size, mode='valid')
        np_plt.plot(range(window_size - 1, len(episode_rewards)), moving_avg, label='Moving Average (20)', color='red', linewidth=2.5)

    np_plt.title('Optimized Double DQN Training Performance on SPEFNNTEnv')
    np_plt.xlabel('Episode')
    np_plt.ylabel('Total Reward')
    np_plt.legend()
    np_plt.grid(True)
    np_plt.tight_layout()
    np_plt.show()