# Contributing to FlightGear AutoTakeoff

First off, thank you for considering contributing to FlightGear AutoTakeoff! Community feedback, testing, and contributions are what make open-source projects great.

Because this is an experimental, amateur-developed script, all skill levels are welcome to help improve the project.

## 🎯 Current Priority Focus

We are currently actively working on runway alignment and lateral stability tracking. Contributions, ideas, or PRs in the following areas are especially appreciated:

- **Rudder & Nose-Wheel Correction** — refining the PD loops (`heading_pd`, `correct_heading_ground`) or correction algorithms to keep the aircraft centered on the runway during rollout.
- **Crosswind Handling** — improving lateral control when facing strong crosswinds.
- **Cross-Platform Keyboard Input** — the pilot override (`a` = abort, `m` = manual takeover) currently uses `msvcrt`, so the script only runs on Windows. Help wanted porting `read_key()` to a cross-platform approach (e.g. `termios`/`tty` on Linux/macOS, or a library like `keyboard`/`pynput`) so Mac and Linux users can run it too.
- **Aircraft Tuning** — testing baseline settings (`ROTATE_SPEED_KT`, `TARGET_PITCH_DEG`, PD gains) across different aircraft models in FlightGear.

## 🛠 How You Can Contribute

### 1. Reporting Bugs & Feedback

If you encounter issues during rollout, rotation, or climb-out:

1. Check the [Issues tab](https://github.com/TheDank/flightgear-autotakeoff/issues) to see if it has already been reported.
2. If not, open a New Issue.
3. Include relevant details:
   - Aircraft model used
   - FlightGear version
   - OS (Windows/Mac/Linux) and Python version
   - Telnet port/settings used (e.g. `--telnet=5500`)
   - Weather/wind conditions during testing
   - What went wrong (e.g., drift to the left, pitch instability, failure to rotate, abort triggered unexpectedly)
   - Relevant console output (speed/heading/pitch log lines printed during the run)

### 2. Suggesting Improvements

Have an idea for better flight dynamics, code structure, or extra features?

- Open an issue describing the feature and why it would be helpful.
- Join the discussion to help refine the idea!

### 3. Submitting Code Changes (Pull Requests)

If you want to write code or fix a bug yourself:

1. Fork the repository to your own GitHub account.
2. Create a new branch for your work:

   ```
   git checkout -b feature/improved-alignment
   ```

3. Set up FlightGear with the Telnet server enabled so you can test your changes:

   ```
   --telnet=5500
   ```

   and install the Python dependency:

   ```
   pip install flightgear_python
   ```

4. Make your changes, then test them end-to-end against a real FlightGear session — ground roll, rotation, and climb-out — on at least one aircraft. Always test with the `a` (abort) and `m` (manual) overrides to confirm they still work.
5. Commit your changes with a clear message, push your branch, and open a Pull Request against `main`.
6. In the PR description, mention:
   - What you changed and why
   - Aircraft/conditions you tested with
   - Any new or changed safety limits or constants

## 📜 License

By contributing, you agree that your contributions will be licensed under the project's [MIT License](https://github.com/TheDank/flightgear-autotakeoff/blob/main/LICENSE).

