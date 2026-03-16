# ECOnet Swarm Robotics Architecture

## 1. Purpose
ECOnet is a distributed swarm robotics system designed for large‑scale environmental cleanup using hundreds to thousands of small autonomous robots. Each robot is inexpensive, semi‑autonomous, and capable of cooperating with others without a central controller.

Primary task example: collection of small waste items such as cigarette butts in urban environments.

The system must:
- scale to 100–5000 robots
- tolerate failures
- operate outdoors
- minimize infrastructure

---

# 2. Robot Physical Platform

## 2.1 Chassis

Dimensions:
- Length: 25–35 cm
- Width: 20–25 cm
- Height: 15–20 cm

Weight target:
- 3–5 kg

Drive:
- 4 wheel differential drive
- rubber off‑road wheels

Motors:
- 4× 12V DC gear motors
- torque ≥ 8 kg·cm

Motor driver:
- dual H‑bridge drivers (DRV8871 / BTS7960)

Speed:
- 0–1 m/s

---

## 2.2 Manipulator Arm

Degrees of freedom:
- Base rotation
- Shoulder
- Elbow
- Wrist

Total: 4 DOF

Actuators:
- smart servo motors (Dynamixel XL330 or equivalent)

End effector:
- small two‑finger gripper

Grip force:
- 1–2 kg

Pickup cycle time:
- ~3 seconds

---

# 3. Sensors

## 3.1 Vision

Primary camera:
- 1080p global shutter
- 60 FPS

Recommended modules:
- Raspberry Pi HQ camera
- Intel RealSense D435

Vision tasks:
- object detection (cigarette butts)
- obstacle detection


## 3.2 Navigation Sensors

IMU:
- MPU9250 or BNO085

Wheel encoders:
- 1024 CPR

Optional GPS:
- u‑blox NEO‑M8N

Accuracy:
- 1–2 meters


## 3.3 Proximity Sensors

Front lidar:
- RPLidar A1

Range:
- 12 meters

Ultrasonic sensors:
- 4× HC‑SR04

Purpose:
- collision avoidance

---

# 4. Compute Architecture

Each robot uses a **two‑layer compute model**.

## 4.1 Low Level Controller

Microcontroller:
- STM32

Responsibilities:
- motor control
- servo control
- sensor reading

Control frequency:
- 200–500 Hz


## 4.2 High Level Computer

Edge computer:

Options:
- Raspberry Pi 5
- Nvidia Jetson Orin Nano

Responsibilities:
- vision
- swarm protocol
- mapping
- planning

RAM:
- 8–16 GB

---

# 5. Communication Network

ECOnet robots form a **mesh network**.

## 5.1 Radio

Primary:
- WiFi 6 mesh

Alternative:
- ESP‑Now

Range:
- 50–120 m


## 5.2 Protocol

Custom lightweight protocol.

Packet structure:

Header
Robot ID
Position
Task state
Local map hash
Energy level

Packet size:
< 200 bytes

Frequency:
2–5 Hz

---

# 6. Swarm Coordination Model

Key concept: **local decision making**.

No global controller.

Robots coordinate using:

1. local maps
2. task tokens
3. density estimation


## 6.1 Task Token System

When a robot detects trash:

1. generate token
2. broadcast location
3. nearest robot claims

Timeout:
10 seconds

Prevents duplication.


## 6.2 Area Partitioning

Environment divided into virtual grid.

Cell size:

1–2 meters

Each robot maintains:

visited score
trash probability

Robots prefer cells with:

high trash probability
low robot density


## 6.3 Density Control

Robots estimate neighbor density:

n = robots detected within radius r

If density > threshold:

robot moves to low density region.

---

# 7. Vision System

Object detection model:

YOLOv8‑nano

Training dataset:

50k images of cigarette butts

Inference time:

10–20 ms


## Detection Pipeline

Camera frame

↓

Neural network

↓

Bounding box

↓

Ground projection

↓

Pickup target

---

# 8. Navigation

Navigation stack:

SLAM + reactive avoidance


## 8.1 SLAM

Algorithm:

ORB‑SLAM3

or

RTAB‑Map


## 8.2 Local Planner

Dynamic Window Approach


## 8.3 Obstacle Avoidance

Using:

lidar

ultrasonic sensors


---

# 9. Energy System

Battery:

Lithium‑ion

Capacity:

200 Wh

Runtime:

4–6 hours


## Charging

Autonomous docking station.

Charging power:

100 W

Charge time:

2 hours


---

# 10. Waste Storage

Internal container:

volume: 1 liter

Capacity:

500 cigarette butts

When full:

robot returns to base.


---

# 11. Software Stack

Operating system:

Ubuntu + ROS2


## Main modules

Perception
Navigation
Swarm coordination
Energy management
Manipulator control


---

# 12. Swarm Scaling

System performance:

100 robots → city block

500 robots → district

1000 robots → small city


Communication load per robot:

<10 KB/s


---

# 13. Manufacturing Cost Target

Target price per robot:

$700–1200

Breakdown:

Chassis and motors $200
Electronics $250
Manipulator $250
Battery $150


---

# 14. Deployment

Deployment procedure:

1. robots unloaded
2. base station started
3. robots self organize
4. swarm spreads automatically


---

# 15. Key Advantages

Fully decentralized

Scales linearly

Fault tolerant

Low infrastructure


---

# 16. Future Improvements

Better manipulation

Trash classification

Recycling sorting


---

END DOCUMENT

