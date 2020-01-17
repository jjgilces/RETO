import cv2
import numpy as np

img_path = 'test.png'
img = cv2.imread(img_path, 0)
matrix=np.logical_not(img)
matrix1=np.array(matrix,dtype=int)

import numpy as np
import porespy as ps
import matplotlib.pyplot as plt
import time 
class Node():
    """A node class for A* Pathfinding"""

    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position

        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self, other):
        return self.position == other.position


def astar(maze, start, end):
    """Returns a list of tuples as a path from the given start to the given end in the given maze"""

    # Create start and end node
    start_node = Node(None, start)
    start_node.g = start_node.h = start_node.f = 0
    end_node = Node(None, end)
    end_node.g = end_node.h = end_node.f = 0

    # Initialize both open and closed list
    open_list = []
    closed_list = []

    # Add the start node
    open_list.append(start_node)

    # Loop until you find the end
    while len(open_list) > 0:

        # Get the current node
        current_node = open_list[0]
        current_index = 0
        for index, item in enumerate(open_list):
            if item.f < current_node.f:
                current_node = item
                current_index = index

        # Pop current off open list, add to closed list
        open_list.pop(current_index)
        closed_list.append(current_node)

        # Found the goal
        if current_node == end_node:
            path = []
            current = current_node
            while current is not None:
                path.append(current.position)
                current = current.parent
            return path[::-1] # Return reversed path

        # Generate children
        children = []
        for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]: # Adjacent squares

            # Get node position
            node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])

            # Make sure within range
            if node_position[0] > (len(maze) - 1) or node_position[0] < 0 or node_position[1] > (len(maze[len(maze)-1]) -1) or node_position[1] < 0:
                continue

            # Make sure walkable terrain
            if maze[node_position[0]][node_position[1]] != 0:
                continue

            # Create new node
            new_node = Node(current_node, node_position)

            # Append
            children.append(new_node)

        # Loop through children
        for child in children:

            # Child is on the closed list
            for closed_child in closed_list:
                if child == closed_child:
                    continue

            # Create the f, g, and h values
            child.g = current_node.g + 1
            child.h = ((child.position[0] - end_node.position[0]) ** 2) + ((child.position[1] - end_node.position[1]) ** 2)
            child.f = child.g + child.h

            # Child is already in the open list
            for open_node in open_list:
                if child == open_node and child.g > open_node.g:
                    continue

            # Add the child to the open list
            open_list.append(child)



def path_star(matrix):
    path_star=np.array(matrix)
    path_star=list(path_star[:,0])
    path_star_=[]
    for count, element in enumerate(path_star):
        if element==0:
            path_star_.append((count,0))
            
            
    return path_star_

def path_end(matrix):
    path_end=np.array(matrix)
    path_end=list(path_end[:,-1])
    tath=len(path_end)-1
    path_end_=[]
    for count, element in enumerate(path_end):
        if element==0:
            path_end_.append((count,tath))
    return path_end_

def tortusity(matrix):
    matrix=matrix
    path_star_list=path_star(matrix)
    path_end_list=path_end(matrix)
    caminos=[]
    array_path=np.array(matrix)
    line=(array_path.shape)[1]
    for star in path_star_list:
        for end in path_end_list:
         
            path = astar(matrix, star, end)
            print(path)
            caminos.append(len(path))
    valor=(np.mean(np.array(caminos)))

    tortusity=valor/int(line)
    return tortusity
print(path_star(matrix1))

