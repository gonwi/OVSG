"""Tools that preprocess the data."""
import open3d as o3d
import os
import numpy as np


def estimate_floor(pcd):
    """Estimate the floor plane of the scene using RANSAC."""
    origin = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.5)

    # Segment the largest plane using RANSAC
    plane_model, inliers = pcd.segment_plane(distance_threshold=0.01,
                                             ransac_n=3,
                                             num_iterations=1000)
    [a, b, c, d] = plane_model
    print(f"Plane equation: {a:.2f}x + {b:.2f}y + {c:.2f}z + {d:.2f} = 0")

    # Create a point cloud for inliers (points that belong to the plane)
    inlier_cloud = pcd.select_by_index(inliers)
    inlier_cloud.paint_uniform_color([1.0, 0, 0])  # Paint the inliers in red

    # Create a point cloud for outliers (points that don"t belong to the plane)
    outlier_cloud = pcd.select_by_index(inliers, invert=True)
    # Compute the centroid of the inlier points
    centroid = np.mean(np.asarray(inlier_cloud.points), axis=0)

    # Visualize inliers and outliers
    # o3d.visualization.draw_geometries([outlier_cloud, origin, inlier_cloud])

    # Compute the normal of the plane
    # The plane equation is ax + by + cz + d = 0
    # So, the normal of the plane is the vector [a, b, c]
    normal = np.array(plane_model[:3])
    # Make sure the normal is pointing downwards. If not, reverse it
    if normal[2] > 0:
        normal *= -1

    # Compute the rotation matrix using the plane normal
    z_axis = normal
    x_axis = np.array([1, 0, 0]) if np.allclose(normal, [0, 1, 0]) else np.cross([0, 1, 0], z_axis)
    x_axis = x_axis / np.linalg.norm(x_axis)
    y_axis = np.cross(z_axis, x_axis)
    rotation_matrix = np.column_stack([x_axis, y_axis, z_axis])

    # Transform the point cloud
    # pcd.translate(-centroid)
    # pcd.rotate(np.linalg.inv(rotation_matrix), center=(0, 0, 0))

    transform_t = np.eye(4, dtype=np.float32)
    transform_t[:3, 3] = -centroid
    transform_r = np.eye(4, dtype=np.float32)
    transform_r[:3, :3] = np.linalg.inv(rotation_matrix)
    transform = np.matmul(transform_r, transform_t)
    pcd.transform(transform)

    # Visualize the transformed point cloud and origin
    # o3d.visualization.draw_geometries([pcd, origin])
    return transform, pcd


def convert_ply2pcd(ply_path, pcd_path):
    """Convert .ply to .pcd."""
    pcd = o3d.io.read_point_cloud(ply_path)
    o3d.io.write_point_cloud(pcd_path, pcd)
    return pcd


if __name__ == "__main__":
    root_dir = os.path.join(os.path.dirname(__file__), "..")
    scene_name = "scene0645_00"  # "scene0645_00", "cus_scene0001_00"
    demo_ply_file = os.path.join(root_dir, "test_data", scene_name, f"{scene_name}_vh_clean_2.ply")
    demo_pcd_file = os.path.join(root_dir, "test_data", scene_name, "scan-00.pcd")  # fit with OVIR-3D format
    # convert_ply2pcd(demo_ply_file, demo_pcd_file)

    # load pcd
    pcd = o3d.io.read_point_cloud(demo_ply_file)

    obb = pcd.get_minimal_oriented_bounding_box()
    obb.color = (1, 0, 0)

    # extract transform from obb
    obb_tf = obb.get_rotation_matrix_from_xyz((0, 0, 0))
    
    aligned_tf = np.eye(4, dtype=np.float32)

    vis_list = [pcd, obb]
    origin = o3d.geometry.TriangleMesh.create_coordinate_frame(size=1.0)
    vis_list.append(origin)
    o3d.visualization.draw_geometries(vis_list)