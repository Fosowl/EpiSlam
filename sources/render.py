"""
Rendu 3D
"""

import cv2 as cv
import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GLU import *
from OpenGL.GL import *
import math

class Camera:
    def __init__(self, fov=45, cam_distance_ = 100, position_=(0.0, 0.0, 0.0)) -> None:
        self.position = position_ 
        self._projection_matrix = None
        self._modelview_matrix = None
        self.orbital_radius = cam_distance_ # orbital_radius from the camera to the origin
        self.polar = np.deg2rad(np.deg2rad(0))
        self.azimuth = np.deg2rad(np.deg2rad(0))
        self.setup(fov_y=fov, aspect_ratio=1.0, near=10, far=50000.0)
        self.update()

    def set_origin(self, position=(0.0, 0.0, 0.0)):
        self.position = position

    def setup(self, fov_y=45, aspect_ratio=1.0, near=0.1, far=1000.0):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glFrustum(-aspect_ratio * math.tan(np.deg2rad(fov_y) / 2),
                  aspect_ratio * math.tan(np.deg2rad(fov_y) / 2),
                  -math.tan(np.deg2rad(fov_y) / 2),
                  math.tan(np.deg2rad(fov_y) / 2),
                  near,
                  far)
        self._projection_matrix = glGetFloatv(GL_PROJECTION_MATRIX)
        self._modelview_matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
        print("Projection matrix:")
        print(self._projection_matrix)

    @property
    def get_projection_matrix(self):
        return self._projection_matrix
    
    @property
    def get_modelview_matrix(self):
        return self._modelview_matrix
    
    @property
    def get_position(self):
        return self.position

    def rotate_azimuth(self, degree=0.0):
        radians = np.deg2rad(degree)
        self.azimuth += radians
        circle = 2.0 * math.pi
        self.azimuth = self.azimuth % circle
        if self.azimuth < 0:
            self.azimuth += circle

    def rotate_polar(self, degree=0.0):
        radians = np.deg2rad(degree)
        self.polar += radians
        polar_cap = math.pi / 2.0 - 0.01
        if self.polar > polar_cap:
            self.polar = polar_cap - 0.01
        elif self.polar < -polar_cap:
            self.polar = -polar_cap + 0.01
    
    def zoom(self, by=0.0):
        self.orbital_radius += by
        if self.orbital_radius < 10:
            self.orbital_radius = 10

    def update(self, rotation_center=(0, 0, 0)):
        x = self.orbital_radius * np.cos(self.polar) * np.cos(self.azimuth)
        y = self.orbital_radius * np.sin(self.polar)
        z = self.orbital_radius * np.cos(self.polar) * np.sin(self.azimuth)
        self.position = (x,
                         y,
                         z)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(*self.position, # from
                  rotation_center[0], rotation_center[1], rotation_center[2], # look at origin
                  0, 1, 0) # axis
    
class Renderer3D:
    def __init__(self, pov_=90.0, cam_distance=100) -> None:
        self.window = (800, 600)
        self.fov = pov_
        pygame.display.set_mode(self.window, DOUBLEBUF | OPENGL)
        self.camera = Camera(fov=self.fov, cam_distance_=cam_distance)
        self.pause = False
        self.saved_points = None

    def handle_inputs(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.MOUSEMOTION:
                mouse_dx, mouse_dy = pygame.mouse.get_rel()
                self.camera.rotate_azimuth(-mouse_dx*0.5)
                self.camera.rotate_polar(mouse_dy*0.5)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE] and event.type == pygame.KEYDOWN:
                self.pause = not self.pause
                print("Paused" if self.pause else "Unpaused")

    def draw_cube(self):
        vertices = [(-0.5, -0.5, -0.5), (0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5),
                    (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5), (-0.5, 0.5, 0.5)]
        edges = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]

        glBegin(GL_LINES)
        for edge in edges:
            for vertex in edge:
                glVertex3fv(vertices[vertex])
        glEnd()
    
    def draw_lines(self, start, end, color=(0.0, 1.0, 0.0)):
        glColor3f(*color)
        glBegin(GL_LINES)
        glVertex3f(*start)
        glVertex3f(*end)
        glEnd()

    def render_axis(self):
        self.draw_lines(start=(0, 0, 0), end=(10, 0, 0), color=(1.0, 0.0, 0.0))
        self.draw_lines(start=(0, 0, 0), end=(0, 10, 0), color=(0.0, 1.0, 0.0))
        self.draw_lines(start=(0, 0, 0), end=(0, 0, 10), color=(0.0, 0.0, 1.0))
    
    def render(self):
        pygame.display.flip()
        pygame.time.wait(10)

    def isRotationMatrix(self, R) :
        Rt = np.transpose(R)
        shouldBeIdentity = np.dot(Rt, R)
        I = np.identity(3, dtype = R.dtype)
        n = np.linalg.norm(I - shouldBeIdentity)
        return n < 1e-6
    
    def rotationMatrixToEulerAngles(self, R) :
        assert(self.isRotationMatrix(R))
        sy = math.sqrt(R[0,0] * R[0,0] +  R[1,0] * R[1,0])
        singular = sy < 1e-6
        if  not singular :
            x = math.atan2(R[2,1] , R[2,2])
            y = math.atan2(-R[2,0], sy)
            z = math.atan2(R[1,0], R[0,0])
        else :
            x = math.atan2(-R[1,2], R[1,1])
            y = math.atan2(-R[2,0], sy)
            z = 0
        return np.array([x, y, z])

    def draw_points(self, points, position, rotation, color=(0.0, 1.0, 0.0)):
        assert points is not None, "No points to draw"
        assert len(points) > 0, "No points to draw"
        """
        glPushMatrix()
        glTranslatef(position[0], position[1], position[2])
        # Extract rotation angles from R_total
        angles = self.rotationMatrixToEulerAngles(rotation)
        # Apply rotation
        glRotatef(np.rad2deg(angles[0]), 1, 0, 0)  # Rotate around x-axis
        glRotatef(np.rad2deg(angles[1]), 0, 1, 0)  # Rotate around y-axis
        glRotatef(np.rad2deg(angles[2]), 0, 0, 1) 
        glPopMatrix()
        """
        glBegin(GL_POINTS)
        for i, point in enumerate(points):
            color = (0.4, 0.8, 0)
            point_wrld = (point[0] + position[0],
                          point[1] + position[1],
                          point[2] + position[2])
            glColor3f(*color)
            glVertex3f(*point_wrld)
        glEnd()

    def draw_trajectory(self, camera_poses, color=(1.0, 0.0, 0.7)):
        T_total = np.zeros((3, 1))
        R_total = np.eye(3)
        glColor3f(*color)
        glBegin(GL_LINE_STRIP)
        for pose in camera_poses:
            T_total += R_total @ pose['t']
            R_total = R_total @ pose['R']
            glVertex3f(*T_total)
        glEnd()
        return T_total

    @property
    def is_paused(self):
        return self.pause

    def render3dSpace(self, points3Dcum, camera_poses=None):
        if points3Dcum is None:
            print("No points to render")
            return
        glClearColor(0, 0, 0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.render_axis()
        print(f"RENDER: {len(camera_poses)} camera poses")
        print(f"RENDER: Rendering {len(points3Dcum)} points groups")
        T_total = np.zeros((3, 1))
        R_total = np.eye(3)
        for i, points3D in enumerate(points3Dcum):
            T_total += R_total @ camera_poses[i]['t']
            R_total = R_total @ camera_poses[i]['R']
            self.draw_points(points3D, T_total, R_total)
        self.draw_trajectory(camera_poses)
        self.draw_cube()
        self.handle_inputs()
        self.camera.update()
