# Contributing to FlightGear AutoTakeoff

First off, thank you for considering contributing to **FlightGear AutoTakeoff**! Community feedback, testing, and contributions are what make open-source projects great.

Because this is an experimental, amateur-developed script, all skill levels are welcome to help improve the project.

---

## 🎯 Current Priority Focus

We are currently actively working on **runway alignment and lateral stability tracking**. Contributions, ideas, or PRs in the following areas are especially appreciated:

- **Rudder & Nose-Wheel Correction:** Refining PID loops or correction algorithms to keep the aircraft centered on the runway during rollout.
- **Crosswind Handling:** Improving lateral control when facing strong crosswinds.
- **Aircraft Tuning:** Testing baseline settings across different aircraft models in FlightGear.

---

## 🛠 How You Can Contribute

### 1. Reporting Bugs & Feedback
If you encounter issues during rollout, rotation, or climb-out:
1. Check the [Issues tab](https://github.com/TheDank/flightgear-autotakeoff/issues) to see if it has already been reported.
2. If not, open a **New Issue**.
3. Include relevant details:
   - Aircraft model used
   - FlightGear version
   - Weather/wind conditions during testing
   - What went wrong (e.g., drift to the left, pitch instability, failure to rotate)

### 2. Suggesting Improvements
Have an idea for better flight dynamics, code structure, or extra features?
- Open an issue describing the feature and why it would be helpful.
- Join the discussion to help refine the idea!

### 3. Submitting Code Changes (Pull Requests)
If you want to write code or fix a bug yourself:
1. **Fork** the repository to your own GitHub account.
2. Create a new branch for your work:
   ```bash
   git checkout -b feature/improved-alignment
