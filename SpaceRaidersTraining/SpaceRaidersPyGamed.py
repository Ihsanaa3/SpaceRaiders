import numpy as np
import pygame
import sys

def glmdistance2(posx1, posx2, posy1, posy2):
    return (pow(posx1 - posx2, 2) + pow(posy1 - posy2, 2))


class SPEFNNT:
    '''Space Raider Engine For Neural Network Training & Visualization''' 

    def __init__(self, noBalls=50):
        self.noBalls = noBalls 
        self.FB_radius = 0.06 
        self.player_radius = 0.04 
        self.player_speed = 1.0 

        self.score = 0
        self.GAMEOVER = False 

        self.FB_position     = np.ones((noBalls, 2), dtype=np.float32) 
        self.FB_velocity     = np.zeros((noBalls, 2), dtype=np.float32)  
        self.FB_acceleration = np.zeros((noBalls,), dtype=np.float32) 
        self.player_position = np.array([0.0, 0.0], dtype=np.float32) 

    def NN1D(self):
        '''Returns a 1D array for the neural network'''
        return np.concatenate([self.player_position, self.FB_position.flatten(), self.FB_velocity.flatten()])
    
    def resetFB(self):
        self.score = 0 
        self.GAMEOVER = False
        self.player_position = np.zeros((2,), dtype=np.float32)

        for i in range(self.noBalls):
            self.FB_position[i, 0] = np.random.uniform(-1.0 + self.FB_radius, 1.0 - self.FB_radius) 
            self.FB_position[i, 1] = 1.0  
            self.FB_velocity[i, 1] = 0.0 
            self.FB_acceleration[i] = np.random.uniform(0.0, 1.0 + (self.score / 1000.0)) 

        return self.NN1D() 

    def NextFrame(self, action):
        '''Takes in a nibble action (0-15) and updates physics''' 

        if self.GAMEOVER:
            return self.NN1D(), 0.0, True 

        dt = 1/40 
        reward = 1.0 
        self.score += 1 

        NN_Move_vec2 = np.array([0.0, 0.0], dtype=np.float32) 

        if action & 1: NN_Move_vec2[0] += 1.0  # Right 
        if action & 2: NN_Move_vec2[0] -= 1.0  # Left 
        if action & 4: NN_Move_vec2[1] += 1.0  # Up (Screen Y is inverted, but in math space Up is +)
        if action & 8: NN_Move_vec2[1] -= 1.0  # Down         

        self.player_position += NN_Move_vec2 * self.player_speed * dt 
        self.player_position = np.clip(self.player_position, -1.0 + self.player_radius, 1.0 - self.player_radius) 

        # Gravity pulls balls down
        self.FB_velocity[:, 1] -= self.FB_acceleration * dt
        self.FB_position[:, 1] += self.FB_velocity[:, 1] * dt 

        for i in range(self.noBalls):
            if self.FB_position[i, 1] < -1.0:
                self.FB_position[i, 1] = 1.0
                self.FB_position[i, 0] = np.random.uniform(-1.0 + self.FB_radius, 1.0 - self.FB_radius)  
                self.FB_velocity[i, 1] = 0.0  
                self.FB_acceleration[i] = np.random.uniform(0.0, 1.0 + (self.score / 1000.0))

            dist = glmdistance2(
                self.FB_position[i, 0], self.player_position[0], 
                self.FB_position[i, 1], self.player_position[1]
            ) 
            twoR2 = pow(self.FB_radius + self.player_radius, 2)  

            if dist < twoR2 - 0.001:
                self.GAMEOVER = True 
                reward = -100.0 
                break 

        return self.NN1D(), reward, self.GAMEOVER


# --- PYGAME GUI SETUP ---
pygame.init()
WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Raiders - Environment Viewer")
clock = pygame.time.Clock()

env = SPEFNNT(noBalls=40)
obs = env.resetFB()

# Helper function to map environment coordinates (-1 to 1) to Screen Pixels (0 to WIDTH/HEIGHT)
def scale_coords(x, y):
    screen_x = int((x + 1.0) / 2.0 * WIDTH)
    # Invert Y because Pygame's 0,0 is at the top-left, but math space 0,0 is center/bottom
    screen_y = int((1.0 - (y + 1.0) / 2.0) * HEIGHT)
    return screen_x, screen_y

def scale_radius(r):
    return int(r * (WIDTH / 2.0))

# Main Game & Rendering Loop
running = True
while running:
    # 1. Handle Input (Keyboard play mode, or switch to AI/Random)
    action = 0
    keys = pygame.key.get_pressed()
    if keys[pygame.K_RIGHT]: action |= 1
    if keys[pygame.K_LEFT]:  action |= 2
    if keys[pygame.K_UP]:    action |= 4
    if keys[pygame.K_DOWN]:    action |= 8

    # If no keys are pressed, you can uncomment line below to watch random AI play instead:
    # action = np.random.randint(0, 16)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 2. Step Environment
    obs, reward, done = env.NextFrame(action)
    
    if done:
        pygame.time.delay(500) # Brief pause on death
        obs = env.resetFB()

    # 3. Drawing / Rendering
    screen.fill((15, 15, 25)) # Dark space background

    # Draw Falling Balls (Red)
    for i in range(env.noBalls):
        bx, by = scale_coords(env.FB_position[i, 0], env.FB_position[i, 1])
        br = scale_radius(env.FB_radius)
        pygame.draw.circle(screen, (230, 50, 50), (bx, by), br)

    # Draw Player (Cyan/Blue)
    px, py = scale_coords(env.player_position[0], env.player_position[1])
    pr = scale_radius(env.player_radius)
    pygame.draw.circle(screen, (50, 200, 255), (px, py), pr)

    # Display Score on Screen
    font = pygame.font.SysFont(None, 24)
    score_surf = font.render(f"Score: {env.score}", True, (255, 255, 255))
    screen.blit(score_surf, (20, 20))

    pygame.display.flip()
    clock.tick(40) # Lock to 40 FPS matching your dt = 1/40 physics step

pygame.quit()
sys.exit()