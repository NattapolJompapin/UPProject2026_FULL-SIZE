from multiprocessing import Process, freeze_support
import os
import cv2
from ultralytics import YOLO
import time


# =========================================================
# CONFIG
# =========================================================

VIDEO_FOLDER = "camset"

MODEL_PATH = "best.pt"

CONF_THRES = 0.5


# =========================================================
# IP CAMERA
# =========================================================

IP_CAMERAS = {
    "CAM01": "http://10.50.10.100:8080/video",
}


# =========================================================
# อ่าน VIDEO จาก Folder
# =========================================================

video_files = [
    os.path.join(VIDEO_FOLDER, f)
    for f in os.listdir(VIDEO_FOLDER)
    if f.lower().endswith((".mp4", ".avi", ".mov"))
]


# =========================================================
# รวม IP CAM + VIDEO
# =========================================================

CAMERAS = {}

# เพิ่ม IP CAM
CAMERAS.update(IP_CAMERAS)


# เพิ่ม MP4
for i, video in enumerate(video_files, start=2):

    cam_id = f"CAM{i:02d}"

    CAMERAS[cam_id] = video


# =========================================================
# CAMERA WORKER
# =========================================================

def run_camera(camera_id, stream_url):

    print(f"[{camera_id}] Starting")
    print(f"[{camera_id}] Source: {stream_url}")

    # -----------------------------------------------------
    # Load YOLO
    # -----------------------------------------------------

    try:

        model = YOLO(MODEL_PATH)

    except Exception as e:

        print(f"[{camera_id}] Cannot load YOLO model")
        print(e)

        return


    # -----------------------------------------------------
    # Open Camera / Video
    # -----------------------------------------------------

    cap = cv2.VideoCapture(stream_url)

    if not cap.isOpened():

        print(f"[{camera_id}] ERROR: Cannot open source")
        print(f"[{camera_id}] {stream_url}")

        return


    # -----------------------------------------------------
    # Resizable Window
    # -----------------------------------------------------

    cv2.namedWindow(
        camera_id,
        cv2.WINDOW_NORMAL
    )

    # ขนาดเริ่มต้น
    cv2.resizeWindow(
        camera_id,
        800,
        600
    )


    print(f"[{camera_id}] Connected successfully")


    # ตรวจว่าเป็น IP CAM หรือ Video File
    is_ip_camera = stream_url.startswith("http://") or \
                   stream_url.startswith("https://") or \
                   stream_url.startswith("rtsp://")


    # -----------------------------------------------------
    # Loop
    # -----------------------------------------------------

    while True:

        ret, frame = cap.read()


        # -------------------------------------------------
        # ถ้าอ่านภาพไม่ได้
        # -------------------------------------------------

        if not ret:

            # IP CAM → reconnect
            if is_ip_camera:

                print(f"[{camera_id}] Connection lost")
                print(f"[{camera_id}] Reconnecting...")

                cap.release()

                time.sleep(2)

                cap = cv2.VideoCapture(stream_url)

                continue


            # Video → เล่นจบแล้วกลับไปเริ่มใหม่
            else:

                print(f"[{camera_id}] Video finished")

                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

                continue


        # -------------------------------------------------
        # YOLO
        # -------------------------------------------------

        results = model(
            frame,
            conf=CONF_THRES,
            verbose=False
        )


        # -------------------------------------------------
        # จำนวนคน
        # -------------------------------------------------

        passenger_count = len(results[0].boxes)


        # -------------------------------------------------
        # Draw
        # -------------------------------------------------

        annotated_frame = results[0].plot()


        # -------------------------------------------------
        # แสดง CAM + จำนวนคน
        # -------------------------------------------------

        frame_h, frame_w = annotated_frame.shape[:2]

        # ใช้ 1280 เป็นค่ามาตรฐาน
        scale_factor = frame_w / 1280

        font_scale = max(0.6, 1.0 * scale_factor)
        font_thickness = max(2, int(2 * scale_factor))

        cv2.putText(
            annotated_frame,
            f"{camera_id} | Passenger: {passenger_count}",
            (20, int(45 * scale_factor)),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (0, 255, 0),
            font_thickness,
            cv2.LINE_AA
        )


        # -------------------------------------------------
        # Show
        # -------------------------------------------------

        cv2.imshow(camera_id, annotated_frame)


        # -------------------------------------------------
        # Q = ปิด
        # -------------------------------------------------

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):

            break


    # -----------------------------------------------------
    # Cleanup
    # -----------------------------------------------------

    cap.release()

    cv2.destroyWindow(camera_id)

    print(f"[{camera_id}] Stopped")


# =========================================================
# PROCESS
# =========================================================

def start_camera_process(camera_id, stream_url):

    print(
        f"[+] Launching {camera_id} : {stream_url}"
    )

    p = Process(
        target=run_camera,
        args=(camera_id, stream_url),
        daemon=True
    )

    p.start()

    return p


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    freeze_support()


    print("=" * 60)
    print("      MULTI SOURCE YOLO DETECTION SYSTEM")
    print("=" * 60)


    # -----------------------------------------------------
    # แสดง Source ทั้งหมด
    # -----------------------------------------------------

    print("\n[CAMERA LIST]")

    for cam_id, source in CAMERAS.items():

        print(f"{cam_id} -> {source}")


    print()


    # -----------------------------------------------------
    # Start Processes
    # -----------------------------------------------------

    processes = []


    for cam_id, source in CAMERAS.items():

        p = start_camera_process(
            cam_id,
            source
        )

        processes.append(p)


    # -----------------------------------------------------
    # Wait
    # -----------------------------------------------------

    try:

        for p in processes:

            p.join()


    except KeyboardInterrupt:

        print("\n[!] Stopping all processes")


        for p in processes:

            if p.is_alive():

                p.terminate()

            p.join()


        print("[✓] System stopped")