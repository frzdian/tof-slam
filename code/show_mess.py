"""Open the ground-truth mesh of one sequence in a 3D window.

Usage:
    python code/show_mesh.py dataset/ZJUL5-SLAM/Kitchen/mesh.ply
"""
import sys

import open3d as o3d  # library for working with 3D data

if len(sys.argv) != 2:
    sys.exit("Usage: python code/show_mesh.py <path_to_mesh.ply>")

# Read the mesh file: points (vertices) and triangles
mesh = o3d.io.read_triangle_mesh(sys.argv[1])

# Stop here if the file could not be read as a mesh
if mesh.is_empty():
    sys.exit("Mesh is empty or could not be read")

print(f"Vertices : {len(mesh.vertices)}")
print(f"Triangles: {len(mesh.triangles)}")

# Compute surface directions so that light and shadow look right
mesh.compute_vertex_normals()

# Open the 3D window
o3d.visualization.draw_geometries([mesh], window_name="Ground Truth Mesh")