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
    servo.Servo(pca.channels[1], min_pulse=500, max_pulse=2500),  # Servo 0 (MG995)
    servo.Servo(pca.channels[2], min_pulse=500, max_pulse=2500),  # Servo 1 (MG995)
    servo.Servo(pca.channels[3], min_pulse=500, max_pulse=2500),  # Servo 2 (MG995)
    servo.Servo(pca.channels[4], min_pulse=500, max_pulse=2500),  # Servo 3 (MG90S)
    servo.Servo(pca.channels[5], min_pulse=500, max_pulse=2500),  # Servo 4 (MG90S)
]

# Global list to track current angles of each servo
current_angles = [90, 90, 30, 90, 20]  # Initial angles

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
        # Ensure we don't overshoot the target
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

# Initialize all servos to their respective angles
def initialize_servos():
    print("Initializing all servos...")
    for i, s in enumerate(servos):
        if i == 2:
            target_angle = 30
        elif i == 4:
            target_angle = 20
        else:
            target_angle = 90
        move_servo_slowly(i, target_angle)

# Main program
def main():
    initialize_servos()
    print("Enter servo number (0-4) and angle (0-180), e.g., '0 90'. Type 'exit' to quit.")

    while True:
        try:
            user_input = input("Enter command: ").strip()
            if user_input.lower() == 'exit':
                print("Exiting program...")
                break

            # Parse input (servo_number angle)
            servo_num, angle = map(float, user_input.split())

            # Validate servo number and angle
            if not 0 <= servo_num <= 4:
                print("Error: Servo number must be between 0 and 4")
                continue
            if not 0 <= angle <= 180:
                print("Error: Angle must be between 0 and 180")
                continue

            servo_num = int(servo_num)
            move_servo_slowly(servo_num, angle)

        except ValueError:
            print("Error: Invalid input. Use format 'servo_number angle' (e.g., '0 90')")
        except Exception as e:
            print(f"Error: {e}")

    # Clean up: Return to initial positions
    print("Returning to initial positions...")
    for i, angle in enumerate([90, 90, 30, 90, 20]):
        move_servo_slowly(i, angle)

    # Deinitialize PCA9685
    pca.deinit()
    print("PCA9685 deinitialized")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
        # Clean up: Return to initial positions
        for i, angle in enumerate([90, 90, 30, 90, 20]):
            move_servo_slowly(i, angle)
        pca.deinit()
        print("PCA9685 deinitialized")
    finally:
        pca.deinit()
        print("PCA9685 deinitialized")