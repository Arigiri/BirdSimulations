Swallows simulations

# Main features

## Birds

- Swallows: A birds, simulated by a triangle
- Swallows moves by boids

- Each birds have some colors. The more hungry, the less alpha be.

- Birds always head to some where have many foods.
- Birds can die after hungry for amount of time

Return information of: 
    - Position
    - Velocity
    - Life durations
    - Time left

Functions:
    - Separations: Tránh va chạm.
    - Alignment: Điều chỉnh bay hướng chung.
    - Cohension: Di chuyển về phía trung tâm đàn.
    - Food Seeking: Di chuyển đến nơi có nhiều đồ ăn.
    - Food Consuming: Tốc độ tiêu hóa đồ ăn (Sau khi ăn, một con chim có thể sống một khoảng thời gian)

## Mathematical Model of Boids

The boid algorithm simulates flocking behavior using three simple steering rules:

1. **Separation (Tách biệt)**: Avoid crowding neighbors
   - Formula: $\vec{S} = \sum_{i}^{N} \frac{\vec{p} - \vec{p_i}}{|\vec{p} - \vec{p_i}|^2}$
   - Where $\vec{p}$ is the position of the current bird, $\vec{p_i}$ is the position of neighbor bird i
   - The weight of separation increases as distance decreases (inverse square)

2. **Alignment (Căn chỉnh)**: Steer towards average heading of neighbors
   - Formula: $\vec{A} = \frac{\sum_{i}^{N} \vec{v_i}}{N}$
   - Where $\vec{v_i}$ is the velocity of neighbor bird i
   - This creates coordinated movement in the flock

3. **Cohesion (Gắn kết)**: Move toward center of mass of neighbors
   - Formula: $\vec{C} = \frac{\sum_{i}^{N} \vec{p_i}}{N} - \vec{p}$
   - Birds try to stay close to their flockmates

For each time step:
1. Calculate steering forces from all three rules
2. Apply weighted sum: $\vec{steer} = w_s\vec{S} + w_a\vec{A} + w_c\vec{C}$
3. Apply steering force to current velocity
4. Normalize resulting vector and scale to maintain constant speed: $\vec{v_{new}} = \hat{v} \cdot |v|$

This model creates complex emergent behavior from simple rules, allowing for realistic flocking simulation without explicitly programming group behavior.

## Fruits

Fruits: Food for birds. Changing annually

Fruits change by a function which can be changed and customize (Called fruits_function)
Fruits have colors that show the ripeness of foods.
Fruits will disappear after amount of times.

Return information of:
    - Positions
    - ripeness $\in [0, 2]$: if ripeness >= 1 \rightarrow ripe. If ripeness == 2 -> disappear. ripeness is a functions based on times and locations.
    - Life durations: Durations fruits appeared

- Functions:
    Based on weather and time to decide the ripeness.
    Fruits randomly appear based on weather in different locations.

## Locations

A function show how environment here is.

Return information of:
    - Weather $\in [0, 1]$: A foat number show how easily foods appear in location
    - Dangerous parameters $\in [0, 1]$: Show percentage how a bird can die here. This parameters changes by a function. 

## Times

A linear functions.

Return information of:
    - Time passed
    - Current season

# Projects structure

## Front-end

- Use python to visualize how boids moves, fruits grow, weather changes.
- Have buttons and slide bars to visualize affect of parameters of functions.
- Have buttons to create birds, in some position.
- Have buttons to show density of birds in periods of time by showing heatmap.

## Back-end

Have functions which simulate the changing flock of birds, fruits grows and changing of weather

### Steering Implementation

The steering behavior is implemented in `model/steering.py`:
- Each steering force (separation, alignment, cohesion) is calculated independently
- Forces are weighted and combined
- Bird movement maintains constant speed while changing direction based on steering
- Additional behaviors (food seeking) are integrated with core rules

# Notes

1. Functions in back-end return information of object to visualize in backend
(Example: position,...).
2. Fronts end use pyglet to visualize, backend use numpy, scipy, numba. (< 10.000 birds>)
3. The constant-speed constraint is essential to realistic bird motion, achieved by normalizing the velocity vector after applying steering forces.

