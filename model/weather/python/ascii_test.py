"""
Simple ASCII test script for the C++ weather model
"""

import os
import sys
import time
import numpy as np

print("Testing the C++ weather module...")
print("Current directory:", os.getcwd())
print("Python version:", sys.version)

# Check if module exists
module_path = os.path.join(os.getcwd(), "cpp_weather.cp310-win_amd64.pyd")
if os.path.exists(module_path):
    print(f"Module found at: {module_path}")
else:
    print(f"Module NOT found at: {module_path}")
    print("Available files in directory:")
    for file in os.listdir(os.getcwd()):
        print(f"  - {file}")

# Try importing the module
try:
    print("\nAttempting to import the C++ weather module...")
    sys.path.append(os.path.dirname(os.getcwd()))  # Add parent directory to path
    from model.weather.python.cpp_weather_interface import WeatherModelCpp
    print("Module imported successfully!")
    
    # Create model
    width, height = 100, 100
    print(f"Creating weather model with size {width}x{height}...")
    model = WeatherModelCpp(width, height)
    print("Model created successfully!")
    
    # Set temperature gradient
    print("Setting temperature gradient...")
    model.set_temperature_gradient(10.0, 30.0, "NORTH_SOUTH")
    
    # Add heat sources
    print("Adding heat sources...")
    model.add_heat_source(width//4, height//4, 10.0, 15.0)
    model.add_heat_source(3*width//4, 3*height//4, 15.0, 20.0)
    
    # Generate wind field
    print("Generating Gaussian wind field...")
    model.generate_wind_field("gaussian", num_vortices=8, strength=3.0, radius=25.0)
    
    # Run simulation
    num_steps = 5
    print(f"Running {num_steps} simulation steps...")
    start_time = time.time()
    
    for i in range(num_steps):
        dt = model.step_simulation()
        print(f"Step {i+1}/{num_steps}, dt = {dt:.6f}")
    
    elapsed = time.time() - start_time
    print(f"Simulation completed in {elapsed:.3f} seconds ({num_steps/elapsed:.2f} steps/second)")
    
    # Get data
    temp = model.get_temperature()
    wind_x, wind_y = model.get_wind_field()
    
    print(f"Temperature field shape: {temp.shape}")
    print(f"Wind field shape: {wind_x.shape}, {wind_y.shape}")
    
    # Print some stats
    print(f"Temperature min: {np.min(temp):.2f}, max: {np.max(temp):.2f}, mean: {np.mean(temp):.2f}")
    print(f"Wind X min: {np.min(wind_x):.2f}, max: {np.max(wind_x):.2f}, mean: {np.mean(wind_x):.2f}")
    print(f"Wind Y min: {np.min(wind_y):.2f}, max: {np.max(wind_y):.2f}, mean: {np.mean(wind_y):.2f}")
    
    print("\nTest completed successfully!")
    
except ImportError as e:
    print(f"Import error: {e}")
    print("This could be due to:")
    print("1. Module not being in the Python path")
    print("2. Missing dependencies")
    print("3. Incompatible Python version (using Python 3.10)")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
