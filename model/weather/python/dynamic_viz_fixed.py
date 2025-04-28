"""
Dynamic Weather Simulation with enhanced visual effects (Fixed version)
Corrected API usage and error handling to avoid negative dimensions error
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
    
    def __init__(self, width=200, height=200, dx=1.0, kappa=0.1):
        """
        Initialize real-time weather simulation with appropriate diffusion.
        
        Args:
            width (int): Grid width
            height (int): Grid height
            dx (float): Grid spacing
            kappa (float): Diffusion coefficient - reduced for stability
        """
        self.width = width
        self.height = height
        self.dx = dx
        self.kappa = kappa  # Reduced from 0.2 for better stability
        
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
        
        # Initialize C++ objects with error checking
        try:
            self.solver = self.cpp_weather.Solver(width, height, dx, kappa)
            print("Created solver")
            
            self.wind_field = self.cpp_weather.WindField(width, height)
            print("Created wind field")
            
            self.temp_field = self.cpp_weather.TemperatureField(width, height)
            print("Created temperature field")
        except Exception as e:
            print(f"Error creating C++ objects: {e}")
            sys.exit(1)
        
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
        """Create mild initial conditions for stability"""
        print("Setting up initial conditions with temperature gradients...")
        
        try:
            # Create temperature gradient in North-South direction with moderate values
            self.temp_field.set_gradient(10.0, 30.0, self.cpp_weather.GradientDirection.NORTH_SOUTH)
            
            # Add a heat source in the middle
            center_x = self.width // 2
            center_y = self.height // 2
            self.temp_field.add_heat_source(center_x, center_y, 15.0, self.width // 8)
            
            # Add modest cool spots
            self.temp_field.add_heat_source(center_x - self.width//4, center_y, -8.0, self.width // 10)
            self.temp_field.add_heat_source(center_x + self.width//4, center_y, -5.0, self.width // 12)
            
            # Add fewer random heat sources with moderate temperatures
            np.random.seed(42)  # For reproducibility
            num_sources = 5
            for _ in range(num_sources):
                x = np.random.randint(0, self.width)
                y = np.random.randint(0, self.height)
                # Randomly choose between hot and cold sources
                strength = np.random.uniform(-10.0, 15.0)  # Less extreme temperatures
                radius = np.random.uniform(self.width // 20, self.width // 10)
                self.temp_field.add_heat_source(x, y, strength, radius)
            
            # Create modest Gaussian wind field
            # Important: use proper function call - was incorrectly using generate_uniform()
            self.wind_field.generate_gaussian_field(5, 2.0, self.width // 8)
            
            # Get initial data
            temp = self.get_temperature()
            wind_x, wind_y = self.get_wind_field()
            
            # Print statistics
            print(f"Initial temperature range: {np.min(temp):.1f} - {np.max(temp):.1f}")
            
            # Verify array shapes
            print(f"Temperature shape: {temp.shape}, size: {temp.size}, expected: {self.width*self.height}")
            print(f"Wind X shape: {wind_x.shape}, Wind Y shape: {wind_y.shape}")
            
            if temp.size != self.width * self.height:
                print("WARNING: Temperature array size mismatch!")
                
        except Exception as e:
            print(f"Error setting initial conditions: {e}")
            raise
    
    def get_temperature(self):
        """Get current temperature field as 2D array"""
        temp = self.temp_field.get_temperature()
        return temp.reshape((self.height, self.width))
    
    def get_wind_field(self):
        """Get current wind field as two 2D arrays (x, y)"""
        wind_x = self.wind_field.get_wind_x().reshape((self.height, self.width))
        wind_y = self.wind_field.get_wind_y().reshape((self.height, self.width))
        return wind_x, wind_y
    
    def step(self):
        """
        Perform one simulation step with stronger effects.
        
        Returns:
            float: Time step used
        """
        try:
            # Get data
            temp = self.temp_field.get_temperature()
            wind_x = self.wind_field.get_wind_x()
            wind_y = self.wind_field.get_wind_y()
            
            # Verify shapes and sizes
            expected_size = self.width * self.height
            if temp.size != expected_size:
                print(f"ERROR: Temperature size mismatch: {temp.size} != {expected_size}")
                # Attempt to fix or return safely
                return 0.1
                
            # Check for NaN or Inf values
            if np.isnan(temp).any() or np.isinf(temp).any():
                print("ERROR: NaN or Inf values in temperature array")
                # Reset temperature to safe values
                self.temp_field.set_uniform(20.0)
                temp = self.temp_field.get_temperature()
            
            # Calculate time step - using a safe fixed dt to avoid instability
            cfl_dt = self.solver.compute_cfl_time_step(wind_x, wind_y)
            
            # Ensure positive value with minimum threshold
            dt = max(0.05, cfl_dt)
            
            # For safety, also enforce a maximum timestep
            dt = min(dt, 0.5)
            
            # For bigger changes, take multiple substeps
            substeps = 2  # Reduced from 3 for stability
            substep_dt = dt / max(1, substeps)  # Avoid division by zero
            
            for i in range(substeps):
                # Update temperature
                try:
                    new_temp = self.solver.solve_rk4_step(temp, wind_x, wind_y, substep_dt)
                    
                    # Reshape if needed to ensure correct dimensions
                    if new_temp.size == self.width * self.height:
                        self.temp_field.set_temperature(new_temp.flatten())
                        temp = new_temp.flatten()  # Update for next substep
                    else:
                        print(f"ERROR: Solver returned wrong size: {new_temp.size}")
                        return dt  # Return current dt and skip this substep
                        
                except ValueError as e:
                    print(f"Error in solver step {i}: {e}")
                    # Return the current dt value so animation continues
                    return dt
            
            # Occasionally update wind field - less frequently for stability
            if self.steps % 15 == 0 and self.steps > 0:  # Every 15 steps
                num_vortices = np.random.randint(3, 8)  # Fewer vortices
                strength = np.random.uniform(1.5, 3.0)   # Weaker wind
                radius = np.random.uniform(self.width // 15, self.width // 8)
                
                self.wind_field.generate_gaussian_field(num_vortices, strength, radius)
                print(f"Wind field updated: {num_vortices} vortices, strength {strength:.1f}")
                
                # Add a random heat/cold source occasionally
                if np.random.random() < 0.3:  # 30% chance instead of 50%
                    x = np.random.randint(0, self.width)
                    y = np.random.randint(0, self.height)
                    strength = np.random.uniform(-10.0, 15.0)  # Less extreme
                    radius = np.random.uniform(self.width // 20, self.width // 12)
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
            
        except Exception as e:
            print(f"Unexpected error in step(): {e}")
            # Return a safe default time step to keep animation running
            return 0.1
    
    def init_animation(self):
        """Initialize animation"""
        # Get initial data
        temp = self.get_temperature()
        wind_x, wind_y = self.get_wind_field()
        
        # Create temperature plot
        self.temp_plot = self.ax.imshow(
            temp, 
            cmap=self.cmap, 
            origin='lower',
            aspect='equal',
            vmin=self.min_temp, 
            vmax=self.max_temp
        )
        
        # Create wind vector plot (quiver)
        # Use a subset of wind vectors for better visualization
        x = np.arange(0, self.width, self.quiver_density)
        y = np.arange(0, self.height, self.quiver_density)
        X, Y = np.meshgrid(x, y)
        
        self.quiver_plot = self.ax.quiver(
            X, Y,
            wind_x[::self.quiver_density, ::self.quiver_density],
            wind_y[::self.quiver_density, ::self.quiver_density],
            color='white', 
            scale=50,
            alpha=0.7
        )
        
        # Add colorbar
        self.colorbar = self.fig.colorbar(self.temp_plot, ax=self.ax)
        self.colorbar.set_label('Temperature (°C)')
        
        # Add title
        self.ax.set_title('Weather Simulation (t=0.0s)')
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        
        # Add instructions
        plt.figtext(0.02, 0.02, 'Keys: Q - Quit, R - Randomize wind & add sources', fontsize=9)
        
        return self.temp_plot, self.quiver_plot
    
    def update_animation(self, frame):
        """Update animation with dynamic color range"""
        try:
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
                try:
                    self.quiver_plot.set_UVC(
                        wind_x[::self.quiver_density, ::self.quiver_density],
                        wind_y[::self.quiver_density, ::self.quiver_density]
                    )
                except Exception as e:
                    print(f"Error updating wind vectors: {e}")
            
            # Update title with statistics
            self.ax.set_title(f'Weather Simulation (t={self.time:.2f}s, step {self.steps})\n'
                             f'FPS: {1.0/max(0.001, compute_time):.1f}, Temp: {np.min(temp):.1f}°C to {np.max(temp):.1f}°C')
            
            return self.temp_plot, self.quiver_plot
            
        except Exception as e:
            print(f"Error in update_animation: {e}")
            return self.temp_plot, self.quiver_plot
    
    def on_key_press(self, event):
        """Handle key press events"""
        if event.key == 'q':
            plt.close(self.fig)
        elif event.key == 'r':
            try:
                # Randomize wind with safer parameters
                num_vortices = np.random.randint(3, 8)
                strength = np.random.uniform(1.5, 3.0)
                radius = np.random.uniform(self.width // 15, self.width // 8)
                
                # Use proper API: generate_gaussian_field instead of generate_uniform
                self.wind_field.generate_gaussian_field(num_vortices, strength, radius)
                
                # Add 1-2 random heat/cold sources
                for _ in range(np.random.randint(1, 3)):
                    x = np.random.randint(0, self.width)
                    y = np.random.randint(0, self.height)
                    strength = np.random.uniform(-10.0, 15.0)
                    radius = np.random.uniform(self.width // 20, self.width // 12)
                    self.temp_field.add_heat_source(x, y, strength, radius)
                
                print("Wind field and temperature sources randomized!")
            except Exception as e:
                print(f"Error randomizing conditions: {e}")
    
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
    print("Dynamic Weather Simulation (Fixed Version)")
    
    try:
        # Simulation parameters - slightly reduced for stability
        width = 180
        height = 180
        frames = 1000
        interval = 50  # ms
        
        # Initialize simulation
        simulation = DynamicWeatherSimulation(width, height)
        simulation.set_initial_conditions()
        
        # Run animation
        simulation.run_animation(num_frames=frames, interval=interval)
        
    except Exception as e:
        print(f"Error in main: {e}")
    
    print("Simulation ended")

if __name__ == "__main__":
    main()
