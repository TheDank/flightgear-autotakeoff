import time
from flightgear_python.fg_if import TelnetConnection

conn = TelnetConnection("127.0.0.1", 5500)
conn.connect()

ROTATE_SPEED_KT = 120
TARGET_CLIMB_AGL_FT = 500
TARGET_PITCH_DEG = 10
HDG_DEADBAND = 1.5  # derajat, di bawah ini tidak usah koreksi


def get_airspeed():
    return conn.get_prop("/velocities/airspeed-kt")


def get_agl():
    return conn.get_prop("/position/altitude-agl-ft")


def get_pitch():
    return conn.get_prop("/orientation/pitch-deg")


def get_heading():
    return conn.get_prop("/orientation/heading-deg")


def get_roll():
    return conn.get_prop("/orientation/roll-deg")


def auto_takeoff():
    print("[AUTO-TAKEOFF] Starting roll...")

    target_heading = get_heading()
    print(f"Target heading locked: {target_heading:.1f} deg")

    for i in range(3):
        conn.set_prop(f"/controls/engines/engine[{i}]/throttle", 1.0)

    conn.set_prop("/controls/flight/flaps", 0.33)
    conn.set_prop("/controls/gear/brake-parking", 0)

    prev_rudder = 0
    prev_aileron = 0

    def heading_error():
        hdg = get_heading()
        return (target_heading - hdg + 540) % 360 - 180

    def correct_heading_ground():
        """Dipakai pas masih di darat: cuma rudder, gain kecil, deadband, tanpa aileron."""
        nonlocal prev_rudder
        err = heading_error()

        if abs(err) < HDG_DEADBAND:
            rudder_cmd = 0.0
        else:
            rudder_cmd = max(-0.08, min(0.08, 0.004 * err))

        max_change = 0.01
        rudder_cmd = prev_rudder + max(-max_change, min(max_change, rudder_cmd - prev_rudder))
        prev_rudder = rudder_cmd

        conn.set_prop("/controls/flight/rudder", rudder_cmd)
        return err, rudder_cmd

    def correct_heading_air():
        """Dipakai pas udah di udara: rudder + aileron, gain lebih longgar."""
        nonlocal prev_rudder, prev_aileron
        err = heading_error()
        roll = get_roll()

        rudder_cmd = 0.0 if abs(err) < HDG_DEADBAND else max(-0.15, min(0.15, 0.008 * err))
        aileron_cmd = max(-0.15, min(0.15, 0.01 * (-roll)))

        max_change = 0.015
        rudder_cmd = prev_rudder + max(-max_change, min(max_change, rudder_cmd - prev_rudder))
        aileron_cmd = prev_aileron + max(-max_change, min(max_change, aileron_cmd - prev_aileron))
        prev_rudder, prev_aileron = rudder_cmd, aileron_cmd

        conn.set_prop("/controls/flight/rudder", rudder_cmd)
        conn.set_prop("/controls/flight/aileron", aileron_cmd)
        return err, rudder_cmd, aileron_cmd

    # --- Ground roll ---
    timeout = time.time() + 60
    while time.time() < timeout:
        speed = get_airspeed()
        err, rud = correct_heading_ground()
        print(f"Speed: {speed:.1f}kt | HdgErr: {err:.1f} | Rudder: {rud:.3f}")
        if speed >= ROTATE_SPEED_KT:
            break
        time.sleep(0.2)
    else:
        print("[ABORT] Speed tidak cukup.")
        return False

    # --- Rotate + climb ---
    print("[AUTO-TAKEOFF] Rotating smoothly...")
    Kp_pitch = 0.02
    MAX_ELEVATOR = 0.2
    prev_elevator = 0
    airborne = False

    timeout = time.time() + 45
    while time.time() < timeout:
        agl = get_agl()
        pitch = get_pitch()
        speed = get_airspeed()

        pitch_error = TARGET_PITCH_DEG - pitch
        elevator_cmd = max(-MAX_ELEVATOR, min(MAX_ELEVATOR, Kp_pitch * pitch_error))
        max_change = 0.02
        elevator_cmd = prev_elevator + max(-max_change, min(max_change, elevator_cmd - prev_elevator))
        prev_elevator = elevator_cmd
        conn.set_prop("/controls/flight/elevator", -elevator_cmd)

        if agl > 10:
            airborne = True

        if airborne:
            hdg_err, rud, ail = correct_heading_air()
        else:
            hdg_err, rud = correct_heading_ground()
            ail = 0

        print(f"Speed: {speed:.1f}kt | Pitch: {pitch:.1f} | AGL: {agl:.0f}ft | HdgErr: {hdg_err:.1f} | Elev: {elevator_cmd:.3f} | Rud: {rud:.3f} | Ail: {ail:.3f}")

        if agl >= TARGET_CLIMB_AGL_FT:
            print("[CLIMB TARGET REACHED]")
            break
        time.sleep(0.2)

    conn.set_prop("/controls/flight/elevator", 0.0)
    conn.set_prop("/controls/flight/rudder", 0.0)
    conn.set_prop("/controls/flight/aileron", 0.0)
    conn.set_prop("/controls/gear/gear-down", False)
    conn.set_prop("/controls/flight/flaps", 0.0)

    print("[AUTO-TAKEOFF] Complete.")
    return True


if __name__ == "__main__":
    input("Pastikan engine running manual, lalu tekan Enter untuk auto-takeoff...")
    auto_takeoff()
