import pygame
import pymunk
import random
import math
import datetime
import time
from enum import Enum
from collections import deque


from sub_PyMunk_Env import printf

# Initialize Pygame
pygame.init()

# Define collision types
COLLTYPE_DEFAULT = 0
COLLTYPE_ROBOT = 1
COLLTYPE_REWARD = 2
COLLTYPE_BORDER = 3
COLLTYPE_IR_TRACKER = 4

class States(Enum):
        # status of the robot
    EXPLORE = 0
    MOVE_TOWARDS = 1
    MOVE_TOWARDS_LOST = 2    
    GRABBED = 3
    RETURN = 4
    STATIC = 5

    def __str__(self):
        return self.name

#initialize the first state
state = States.EXPLORE  

# Screen settings
WIDTH, HEIGHT = 1200, 600
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Autonomous Robot with 120° LiDAR")

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

# Pymunk Physics Setup
space = pymunk.Space()
space.gravity = (0, 0)  # No gravity (top-down simulation)

# Robot (Autonomous Agent)
robot_size = 40  # Length of the sides of the square
robot_body = pymunk.Body(1, pymunk.moment_for_box(1, (robot_size, robot_size)))
robot_body.position = (WIDTH // 2, HEIGHT // 2)
robot_shape = pymunk.Poly.create_box(robot_body, (robot_size, robot_size))
robot_shape.collision_type = COLLTYPE_ROBOT
robot_shape.color = BLUE  # not sure why this is needed
robot_shape.elasticity = 0.5  # not sure why this is needed
space.add(robot_body, robot_shape)


# border
BORDER_WIDTH = 800
BORDER_HEIGHT = 400
BORDER_OUTLINE_THICKNESS = 5

# Generate IR Line Tracker
num_ir_trackers = 4
ir_tracker_radius = 8
ir_trackers = []

# Movement settings
speed = 200  # Pixels per second
scan_range = 1000  # LiDAR scan range, AKA length
center_range = 20  # Angle increment per LiDAR ray
robot_direction = 0  # Facing direction in degrees (initialized)

# DEFINING THE IR LINE TRACKER
ANGLES = [45, 135, 225, 315] # convert to radians
ANGLES_RADIANS = [math.radians(angle) for angle in ANGLES]

# becuase we need it to be relative to this direction
rad_angle = math.radians(robot_direction)

#initialization
ir_trackers = []
num_ir_trackers = 4
ir_tracker_position_x = 0
ir_tracker_position_y = 0

# Define the ir_trackers
for _ in range(num_ir_trackers):
    ir_tracker_body = pymunk.Body(1, pymunk.moment_for_circle(1, 0, ir_tracker_radius))
    ir_tracker_body.position = ((WIDTH // 2) + (math.sqrt((robot_size//2)**2 + (robot_size//2)**2) + ir_tracker_radius) * math.cos(math.radians(robot_direction) + ANGLES_RADIANS[_]), (HEIGHT // 2) + (math.sqrt((robot_size//2)**2 + (robot_size//2)**2) + ir_tracker_radius) * math.cos(math.radians(robot_direction) + ANGLES_RADIANS[_]))
    ir_tracker_shape = pymunk.Circle(ir_tracker_body, ir_tracker_radius)
    ir_tracker_shape.collision_type = COLLTYPE_IR_TRACKER
    ir_tracker_shape.color = RED
    ir_tracker_shape.elasticity = 0.5 # not sure why this is needed
    ir_trackers.append(ir_tracker_shape)
    space.add(ir_tracker_body, ir_tracker_shape)

# Function to check if a point is inside a circle
def is_point_in_circle(point, circle_center, circle_radius):
    return (point[0] - circle_center[0]) ** 2 + (point[1] - circle_center[1]) ** 2 <= circle_radius ** 2

# Function to handle mouse click events
def handle_mouse_click():
    global rewards
    mouse_pos = pygame.mouse.get_pos()
    for reward in rewards:
        if is_point_in_circle(mouse_pos, reward.body.position, reward_radius):
            space.remove(reward, reward.body)
            rewards.remove(reward)
            break

# Generate rewards (Green circles)
reward_radius = 5
num_rewards = 10
rewards = []

#datetime used for zigzag strategy
zigzag_interval = 0.2  # seconds
zigzag_count = 1 #initialise the zigzag count, cannot be 0
curr_time = datetime.datetime.now()

# DEFINING THE REWARD
for _ in range(num_rewards):
    START_X = (WIDTH - BORDER_WIDTH) // 2 + BORDER_OUTLINE_THICKNESS + reward_radius
    END_X = (WIDTH + BORDER_WIDTH) // 2 - BORDER_OUTLINE_THICKNESS - reward_radius
    START_Y = (HEIGHT - BORDER_HEIGHT) // 2 + BORDER_OUTLINE_THICKNESS + reward_radius
    END_Y = (HEIGHT + BORDER_HEIGHT) // 2 - BORDER_OUTLINE_THICKNESS - reward_radius

    x = random.randint(START_X, END_X)
    y = random.randint(START_Y, END_Y)
    
    # x = random.randint((WIDTH - BORDER_WIDTH)//2 + BORDER_OUTLINE_THICKNESS + reward_radius, (WIDTH + BORDER_WIDTH)//2 -BORDER_OUTLINE_THICKNESS - reward_radius)
    # y = random.randint((HEIGHT - BORDER_HEIGHT)//2 + BORDER_OUTLINE_THICKNESS + reward_radius, (HEIGHT + BORDER_HEIGHT)//2 - BORDER_OUTLINE_THICKNESS - reward_radius)
    reward_body = pymunk.Body(body_type=pymunk.Body.STATIC)
    reward_body.position = (x, y)
    reward_shape = pymunk.Circle(reward_body, reward_radius)
    reward_shape.collision_type = COLLTYPE_REWARD
    reward_shape.color = GREEN
    rewards.append(reward_shape)
    space.add(reward_body, reward_shape)
    

# DEFINING THE YELLOW BORDER
#create the starting and ending coordinate
RECT_START_X = (WIDTH - BORDER_WIDTH) // 2 + BORDER_OUTLINE_THICKNESS 
RECT_END_X = (WIDTH + BORDER_WIDTH) // 2 - BORDER_OUTLINE_THICKNESS 
RECT_START_Y = (HEIGHT - BORDER_HEIGHT) // 2 + BORDER_OUTLINE_THICKNESS 
RECT_END_Y = (HEIGHT + BORDER_HEIGHT) // 2 - BORDER_OUTLINE_THICKNESS 

# Define border positions
border_segments = [
    [(RECT_START_X, RECT_START_Y), (RECT_END_X, RECT_START_Y)],  # Top border
    [(RECT_START_X, RECT_END_Y), (RECT_END_X, RECT_END_Y)],  # Bottom border
    [(RECT_START_X, RECT_START_Y), (RECT_START_X, RECT_END_Y)],  # Left border
    [(RECT_END_X, RECT_START_Y), (RECT_END_X, RECT_END_Y)],  # Right border
]

for segment in border_segments:
    border_shape = pymunk.Segment(space.static_body, segment[0], segment[1], BORDER_OUTLINE_THICKNESS)
    border_shape.elasticity = 1.0  # Makes sure the robot bounces off properly
    border_shape.friction = 0.5
    border_shape.collision_type = COLLTYPE_BORDER
    space.add(border_shape)


def draw_text(text, position, color=BLACK, font_size=24):
    font = pygame.font.Font(None, font_size)
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, position)

def normalize_angle(angle):
    """Normalize the angle to be within the range of -180 to 180 degrees."""
    while angle > 180:
        angle -= 360
    while angle < -180:
        angle += 360
    return angle
    

def lidar_scan():
    """Simulate a single LiDAR ray in front of the robot to detect rewards."""
    global state

    temp_lidar_object = None #lidar_scan object holder

    rad_angle = math.radians(robot_direction)

    # Check if any rewards are within the scan range
    for reward in rewards:
        distance = (reward.body.position - robot_body.position).length
        reward_angle = math.degrees(math.atan2(reward.body.position.y - robot_body.position.y,
                                               reward.body.position.x - robot_body.position.x))

        # Ensure reward is directly in front of the robot
        if distance < scan_range and abs(reward_angle - robot_direction) < center_range / 2:            
            temp_lidar_object = reward
            #printf(f"                                   the obejct is = {temp_lidar_object}", "DEBUG")
            state = States.MOVE_TOWARDS #if detected, change the state to move towards
            return temp_lidar_object
    
    temp_lidar_object = None
    #printf(f"                                   the obejct is = {temp_lidar_object}", "DEBUG")
    
    if state == States.MOVE_TOWARDS_LOST: #check if its caused by move_towards_lost
        pass
    else:
        state = States.EXPLORE #if detected, change the state to move towards
    
    return temp_lidar_object
"""
def move_towards(target):
    #Move the robot towards a target position and update direction.
    global state 
    global robot_body
    global robot_direction
    
    #update the state
    state = States.MOVE_TOWARDS
    
    # Move straight in the existing direction
    rad_angle = math.radians(robot_direction)
    robot_body.velocity = pymunk.Vec2d(math.cos(rad_angle) * speed, math.sin(rad_angle) * speed)
#=======================================================================================================
    # # Calculate the direction vector from the robot to the target reward
    # direction_vector = target.body.position - robot_body.position
    
    # # Normalize the direction vector and scale it by the robot's speed
    # direction_vector = direction_vector.normalized() * speed
    
    # # Set the robot's velocity to move towards the target reward
    # robot_body.velocity = direction_vector
    

    # Update robot direction to face the target
    #robot_direction = math.degrees(math.atan2(direction_vector.y, direction_vector.x))
#=======================================================================================================

    # Ensure the robot direction is within valid bounds (-180 to 180 degrees)
    robot_direction = normalize_angle(robot_direction)
"""

# Initialize variables
rotation_sequence = [-15, 30, -15]  # Sweep left 15°, right 30°, left 15° (back to original)
rotation_index = 0  # Track which step we're at
rotation_timer = 0  # Track time of last rotation update
rotation_delay = 500  # Delay between rotations (in milliseconds)

def stop_and_sweep():
    """Handles non-blocking rotation of the robot in a sweeping motion."""
    global robot_direction, rotation_index, rotation_timer, state, robot_body

    
    robot_body.velocity = pymunk.Vec2d(0,0) # stop the bot
    
    current_time = pygame.time.get_ticks()  # Get current time in milliseconds

    # Only update rotation if enough time has passed
    if current_time - rotation_timer >= rotation_delay:
        if rotation_index < len(rotation_sequence):  # If more rotations left in sequence
            robot_direction += rotation_sequence[rotation_index]  # Apply rotation step
            robot_direction = normalize_angle(robot_direction)  # Keep within -180 to 180
            robot_body.angle = math.radians(robot_direction)  # Update physics engine

            rotation_index += 1  # Move to next step
            rotation_timer = current_time  # Reset timer

        else:
            printf("Sweeping Complete.", "SUCCESS")
            state = States.EXPLORE  # Return to exploration mode



# def move_towards(target):
#     """Move the robot towards a target position and update direction."""
#     global state 
#     global robot_body
#     global robot_direction
#     global rad_angle
    
#     lost = False

#     # while not lost
#     while not lost:
#         temp_prev_dist_robot_reward = (target.body.position - robot_body.position).length #store the initial distance between the robot and the target
#         #update the state
#         state = States.MOVE_TOWARDS
        
#         # Move straight in the existing direction
#         rad_angle = math.radians(robot_direction)
#         robot_body.velocity = pymunk.Vec2d(math.cos(rad_angle) * speed, math.sin(rad_angle) * speed)

#         # None = lost
#         if lidar_scan() == None:
#             # i want the robot to rotate 15 degree sweep left and right
#             lost = stop_and_sweep(temp_prev_dist_robot_reward)

#     # Ensure the robot direction is within valid bounds (-180 to 180 degrees)
#     robot_direction = normalize_angle(robot_direction)

def move_towards(target):
    """Move the robot towards a target position and update direction."""
    global state 
    global robot_body
    global robot_direction
    global rad_angle

    temp_prev_dist_robot_reward = (target.body.position - robot_body.position).length  # store the initial distance between the robot and the target
    
    # Move straight in the existing direction
    rad_angle = math.radians(robot_direction)
    robot_body.velocity = pymunk.Vec2d(math.cos(rad_angle) * speed, math.sin(rad_angle) * speed)

    # Check if the target is lost
    if target is None:
        #change state 
        state = States.MOVE_TOWARDS_LOST

    # Ensure the robot direction is within valid bounds (-180 to 180 degrees)
    robot_direction = normalize_angle(robot_direction)



# Exploration Mode - Random movement when no rewards detected
def explore():
    """Move straight until it hits the corner, then change direction."""
    global robot_direction
    global curr_time
    global zigzag_count
    global state
    global rad_angle

    state = States.EXPLORE

    #zigzag strategy
    if (datetime.datetime.now() - curr_time).total_seconds() >= zigzag_interval and zigzag_count % 2 == 0:
        curr_time = datetime.datetime.now()
        robot_direction += 10
        robot_direction = normalize_angle(robot_direction) # Ensure the robot direction is within valid bounds (-180 to 180 degrees)
        zigzag_count += 1
        
    
    elif (datetime.datetime.now() - curr_time).total_seconds() >= zigzag_interval and zigzag_count % 2 != 0:
        curr_time = datetime.datetime.now()
        robot_direction -= 10
        robot_direction = normalize_angle(robot_direction) # Ensure the robot direction is within valid bounds (-180 to 180 degrees)
        zigzag_count += 1
    
    rad_angle = math.radians(robot_direction)
    robot_body.velocity = pymunk.Vec2d(math.cos(rad_angle) * speed, math.sin(rad_angle) * speed)



def draw_lidar():
        for angle_offset in [-10, 0, 10]:
            rad_angle = math.radians(robot_direction + angle_offset)
            ray_x = robot_body.position.x + scan_range * math.cos(rad_angle)
            ray_y = robot_body.position.y + scan_range * math.sin(rad_angle)
            pygame.draw.line(screen, BLACK, (robot_body.position.x, robot_body.position.y), (ray_x, ray_y), 1)
    

# Add the yellow border to the physics simulation
def draw_yellow_border():
    """Draws the border in Pygame using yellow lines."""
    for segment in border_segments:
        pygame.draw.line(screen, YELLOW, segment[0], segment[1], BORDER_OUTLINE_THICKNESS)     

def rotate_robot(corners, rad_angle): #rad angle is radians
        # Rotate the corners around the center of the robot 
        rotated_corners = []

        for x, y in corners:
            # Translate point to origin
            temp_x = x - robot_body.position.x
            temp_y = y - robot_body.position.y
            
            # Rotate point
            rotated_x = temp_x * math.cos(rad_angle) - temp_y * math.sin(rad_angle)
            rotated_y = temp_x * math.sin(rad_angle) + temp_y * math.cos(rad_angle)
            
            rotated_corners.append((rotated_x + robot_body.position.x, rotated_y + robot_body.position.y)) # Translate point back

        return rotated_corners
    
def state_manager(state_args, target_reward_args):
    if state_args == States.EXPLORE:
        explore()

    elif state_args == States.MOVE_TOWARDS:
        move_towards(target_reward_args)
        
    elif state_args == States.MOVE_TOWARDS_LOST:
        stop_and_sweep()

    elif state_args == States.STATIC:
        pass

    else:
        printf("Error", "WARN")    


# Collision handler for robot and rewards
def robot_reward_collision(arbiter, space, data):
    global rewards

    robot_shape, reward_shape = arbiter.shapes  # Get the two colliding shapes
    space.remove(reward_shape, reward_shape.body)  # Remove reward from the physics simulation
    printf(f"                                               {reward_shape}", "WARN")
    rewards.remove(reward_shape)  # Remove reward from the game listrd_shape}", "WARN")
    return True

handler = space.add_collision_handler(COLLTYPE_ROBOT, COLLTYPE_REWARD)
handler.begin = robot_reward_collision

# Collision handler for robot and rewards
def ir_tracker_boarder_collision(arbiter, space, data):
    global robot_direction

    # Get collision normal to determine reflection direction
    normal = arbiter.contact_point_set.normal  # Direction of impact
    robot_direction = math.degrees(math.atan2(-normal.y, -normal.x))  # Reflect angle
    robot_direction = normalize_angle(robot_direction) # Ensure the robot direction is within valid bounds (-180 to 180 degrees)

    # Add randomness to prevent repeating paths
    robot_direction += random.randint(-60, -40) if random.random() < 0.5 else random.randint(40, 60)
    # Ensure the robot direction is within valid bounds (-180 to 180 degrees)
    robot_direction = normalize_angle(robot_direction)
    
    # Update velocity based on new direction
    rad_angle = math.radians(robot_direction)
    robot_body.velocity = pymunk.Vec2d(math.cos(rad_angle) * speed, math.sin(rad_angle) * speed)
    return True

# Register the fixed collision handler
handler = space.add_collision_handler(COLLTYPE_IR_TRACKER, COLLTYPE_BORDER)
handler.begin = ir_tracker_boarder_collision

def robot_border_collision(arbiter, space, data):
    screen.fill(BLACK)
    return True

handler = space.add_collision_handler(COLLTYPE_ROBOT, COLLTYPE_BORDER)
handler.begin = robot_border_collision

def dynamic_main():
    global ir_tracker_position_x
    global ir_tracker_position_y
    global robot_direction
    
    # Game loop
    clock = pygame.time.Clock()
    running = True
    
    running_count = 0
    # simulation running
    while running:
       
        # running log
        running_count += 1
        printf(f"Running count: {running_count}", "LOG")
        printf(f"           Location of the robot -  x,y = [{robot_body.position.x:7.2f}, {robot_body.position.y:7.2f}]", "LOG")
        
        screen.fill(WHITE)
        
        # Add this function call inside the game loop in dynamic_main
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                handle_mouse_click()

        #printf(f"                                       target_reward = {target_reward}", "DEBUG")

        draw_yellow_border() # Draw the border
        draw_lidar() # Draw LiDAR rays 
        
        # update the ir tracker
        for _ in range(num_ir_trackers):
            #to fit the circles inside
            offset_number = 0.7
            ir_tracker_position_x = robot_body.position.x + offset_number * (math.sqrt((robot_size//2)**2 + (robot_size//2)**2) + ir_tracker_radius) * math.cos(math.radians(robot_direction) + ANGLES_RADIANS[_]) 
            ir_tracker_position_y = robot_body.position.y + offset_number * (math.sqrt((robot_size//2)**2 + (robot_size//2)**2) + ir_tracker_radius) * math.sin(math.radians(robot_direction) + ANGLES_RADIANS[_]) 
            ir_trackers[_].body.position = (ir_tracker_position_x, ir_tracker_position_y)  # Update Pymunk body position
            pygame.draw.circle(screen, RED, (int(ir_tracker_position_x), int(ir_tracker_position_y)), ir_tracker_radius)
    
        
        # Calculate the top-left corner of the square
        top_left_x = int(robot_body.position.x - robot_size / 2)
        top_left_y = int(robot_body.position.y - robot_size / 2)
        
        # Calculate the rotated corners of the square
        corners = [
            (top_left_x, top_left_y),
            (top_left_x + robot_size, top_left_y),
            (top_left_x + robot_size, top_left_y + robot_size),
            (top_left_x, top_left_y + robot_size)
        ]

        rad_angle = math.radians(robot_direction) #update the angle to be fed into rotate robot
        rotated_corners = rotate_robot(corners, rad_angle) #rotate the robot
        
# =============================================================================

        target_reward = lidar_scan() # Detect rewards using LiDAR   
        pygame.draw.polygon(screen, BLUE, rotated_corners) # Draw the rotated square

        # Move towards detected reward, otherwise explore randomly
        printf(f"           target_reward = {target_reward}", "DEBUG")
        state_manager(state, target_reward)

        # Step the physics engine    
        dt = clock.get_time() / 1000.0 # time elasped between two consecutive clock.get_time() calls
        space.step(dt)

        # Draw rewards
        for reward in rewards:
            pygame.draw.circle(screen, GREEN, (int(reward.body.position.x), int(reward.body.position.y)), reward_radius)


        # Text for the simulation
        draw_text(f"Status : {state}", (10, 10))
        draw_text(f"{target_reward}", (10, 30))
        draw_text(f"Angle of the robot = {robot_direction} degres", (10, 50))
        draw_text(f"Location of the robot -  x,y = [{robot_body.position.x:7.2f}, {robot_body.position.y:7.2f}]", (10, 70))
        draw_text(f"Location of IR tracker -  x,y = [{robot_direction + ANGLES[0]:7.2f}, {robot_direction + ANGLES[0]:7.2f}] degres", (10, 90))
        
        # Update the display
        pygame.display.flip()

        clock.tick(60)

    pygame.quit()
    # Function to draw text on the screen



 
dynamic_main()
