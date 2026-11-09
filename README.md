# FlightGear AutoTakeoff

**FlightGear AutoTakeoff** is an experimental, amateur-developed flight control script by **TheDank** designed to automate the takeoff phase in the [FlightGear Flight Simulator](https://www.flightgear.org/). 

By interfacing directly with FlightGear's internal property tree and native autopilot channels, the script attempts to manage the full takeoff sequence—from initial taxi alignment through rotation to initial climb-out.

---

## 🛠 Project Status & Current Focus

> ⚠️ **Work in Progress:** This script is currently under active development and testing. 

* **Active Development Focus:** Refining the **runway alignment and lateral stability tracking system**. The primary goal is improving corrective rudder/steering logic to ensure the aircraft consistently realigns and stays centered along the runway heading during high-thrust ground roll.
* **Intended Scope:** Creating a lightweight, modular script that can execute smooth, repeatable takeoffs across various aircraft types in FlightGear.

---

## 🚀 Key Features

* **Runway Realignment & Steering:** Dynamically adjusts rudder and nose-wheel steering to track the runway centerline and correct drift before rotation.
* **Throttle Management:** Automatically advances throttle settings for smooth power delivery up to takeoff thrust.
* **Rotation Control ($V_r$):** Detects rotation speed and applies precise pitch commands to establish a target climb attitude.
* **Initial Climb-Out:** Transitions into a steady pitch-and-heading hold for clean separation and climb.

---

## 💡 How It Works

1. **Property Tree Integration:** Reads real-time flight telemetry (airspeed, heading, ground offset, pitch) straight from FlightGear.
2. **Control Corrections:** Computes steering inputs to maintain alignment during acceleration.
3. **Phase Execution:** Triggers automated pitch-up once rotation velocity is reached, followed by initial altitude transition.

---

## 🤝 Note from the Developer
This project was built out of enthusiasm for flight simulation control systems. Feedback, testing reports, and pull requests—especially regarding lateral tracking and alignment tuning—are welcome!
