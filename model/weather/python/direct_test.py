"""
Test importing the C++ module directly
"""

import os
import sys
import numpy as np

def main():
    # Add the current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    print(f"Python path: {sys.path}")
    print(f"Current directory: {current_dir}")
    
    # List files in current directory
    print("\nFiles in current directory:")
    for file in os.listdir(current_dir):
        print(f"  - {file}")
    
    # Try to import the C++ module directly
    try:
        print("\nTrying to import cpp_weather module directly...")
        import cpp_weather
        print("Module imported successfully!")
        print(f"Module contents: {dir(cpp_weather)}")
        
        # Test creating objects
        print("\nTesting object creation...")
        solver = cpp_weather.Solver(100, 100, 1.0, 0.1)
        print("Solver created successfully!")
        
        wind_field = cpp_weather.WindField(100, 100)
        print("WindField created successfully!")
        
        temp_field = cpp_weather.TemperatureField(100, 100)
        print("TemperatureField created successfully!")
        
        # Test basic functionality
        print("\nTesting basic functionality...")
        temp_field.set_uniform(20.0)
        print("Set uniform temperature successfully!")
        
        wind_field.generate_gaussian_field(5, 2.0, 10.0)
        print("Generated Gaussian wind field successfully!")
        
        # Get data
        temp_data = temp_field.get_temperature()
        print(f"Temperature data shape: {temp_data.shape}, type: {type(temp_data)}")
        
        wind_x = wind_field.get_wind_x()
        wind_y = wind_field.get_wind_y()
        print(f"Wind X data shape: {wind_x.shape}, type: {type(wind_x)}")
        print(f"Wind Y data shape: {wind_y.shape}, type: {type(wind_y)}")
        
        # Calculate time step
        dt = solver.compute_cfl_time_step(wind_x, wind_y)
        print(f"Calculated CFL time step: {dt}")
        
        # Run a simulation step
        new_temp = solver.solve_rk4_step(temp_data, wind_x, wind_y, dt)
        print(f"Simulation step completed, new temperature shape: {new_temp.shape}")
        
        print("\nAll tests passed successfully!")
        
    except ImportError as e:
        print(f"Import error: {e}")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
