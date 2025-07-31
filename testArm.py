import time
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

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

# Interpolation functions from your original ArmControl.py
def interpolate_servo0(file_num):
    points = [
        (1, 130),  # Average of a1 (135) and a4 (125)
        (4, 102.5),  # Average of d1 (105) and d4 (100)
        (5, 90),  # e1, e4
        (8, 51)  # Average of h1 (45) and h4 (57)
    ]
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        if x0 <= file_num <= x1:
            return y0 + (y1 - y0) * (file_num - x0) / (x1 - x0)
    return 90

def interpolate_servo2(rank):
    west_rank1 = 60  # a1, h1
    west_rank4 = 80  # a4, h4
    east_rank1 = 20  # d1, e1
    east_rank4 = 65  # d4, e4
    if 1 <= rank <= 4:
        west_angle = west_rank1 + (west_rank4 - west_rank1) * (rank - 1) / 3
        east_angle = east_rank1 + (east_rank4 - east_rank1) * (rank - 1) / 3
        return (west_angle + east_angle) / 2
    else:
        west_angle = west_rank4 + (west_rank4 - west_rank1) / 3 * (rank - 4)
        east_angle = east_rank4 + (east_rank4 - east_rank1) / 3 * (rank - 4)
        return min((west_angle + east_angle) / 2, 180)

def interpolate_servo1_and_3(file_num, rank):
    corners = {
        (1, 1): (180, 180),  # a1
        (1, 4): (180, 155),  # a4
        (8, 1): (170, 180),  # h1
        (8, 4): (180, 160),  # h4
        (4, 1): (140, 160),  # d1
        (4, 4): (170, 160),  # d4
        (5, 1): (140, 160),  # e1
        (5, 4): (170, 160),  # e4
    }
    file_points = sorted(set(f for f, _ in corners.keys()))
    rank_points = sorted(set(r for _, r in corners.keys()))
    f0 = max([f for f in file_points if f <= file_num], default=file_points[0])
    f1 = min([f for f in file_points if f >= file_num], default=file_points[-1])
    r0 = max([r for r in rank_points if r <= rank], default=rank_points[0])
    r1 = min([r for r in rank_points if r >= rank], default=rank_points[-1])
    s1_00, s3_00 = corners.get((f0, r0), (170, 160))
    s1_01, s3_01 = corners.get((f0, r1), (170, 160))
    s1_10, s3_10 = corners.get((f1, r0), (170, 160))
    s1_11, s3_11 = corners.get((f1, r1), (170, 160))
    if f1 == f0:
        t = 0
    else:
        t = (file_num - f0) / (f1 - f0)
    if r1 == r0:
        u = 0
    else:
        u = (rank - r0) / (r1 - r0)
    servo1 = (1 - t) * (1 - u) * s1_00 + t * (1 - u) * s1_10 + (1 - t) * u * s1_01 + t * u * s1_11
    servo3 = (1 - t) * (1 - u) * s3_00 + t * (1 - u) * s3_10 + (1 - t) * u * s3_01 + t * u * s3_11
    return (min(max(servo1, 0), 180), min(max(servo3, 0), 180))

# Function to move to a square
def move_to_position(target_square):
    file_letter = target_square[0].lower()
    rank = int(target_square[1])
    file_num = ord(file_letter) - ord('a') + 1  # a=1, h=8

    # Map to bot's perspective (Black side, a-h mirrored)
    bot_file_num = 9 - file_num  # e.g., a (1) -> h (8)
    bot_rank = 9 - rank          # e.g., 1 -> 8

    print(f"Standard coordinates (human perspective): {file_letter}{rank} (file_num={file_num}, rank={rank})")
    print(f"Bot's perspective: {chr(ord('a') + 9 - bot_file_num - 1)}{bot_rank} (file_num={bot_file_num}, rank={bot_rank})")

    # Interpolate servo angles using bot's perspective
    servo0_angle = interpolate_servo0(bot_file_num)
    servo2_angle = interpolate_servo2(bot_rank)
    servo1_angle, servo3_angle = interpolate_servo1_and_3(bot_file_num, bot_rank)

    # Servo 4 (gripper) set to open (30°)
    servo4_angle = 30

    angles = [servo0_angle, servo1_angle, servo2_angle, servo3_angle, servo4_angle]
    print(f"Moving to {target_square} with angles (Servos 0-4): {[round(a, 1) for a in angles]}")

    for i, angle in enumerate(angles):
        servos[i].angle = angle
        print(f"Set servo {i} (channel {i+1}) to {angle:.1f} degrees")
        time.sleep(0.5)  # Delay for smooth movement

# Main function to test the arm
def main():
    # Initialize servos to a neutral position
    print("Initializing all servos to 90 degrees...")
    neutral_angles = [90, 90, 90, 90, 0]  # Rest position (gripper closed)
    for i, angle in enumerate(neutral_angles):
        servos[i].angle = angle
        print(f"Set servo {i} (channel {i+1}) to {angle} degrees")
        time.sleep(0.5)

    print("\nEnter a chess square (e.g., 'A7', 'D4') to move the arm to that position.")
    print("Type 'exit' to quit.")

    while True:
        # Prompt for input
        user_input = input("Enter square (e.g., 'A7'): ").strip().upper()
        
        if user_input.lower() == 'exit':
            print("Exiting program...")
            break

        # Validate input
        if len(user_input) != 2:
            print("Invalid input. Please enter a square like 'A7' or 'D4'.")
            continue

        file_char, rank_char = user_input[0], user_input[1]
        if file_char not in 'ABCDEFGH' or rank_char not in '12345678':
            print("Invalid square. File must be A-H, rank must be 1-8.")
            continue

        target_square = file_char.lower() + rank_char
        print(f"Testing position: {target_square}")

        try:
            move_to_position(target_square)
            print(f"Arm moved to {target_square} successfully.")
        except Exception as e:
            print(f"Error moving arm to {target_square}: {e}")

    # Cleanup: Return to neutral position and deinitialize
    print("Returning to neutral position...")
    for i, angle in enumerate(neutral_angles):
        servos[i].angle = angle
        print(f"Set servo {i} (channel {i+1}) to {angle} degrees")
        time.sleep(0.5)
    pca.deinit()
    print("PCA9685 deinitialized")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
        # Cleanup on exit
        neutral_angles = [90, 90, 90, 90, 0]
        for i, angle in enumerate(neutral_angles):
            servos[i].angle = angle
            print(f"Set servo {i} (channel {i+1}) to {angle} degrees")
            time.sleep(0.5)
        pca.deinit()
        print("PCA9685 deinitialized")