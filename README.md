![Thumbnail](https://github.com/user-attachments/assets/db909476-69a8-483c-a158-756701fb78a6)

# 🧠♟️ Automated Chess Playing Robot using Raspberry Pi 🤖

# 📽️ Project Video :

# 📌 Introduction
This project presents the design and implementation of an Automated Chess Playing Robot that uses Raspberry Pi, a webcam, and a 6-DOF robotic arm to play real-time chess against a human opponent. The system captures the physical chessboard using computer vision (OpenCV), processes the board state, determines the best move using the Stockfish chess engine, and physically moves the chess pieces using servo motors with precise coordination.

This interactive robot is not only entertaining but also serves as an educational platform for understanding robotics, AI, computer vision, and IoT.

# Project Preview
![Picture4](https://github.com/user-attachments/assets/90dea4a9-a18e-4ac5-a4fd-5c36b4fc67e4)

# ✅ Features
**♟️Fully Automated Gameplay** – Real-time move analysis and execution on a physical board

**📷Computer Vision -** OpenCV used to detect piece positions on the board

**🧠Stockfish Chess Engine -** Calculates best moves dynamically using AI

**🤖Robotic Arm Control -** 6 Servo Motors simulate human-like movement

**🧩Raspberry Pi Powered -** Compact, efficient, and cost-effective control unit

**🎮User-Friendly GUI -** Built with Tkinter for manual input and move visualization

**📝Modular Design -** Easily upgradable with ML-based detection or voice controls

**🔁Educational Value -** Demonstrates real-world applications of embedded systems, robotics, and vision systems

# Circuit Diagram
<img width="934" height="471" alt="Picture1" src="https://github.com/user-attachments/assets/4e57ed02-aafa-434b-bf86-39c94ac5d727" />


# 🔩 Hardware Requirements
| Component          | Specification           |
| ------------------ | ----------------------- |
| Raspberry Pi 4B    | 4GB RAM, 40 GPIO pins   |
| Robotic Arm        | 6 DOF (MG995 + MG90S)   |
| Webcam             | HD (720p or higher)     |
| PCA9685 PWM Driver | 16-Channel Servo Driver |
| SMPS               | 5V, 10A                 |
| Chessboard         | Standard 8x8 board      |

# 💻 Software & Tools
**Language**: Python 3

**Libraries & Frameworks:**

**OpenCV** – Image processing

**python-chess** – Board state management

**Stockfish** – Move computation

**NumPy, GPIOZero, pigpio** – Servo and logic control

**Tkinter** – GUI interface

**Platform:** Raspbian OS (on Raspberry Pi)

**IDE:** Thonny / VS Code

**Other Tools:** JSON for square-to-angle mapping

# 🔄 System Flow
Start New Game via GUI

Camera Calibrates to Empty Board

User Places Pieces and Selects Quadrants

Webcam Captures Moves

OpenCV Detects Current Positions

Stockfish Computes Best Move

Raspberry Pi Translates Move into Servo Coordinates

Robotic Arm Executes Move

Loop Until Checkmate or Game End

# 🧠 Technologies Used
**IoT & Embedded Systems** – Raspberry Pi, GPIO communication

**Artificial Intelligence** – Chess decision logic via Stockfish

**Computer Vision** – Real-time piece detection with OpenCV

**Robotics** – Pick-and-place execution using robotic arm

**Automation** – Minimal human intervention needed during gameplay

# 📸 Result Highlights

**Physical Prototypes**

![Picture3](https://github.com/user-attachments/assets/b29658f8-48d2-451a-b855-756fb69bdcce)
![Picture5](https://github.com/user-attachments/assets/f0a256d3-b977-462a-b22e-0164313b2f86)
<div>
  <img src="https://github.com/user-attachments/assets/32f1ea50-5429-4b3d-990c-cf004068fe47" height="300" style="margin-right: 25px;" />
  <img src="https://github.com/user-attachments/assets/918ee299-94ae-4fd9-a53b-66def1f5b436" height="300" />
</div>




**🖥️ GUI**

<div>
  <img src="https://github.com/user-attachments/assets/ed686caf-a273-454d-a960-c7f7e4b61d81" height="200" style="margin-right: 15px;" />
  <img src="https://github.com/user-attachments/assets/b4042bff-c5db-44fc-9f82-aea707487266" height="200" style="margin-right: 15px;" />
  <img src="https://github.com/user-attachments/assets/6a879a63-3535-435e-a112-ba9f1ed6c7fd" height="200" />
</div>

<br>

<div>
  <img src="https://github.com/user-attachments/assets/ab06eeb4-f267-4877-8459-18fece2bbda8" height="200" style="margin-right: 15px;" />
  <img src="https://github.com/user-attachments/assets/16babb6f-343d-477b-87a0-ca9ca2fff52a" height="200" />
</div>





# 👥 Project Team
Ritesh Mohanty
Email: riteshmohanty2003@gmail.com
LinkedIn | GitHub

Jyotismita Nath
Email: joytismitanath2003@gmail.com
LinkedIn | GitHub

Nikhilesh Kumar Mohanta, Sanjay Panigrahy, Aryan Mohanty, Nandita Satapathy, Nyayabrat Choudhury

# 🔮 Future Enhancements
ML-based advanced piece recognition

Touch-sensitive chessboard or magnetic feedback

Remote gameplay over cloud (via MQTT/HTTP dashboard)

Voice command or mobile app integration

Learning from previous games using data analytics
