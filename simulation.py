"""
Simple 2D robot simulator in Python+Pygame

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""


import os, pygame
from pygame.locals import *
import math
import random
import time

fps                 = 20        #at most  this many frames per second
display_cols        = 1200
display_rows        = 700
wall_thickness      = 5         #thickness in pixels
wall_color          = 'black'
target_color        = 'green'
trace_color         = 'blue'
trace_decrease      = -17       #negative, subtracts from robot size to make a smaller trace
color_of_nothing    = 'white'

r_init_azi       = 0        #azimuth, in degrees (up is 0)
r_init_x_topleft = 10       #must be >= wall_thickness
r_init_y_topleft = display_rows-60
r_step_tele      = 10       #steps for teleop, equal in x or y (in pixels)
r_step_theta     = 7.5      #step for teleop, in azimuth
r_init_fwd_speed = 5        #pixels per simulation cycle
r_init_spin_speed= 3        #degrees per simulation cycle
r_transparency   = 75       #0 is totally transp., 255 totally opaque
r_visual_range   = 200      #measured from robot center
r_visual_angle   = 15       #in degrees, must divide 90 exactly!
r_visual_granularity = 5    #must be < wall_thickness for walls to be detected correctly!


main_dir = os.path.split(os.path.abspath(__file__))[0]
screen = pygame.display.set_mode((display_cols, display_rows))
list_obstacles = []
list_rect_obstacles = []

class Trace():
    def __init__(self, from_rect):
        self.rect       = from_rect

class Obstacle(pygame.Rect):
    def __init__(self, x_topleft, y_topleft, width, height, color):
        self.x_topleft  = x_topleft
        self.y_topleft  = y_topleft
        self.width      = width
        self.height     = height
        self.color      = pygame.Color(color)

class Robot(pygame.sprite.Sprite):
    def __init__(self, image, x_topleft, y_topleft, azimuth, fwd_speed, spin_speed,\
                 visual_range, visual_angle):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        #Sprites must have an image and a rectangle
        self.image          = image
        self.image_original = self.image    #unchanging copy, for rotations
        self.rect           = image.get_rect()
        self.rect_original  = self.rect     #unchanging copy, for rotations
        self.rect.topleft   = x_topleft, y_topleft  #for now used only for initial position
        self.fwd_speed      = fwd_speed
        self.spin_speed     = spin_speed
        self.leave_trace    = 1
        self.start_time     = 0
        self.end_time       = 0
        self.list_traces    = []
        self.azi            = azimuth       #in degrees
        self.collided       = False
        self.opmode         = 0             
        self.spin_angle_left= 0             #relative angle left to spin
        #these are the parameters of the range-sensing system
        self.visual_range   = visual_range
        self.visual_angle   = visual_angle
        self.nr_sensors     = 2*90/self.visual_angle+1
        self.retina         = list([self.visual_range, pygame.Color(color_of_nothing)]\
                                   for i in range(int(self.nr_sensors)))

    def printRetina(self):
        distances = []
        for s in self.retina:
            distances.append(s[0])
        return distances

    def update(self):
        self.sense() 

    def move_fwd(self):
        self.sense()
        if self.collided:       #collision in prev. cycle --> start SPIN
                self.collided = False
        temp_unghi = self.azi*math.pi/180
        walk_dx = -self.fwd_speed*math.sin(temp_unghi)
        walk_dy = -self.fwd_speed*math.cos(temp_unghi)
        self.move(walk_dx, walk_dy)

    def move(self,dx,dy):
        previous_rect = self.rect           #remember in case undo is necessary
        self.rect = self.rect.move(dx,dy)
        if self.rect.collidelist(list_rect_obstacles) != -1:#if collision exists
            self.rect = previous_rect                   #undo the move
            self.collided = True
        else:                   #if there was no collision
            if self.leave_trace:     #update trace list
                tr = self.rect.inflate(trace_decrease, trace_decrease)
                self.list_traces.append(Trace(tr))


    def spin(self,dtheta):
        self.sense()
        if self.collided:       #collision in prev. cycle --> start SPIN
                self.collided = False
        center = self.rect.center
        self.azi += dtheta
        if self.azi >= 360:         #keep theta between -360..360
            self.azi = self.azi-360
        if self.azi <= -360: 
            self.azi = self.azi+360
        original_rect = self.image_original.get_rect()
        rotated_image = pygame.transform.rotate(self.image_original, self.azi)
        rotated_rect  = original_rect.copy()
        rotated_rect.center = rotated_image.get_rect().center
        self.image = rotated_image.subsurface(rotated_rect).copy()
        self.image = change_alpha_for_alpha(self.image, r_transparency)
        if self.leave_trace:     #update trace lis
            tr = self.rect.inflate(trace_decrease, trace_decrease)
            self.list_traces.append(Trace(tr))
    
    #this function's job is to place in self.retina the range sensed by each sensor
    def sense(self):
        n = int((self.nr_sensors - 1)/2)#the "natural" sensor range is -n to +n
        granu = r_visual_granularity    #must be at least as large as the wall thickness!!
        for i in range(-n,n+1):         #sense with each of the 2n+1 range sensors
            ang = (self.azi - i*self.visual_angle)*math.pi/180
            for distance in range(granu, self.visual_range+granu, granu):
                x = self.rect.center[0]-distance*math.sin(ang)  #endpoint coordinates
                y = self.rect.center[1]-distance*math.cos(ang)
                nr_collisions = 0
                count = -1          #needed to coordinate the two lists, to extract color after loop
                for ob in list_rect_obstacles:  #use the stripped-down list of rectangles for speed
                    count = count + 1
                    if ob.collidepoint(x,y):
                        nr_collisions = 1
                        break       #breaks out of wall loop
                if nr_collisions:   #non-zero collision
                    break           #breaks out of distance loop
            #distance now has the min. between the visual range and the first collision
            self.retina[i+n][0] = distance
            if nr_collisions:       #nr_collisions is 1 if a collision has occurred
                self.retina[i+n][1] = list_obstacles[count].color #color comes form the larger list
            else:
                self.retina[i+n][1] = pygame.Color(color_of_nothing)
        return self.printRetina()

          
    def draw_rays(self, target_surf):
        n = int((self.nr_sensors - 1)/2 )#the "natural" sensor range -n to +n
        for i in range(-n,n+1):     #draw the 2n+1 rays of the range sensors
            ang = (self.azi - i*self.visual_angle)*math.pi/180
            x = self.rect.center[0]-self.retina[i+n][0]*math.sin(ang)
            y = self.rect.center[1]-self.retina[i+n][0]*math.cos(ang)
            #use aaline for smoother (but slower) lines
            pygame.draw.line(target_surf, (0,0,0), self.rect.center, (x,y))


    def get_traces(self):
        list_final=[]
        for t in self.list_traces:
            list_final.append((t.rect.center[0],t.rect.center[1]))
        return list_final

    def get_pos(self):
        return tuple(self.rect.center)

    def get_angle(self):
        return self.azi

    def get_collision(self):
        return self.collided

    def read_sensors(self):
        return self.printRetina()


    def target(self):
        if self.rect.center[0]>= 1120 and self.rect.center[1] <= 68:
                self.end_time = time.time()
                return True
        return False

    def get_time(self):
        return self.end_time-self.start_time

    
########end of Robot class########


def change_alpha_for_white(surface,new_alpha):
    size = surface.get_size()
    if size[0]>300 or size[1]>300:
        return surface
    for y in range(size[1]):
        for x in range(size[0]):
            r,g,b,a = surface.get_at((x,y))
            if r==255 and g==255 and b==255:
                surface.set_at((x,y),(r,g,b,new_alpha))
    return surface

def change_alpha_for_alpha(surface,new_alpha):
    size = surface.get_size()
    for y in range(size[1]):
        for x in range(size[0]):
            r,g,b,a = surface.get_at((x,y))
            if a<200:
                surface.set_at((x,y),(r,g,b,new_alpha))
    return surface

def draw_traces(robot,target_surf):
    for t in robot.list_traces:
        pygame.draw.circle(target_surf, pygame.Color(trace_color), t.rect.center, 2, 0) 
    return robot.target()

def load_image(name):
    path = os.path.join(main_dir, name)
    temp_image = pygame.image.load(path).convert_alpha()  #need this if using ppalpha
    return change_alpha_for_white(temp_image, r_transparency)  


def init_simulation(obstacles=10,ambiente=0):
    pygame.init()  
    pygame.display.set_caption('Pyweekend - 1er Hackathon ESPOL 2018')
    pygame.display.set_icon(pygame.image.load('ESPOL.png'))
    r_sprite = load_image('robo1.bmp')

    r=Robot(r_sprite, r_init_x_topleft, r_init_y_topleft,r_init_azi, r_init_fwd_speed,r_init_spin_speed, r_visual_range, r_visual_angle)

    w01 = Obstacle(0,0,display_cols,wall_thickness, wall_color)                          #top wall
    list_obstacles.append(w01)
    w02 = Obstacle(display_cols-wall_thickness,0,wall_thickness,display_rows,wall_color) #right wall
    list_obstacles.append(w02)
    w03 = Obstacle(0,display_rows-wall_thickness,display_cols,wall_thickness,wall_color) #bottom wall
    list_obstacles.append(w03)
    w04 = Obstacle(0,0,wall_thickness,display_rows, wall_color)                          #left wall
    list_obstacles.append(w04)

    if ambiente == 1:
        ambiente1(list_obstacles)
    elif ambiente == 2:
        ambiente2(list_obstacles)
    else:
        for i in range(int(obstacles/2)):
            col=random.randint(0,display_cols-30)
            row=random.randint(0,display_rows-120)
            obs = Obstacle(col,row,30,120,wall_color)
            list_obstacles.append(obs)
    
            col=random.randint(0,display_cols-120)
            row=random.randint(0,display_rows-30)
            obs = Obstacle(col,row,120,30,wall_color)
            list_obstacles.append(obs)


    target = Obstacle(1150,20,20,20,target_color)
    list_obstacles.append(target)
    for ob in list_obstacles:
        list_rect_obstacles.append(pygame.Rect(ob.x_topleft,ob.y_topleft,ob.width,ob.height))
    r.start_time = time.time()
    return r

def display_obstacles():
    for i in range(len(list_obstacles)):
        s = pygame.display.get_surface()
        s.fill(list_obstacles[i].color, list_rect_obstacles[i])


def ambiente1(list_obstacles):
        obs = Obstacle(display_cols/2,display_rows-200,10,200,wall_color)
        list_obstacles.append(obs)
        obs = Obstacle(display_cols/2,display_rows-200,80,10,wall_color)
        list_obstacles.append(obs)
        obs = Obstacle(200,200,200,10,wall_color)
        list_obstacles.append(obs)
        obs = Obstacle(200,200,10,200,wall_color)
        list_obstacles.append(obs)
        obs = Obstacle(800,150,10,200,wall_color)
        list_obstacles.append(obs)
        obs = Obstacle(1000,0,10,200,wall_color)
        list_obstacles.append(obs)



def ambiente2(list_obstacles):
        obs = Obstacle(display_cols/2,display_rows-200,10,200,wall_color)
        list_obstacles.append(obs)
        obs = Obstacle(100,400,200,10,wall_color)
        list_obstacles.append(obs)
        obs = Obstacle(300,400,10,200,wall_color)
        list_obstacles.append(obs)
        obs = Obstacle(0,200,200,10,wall_color)
        list_obstacles.append(obs)
        obs = Obstacle(400,0,10,100,wall_color)
        list_obstacles.append(obs)
        obs = Obstacle(400,100,100,10,wall_color)
        list_obstacles.append(obs)
        obs = Obstacle(500,250,10,100,wall_color)
        list_obstacles.append(obs)
        obs = Obstacle(750,250,10,200,wall_color)
        list_obstacles.append(obs)
        obs = Obstacle(500,350,250,10,wall_color)
        list_obstacles.append(obs)
        obs = Obstacle(display_cols-150,500,150,10,wall_color)
        list_obstacles.append(obs)
        obs = Obstacle(900,150,100,200,wall_color)
        list_obstacles.append(obs)
        obs = Obstacle(750,250,10,200,wall_color)
        list_obstacles.append(obs)
























