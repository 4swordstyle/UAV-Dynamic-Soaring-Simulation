# ==============================================================================
# FINAL EXPERIMENT: DYNAMIC SOARING VS. DIRECT FLIGHT
# ==============================================================================
import numpy as np
import matplotlib.pyplot as plt

# ==============================================================================
# 1. THE ENVIRONMENT AND PHYSICS (Same as before)
# ==============================================================================

# --- World Parameters ---
WORLD_X_METERS = 1000
WORLD_Y_METERS = 1000
WORLD_Z_METERS = 500
TARGET_POSITION = np.array([800.0, 500.0, 50.0]) # Target coordinates

# --- Wind Model ---
BASE_WIND_SPEED_MPS = 5.0
WIND_SHEAR_COEFFICIENT = 0.05
def get_wind_at_altitude(altitude_z):
    wind_speed = BASE_WIND_SPEED_MPS + (altitude_z * WIND_SHEAR_COEFFICIENT)
    return np.array([wind_speed, 0.0, 0.0])

# --- Physical Constants ---
GRAVITY = 9.81
DRONE_THRUST_FORCE = 25.0 # The constant force the drone's propellers can exert

# ==============================================================================
# 2. THE DRONE BLUEPRINT (Slightly updated)
# ==============================================================================

class Drone:
    def __init__(self, start_pos):
        self.mass_kg = 1.5
        self.position = np.array(start_pos, dtype=float)
        self.velocity = np.array([0.0, 0.0, 0.0])
        
        # Data recording for plots
        self.history = [self.position.copy()]
        self.energy_history = [self.get_total_energy()]

    def update_state(self, pilot_thrust_vector, dt):
        """Updates the drone's state based on thrust, drag, wind, and gravity."""
        # Forces acting on the drone
        wind_force = get_wind_at_altitude(self.position[2]) # Simplified: treating wind as a force for this model
        gravity_force = np.array([0.0, 0.0, -GRAVITY * self.mass_kg])
        
        # Total force = thrust from pilot + wind + gravity
        total_force = pilot_thrust_vector + wind_force + gravity_force
        
        # Newton's Second Law: F = ma  =>  a = F/m
        acceleration = total_force / self.mass_kg
        
        # Update velocity and position
        self.velocity += acceleration * dt
        self.position += self.velocity * dt
        
        # Stop the drone if it hits the ground
        if self.position[2] < 0:
            self.position[2] = 0
            self.velocity = np.array([0.0, 0.0, 0.0])

        # Record data
        self.history.append(self.position.copy())
        self.energy_history.append(self.get_total_energy())

    def get_kinetic_energy(self):
        speed_mps = np.linalg.norm(self.velocity)
        return 0.5 * self.mass_kg * (speed_mps ** 2)
        
    def get_potential_energy(self):
        altitude_h = self.position[2]
        if altitude_h < 0: altitude_h = 0
        return self.mass_kg * GRAVITY * altitude_h
        
    def get_total_energy(self):
        return self.get_kinetic_energy() + self.get_potential_energy()

# ==============================================================================
# 3. THE PILOT ALGORITHMS (The "Brains")
# ==============================================================================

class DumbPilot:
    """Flies in a straight line towards the target."""
    def __init__(self, target):
        self.target = target

    def get_thrust_command(self, drone_state):
        direction_to_target = self.target - drone_state.position
        # Normalize the vector to get a pure direction (length = 1)
        norm = np.linalg.norm(direction_to_target)
        if norm > 1:
            direction_to_target = direction_to_target / norm
        
        # Apply full thrust in that direction
        return direction_to_target * DRONE_THRUST_FORCE

class SmartPilot:
    """Uses dynamic soaring to conserve energy."""
    def __init__(self, target):
        self.target = target
        self.soaring_state = "CLIMBING" # Start by climbing
        self.high_alt_threshold = 350.0 # Altitude to switch to diving
        self.low_alt_threshold = 50.0 # Altitude to switch to climbing

    def get_thrust_command(self, drone_state):
        # State machine logic
        if self.soaring_state == "CLIMBING" and drone_state.position[2] > self.high_alt_threshold:
            self.soaring_state = "DIVING"
        elif self.soaring_state == "DIVING" and drone_state.position[2] < self.low_alt_threshold:
            self.soaring_state = "CLIMBING"
            
        # Command logic based on state
        if self.soaring_state == "CLIMBING":
            # Fly up and into the wind (negative x direction)
            thrust_direction = np.array([-0.7, 0.1, 0.7]) # Diagonal up and into wind
        else: # DIVING
            # Fly down and with the wind (positive x direction)
            thrust_direction = np.array([0.8, 0.1, -0.6]) # Diagonal down and with wind
            
        return thrust_direction * DRONE_THRUST_FORCE

# ==============================================================================
# 4. THE SIMULATION RUNNER
# ==============================================================================
def run_simulation(pilot, start_pos, duration_sec, dt):
    """Runs a full simulation for a given pilot."""
    drone = Drone(start_pos=start_pos)
    num_steps = int(duration_sec / dt)
    
    for step in range(num_steps):
        # 1. Pilot makes a decision
        thrust_command = pilot.get_thrust_command(drone)
        # 2. Drone state is updated
        drone.update_state(thrust_command, dt)
        # 3. Check if we reached the target
        if np.linalg.norm(drone.position - TARGET_POSITION) < 50: # 50m radius
            print(f"Target reached by {pilot.__class__.__name__} at step {step}.")
            break
            
    return drone.history, drone.energy_history

# --- Main Experiment Execution ---
print("--- Starting UAV Flight Simulation Experiment ---")

# Simulation Parameters
START_POS = [50.0, 500.0, 50.0]
SIM_DURATION = 200
TIME_STEP = 0.5

# Run simulation for the Dumb Pilot
print("Running simulation for DumbPilot...")
dumb_pilot = DumbPilot(target=TARGET_POSITION)
dumb_history, dumb_energy = run_simulation(dumb_pilot, START_POS, SIM_DURATION, TIME_STEP)
print("DumbPilot simulation finished.")

# Run simulation for the Smart Pilot
print("Running simulation for SmartPilot...")
smart_pilot = SmartPilot(target=TARGET_POSITION)
smart_history, smart_energy = run_simulation(smart_pilot, START_POS, SIM_DURATION, TIME_STEP)
print("SmartPilot simulation finished.")

print("--- All simulations complete. Generating plots... ---")

# ==============================================================================
# 5. PLOTTING THE RESULTS (The Research Findings)
# ==============================================================================

# Convert history lists to numpy arrays for easier plotting
dumb_path = np.array(dumb_history)
smart_path = np.array(smart_history)

# --- Plot 1: Flight Paths (Top-Down View) ---
plt.figure(figsize=(12, 12))
plt.subplot(2, 1, 1) # Create a figure with 2 rows, 1 column, and select plot 1
plt.plot(dumb_path[:, 0], dumb_path[:, 1], 'r-', label='Dumb Pilot (Direct)')
plt.plot(smart_path[:, 0], smart_path[:, 1], 'g-', label='Smart Pilot (Soaring)')
plt.plot(START_POS[0], START_POS[1], 'ko', markersize=10, label='Start')
plt.plot(TARGET_POSITION[0], TARGET_POSITION[1], 'kx', markersize=10, mew=3, label='Target')
plt.title('Top-Down Flight Paths', fontsize=16)
plt.xlabel('East-West Position (m)')
plt.ylabel('North-South Position (m)')
plt.legend()
plt.grid(True)
plt.axis('equal')

# --- Plot 2: Energy Over Time ---
time_axis_dumb = np.arange(len(dumb_energy)) * TIME_STEP
time_axis_smart = np.arange(len(smart_energy)) * TIME_STEP

plt.subplot(2, 1, 2) # Select plot 2
plt.plot(time_axis_dumb, dumb_energy, 'r-', label='Dumb Pilot Energy')
plt.plot(time_axis_smart, smart_energy, 'g-', label='Smart Pilot Energy')
plt.title('Total Mechanical Energy vs. Time', fontsize=16)
plt.xlabel('Time (s)')
plt.ylabel('Energy (Joules)')
plt.legend()
plt.grid(True)

plt.tight_layout() # Adjusts plot to prevent labels from overlapping
plt.show()

print("--- Experiment Finished ---")