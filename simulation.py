# ==============================================================================
# PHASE 3: FINAL DEMONSTRATION - DISTORTED SQUARE PATTERN (WAY LARGER WORLD)
# ==============================================================================
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# --- World Parameters ---
# CHANGED: Massively increased the world size again.
WORLD_X_METERS = 20000
WORLD_Y_METERS = 8000

# --- Wind Model (Wind blows from left to right) ---
WIND_VELOCITY = np.array([30.0, 0.0, 0.0]) # A strong, constant wind for a clear effect

# --- Drone Class ---
class Drone:
    def __init__(self, start_pos):
        self.position = np.array(start_pos, dtype=float)
        # The drone's own propulsion speed, separate from the wind
        self.airspeed = 25.0 
        self.velocity = np.array([0.0, 0.0, 0.0]) # This is the drone's velocity relative to the air
        self.history = [self.position.copy()]

    def set_heading(self, direction_vector):
        """Points the drone in a specific direction."""
        # Normalize the vector to ensure constant speed
        norm = np.linalg.norm(direction_vector)
        if norm > 0:
            self.velocity = (direction_vector / norm) * self.airspeed

    def update_state(self, dt):
        """Update drone's actual position based on its own velocity plus the wind."""
        # The drone's true ground speed is its own velocity plus the wind's velocity
        ground_velocity = self.velocity + WIND_VELOCITY
        self.position += ground_velocity * dt
        self.history.append(self.position.copy())

# ==============================================================================
# SIMULATION AND VISUALIZATION
# ==============================================================================

# --- Simulation Setup ---
SIM_DURATION_SECONDS = 160 
TIME_STEP_DT = 0.5 

# Start position will auto-adjust to the middle of the new world
start_position = [WORLD_X_METERS / 2, WORLD_Y_METERS / 2, 0.0]
drone = Drone(start_pos=start_position)

# --- Visualization Setup ---
fig, ax = plt.subplots(figsize=(12, 8)) 
ax.set_xlim(0, WORLD_X_METERS)
ax.set_ylim(0, WORLD_Y_METERS)
ax.set_aspect('equal')
ax.set_title('Demonstration of Wind Effect on UAV Flight Path')
ax.set_xlabel('East-West Position (m)')
ax.set_ylabel('North-South Position (m)')
ax.grid(True)

path_line, = ax.plot([], [], 'b-', lw=2, label='Actual Path')
drone_point, = ax.plot([], [], 'ro', markersize=8, label='Drone')
ax.legend()
time_text = ax.text(0.02, 0.95, '', transform=ax.transAxes)

# --- MAIN PILOT LOGIC ---
def update_animation(frame_num):
    current_time = frame_num * TIME_STEP_DT
    
    # The drone attempts to fly a square pattern
    if current_time < 40:
        # 1. Fly North (Up)
        drone.set_heading(np.array([0.0, 1.0, 0.0]))
    elif current_time < 80:
        # 2. Fly West (Left, AGAINST the wind)
        drone.set_heading(np.array([-1.0, 0.0, 0.0]))
    elif current_time < 120:
        # 3. Fly South (Down)
        drone.set_heading(np.array([0.0, -1.0, 0.0]))
    else:
        # 4. Fly East (Right, WITH the wind)
        drone.set_heading(np.array([1.0, 0.0, 0.0]))
    
    drone.update_state(TIME_STEP_DT)
    
    # Update the plot
    path_data = np.array(drone.history)
    path_line.set_data(path_data[:, 0], path_data[:, 1])
    drone_point.set_data([drone.position[0]], [drone.position[1]])
    time_text.set_text(f'Time: {current_time:.1f}s')
    
    return path_line, drone_point, time_text

# Create and run the animation
ani = FuncAnimation(fig, update_animation, frames=int(SIM_DURATION_SECONDS / TIME_STEP_DT), blit=True, interval=20)
plt.show()