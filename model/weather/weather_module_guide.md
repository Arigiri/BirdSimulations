# Weather Module Guide

## Overview

The weather module provides a high-performance weather simulation system that models temperature diffusion and wind field dynamics. The module uses C++ backend for calculations with a Python interface for easy integration into the BirdSimulations project.

## Core Components

The weather module consists of three main components:

1. **C++ Backend**: Provides fast numerical solvers for weather simulation
2. **Python Interface**: Wrapper around the C++ functionality for easy use
3. **Visualization Tools**: Real-time visualization of temperature and wind fields

## Installation

Before using the module, ensure the C++ part is compiled:

```bash
python -m model.weather.python.build_cpp_module
```

## Python API Reference

### Weather Model Interface (`cpp_weather_interface.py`)

The main interface class `WeatherModelCpp` provides methods to set up and run weather simulations.

#### Class: `WeatherModelCpp`

```python
from model.weather.python.cpp_weather_interface import WeatherModelCpp

# Initialize the model
model = WeatherModelCpp(width=100, height=100, dx=1.0, kappa=0.1)
```

**Parameters**:
- `width` (int): Width of the simulation grid
- `height` (int): Height of the simulation grid
- `dx` (float, optional): Grid spacing (default: 1.0)
- `kappa` (float, optional): Heat diffusion coefficient (default: 0.1)

**Methods**:

##### `set_uniform_temperature(temp_value)`
Sets a uniform temperature across the entire grid.

```python
model.set_uniform_temperature(20.0)  # Set temperature to 20°C
```

##### `set_temperature_gradient(min_temp, max_temp, direction="NORTH_SOUTH")`
Creates a temperature gradient in the specified direction.

```python
# Create gradient from 10°C to 30°C (north to south)
model.set_temperature_gradient(10.0, 30.0, "NORTH_SOUTH")
```

**Direction options**: "NORTH_SOUTH", "SOUTH_NORTH", "EAST_WEST", "WEST_EAST", "RADIAL_IN", "RADIAL_OUT"

##### `set_custom_temperature_gradient(min_temp, max_temp, angle_degrees)`
Creates a temperature gradient at a custom angle.

```python
# Create gradient at 45 degrees
model.set_custom_temperature_gradient(10.0, 30.0, 45.0)
```

##### `add_heat_source(x, y, strength, radius)`
Adds a heat source at the specified position.

```python
# Add heat source at position (50, 50) with strength 10 and radius 5
model.add_heat_source(50, 50, 10.0, 5.0)
```

##### `generate_wind_field(method, **kwargs)`
Generates a wind field using different methods.

```python
# Generate Gaussian wind field
model.generate_wind_field("gaussian", num_vortices=5, strength=2.0, radius=10.0)

# Generate Perlin noise wind field
model.generate_wind_field("perlin", scale=10.0, octaves=4, persistence=0.5)

# Generate vortex wind field
centers = [(50, 50), (30, 70)]
strengths = [2.0, -1.5]
radiuses = [10.0, 15.0]
model.generate_wind_field("vortex", centers=centers, strengths=strengths, radiuses=radiuses)
```

##### `step_simulation(dt=None)`
Advances the simulation by one time step.

```python
# Auto time step (based on CFL condition)
dt = model.step_simulation()

# Fixed time step
dt = model.step_simulation(dt=0.1)
```

##### `get_temperature()`
Returns the current temperature field as a 2D NumPy array.

```python
temperature = model.get_temperature()  # Shape: (height, width)
```

##### `get_wind_field()`
Returns the current wind field as two 2D NumPy arrays.

```python
wind_x, wind_y = model.get_wind_field()  # Shape: (height, width)
```

##### `set_temperature_data(temperature_array)`
Sets the temperature field directly from a 2D NumPy array.

```python
# Assuming temp_data is a numpy array of shape (height, width)
model.set_temperature_data(temp_data)
```

### Real-time Simulation (`realtime_simulation.py`)

The `RealtimeWeatherSimulation` class provides a ready-to-use simulation with real-time visualization.

#### Class: `RealtimeWeatherSimulation`

```python
from model.weather.python.realtime_simulation import RealtimeWeatherSimulation

# Initialize the simulation
sim = RealtimeWeatherSimulation(width=200, height=200)

# Set up initial conditions
sim.set_initial_conditions()

# Run the animation
sim.run_animation(num_frames=1000, interval=50)
```

**Methods**:

##### `set_initial_conditions()`
Sets up a realistic initial state with temperature gradients and heat sources.

##### `step()`
Advances the simulation by one time step.

##### `get_temperature()`
Returns the current temperature field.

##### `get_wind_field()`
Returns the current wind field components.

##### `run_animation(num_frames=1000, interval=50)`
Runs the animation for the specified number of frames.
- `num_frames` (int): Number of frames to simulate
- `interval` (int): Time between frames in milliseconds

## Example Usage

### Basic Simulation

```python
from model.weather.python.cpp_weather_interface import WeatherModelCpp
import numpy as np
import matplotlib.pyplot as plt

# Create the model
model = WeatherModelCpp(width=100, height=100)

# Set up initial conditions
model.set_temperature_gradient(10.0, 30.0, "NORTH_SOUTH")
model.add_heat_source(50, 50, 15.0, 10.0)
model.generate_wind_field("gaussian", num_vortices=3, strength=2.0, radius=15.0)

# Run simulation for 100 steps
for _ in range(100):
    model.step_simulation()

# Get results
temp = model.get_temperature()
wind_x, wind_y = model.get_wind_field()

# Visualize results
plt.figure(figsize=(10, 5))

plt.subplot(1, 2, 1)
plt.imshow(temp, origin='lower', cmap='hot')
plt.colorbar(label='Temperature (°C)')
plt.title('Temperature Field')

plt.subplot(1, 2, 2)
y, x = np.mgrid[0:100:5, 0:100:5]
plt.quiver(x, y, wind_x[::5, ::5], wind_y[::5, ::5], color='blue')
plt.title('Wind Field')

plt.tight_layout()
plt.show()
```

### Interactive Simulation

```python
from model.weather.python.realtime_simulation import RealtimeWeatherSimulation

# Create and run the simulation
sim = RealtimeWeatherSimulation(width=200, height=200)
sim.set_initial_conditions()
sim.run_animation(num_frames=1000, interval=50)
```

## Integration with Bird Simulations

The weather module can provide realistic environmental conditions for bird simulations. Birds can be affected by:

1. Temperature gradients affecting flight paths
2. Wind fields influencing energy expenditure and movement
3. Thermals created by heat sources to enable soaring behavior

To integrate with bird behavior models, use the weather model to obtain temperature and wind data at bird positions, then factor these into the bird movement algorithms.
