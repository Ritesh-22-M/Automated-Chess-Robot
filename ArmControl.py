import time
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo
import VisionModule as vm
import numpy as np
from math import sqrt, copysign

# Setup I2C and PCA9685
i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c, address=0x40)
pca.frequency = 50  # Set PWM frequency to 50 Hz for servos

# Initialize servos on channels 1-5 (servo 0-4)
servos = [
    servo.Servo(pca.channels[1], min_pulse=500, max_pulse=2500),  # Servo 0 (MG995, Base)
    servo.Servo(pca.channels[2], min_pulse=500, max_pulse=2500),  # Servo 1 (MG995, Shoulder)
    servo.Servo(pca.channels[3], min_pulse=500, max_pulse=2500),  # Servo 2 (MG995, Elbow)
    servo.Servo(pca.channels[4], min_pulse=500, max_pulse=2500),  # Servo 3 (MG90S, Wrist)
    servo.Servo(pca.channels[5], min_pulse=500, max_pulse=2500),  # Servo 4 (MG90S, Gripper)
]

# Global list to track current angles of each servo
current_angles = [90, 90, 30, 90, 0]  # Initial/rest position

# Lookup table for servo angles based on green_chess_board.docx
# Format: "square": [servo0, servo1, servo2, servo3]
square_angles = {
    "A8": [40, 165, 40, 170], "B8": [55, 155, 25, 170], "C8": [60, 150, 15, 160], "D8": [80, 140, 0, 150],
    "E8": [100, 140, 0, 150], "F8": [120, 150, 15, 160], "G8": [140, 160, 25, 170], "H8": [140, 160, 25, 155],
    "H7": [135, 170, 40, 155], "G7": [127, 170, 40, 165], "F7": [115, 170, 40, 170], "E7": [103, 170, 40, 175],
    "D7": [87, 170, 40, 175], "C7": [75, 170, 40, 170], "B7": [65, 170, 40, 165], "A7": [55, 170, 40, 160],
    "A6": [57, 180, 60, 165], "B6": [70, 180, 60, 175], "C6": [77, 180, 60, 180], "D6": [90, 180, 60, 180],
    "E6": [100, 180, 60, 180], "F6": [113, 180, 60, 180], "G6": [122, 180, 60, 175], "H6": [127, 180, 60, 165],
    "H5": [122, 180, 60, 150], "G5": [115, 180, 60, 157], "F5": [107, 180, 60, 163], "E5": [97, 180, 60, 165],
    "D5": [85, 180, 60, 165], "C5": [77, 180, 60, 163], "B5": [67, 180, 60, 157], "A5": [58, 180, 60, 150],
    "A4": [65, 180, 55, 130], "B4": [73, 180, 55, 135], "C4": [79, 180, 55, 137], "D4": [87, 180, 55, 140],
    "E4": [94, 180, 55, 143], "F4": [105, 180, 55, 137], "G4": [110, 180, 55, 135], "H4": [120, 180, 55, 130],
    "H3": [120, 180, 47, 110], "G3": [115, 180, 47, 110], "F3": [107, 177, 47, 118], "E3": [100, 177, 47, 118],
    "D3": [92, 177, 47, 118], "C3": [84, 177, 47, 118], "B3": [75, 177, 50, 118], "A3": [70, 180, 50, 110]
}

# Method to move a servo slowly and smoothly to the target angle
def move_servo_slowly(servo_num, target_angle):
    global current_angles
    if not 0 <= target_angle <= 180:
        print(f"Error: Target angle {target_angle} for servo {servo_num} must be between 0 and 180 degrees")
        return

    current_angle = current_angles[servo_num]
    print(f"Moving servo {servo_num} (channel {servo_num+1}) from {current_angle} to {target_angle} degrees")

    # Calculate the step direction and total steps
    step = 1 if target_angle > current_angle else -1  # 1-degree steps
    steps = int(abs(target_angle - current_angle))  # Number of 1-degree steps

    # Move in increments of 1 degree
    for i in range(steps + 1):
        intermediate_angle = current_angle + (i * step)
        if step > 0:
            if intermediate_angle > target_angle:
                intermediate_angle = target_angle
        else:
            if intermediate_angle < target_angle:
                intermediate_angle = target_angle

        try:
            servos[servo_num].angle = intermediate_angle
            print(f"Set servo {servo_num} (channel {servo_num+1}) to {intermediate_angle:.1f} degrees")
            current_angles[servo_num] = intermediate_angle
            time.sleep(0.04)  # Delay of 0.04 seconds for every 1-degree change
        except Exception as e:
            print(f"Error setting servo {servo_num} to {intermediate_angle:.1f} degrees: {e}")
            return

    # Ensure the final angle is exactly the target
    if current_angles[servo_num] != target_angle:
        try:
            servos[servo_num].angle = target_angle
            print(f"Set servo {servo_num} (channel {servo_num+1}) to {target_angle:.1f} degrees (final)")
            current_angles[servo_num] = target_angle
            time.sleep(0.04)
        except Exception as e:
            print(f"Error setting servo {servo_num} to {target_angle:.1f} degrees (final): {e}")

# Initialize all servos to their rest position
def initialize_servos():
    print("Initializing all servos to rest position...")
    angles_rest = [90, 90, 30, 90, 0]  # Rest position: [S0, S1, S2, S3, S4]
    for i in [1, 2, 3, 0, 4]:  # Order: 1, 2, 3, 0, 4
        move_servo_slowly(i, angles_rest[i])

def move_to_position(target_square, params, color, goDown):
    """
    Move the arm to the specified chessboard square using lookup table.

    Args:
        target_square (str): Chessboard square (e.g., "a1").
        params (dict): Physical parameters (baseradius, cbFrame, sqSize, etc.).
        color (bool): True if playing as white, False as black.
        goDown (float): Height adjustment for picking/placing (in cm).

    Returns:
        bool: True if moved successfully.
    """
    # Convert to uppercase for lookup (e.g., "a8" -> "A8")
    target_square_upper = target_square.upper()

    # Check if the square exists in the lookup table
    if target_square_upper not in square_angles:
        print(f"Error: Square {target_square} not found in the angle lookup table")
        return False

    # Get servo angles from the lookup table
    angles = square_angles[target_square_upper]  # [servo0, servo1, servo2, servo3]
    print(f"Moving to {target_square} with angles (Servos 0-3): {[round(a, 1) for a in angles]}")

    # Move servos in the specified order: 0, 3, 2, 1
    servo_order = [0, 3, 2, 1]
    for i in servo_order:
        move_servo_slowly(i, angles[i])
    
    return True

def CBtoXY(targetCBsq, params, color):
    """
    Convert chessboard square to (x, y) coordinates.

    Args:
        targetCBsq (str): Chessboard square (e.g., "a1").
        params (dict): Physical parameters (baseradius, cbFrame, sqSize, etc.).
        color (bool): True if playing as white, False as black.

    Returns:
        tuple: (x, y) coordinates in cm.
    """
    wletterWeight = [-4, -3, -2, -1, 1, 2, 3, 4]
    bletterWeight = [4, 3, 2, 1, -1, -2, -3, -4]
    bnumberWeight = [8, 7, 6, 5, 4, 3, 2, 1]

    if targetCBsq[0] == 'k':  # Graveyard
        x = 6 * params["sqSize"]
        y = 6 * params["sqSize"]
    else:
        if color:  # White -> Robot plays black
            sqletter = bletterWeight[ord(targetCBsq[0]) - 97]
            sqNumber = bnumberWeight[int(targetCBsq[1]) - 1]
        else:  # Black
            sqletter = wletterWeight[ord(targetCBsq[0]) - 97]
            sqNumber = int(targetCBsq[1])

        x = params["baseradius"] + params["cbFrame"] + params["sqSize"] * sqNumber - params["sqSize"] * 0.5
        y = params["sqSize"] * sqletter - copysign(params["sqSize"] * 0.5, sqletter)

    return (x, y)

def executeMove(move, params, color, homography, cap, selectedCam):
    """
    Execute a chess move by moving the arm to specified squares.

    Args:
        move (str): Sequence of squares (e.g., "e2e4" for a move, or "e7k0e2e7" for a capture).
        params (dict): Physical parameters.
        color (bool): Player color.
        homography: Homography matrix for vision.
        cap: Camera capture object.
        selectedCam: Camera selection (for VisionModule).

    Returns:
        bool: True if move executed successfully.
    """
    angles_rest = [90, 90, 30, 90, 0]  # Rest position
    gClose = 10    # Gripper closed
    gOpen = 25    # Gripper open
    goDown = 0.6 * params["pieceHeight"]
    gripState = gClose  # Start with gripper closed
    x, y = 0, 0

    for i in range(0, len(move), 2):
        # Calculate position
        x0, y0 = x, y
        x, y = CBtoXY((move[i], move[i+1]), params, color)
        distance = sqrt(((x0 - x) ** 2) + ((y0 - y) ** 2))

        # Move to the square
        target_square = move[i:i+2]
        print(f"1) MOVE TO {target_square}")

        # For picking (first square in pair, i.e., i/2 is even)
        if (i / 2) % 2 == 0:
            # Open the gripper before moving
            print(f"1.1) OPEN the gripper (Servo 4 at {gOpen})")
            move_servo_slowly(4, gOpen)
            gripState = gOpen

            # Move to the square
            arrived = move_to_position(target_square, params, color, goDown)
            askPermision(arrived, homography, cap, selectedCam)

            # Close the gripper (Servo 4)
            print(f"2) CLOSE the gripper (Servo 4 at {gClose})")
            move_servo_slowly(4, gClose)

            # Return to initial position in order 1, 2, 3, 0 (gripper remains closed)
            print("3) RETURN TO INITIAL POSITION")
            for servo_idx in [1, 2, 3, 0]:
                move_servo_slowly(servo_idx, angles_rest[servo_idx])
            gripState = gClose
            goDown = 0.5 * params["pieceHeight"]

        # For placing (second square in pair, i.e., i/2 is odd)
        else:
            arrived = move_to_position(target_square, params, color, goDown)
            askPermision(arrived, homography, cap, selectedCam)

            # Open the gripper (Servo 4)
            print(f"2) OPEN the gripper (Servo 4 at {gOpen})")
            move_servo_slowly(4, gOpen)
            gripState = gOpen
            goDown = 0.6 * params["pieceHeight"]

    # Return to rest position
    print("4) REST")
    for i in [1, 2, 3, 0, 4]:  # Order: 1, 2, 3, 0, 4
        move_servo_slowly(i, angles_rest[i])

    return True

def askPermision(arrived, homography, cap, selectedCam):
    """
    Check if it is safe to move using vision module.

    Args:
        arrived (bool): Whether the arm reached the position.
        homography: Homography matrix.
        cap: Camera capture object.
        selectedCam: Camera selection.
    """
    angles_rest = [90, 90, 30, 90, 0]
    sec = 0

    while not arrived:
        print("Obstacle detected or move failed")
        # Move to rest position
        for i in [1, 2, 3, 0, 4]:
            move_servo_slowly(i, angles_rest[i])

        while not arrived and sec < 3:
            if vm.safetoMove(homography, cap, selectedCam) or sec == 2:
                print("- Retrying")
                arrived = move_to_position(target_square, params, color, goDown)
            else:
                print("Waiting for clear path...")
                time.sleep(1)
            sec += 1

def cleanup():
    """Deinitialize PCA9685 on program exit."""
    angles_rest = [90, 90, 30, 90, 0]
    print("Returning to rest position before cleanup...")
    for i in [1, 2, 3, 0, 4]:
        move_servo_slowly(i, angles_rest[i])
    pca.deinit()
    print("PCA9685 deinitialized")

# Initialize servos on startup
if __name__ == "__main__":
    try:
        initialize_servos()
        print("Arm control initialized. Ready to execute moves.")
        # Main loop or testing code can be added here if needed
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
        cleanup()
    except Exception as e:
        print(f"Error: {e}")
        cleanup()
