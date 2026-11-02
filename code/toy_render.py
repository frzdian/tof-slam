"""Toy version of the paper's rendering (Eq. 3 and Eq. 4), with no neural network.

The "map" here is a hand-written function: a wall 2 m in front of the camera,
red on the left and blue on the right. In the paper, the feature grids and
decoders play this role, and they are learned instead of hand-written.

Usage:
    python code/toy_render.py
"""
import numpy as np

WALL_Z = 2.0     # the wall is at z = 2 m
SHARPNESS = 50   # how sharp the surface looks to the renderer


def map_sdf(points):
    """Signed distance to the wall: positive in front of it, negative behind."""
    return WALL_Z - points[:, 2]


def map_color(points):
    """Color (R, G, B) of each point: red if x < 0, blue otherwise."""
    colors = np.zeros((len(points), 3))
    colors[points[:, 0] < 0] = [1.0, 0.0, 0.0]
    colors[points[:, 0] >= 0] = [0.0, 0.0, 1.0]
    return colors


def render_ray(origin, direction, n_samples=64, near=0.1, far=4.0):
    """Follow one ray through the map and return (rendered color, rendered depth)."""
    # Step 1: pick points along the ray: x_i = o + d_i * r
    d = np.linspace(near, far, n_samples)
    points = origin + d[:, None] * direction

    # Step 2: ask the map about every point
    sdf = map_sdf(points)
    colors = map_color(points)

    # Step 3: turn SDF into opacity alpha (the NeuS formula the paper follows).
    # alpha is large only where the SDF drops between two neighboring points,
    # which is what happens when the ray crosses a surface.
    phi = 1.0 / (1.0 + np.exp(-SHARPNESS * sdf))
    alpha = np.clip((phi[:-1] - phi[1:]) / (phi[:-1] + 1e-8), 0.0, 1.0)

    # Step 4: T_i = how much light is still left when it reaches point i.
    # T_1 = 1, T_2 = (1 - alpha_1), T_3 = (1 - alpha_1)(1 - alpha_2), ...
    T = np.cumprod(np.concatenate([[1.0], 1.0 - alpha[:-1]]))
    weight = T * alpha

    # Step 5: Eq. 3 sums colors and Eq. 4 sums distances, using the same weights
    rendered_color = np.sum(weight[:, None] * colors[:-1], axis=0)
    rendered_depth = np.sum(weight * d[:-1])
    return rendered_color, rendered_depth


def unit(vector):
    """Scale a direction so its length is 1."""
    vector = np.array(vector, dtype=float)
    return vector / np.linalg.norm(vector)


np.set_printoptions(precision=2, suppress=True)
camera = np.array([0.0, 0.0, 0.0])

print("A. Same camera, different rays")
for name, direction in [("left ray ", [-0.3, 0, 1]), ("right ray", [0.3, 0, 1])]:
    color, depth = render_ray(camera, unit(direction))
    print(f"   {name}: color={color}  depth={depth:.2f} m")

print("B. Same ray, camera moved forward")
for z in [0.0, 0.4]:
    color, depth = render_ray(np.array([0.0, 0.0, z]), unit([0.3, 0, 1]))
    print(f"   camera z={z}: depth={depth:.2f} m")

print("C. One ToF zone: rays over an area vs. one ray from the zone center")
xs = np.linspace(-0.3, 0.3, 7)
depths = [render_ray(camera, unit([x, 0, 1]))[1] for x in xs]
center_depth = render_ray(camera, unit([0, 0, 1]))[1]
print(f"   average of {len(xs)} rays: {np.mean(depths):.2f} m")
print(f"   zone center ray: {center_depth:.2f} m")
