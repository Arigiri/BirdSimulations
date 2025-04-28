# Weather Core Module

## Overview

The Core module provides the essential functionality for the weather simulation system. It serves as the main interface between Python and the underlying C++ implementation, offering high-performance simulation capabilities.

## Components

### C++ Weather Interface (`cpp_weather_interface.py`)

The main interface to the C++ backend, providing classes for:
- Temperature field manipulation
- Wind field generation
- Advection-diffusion simulation

### Binary Components

- `cpp_weather.*.pyd`: Compiled C++ extension
- Supporting DLLs: Required for the C++ module to operate

## Usage

```python
from model.weather.python.core import WeatherModelCpp

# Create a model
model = WeatherModelCpp(width=100, height=100)

# Configure temperature
model.set_temperature_gradient(10.0, 30.0, "NORTH_SOUTH")

# Set up wind field
model.generate_wind_field("gaussian", num_vortices=5, strength=2.0, radius=10.0)

# Run simulation
for _ in range(100):
    model.step_simulation()

# Get results
temperature = model.get_temperature()
wind_x, wind_y = model.get_wind_field()
```

## Features

- Temperature field manipulation (uniform, gradients, heat sources)
- Wind field generation (Gaussian, Perlin noise, vortex)
- Physical simulation with diffusion and advection
- Automatic time step calculation based on CFL condition
- Direct access to NumPy arrays for integration with other Python tools
