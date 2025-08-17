# ==============================================================================
# FINAL RSI-LEVEL EXPERIMENT: STATION-KEEPING WITH FUEL CONSUMPTION
# ==============================================================================
import numpy as np
import matplotlib.pyplot as plt

# ==============================================================================
# 1. THE ENVIRONMENT AND PHYSICS
# ==============================================================================

# --- World Parameters ---
LOITER_POINT = np.array([1000.0, 1000.0, 200.0]) # The point to stay near

# --- Wind Model ---
BASE_WIND_SPEED_MPS = 5.0
WIND_SHEAR_COEFFICIENT = 0.05
def get_wind_at_altitude(altitude_z):
    wind_speed = BASE_WIND_SPEED_MPS + (altitude_z * WIND_SHEAR_COEFFICIENT)
    return np.array([wind_speed, 0.0, 0.0])

# --- Physical Constants ---
GRAVITY = 9.81
DRONE_THRUST_FORCE = 30.0 

# ==============================================================================
# 2. THE DRONE BLUEPRINT (With a Fuel Tank)
# ==============================================================================

class Drone:
    def __init__(self, start_pos):
        self.mass_kg = 1.5
        self.position = np.array(start_pos, dtype=float)
        self.velocity = np.array([0.0, 0.0, 0.0])
        self.is_active = True 
        
        # *** NEW FEATURE: Fuel Tank ***
        # The drone has a limited amount of fuel (energy budget)
        self.fuel = 10000.0 
        
        self.history = [self.position.copy()]
        self.energy_history = [self.get_total_energy()]

    def update_state(self, pilot_thrust_vector, dt):
        # Consume fuel based on how much thrust is used
        thrust_magnitude = np.linalg.norm(pilot_thrust_vector)
        self.fuel -= thrust_magnitude * dt
        
        # If fuel runs out, the drone is no longer active
        if self.fuel <= 0:
            self.is_active = False
            # *** THIS IS THE FIX (Option 1) ***
            # When fuel runs out, velocity stops instantly.
            self.velocity = np.array([0.0, 0.0, 0.0])

        if not self.is_active:
            pilot_thrust_vector = np.array([0.0, 0.0, 0.0]) # No thrust if inactive

        wind_force = get_wind_at_altitude(self.position[2]) 
        gravity_force = np.array([0.0, 0.0, -GRAVITY * self.mass_kg])
        
        total_force = pilot_thrust_vector + wind_force + gravity_force
        acceleration = total_force / self.mass_kg
        
        self.velocity += acceleration * dt
        self.position += self.velocity * dt
        
        if self.position[2] < 0:
             self.is_active = False
             self.position[2] = 0
             self.velocity = np.array([0.0, 0.0, 0.0])

        self.history.append(self.position.copy())
        self.energy_history.append(self.get_total_energy())

    def get_total_energy(self):
        if not self.is_active:
            return 0
        
        speed_mps = np.linalg.norm(self.velocity)
        kinetic_energy = 0.5 * self.mass_kg * (speed_mps ** 2)
        potential_energy = self.mass_kg * GRAVITY * self.position[2]
        return kinetic_energy + potential_energy

# ==============================================================================
# 3. THE PILOT ALGORITHMS
# ==============================================================================

class DumbPilot:
    """Fights the wind to stay perfectly still, consuming lots of fuel."""
    def __init__(self, loiter_point):
        self.loiter_point = loiter_point

    def get_thrust_command(self, drone_state):
        error_pos = self.loiter_point - drone_state.position
        error_vel = -drone_state.velocity
        thrust_direction = error_pos + error_vel
        return thrust_direction * 2.0 

class SmartPilot:
    """Uses dynamic soaring S-curves to conserve fuel."""
    def __init__(self, loiter_point):
        self.loiter_point = loiter_point
        self.soaring_state = "CLIMBING"
        self.high_alt_threshold = 350.0
        self.low_alt_threshold = 50.0

    def get_thrust_command(self, drone_state):
        if self.soaring_state == "CLIMBING" and drone_state.position[2] > self.high_alt_threshold:
            self.soaring_state = "DIVING"
        elif self.soaring_state == "DIVING" and drone_state.position[2] < self.low_alt_threshold:
            self.soaring_state = "CLIMBING"
            
        if self.soaring_state == "CLIMBING":
            thrust_direction = np.array([-0.7, 0.1, 0.7])
        else: # DIVING
            thrust_direction = np.array([0.8, 0.1, -0.6])
            
        return thrust_direction * DRONE_THRUST_FORCE

# ==============================================================================
# 4. THE SIMULATION RUNNER
# ==============================================================================
def run_simulation(pilot, start_pos, duration_sec, dt):
    drone = Drone(start_pos=start_pos)
    num_steps = int(duration_sec / dt)
    
    for step in range(num_steps):
        if not drone.is_active:
            remaining_steps = num_steps - step
            last_pos = drone.history[-1]
            drone.history.extend([last_pos] * remaining_steps)
            drone.energy_history.extend([0] * remaining_steps)
            print(f"{pilot.__class__.__name__} ran out of fuel at step {step}.")
            break
        
        thrust_command = pilot.get_thrust_command(drone)
        drone.update_state(thrust_command, dt)
            
    return drone.history, drone.energy_history

# --- Main Experiment Execution ---
print("--- Starting UAV Station-Keeping Endurance Test ---")

SIM_DURATION = 180 
TIME_STEP = 0.5

print("Running simulation for DumbPilot (Fighter)...")
dumb_pilot = DumbPilot(loiter_point=LOITER_POINT)
dumb_history, dumb_energy = run_simulation(dumb_pilot, LOITER_POINT, SIM_DURATION, TIME_STEP)
print("DumbPilot simulation finished.")

print("Running simulation for SmartPilot (Soarer)...")
smart_pilot = SmartPilot(loiter_point=LOITER_POINT)
smart_history, smart_energy = run_simulation(smart_pilot, LOITER_POINT, SIM_DURATION, TIME_STEP)
print("SmartPilot simulation finished.")

print("--- All simulations complete. Generating and saving plot... ---")

# ==============================================================================
# 5. PLOTTING AND SAVING THE RESULTS
# ==============================================================================

dumb_path = np.array(dumb_history)
smart_path = np.array(smart_history)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))
fig.suptitle('UAV Endurance Comparison: Station-Keeping in Wind', fontsize=18)

# --- Plot 1: Flight Paths (Top-Down View) ---
ax1.plot(dumb_path[:, 0], dumb_path[:, 1], 'r-', label='Dumb Pilot (Fighting Wind)')
ax1.plot(smart_path[:, 0], smart_path[:, 1], 'g-', label='Smart Pilot (Soaring)')
ax1.plot(LOITER_POINT[0], LOITER_POINT[1], 'kx', markersize=12, mew=3, label='Loiter Point')
ax1.set_title('Top-Down Flight Paths', fontsize=16)
ax1.set_xlabel('East-West Position (m)')
ax1.set_ylabel('North-South Position (m)')
ax1.legend()
ax1.grid(True)
ax1.axis('equal')

# --- Plot 2: Energy Over Time ---
time_axis = np.arange(len(dumb_energy)) * TIME_STEP

ax2.plot(time_axis, dumb_energy, 'r-', lw=2, label='Dumb Pilot Energy')
ax2.plot(time_axis, smart_energy, 'g-', lw=2, label='Smart Pilot Energy')
ax2.set_title('Total Mechanical Energy vs. Time', fontsize=16)
ax2.set_xlabel('Time (s)')
ax2.set_ylabel('Energy (Joules)')
ax2.legend()
ax2.grid(True)

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.savefig('results_plot.png') 
plt.show() 

print("--- Experiment Finished. 'results_plot.png' has been saved. ---")
