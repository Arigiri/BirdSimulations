# Weather Visualization Module

## Overview

The Visualization module provides tools for visualizing weather simulation data, including temperature fields and wind vectors. It offers both static and dynamic visualization capabilities.

## Components

### Dynamic Visualization (`dynamic_viz.py`)

Interactive, real-time visualization of weather simulations with:
- Temperature field colormaps
- Wind vector field overlays
- Animation controls for time progression

### Fixed Visualization (`dynamic_viz_fixed.py`)

Enhanced version of the dynamic visualization with fixed viewport and improved performance for:
- Consistent rendering across different display environments
- Optimized rendering for large datasets
- Stable animation performance

## Usage

```python
from model.weather.python.visualization import WeatherVisualizer
from model.weather.python.core import WeatherModelCpp

# Create and set up the weather model
model = WeatherModelCpp(width=200, height=200)
model.set_temperature_gradient(10.0, 30.0, "NORTH_SOUTH")
model.generate_wind_field("gaussian", num_vortices=5, strength=2.0, radius=10.0)

# Create visualizer
visualizer = WeatherVisualizer(model)

# Run visualization
visualizer.run_animation(num_frames=500, interval=50)
```

## Features

- Real-time visualization of temperature and wind fields
- Customizable color maps for temperature display
- Adjustable wind vector density and scaling
- Animation controls (play, pause, step)
- Recording capabilities for saving animations
- Interactive controls for adding heat sources during simulation
