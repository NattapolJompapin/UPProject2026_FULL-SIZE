from multiprocessing import Process, freeze_support
from camera_worker import run_camera


# -------------------------
# IP CAMERA CONFIG
# -------------------------

CAMERAS = {
    "CAM01": "http://10.50.10.100:8080/video",
}


# -------------------------
def start_camera_process(camera_id, stream_url):

    print(f"[+] Launching {camera_id} : {stream_url}")

    p = Process(
        target=run_camera,
        args=(camera_id, stream_url),
        daemon=True
    )

    p.start()

    return p


# -------------------------
if __name__ == "__main__":

    freeze_support()

    print("[@] Starting IP Camera detection system")

    processes = []

    for cam_id, url in CAMERAS.items():

        p = start_camera_process(cam_id, url)

        processes.append(p)

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