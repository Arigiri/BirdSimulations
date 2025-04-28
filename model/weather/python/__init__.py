"""
Weather Module for BirdSimulations

This package provides weather simulation capabilities including temperature diffusion,
wind field generation, and visualization tools.

The module is organized into the following subpackages:
- core: Essential functionality and C++ interface
- visualization: Visualization tools for temperature and wind fields
- performance: Performance-optimized implementations
- utils: Build and utility tools
"""

# Import main classes for backwards compatibility
from model.weather.python.core.cpp_weather_interface import WeatherModelCpp
from model.weather.python.visualization.realtime_simulation import RealtimeWeatherSimulation

# Make key classes available at the top level
__all__ = ['WeatherModelCpp', 'RealtimeWeatherSimulation']
