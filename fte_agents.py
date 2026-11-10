import math
import time
import msvcrt
from flightgear_python.fg_if import TelnetConnection

conn = TelnetConnection("127.0.0.1", 5500)
conn.connect()

ROTATE_SPEED_KT = 120
TARGET_CLIMB_AGL_FT = 500
TARGET_PITCH_DEG = 15

# --- Safety limits (auto abort) ---
MAX_HDG_ERR_GROUND = 12.0   # deg, keluar jalur runway
MAX_HDG_ERR_AIR = 25.0      # deg
MAX_XTRACK_M = 15.0         # meter dari garis tengah (di darat)
MAX_ROLL_DEG = 30.0
MAX_PITCH_DEG = 25.0
MIN_AIR_SPEED_KT = 90.0     # di udara, di bawah ini = bahaya stall

# --- Tombol keyboard ---
KEY_ABORT = "a"    # abort: darat = throttle idle + rem, udara = serahkan ke pilot
KEY_MANUAL = "m"   # manual: lepas semua kontrol, pilot ambil alih


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


def get_lat():
    return conn.get_prop("/position/latitude-deg")


def get_lon():
    return conn.get_prop("/position/longitude-deg")


def get_mag_heading():
    return conn.get_prop("/orientation/heading-magnetic-deg")


def on_ground():
    """Deteksi darat pakai weight-on-wheels; fallback ke AGL."""
    try:
        v = conn.get_prop("/gear/gear[0]/wow")
        if isinstance(v, str):
            return v.strip().lower() in ("true", "1")
        return bool(v)
    except Exception:
        return get_agl() < 10


def neutral_controls():
    conn.set_prop("/controls/flight/elevator", 0.0)
    conn.set_prop("/controls/flight/rudder", 0.0)
    conn.set_prop("/controls/flight/aileron", 0.0)


def read_key():
    """Non-blocking: kembalikan satu karakter kalau ada tombol ditekan."""
    if msvcrt.kbhit():
        return msvcrt.getwch().lower()
    return None


def manual_takeover(reason):
    """Lepas semua kontrol otomatis. Throttle dibiarkan, pilot yang atur."""
    neutral_controls()
    print(f"\n[MANUAL TAKEOVER] {reason}")
    print("Autopilot lepas kontrol. Pilot, kamu yang terbang sekarang.")


def abort_takeoff(reason, airborne):
    print(f"\n[ABORT] {reason}")
    # Cek ulang saat ini juga: roda masih nempel (masih rotate di runway) = abort darat.
    if airborne and (on_ground() or get_agl() < 5):
        airborne = False
    if airborne:
        # Di udara tidak bisa dibatalkan: serahkan ke pilot, jangan matikan engine.
        neutral_controls()
        print("Sudah di udara: kontrol dilepas, pilot ambil alih. Throttle TIDAK diubah.")
    else:
        for i in range(3):
            conn.set_prop(f"/controls/engines/engine[{i}]/throttle", 0.0)
        neutral_controls()
        # Turunkan hidung kalau lagi rotate (elevator positif = nose down)
        conn.set_prop("/controls/flight/elevator", 0.15 if get_pitch() > 2 else 0.0)
        conn.set_prop("/controls/gear/brake-left", 1.0)
        conn.set_prop("/controls/gear/brake-right", 1.0)
        conn.set_prop("/controls/flight/speedbrake", 1.0)
        print("Throttle idle, rem ON, speedbrake ON. Pilot: reverse thrust manual kalau perlu.")


def auto_takeoff():
    print("[AUTO-TAKEOFF] Starting roll...")
    print(f"Tekan '{KEY_ABORT}' = ABORT | '{KEY_MANUAL}' = MANUAL takeover (kapan saja)")

    # Garis tengah runway = garis lurus dari posisi start sepanjang heading start.
    # Pastikan pesawat sudah sejajar di tengah runway sebelum menekan Enter.
    target_heading = get_heading()
    lat0, lon0 = get_lat(), get_lon()
    print(f"Target heading locked: {target_heading:.1f} deg (true) | "
          f"magnetic: {get_mag_heading():.1f} deg (angka ini yang tampil di FlightGear)")

    for i in range(3):
        conn.set_prop(f"/controls/engines/engine[{i}]/throttle", 1.0)

    conn.set_prop("/controls/flight/flaps", 0.33)
    conn.set_prop("/controls/gear/brake-parking", 0)

    prev_rudder = 0
    prev_aileron = 0
    prev_err = 0.0
    prev_t = time.time()
    d_filt = 0.0  # laju perubahan error (deg/s), sudah di-filter

    # PD: Kp kecil, Kd meredam goyangan kiri-kanan
    KP_GROUND, KD_GROUND, MAX_RUD_GROUND = 0.010, 0.025, 0.15
    KP_AIR, KD_AIR, MAX_RUD_AIR = 0.008, 0.030, 0.15

    KX = 0.8          # deg heading koreksi per meter melenceng
    MAX_XT_CORR = 4.0  # deg, batas koreksi heading dari cross-track
    KIX = 0.05        # integral cross-track (deg per meter*detik)
    MAX_IX = 2.0
    ix = 0.0
    last_xt = 0.0
    last_xt_t = time.time()

    def cross_track():
        """Jarak ke garis tengah (meter). Positif = di kanan garis."""
        lat, lon = get_lat(), get_lon()
        dn = (lat - lat0) * 111320.0
        de = (lon - lon0) * 111320.0 * math.cos(math.radians(lat0))
        h = math.radians(target_heading)
        return de * math.cos(h) - dn * math.sin(h)

    def heading_error():
        """Error terhadap heading yang diinginkan (sudah termasuk koreksi ke garis tengah)."""
        nonlocal ix, last_xt, last_xt_t
        xt = cross_track()
        now = time.time()
        ix = max(-MAX_IX, min(MAX_IX, ix + KIX * xt * (now - last_xt_t)))
        last_xt, last_xt_t = xt, now
        corr = max(-MAX_XT_CORR, min(MAX_XT_CORR, KX * xt + ix))
        desired = target_heading - corr  # di kanan garis -> belok kiri
        hdg = get_heading()
        return (desired - hdg + 540) % 360 - 180

    def heading_pd(kp, kd, max_rud):
        """PD tanpa deadband (deadband bikin limit-cycle kiri-kanan)."""
        nonlocal prev_err, prev_t, d_filt
        err = heading_error()
        now = time.time()
        dt = max(now - prev_t, 1e-3)
        raw_d = (err - prev_err) / dt
        d_filt = 0.7 * d_filt + 0.3 * raw_d  # low-pass supaya tidak noisy
        prev_err, prev_t = err, now
        cmd = kp * err + kd * d_filt
        return err, max(-max_rud, min(max_rud, cmd))

    def correct_heading_ground():
        """Di darat: cuma rudder, PD, slew-rate dibatasi."""
        nonlocal prev_rudder
        err, rudder_cmd = heading_pd(KP_GROUND, KD_GROUND, MAX_RUD_GROUND)

        max_change = 0.03
        rudder_cmd = prev_rudder + max(-max_change, min(max_change, rudder_cmd - prev_rudder))
        prev_rudder = rudder_cmd

        conn.set_prop("/controls/flight/rudder", rudder_cmd)
        return err, rudder_cmd

    def correct_heading_air():
        """Di udara: rudder PD + aileron jaga sayap level."""
        nonlocal prev_rudder, prev_aileron
        err, rudder_cmd = heading_pd(KP_AIR, KD_AIR, MAX_RUD_AIR)
        roll = get_roll()
        aileron_cmd = max(-0.15, min(0.15, 0.01 * (-roll)))

        max_change = 0.03
        rudder_cmd = prev_rudder + max(-max_change, min(max_change, rudder_cmd - prev_rudder))
        aileron_cmd = prev_aileron + max(-max_change, min(max_change, aileron_cmd - prev_aileron))
        prev_rudder, prev_aileron = rudder_cmd, aileron_cmd

        conn.set_prop("/controls/flight/rudder", rudder_cmd)
        conn.set_prop("/controls/flight/aileron", aileron_cmd)
        return err, rudder_cmd, aileron_cmd

    def check_pilot_keys(airborne):
        """Return True kalau pilot minta stop (abort/manual)."""
        key = read_key()
        if key == KEY_ABORT:
            abort_takeoff("Pilot menekan tombol ABORT", airborne)
            return True
        if key == KEY_MANUAL:
            manual_takeover("Pilot menekan tombol MANUAL")
            return True
        return False

    def check_safety(airborne, hdg_err):
        """Return alasan abort kalau ada kondisi berbahaya, else None."""
        roll = get_roll()
        pitch = get_pitch()
        if abs(roll) > MAX_ROLL_DEG:
            return f"Roll {roll:.1f} melebihi batas {MAX_ROLL_DEG}"
        if pitch > MAX_PITCH_DEG:
            return f"Pitch {pitch:.1f} melebihi batas {MAX_PITCH_DEG}"
        if airborne:
            if abs(hdg_err) > MAX_HDG_ERR_AIR:
                return f"Heading error {hdg_err:.1f} melebihi batas {MAX_HDG_ERR_AIR}"
            speed = get_airspeed()
            if speed < MIN_AIR_SPEED_KT:
                return f"Speed {speed:.0f}kt di bawah minimum {MIN_AIR_SPEED_KT}"
        else:
            if abs(hdg_err) > MAX_HDG_ERR_GROUND:
                return f"Melenceng dari runway: error {hdg_err:.1f} > {MAX_HDG_ERR_GROUND}"
            if abs(last_xt) > MAX_XTRACK_M:
                return f"Melenceng dari garis tengah {last_xt:.1f} m > {MAX_XTRACK_M} m"
        return None

    # --- Ground roll ---
    timeout = time.time() + 60
    while time.time() < timeout:
        if check_pilot_keys(airborne=False):
            return False
        speed = get_airspeed()
        err, rud = correct_heading_ground()
        reason = check_safety(False, err)
        if reason:
            abort_takeoff(reason, airborne=False)
            return False
        print(f"Speed: {speed:.1f}kt | HdgErr: {err:.1f} | XTrack: {last_xt:+.1f}m | Rudder: {rud:.3f}")
        if speed >= ROTATE_SPEED_KT:
            break
        time.sleep(0.05)
    else:
        abort_takeoff("Speed tidak cukup (timeout)", airborne=False)
        return False

    # --- Rotate + climb ---
    print("[AUTO-TAKEOFF] Rotating smoothly...")
    Kp_pitch = 0.03
    MAX_ELEVATOR = 0.3
    prev_elevator = 0
    prev_elev_t = time.time()
    ELEV_RATE_PER_SEC = 0.25  # elevator berubah max 0.25 per detik
    airborne = False

    timeout = time.time() + 45
    while time.time() < timeout:
        if check_pilot_keys(airborne):
            return False

        agl = get_agl()
        pitch = get_pitch()
        speed = get_airspeed()

        pitch_error = TARGET_PITCH_DEG - pitch
        elevator_cmd = max(-MAX_ELEVATOR, min(MAX_ELEVATOR, Kp_pitch * pitch_error))
        # Slew berdasarkan waktu nyata (loop telnet lambat, jadi jangan per-iterasi)
        now_e = time.time()
        max_change = ELEV_RATE_PER_SEC * min(now_e - prev_elev_t, 0.5)
        prev_elev_t = now_e
        elevator_cmd = prev_elevator + max(-max_change, min(max_change, elevator_cmd - prev_elevator))
        prev_elevator = elevator_cmd
        conn.set_prop("/controls/flight/elevator", -elevator_cmd)

        if not on_ground():
            airborne = True

        if airborne:
            hdg_err, rud, ail = correct_heading_air()
        else:
            hdg_err, rud = correct_heading_ground()
            ail = 0

        # Setelah rotate speed, auto-abort di darat DIMATIKAN (sudah lewat titik aman
        # untuk berhenti). Abort manual (tombol 'a') tetap aktif. Auto-abort cuma
        # untuk kondisi di udara -> serah-terima kontrol ke pilot.
        if airborne:
            reason = check_safety(True, hdg_err)
            if reason:
                abort_takeoff(reason, True)
                return False

        print(f"Speed: {speed:.1f}kt | Pitch: {pitch:.1f} | AGL: {agl:.0f}ft | HdgErr: {hdg_err:.1f} | XTrack: {last_xt:+.1f}m | Elev: {elevator_cmd:.3f} | Rud: {rud:.3f} | Ail: {ail:.3f}")

        if agl >= TARGET_CLIMB_AGL_FT:
            print("[CLIMB TARGET REACHED]")
            break
        time.sleep(0.05)

    neutral_controls()
    conn.set_prop("/controls/gear/gear-down", False)
    conn.set_prop("/controls/flight/flaps", 0.0)

    print("[AUTO-TAKEOFF] Complete.")
    return True


if __name__ == "__main__":
    input("Pastikan engine running manual, lalu tekan Enter untuk auto-takeoff...")
    auto_takeoff()
