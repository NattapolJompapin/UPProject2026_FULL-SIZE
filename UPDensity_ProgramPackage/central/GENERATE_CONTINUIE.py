import mysql.connector
from datetime import datetime, timedelta
import random
import time


# =========================================================
# CONFIG
# =========================================================

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "Chizo1412Za@",
    "database": "BusStop"
}

CAMERAS = [
    "CAM01",
    "CAM02",
    "CAM03",
    "CAM04"
]

# Generate ทุก ๆ 5 วินาที
INTERVAL_SECONDS = 5


# =========================================================
# ช่วงเวลาหนาแน่นของแต่ละกล้อง
# =========================================================

CAM_PEAK_TIMES = {

    "CAM01": [
        "07:30",
        "10:00",
        "13:00",
        "15:30"
    ],

    "CAM02": [
        "07:00",
        "10:00",
        "13:30",
        "15:30",
        "16:30"
    ],

    "CAM03": [
        "08:00",
        "10:00",
        "13:00",
        "15:00",
        "17:00"
    ],

    "CAM04": [
        "11:00",
        "13:30",
        "15:30",
        "17:30",
        "18:30"
    ]
}

PEAK_WINDOW_MIN = 25


# =========================================================
# Zero period
# =========================================================

ZERO_UNTIL = {
    cam: None
    for cam in CAMERAS
}


# =========================================================
# Daily Factor
# =========================================================

def get_daily_factor(date):

    weekday = date.weekday()
    # 0 = Monday
    # 5 = Saturday
    # 6 = Sunday

    # -------------------------
    # Weekend
    # -------------------------

    if weekday >= 5:

        base = random.uniform(
            0.5,
            0.8
        )

    # -------------------------
    # Weekday
    # -------------------------

    else:

        base = random.uniform(
            0.9,
            1.2
        )

    # -------------------------
    # Special random day
    # -------------------------

    event = random.random()

    # 10% คนน้อย
    if event < 0.1:

        base *= 0.5

    # 10% คนเยอะ
    elif event > 0.9:

        base *= 1.8

    return base


# =========================================================
# Peak Time Check
# =========================================================

def is_peak_time(
    camera_id,
    current_time
):

    for t in CAM_PEAK_TIMES[camera_id]:

        peak_time = datetime.strptime(
            t,
            "%H:%M"
        ).time()

        peak_dt = current_time.replace(

            hour=peak_time.hour,
            minute=peak_time.minute,
            second=0,
            microsecond=0

        )

        difference = abs(
            (
                current_time -
                peak_dt
            ).total_seconds()
        )

        if difference <= PEAK_WINDOW_MIN * 60:

            return True

    return False


# =========================================================
# Generate Passenger Count
# =========================================================

def generate_passenger_count(
    camera_id,
    current_time,
    factor
):

    global ZERO_UNTIL

    # -----------------------------------------------------
    # ยังอยู่ในช่วง Zero
    # -----------------------------------------------------

    if (
        ZERO_UNTIL[camera_id]
        and
        current_time <
        ZERO_UNTIL[camera_id]
    ):
        return 0


    # -----------------------------------------------------
    # สุ่มเริ่มช่วง Zero
    # -----------------------------------------------------

    if random.random() < 0.02:

        duration = random.randint(1, 4)

        ZERO_UNTIL[camera_id] = (
            current_time +
            timedelta(minutes=duration)
        )

        return 0


    hour = current_time.hour


    # -----------------------------------------------------
    # กลางคืน
    # -----------------------------------------------------

    if hour < 8 or hour >= 21:

        base = random.randint(
            15,
            20
        )


    # -----------------------------------------------------
    # Peak
    # -----------------------------------------------------

    elif is_peak_time(
        camera_id,
        current_time
    ):

        base = random.randint(
            25,
            54
        )


    # -----------------------------------------------------
    # เวลาปกติ
    # -----------------------------------------------------

    else:

        base = random.randint(
            15,
            27
        )


    # -----------------------------------------------------
    # Apply Daily Factor
    # -----------------------------------------------------

    value = int(
        base * factor
    )

    return max(
        0,
        value
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("=" * 60)
    print("🚀 REAL-TIME BUS DENSITY GENERATOR")
    print("=" * 60)

    print(
        f"📷 Cameras   : {', '.join(CAMERAS)}"
    )

    print(
        f"⏱️ Interval  : {INTERVAL_SECONDS} seconds"
    )

    print(
        f"🕐 Start     : "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    print(
        "🔄 Mode      : RUN FOREVER"
    )

    print(
        "🛑 Stop      : CTRL+C"
    )

    print("=" * 60)
    print()


    # =====================================================
    # Connect MySQL
    # =====================================================

    try:

        conn = mysql.connector.connect(
            **DB_CONFIG
        )

        cursor = conn.cursor()

        print("✅ Connected to MySQL")

    except mysql.connector.Error as err:

        print(
            f"❌ MySQL connection error: {err}"
        )

        return


    # =====================================================
    # Initial values
    # =====================================================

    cursor.execute("""
        SELECT MAX(CAST(SUBSTRING(DensityCount_ID, 3) AS UNSIGNED))
        FROM DensityCount
        WHERE DensityCount_ID LIKE 'DC%'
    """)

    result = cursor.fetchone()

    if result[0] is None:
        dc_num = 1
    else:
        dc_num = result[0] + 1

    current_day = None

    daily_factor = 1.0

    current_time = datetime.now()


    # =====================================================
    # RUN FOREVER
    # =====================================================

    try:

        while True:

            # -------------------------------------------------
            # ตรวจสอบวันใหม่
            # -------------------------------------------------

            if current_day != current_time.date():

                current_day = current_time.date()

                daily_factor = get_daily_factor(
                    current_day
                )

                print()
                print(
                    f"📅 New day: {current_day}"
                )

                print(
                    f"📊 Daily Factor: "
                    f"{daily_factor:.2f}"
                )

                print()


            # -------------------------------------------------
            # Generate CAM01-CAM04
            # -------------------------------------------------

            rows = []

            for cam in CAMERAS:

                count = generate_passenger_count(

                    cam,
                    current_time,
                    daily_factor

                )

                rows.append((

                    f"DC{dc_num:06d}",

                    cam,

                    count,

                    current_time

                ))

                dc_num += 1


            # -------------------------------------------------
            # Insert ลง MySQL ทันที
            # -------------------------------------------------

            cursor.executemany("""

                INSERT INTO DensityCount
                (
                    DensityCount_ID,
                    Camera_ID,
                    PassengerCount,
                    Timestamp
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s
                )

            """, rows)


            conn.commit()


            # -------------------------------------------------
            # แสดงผล
            # -------------------------------------------------

            print(

                f"🕐 "
                f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} | "

                f"CAM01 = {rows[0][2]:2d} | "
                f"CAM02 = {rows[1][2]:2d} | "
                f"CAM03 = {rows[2][2]:2d} | "
                f"CAM04 = {rows[3][2]:2d}"

            )


            # -------------------------------------------------
            # รอ 5 วินาที
            # -------------------------------------------------

            time.sleep(
                INTERVAL_SECONDS
            )


            # -------------------------------------------------
            # เอาเวลาปัจจุบันใหม่
            # -------------------------------------------------

            current_time = datetime.now()


    # =====================================================
    # Ctrl + C
    # =====================================================

    except KeyboardInterrupt:

        print()
        print()
        print("=" * 60)
        print("🛑 STOPPED BY USER")
        print("=" * 60)


    # =====================================================
    # Close MySQL
    # =====================================================

    finally:

        cursor.close()

        conn.close()

        print(
            "🔌 MySQL connection closed"
        )

        print(
            f"📦 Total generated rows: "
            f"{dc_num - 1:,}"
        )

        print(
            "👋 Generator stopped"
        )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    main()