"""
Dynamic Weather Simulation with enhanced visual effects
"""

import os
import sys
import numpy as np
import time
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.animation import FuncAnimation
from matplotlib.colors import Normalize

# Adjust Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

class DynamicWeatherSimulation:
    """Real-time weather simulation with dynamic color changes"""
    
    def __init__(self, width=200, height=200, dx=1.0, kappa=0.2):
        """
        Initialize real-time weather simulation with higher diffusion.
        
        Args:
            width (int): Grid width
            height (int): Grid height
            dx (float): Grid spacing
            kappa (float): Diffusion coefficient - increased for more visible changes
        """
        self.width = width
        self.height = height
        self.dx = dx
        self.kappa = kappa  # Increased diffusion coefficient
        
        print(f"Initializing dynamic weather simulation ({width}x{height})")
        
        # Import C++ module
        try:
            import cpp_weather
            self.cpp_weather = cpp_weather
            print("Successfully loaded C++ module")
        except ImportError as e:
            print(f"Error importing C++ module: {e}")
            print("Make sure the C++ module is compiled and in Python path")
            sys.exit(1)
        
        # Initialize C++ objects
        self.solver = self.cpp_weather.Solver(width, height, dx, kappa)
        self.wind_field = self.cpp_weather.WindField(width, height)
        self.temp_field = self.cpp_weather.TemperatureField(width, height)
        print("Initialized C++ objects")
        
        # Initialize storage
        self.time = 0.0
        self.steps = 0
        self.dt_history = []
        self.temp_min_history = []
        self.temp_max_history = []
        
        # Create figure and axes for animation
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.fig.canvas.manager.set_window_title('Dynamic Weather Simulation')
        
        # Create plots to update later
        self.temp_plot = None
        self.quiver_plot = None
        self.colorbar = None
        
        # Display parameters
        self.quiver_density = 10  # Display 1 arrow for each quiver_density cells
        
        # Physical parameters
        self.min_temp = 0
        self.max_temp = 40
        self.dynamic_color_range = True  # Enable dynamic color range updates
        
        # Color mapping function
        self.cmap = cm.plasma  # Changed to a more dynamic colormap
    
    def set_initial_conditions(self):
        """Create extreme initial conditions for visible changes"""
        print("Setting up initial conditions with strong temperature gradients...")
        
        # Create temperature gradient in North-South direction with more extreme values
        self.temp_field.set_gradient(5.0, 35.0, self.cpp_weather.GradientDirection.NORTH_SOUTH)
        
        # Add a stronger heat source in the middle
        center_x = self.width // 2
        center_y = self.height // 2
        self.temp_field.add_heat_source(center_x, center_y, 25.0, self.width // 8)
        
        # Add cold spots
        self.temp_field.add_heat_source(center_x - self.width//4, center_y, -15.0, self.width // 10)
        self.temp_field.add_heat_source(center_x + self.width//4, center_y, -10.0, self.width // 12)
        
        # Add random heat sources with more extreme temperatures
        np.random.seed(42)  # For reproducibility
        num_sources = 8
        for _ in range(num_sources):
            x = np.random.randint(0, self.width)
            y = np.random.randint(0, self.height)
            # Randomly choose between hot and cold sources
            strength = np.random.uniform(-20.0, 20.0)
            radius = np.random.uniform(self.width // 30, self.width // 15)
            self.temp_field.add_heat_source(x, y, strength, radius)
        
        # Create a stronger wind field with more vortices
        self.wind_field.generate_gaussian_field(12, 4.0, self.width // 12)
        
        # Get initial data
        temp = self.get_temperature()
        
        # Save initial statistics
        self.temp_min_history.append(np.min(temp))
        self.temp_max_history.append(np.max(temp))
        
        # Update temperature range
        self.min_temp = max(-10, np.min(temp) - 5)
        self.max_temp = min(50, np.max(temp) + 5)
        print(f"Initial temperature range: {self.min_temp:.1f} - {self.max_temp:.1f}")
        
        print("Initial conditions set up")
    
    def get_temperature(self):
        """Get current temperature field as 2D array"""
        return self.temp_field.get_temperature().reshape(self.height, self.width)
    
    def get_wind_field(self):
        """Get current wind field as two 2D arrays (x, y)"""
        wind_x = self.wind_field.get_wind_x().reshape(self.height, self.width)
        wind_y = self.wind_field.get_wind_y().reshape(self.height, self.width)
        return wind_x, wind_y
    
    def step(self):
        """
        Perform one simulation step with stronger effects.
        
        Returns:
            float: Time step used
        """
        # Get data
        temp = self.temp_field.get_temperature()
        wind_x = self.wind_field.get_wind_x()
        wind_y = self.wind_field.get_wind_y()
        
        # Calculate time step - using a fixed dt to avoid instability
        cfl_dt = self.solver.compute_cfl_time_step(wind_x, wind_y)
        dt = max(0.05, cfl_dt)  # Ensure positive value with minimum threshold
        
        # For bigger changes, take multiple substeps
        substeps = 3  # Take 3 substeps per frame for more visible changes
        substep_dt = dt / max(1, substeps)  # Avoid division by zero
        
        for _ in range(substeps):
            # Update temperature
            new_temp = self.solver.solve_rk4_step(temp, wind_x, wind_y, substep_dt)
            self.temp_field.set_temperature(new_temp.flatten())
            temp = new_temp.flatten()  # Update for next substep
        
        # Occasionally update wind field to create changes - more frequent
        if self.steps % 10 == 0 and self.steps > 0:  # Every 10 steps instead of 20
            num_vortices = np.random.randint(3, 15)  # More vortices
            strength = np.random.uniform(2.0, 5.0)   # Stronger wind
            radius = np.random.uniform(self.width // 15, self.width // 8)
            self.wind_field.generate_gaussian_field(num_vortices, strength, radius)
            print(f"Wind field updated: {num_vortices} vortices, strength {strength:.1f}")
            
            # Add a random heat/cold source occasionally
            if np.random.random() < 0.5:  # 50% chance
                x = np.random.randint(0, self.width)
                y = np.random.randint(0, self.height)
                strength = np.random.uniform(-15.0, 20.0)
                radius = np.random.uniform(self.width // 25, self.width // 15)
                self.temp_field.add_heat_source(x, y, strength, radius)
                print(f"Added {'heat' if strength > 0 else 'cold'} source: strength {strength:.1f}")
        
        # Update state
        self.time += dt
        self.steps += 1
        self.dt_history.append(dt)
        
        # Update temperature statistics
        current_temp = self.get_temperature()
        self.temp_min_history.append(np.min(current_temp))
        self.temp_max_history.append(np.max(current_temp))
        
        return dt
    
    def init_animation(self):
        """Initialize animation"""
        # Get initial data
        temp = self.get_temperature()
        wind_x, wind_y = self.get_wind_field()
        
        # Initial temperature range
        norm = Normalize(vmin=self.min_temp, vmax=self.max_temp)
        
        # Plot temperature field
        self.temp_plot = self.ax.imshow(temp, origin='lower', cmap=self.cmap, norm=norm, animated=True)
        
        # Add colorbar
        self.colorbar = self.fig.colorbar(self.temp_plot, ax=self.ax)
        self.colorbar.set_label('Temperature (C)')
        
        # Create grid for wind vectors
        y, x = np.mgrid[0:self.height:self.quiver_density, 0:self.width:self.quiver_density]
        
        # Plot wind
        self.quiver_plot = self.ax.quiver(
            x, y,
            wind_x[::self.quiver_density, ::self.quiver_density],
            wind_y[::self.quiver_density, ::self.quiver_density],
            color='white', scale=50, alpha=0.7
        )
        
        # Add title and labels
        self.ax.set_title(f'Weather Simulation (t={self.time:.2f}s, step {self.steps})')
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        
        # Add instructions
        plt.figtext(0.02, 0.02, 'Keys: Q - Quit, R - Randomize wind & add sources', fontsize=9)
        
        return self.temp_plot, self.quiver_plot
    
    def update_animation(self, frame):
        """Update animation with dynamic color range"""
        # Perform one simulation step
        start_time = time.time()
        dt = self.step()
        compute_time = time.time() - start_time
        
        # Get new data
        temp = self.get_temperature()
        wind_x, wind_y = self.get_wind_field()
        
        # Update temperature field
        self.temp_plot.set_array(temp)
        
        # Dynamically update color range for better visualization
        if self.dynamic_color_range and frame % 5 == 0:  # Update every 5 frames
            current_min = np.min(temp)
            current_max = np.max(temp)
            
            # Smooth transitions for color range
            self.min_temp = min(self.min_temp, max(-10, current_min - 2))
            self.max_temp = max(self.max_temp, min(50, current_max + 2))
            
            # Apply new color range
            self.temp_plot.set_clim(self.min_temp, self.max_temp)
            self.colorbar.update_normal(self.temp_plot)
        
        # Update wind vectors
        if frame % 2 == 0:  # Only update wind every 2 frames for better performance
            self.quiver_plot.set_UVC(
                wind_x[::self.quiver_density, ::self.quiver_density],
                wind_y[::self.quiver_density, ::self.quiver_density]
            )
        
        # Update title with statistics
        self.ax.set_title(f'Weather Simulation (t={self.time:.2f}s, step {self.steps})\n'
                         f'FPS: {1.0/max(0.001, compute_time):.1f}, Temp: {np.min(temp):.1f}°C to {np.max(temp):.1f}°C')
        
        return self.temp_plot, self.quiver_plot
    
    def on_key_press(self, event):
        """Handle key press events"""
        if event.key == 'q':
            plt.close(self.fig)
        elif event.key == 'r':
            # Randomize wind and add heat/cold sources
            num_vortices = np.random.randint(5, 15)
            strength = np.random.uniform(3.0, 6.0)
            radius = np.random.uniform(self.width // 15, self.width // 8)
            self.wind_field.generate_gaussian_field(num_vortices, strength, radius)
            
            # Add 2-3 random heat/cold sources
            for _ in range(np.random.randint(2, 4)):
                x = np.random.randint(0, self.width)
                y = np.random.randint(0, self.height)
                strength = np.random.uniform(-20.0, 25.0)
                radius = np.random.uniform(self.width // 25, self.width // 12)
                self.temp_field.add_heat_source(x, y, strength, radius)
            
            print("Wind field and temperature sources randomized!")
    
    def run_animation(self, num_frames=1000, interval=50):
        """
        Run real-time animation.
        
        Args:
            num_frames (int): Number of frames
            interval (int): Interval between frames (ms)
        """
        print(f"Running animation with {num_frames} frames, interval={interval}ms")
        
        # Connect key press event
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        
        # Create animation
        self.animation = FuncAnimation(
            self.fig, self.update_animation, frames=num_frames,
            init_func=self.init_animation, blit=True, interval=interval
        )
        
        # Display animation
        plt.tight_layout()
        plt.show()

def main():
    """Main function"""
    print("Dynamic Weather Simulation")
    
    # Simulation parameters
    width = 200
    height = 200
    frames = 1000
    interval = 50  # ms
    
    # Initialize simulation
    simulation = DynamicWeatherSimulation(width, height)
    simulation.set_initial_conditions()
    
    # Run animation
    simulation.run_animation(num_frames=frames, interval=interval)
    
    print("Simulation ended")

if __name__ == "__main__":
    main()
