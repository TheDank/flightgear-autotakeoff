# FlightGear AutoTakeoff

FlightGear AutoTakeoff is an experimental, amateur-developed flight control script by TheDank designed to automate the takeoff phase in the [FlightGear Flight Simulator](https://www.flightgear.org/).

It connects to FlightGear over its **Telnet property-tree interface** (via the [`flightgear_python`](https://pypi.org/project/flightgear-python/) library) and manages the full takeoff sequence — runway alignment, throttle, rotation, and initial climb-out — while giving the pilot a live keyboard override at every stage.

## ⚠️ Project Status & Current Focus

**Work in Progress:** this script is under active development and testing.

- **Active Development Focus:** refining the runway alignment and lateral stability tracking system (PD heading control + cross-track correction) so the aircraft reliably realigns and stays centered on the runway heading during high-thrust ground roll.
- **Intended Scope:** a lightweight, modular script that executes smooth, repeatable takeoffs across different aircraft types in FlightGear.

## 🔌 Connecting to FlightGear

1. Enable FlightGear's Telnet server. In the launcher, go to **Settings → Additional Settings**, and add:
   ```
   --telnet=5500
   ```
2. Click **Fly!** and let the aircraft fully load on the runway, aligned with the centerline.
3. Install the Python dependency:
   ```
   pip install flightgear_python
   ```
4. Run the script:
   ```
   python autotakeoff.py
   ```
   It connects to `127.0.0.1:5500`, locks the current heading as the runway centerline, and waits for Enter to start the roll.

> **Note:** the script currently uses `msvcrt` for non-blocking keyboard input, so it runs on **Windows only**. See [Contributing](CONTRIBUTING.md) if you'd like to help add cross-platform key handling.

## 🚀 Key Features

- **Runway Realignment & Steering** — PD controller on heading error, plus a cross-track (centerline distance) term computed from GPS lat/lon, dynamically corrects rudder and nose-wheel steering during the ground roll.
- **Throttle Management** — advances all engines to takeoff thrust at roll start.
- **Rotation Control (Vr)** — monitors airspeed against a configurable rotate speed (`ROTATE_SPEED_KT`) and applies a rate-limited elevator command toward a target pitch (`TARGET_PITCH_DEG`).
- **Initial Climb-Out** — holds pitch and heading (rudder + aileron-for-wings-level) until a target AGL altitude (`TARGET_CLIMB_AGL_FT`) is reached.
- **Live Safety Monitor** — continuously checks roll, pitch, heading error, cross-track distance, and minimum airspeed; auto-aborts on exceeding configured limits.
- **Pilot Override, Always-On:**
  - Press **`a`** — **Abort.** On the ground: throttle idle, brakes + speedbrake on. In the air: hands control back to the pilot without touching throttle.
  - Press **`m`** — **Manual takeover.** Immediately neutralizes all automated control inputs.

## 💡 How It Works

1. **Property Tree Integration** — reads live telemetry (airspeed, heading, magnetic heading, pitch, roll, lat/lon, AGL, weight-on-wheels) directly from FlightGear's property tree over Telnet.
2. **Control Corrections** — computes rate-limited rudder, aileron, and elevator commands each loop using PD control on heading/pitch error, with a low-pass filter on the derivative term to reduce noise-driven jitter.
3. **Phase Execution:**
   - **Ground roll** — hold centerline until rotate speed is reached (60s timeout).
   - **Rotate + climb** — pitch up smoothly, detect liftoff via weight-on-wheels/AGL, switch to airborne heading/roll control, climb to target altitude (45s timeout).
4. **Safety limits are configurable** at the top of the script (`MAX_HDG_ERR_GROUND`, `MAX_HDG_ERR_AIR`, `MAX_XTRACK_M`, `MAX_ROLL_DEG`, `MAX_PITCH_DEG`, `MIN_AIR_SPEED_KT`).

## 📜 License & Contributing

- **License:** this project is licensed under the [MIT License](https://github.com/TheDank/flightgear-autotakeoff/blob/main/LICENSE).
- **Contributing:** want to help improve runway alignment or flight stability? Check out our [Contributing Guidelines](https://github.com/TheDank/flightgear-autotakeoff/blob/main/CONTRIBUTING.md) to get started!

## 🤝 Note from the Developer

This project was built out of enthusiasm for flight simulation control systems. Feedback, testing reports, and pull requests — especially regarding lateral tracking and alignment tuning — are welcome!

