# Heat Simulation Model - Documentation

## 1. User Interface (UI)

- **Heatmap Display**:
  - Represents temperature field as a 2D color map.
  - Grid points are spaced every `k` units apart.
  - Colors:
    - Green: low temperature.
    - Yellow: medium temperature.
    - Red: high temperature.

- **Colorbar**:
  - Shown at the left side of the heatmap.
  - Maps temperature values to colors.

- **Control Panel**:
  - Options to:
    - Adjust grid spacing `k`.
    - Start / Stop the simulation.
    - Reset the model.
    - Change thermal diffusivity coefficient `κ`.

- **Status Information**:
  - Display current simulation time `t`.
  - Display total heat energy in the domain.

---

## 2. Mathematical Foundation

The model is based on the 2D **Advection-Diffusion Equation**:

\[
\frac{\partial T}{\partial t} + \vec{v} \cdot \nabla T = \kappa \nabla^2 T
\]

Where:
- \( T(x, y, t) \): Temperature at location \((x, y)\) and time \(t\).
- \( \vec{v}(x,y,t) = (v_x(x,y,t), v_y(x,y,t)) \): Wind velocity vector generated randomly at each grid point.
- \( \kappa \): Thermal diffusivity coefficient.

**Wind Model**:
- At every timestep, a new random wind vector \((v_x, v_y)\) is generated at each grid point.
- Two possible methods:
  - Gaussian random noise.
  - Perlin noise (for smoother fields).

**Numerical Method**:
- Finite Difference Method (FDM) is used to discretize the equation.
- Update rule at each grid point:

\[
T(x,y,t+\Delta t) = T(x,y,t) + \Delta t \times \left( -\vec{v}\cdot\nabla T + \kappa \nabla^2 T \right)
\]

---

## 3. Simulation Logic

- **Initialization**:
  - Set up 2D domain with size determined by `config`.
  - Initial temperatures assigned based on a starting field (e.g., fixed or random).
  - Grid points separated by distance `k`.

- **Timestep Loop**:
  1. At each grid point, generate a random wind vector.
  2. Compute:
     - Advection term: \( \vec{v}\cdot\nabla T \)
     - Diffusion term: \( \nabla^2 T \)
  3. Update temperature using explicit Euler method.
  4. Update the heatmap visualization accordingly.

- **Termination**:
  - Simulation stops either manually or when a maximum time limit \( t_{\text{max}} \) is reached.

---

## 4. Module Architecture

/heat_simulation ├── main.py # Entry point: UI management and main loop ├── config.py # Simulation settings (k, κ, domain size, etc.) ├── ui.py # Heatmap and controls ├── model.py # Manage temperature and wind fields ├── wind_generator.py # Random wind generation ├── solver.py # Discretization and temperature update logic ├── visualization.py # Heatmap drawing functions ├── utils.py # Helper functions (e.g., normalization) └── assets/ └── colormaps/ # Custom colormap files


**Descriptions**:
- `main.py`: Connects UI, solver, and model logic.
- `model.py`: Stores and updates temperature and wind data.
- `solver.py`: Calculates the next timestep based on FDM.
- `wind_generator.py`: Produces random wind vectors based on chosen noise model.

---

## 5. Notes and Extensions

- **Wind Smoothness**:
  - Replace simple random noise with Perlin noise to simulate realistic wind fields.

- **Performance**:
  - Use NumPy arrays heavily for efficient computation.
  - Consider using Numba `@njit` to accelerate solver if necessary.

- **Boundary Conditions**:
  - Periodic (wrap around).
  - Dirichlet (fixed temperatures at borders).
  - Neumann (no heat flux across boundaries).

---

## 6. Example Configuration (config.py)

```python
GRID_SIZE_X = 100  # number of grid points along x
GRID_SIZE_Y = 100  # number of grid points along y
GRID_SPACING_K = 10  # spacing between grid points (units)
THERMAL_DIFFUSIVITY = 0.01  # κ value
DELTA_T = 0.1  # time step size
T_MAX = 100  # maximum simulation time
WIND_NOISE_TYPE = "gaussian"  # or "perlin"

7. Pseudocode for functions
def compute_gradient_x(T, x, y, k):
    """
    Approximate the partial derivative dT/dx at point (x, y)
    """
    return (T[x + k, y] - T[x - k, y]) / (2 * k)

def compute_gradient_y(T, x, y, k):
    """
    Approximate the partial derivative dT/dy at point (x, y)
    """
    return (T[x, y + k] - T[x, y - k]) / (2 * k)

def compute_laplacian(T, x, y, k):
    """
    Approximate the Laplacian of T at point (x, y)
    """
    laplacian_x = (T[x + k, y] - 2 * T[x, y] + T[x - k, y]) / (k * k)
    laplacian_y = (T[x, y + k] - 2 * T[x, y] + T[x, y - k]) / (k * k)
    return laplacian_x + laplacian_y

def update_temperature(T, v_x, v_y, x, y, dt, k, κ):
    """
    Compute the updated temperature at (x, y) based on advection and diffusion
    """
    grad_x = compute_gradient_x(T, x, y, k)
    grad_y = compute_gradient_y(T, x, y, k)
    lap = compute_laplacian(T, x, y, k)

    advection_term = v_x * grad_x + v_y * grad_y
    diffusion_term = κ * lap

    T_new = T[x, y] + dt * (-advection_term + diffusion_term)
    return T_new
