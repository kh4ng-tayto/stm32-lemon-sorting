from ultralytics import YOLO
import cv2
import logging
import math
import os
import queue
import re
import serial
import serial.tools.list_ports
import threading
import time
from datetime import datetime

# =========================================================
# CAU HINH
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_CANDIDATES = (
    os.path.join(BASE_DIR, "best.pt"),
    os.path.join(BASE_DIR, "best .pt"),
)
MODEL_PATH = next(
    (path for path in MODEL_CANDIDATES if os.path.isfile(path)),
    MODEL_CANDIDATES[0],
)
MANUAL_COM_PORT = None       # Vi du: "COM4". De None de tu dong tim.
BAUD_RATE = 9600
USB_CAMERA_ID = 1          # Webcam USB thuong la 1. Neu khong mo duoc, thu 2 hoac 3.
USB_CAMERA_FALLBACK_IDS = (2, 0)
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CONFIDENCE = 0.60
IMAGE_SIZE = 320
# Bang chuyen di theo chieu doc tren khung hinh.
# Dat duong ngang nay TRUOC cam bien de gui ket qua som.
SORT_LINE_Y = 160

# Chieu di chuyen:
# "top_to_bottom" = tu tren xuong duoi
# "bottom_to_top" = tu duoi len tren
BELT_DIRECTION = "bottom_to_top"

TRIGGER_BAND = 18
MIN_STABLE_FRAMES = 3
CLASSIFICATION_SEND_COOLDOWN = 0.65
# Cau hinh thu nghiem chi cho phep mot san pham cho xu ly tren STM32.
MAX_STM_QUEUE = 1
STATUS_QUERY_INTERVAL = 1.5

CMD_GOOD = b"1"
CMD_BAD = b"2"
CMD_RESET = b"R"
CMD_QUERY = b"Q"

# Tu khoa dung de anh xa ten lop YOLO sang lenh UART.
GOOD_KEYWORDS = ("good", "fresh")
BAD_KEYWORDS = ("bad", "defective", "rotten")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


# =========================================================
# UART
# =========================================================

class UARTManager:
    STATUS_PATTERN = re.compile(r"G:(\d+)\s+B:(\d+)\s+Q:(\d+)")

    def __init__(self, port, baud_rate):
        self.port = port
        self.baud_rate = baud_rate
        self.ser = None
        self.connected = False
        self.good_count = 0
        self.bad_count = 0
        self.queue_count = 0
        self.last_send_time = 0.0
        self.last_classification_time = 0.0
        self.minimum_send_gap = 0.05
        self.last_write_end_perf = 0.0
        self.write_lock = threading.Lock()
        self.received_messages = queue.Queue()
        self.reader_stop = threading.Event()
        self.reader_thread = None

    def connect(self):
        if not self.port:
            return False

        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=0.02,
                write_timeout=0.2,
            )
            time.sleep(1.0)
            self.ser.reset_input_buffer()
            self.connected = True
            self.reader_stop.clear()
            self.reader_thread = threading.Thread(
                target=self._reader_loop,
                name="stm32-uart-reader",
                daemon=True,
            )
            self.reader_thread.start()
            logging.info("UART connected: %s", self.port)
            self.send(CMD_QUERY)
            return True
        except (serial.SerialException, OSError) as exc:
            logging.error("Cannot open UART %s: %s", self.port, exc)
            self.connected = False
            self.ser = None
            return False

    def send(self, command):
        """Gui dung mot byte lenh, khong gui kem \r hoac \n."""
        if not self.connected or self.ser is None:
            return False

        try:
            with self.write_lock:
                # Giu khoang cach ngan giua hai byte de tranh mat lenh.
                elapsed = time.perf_counter() - self.last_write_end_perf
                if elapsed < self.minimum_send_gap:
                    time.sleep(self.minimum_send_gap - elapsed)

                self.ser.write(command)
                self.ser.flush()
                self.last_write_end_perf = time.perf_counter()
                self.last_send_time = time.time()
            return True
        except (serial.SerialException, OSError) as exc:
            logging.error("UART send error: %s", exc)
            self.connected = False
            return False

    def poll(self):
        """Lay cac dong da duoc thread UART timestamp khi vua nhan xong."""
        messages = []
        while True:
            try:
                message, received_perf = self.received_messages.get_nowait()
            except queue.Empty:
                break

            messages.append((message, received_perf))
            match = self.STATUS_PATTERN.search(message)
            if match:
                self.good_count = int(match.group(1))
                self.bad_count = int(match.group(2))
                self.queue_count = int(match.group(3))

        return messages

    def _reader_loop(self):
        """Doc UART nen de khong chan vong lap xu ly camera."""
        buffer = bytearray()

        while not self.reader_stop.is_set():
            if not self.connected or self.ser is None:
                break

            try:
                waiting = self.ser.in_waiting
                chunk = self.ser.read(waiting if waiting > 0 else 1)
                if not chunk:
                    continue

                buffer.extend(chunk)
                while b"\n" in buffer:
                    raw, _, remainder = buffer.partition(b"\n")
                    buffer = bytearray(remainder)
                    message = raw.decode("utf-8", errors="ignore").strip()
                    if message:
                        self.received_messages.put(
                            (message, time.perf_counter())
                        )

            except (serial.SerialException, OSError) as exc:
                if not self.reader_stop.is_set():
                    logging.error("UART receive error: %s", exc)
                self.connected = False
                break

    def request_status(self):
        if time.time() - self.last_classification_time < 0.25:
            return False
        return self.send(CMD_QUERY)

    def send_classification(self, command):
        if not self.send(command):
            return False

        # Cap nhat tam thoi ngay sau khi gui de khong gui them san pham
        # truoc lan truy van trang thai ke tiep tu STM32.
        self.queue_count = min(self.queue_count + 1, MAX_STM_QUEUE)
        self.last_classification_time = time.time()
        return True

    def reset_system(self):
        if not self.connected or self.ser is None:
            return False

        while True:
            try:
                self.received_messages.get_nowait()
            except queue.Empty:
                break

        if not self.send(CMD_RESET):
            return False

        deadline = time.time() + 1.2
        while time.time() < deadline:
            for message, _ in self.poll():
                if message == "RESET_OK":
                    self.good_count = 0
                    self.bad_count = 0
                    self.queue_count = 0
                    logging.info("STM32 reset successful")
                    return True
            time.sleep(0.02)

        logging.warning("STM32 did not return RESET_OK")
        return False

    def close(self):
        self.reader_stop.set()
        if self.reader_thread is not None and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=0.2)
        if self.ser is not None and self.ser.is_open:
            self.ser.close()
        self.connected = False


# =========================================================
# TRACKING DON GIAN THEO TAM VAT THE
# =========================================================

class CentroidTracker:
    def __init__(self, max_distance=80, max_missing_frames=20):
        self.max_distance = max_distance
        self.max_missing_frames = max_missing_frames
        self.next_id = 1
        self.objects = {}

    def reset(self):
        self.next_id = 1
        self.objects.clear()

    def update(self, detections, frame_number):
        """
        Gan ID on dinh hon cho vat the bang khoang cach tam giua hai frame.
        detections la danh sach dict co cx, cy.
        """
        available_ids = set(self.objects.keys())

        # Uu tien detection co confidence cao.
        ordered = sorted(
            enumerate(detections),
            key=lambda item: item[1]["confidence"],
            reverse=True,
        )

        for _, detection in ordered:
            best_id = None
            best_distance = self.max_distance + 1

            for object_id in available_ids:
                old = self.objects[object_id]
                distance = math.hypot(
                    detection["cx"] - old["cx"],
                    detection["cy"] - old["cy"],
                )

                if distance < best_distance:
                    best_distance = distance
                    best_id = object_id

            if best_id is None or best_distance > self.max_distance:
                best_id = self.next_id
                self.next_id += 1
            else:
                available_ids.remove(best_id)

            previous = self.objects.get(best_id)
            detection["track_id"] = best_id
            detection["previous_y"] = previous["cy"] if previous else None

            if previous and previous.get("category") == detection["category"]:
                stable_frames = previous.get("stable_frames", 1) + 1
            else:
                stable_frames = 1

            detection["stable_frames"] = stable_frames

            self.objects[best_id] = {
                "cx": detection["cx"],
                "cy": detection["cy"],
                "category": detection["category"],
                "stable_frames": stable_frames,
                "last_seen": frame_number,
            }

        stale_ids = [
            object_id
            for object_id, value in self.objects.items()
            if frame_number - value["last_seen"] > self.max_missing_frames
        ]
        for object_id in stale_ids:
            del self.objects[object_id]

        return detections


# =========================================================
# HAM HO TRO
# =========================================================

def find_usb_uart_port():
    if MANUAL_COM_PORT:
        return MANUAL_COM_PORT

    keywords = ("usb serial", "usb-serial", "ch340", "cp210", "ftdi", "uart")
    ports = list(serial.tools.list_ports.comports())

    for port in ports:
        description = (port.description or "").lower()
        if any(keyword in description for keyword in keywords):
            return port.device

    return None


def open_camera():
    """
    Chi mo webcam USB ngoai. Khong thu camera 0 de tranh lay nham
    camera tich hop cua laptop.
    """
    camera_ids = (USB_CAMERA_ID,) + tuple(
        camera_id
        for camera_id in USB_CAMERA_FALLBACK_IDS
        if camera_id != USB_CAMERA_ID
    )

    for camera_id in camera_ids:
        cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)

        if not cap.isOpened():
            cap.release()
            logging.warning("Cannot open USB camera ID %s", camera_id)
            continue

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, 30)

        # Doc thu mot frame de chac chan camera USB hoat dong.
        success, _ = cap.read()
        if success:
            logging.info("USB camera opened: ID %s", camera_id)
            return cap

        cap.release()
        logging.warning("USB camera ID %s opened but returned no frame", camera_id)

    return None


def build_class_map(model_names):
    class_map = {}

    for class_id, class_name in model_names.items():
        normalized = str(class_name).lower()

        if any(keyword in normalized for keyword in GOOD_KEYWORDS):
            class_map[int(class_id)] = (CMD_GOOD, "GOOD")
        elif any(keyword in normalized for keyword in BAD_KEYWORDS):
            class_map[int(class_id)] = (CMD_BAD, "BAD")

    return class_map


def is_crossing_line(previous_y, current_y, line_y):
    """Kiem tra vat the cat duong ngang theo dung chieu bang chuyen."""
    inside_band = abs(current_y - line_y) <= TRIGGER_BAND

    if previous_y is None:
        return inside_band

    if BELT_DIRECTION == "bottom_to_top":
        crossed = previous_y > line_y >= current_y
    else:
        crossed = previous_y < line_y <= current_y

    return crossed or inside_band


def draw_panel(frame, uart, fps, local_good, local_bad):
    height, width = frame.shape[:2]

    # Nen mo de thong tin de doc nhung khong che camera qua nhieu.
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (width, 82), (20, 20, 20), -1)
    cv2.rectangle(overlay, (0, height - 34), (width, height), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.70, frame, 0.30, 0, frame)

    if uart.connected:
        good = uart.good_count
        bad = uart.bad_count
        queue = str(uart.queue_count)
        uart_text = f"UART {uart.port}: ONLINE"
        uart_color = (80, 220, 80)
    else:
        good = local_good
        bad = local_bad
        queue = "--"
        uart_text = "UART: OFFLINE"
        uart_color = (60, 60, 255)

    cv2.putText(
        frame,
        "LEMON SORTING",
        (14, 29),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.72,
        (255, 255, 255),
        2,
    )

    uart_size = cv2.getTextSize(
        uart_text, cv2.FONT_HERSHEY_SIMPLEX, 0.50, 1
    )[0]
    cv2.putText(
        frame,
        uart_text,
        (max(14, width - uart_size[0] - 14), 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.50,
        uart_color,
        1,
    )

    info = f"GOOD: {good}    BAD: {bad}    QUEUE: {queue}    FPS: {fps:.1f}"
    cv2.putText(
        frame,
        info,
        (14, 62),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.56,
        (255, 255, 255),
        1,
    )

    controls = "Q/ESC: Exit     R: Reset     S: Save image"
    cv2.putText(
        frame,
        controls,
        (14, height - 11),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (230, 230, 230),
        1,
    )


def draw_notice(frame, text):
    if not text:
        return

    height, width = frame.shape[:2]
    size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2)[0]
    x = max(10, (width - size[0]) // 2)
    y = max(115, height // 2)

    cv2.rectangle(
        frame,
        (x - 12, y - size[1] - 12),
        (x + size[0] + 12, y + 10),
        (20, 20, 20),
        -1,
    )
    cv2.putText(
        frame,
        text,
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (255, 255, 255),
        2,
    )


# =========================================================
# MAIN
# =========================================================

def main():
    # Model
    try:
        model = YOLO(MODEL_PATH)
    except Exception as exc:
        logging.error("Cannot load model '%s': %s", MODEL_PATH, exc)
        return

    class_map = build_class_map(model.names)
    if not class_map:
        logging.error("No Good/Bad class found. Model classes: %s", model.names)
        return

    logging.info("Class mapping: %s", class_map)

    # UART
    com_port = find_usb_uart_port()
    uart = UARTManager(com_port, BAUD_RATE)
    uart.connect()

    if com_port is None:
        logging.warning("USB-UART not found. Running without STM32.")

    # Camera
    cap = open_camera()
    if cap is None:
        logging.error("Cannot open USB camera. Try changing USB_CAMERA_ID to 2 or 3.")
        uart.close()
        return

    tracker = CentroidTracker()
    sent_track_ids = set()
    # Ghi nho vat da cat SEND LINE de khong bi bo sot neu luc cat line
    # stable/cooldown/queue chua san sang.
    crossed_track_ids = set()

    local_good = 0
    local_bad = 0
    frame_number = 0
    last_frame_time = time.time()
    smooth_fps = 0.0
    last_query_time = 0.0
    notice_text = ""
    notice_until = 0.0
    last_classification_send = 0.0

    window_name = "Lemon Sorting System"

    try:
        while True:
            success, frame = cap.read()
            if not success:
                logging.warning("Cannot read camera frame")
                break

            frame_number += 1
            height, width = frame.shape[:2]
            line_y = min(max(SORT_LINE_Y, 0), height - 1)

            try:
                result = model.predict(
                    frame,
                    imgsz=IMAGE_SIZE,
                    conf=CONFIDENCE,
                    verbose=False,
                )[0]
            except Exception as exc:
                logging.error("YOLO inference error: %s", exc)
                continue

            detections = []
            boxes = result.boxes

            if boxes is not None:
                for box in boxes:
                    class_id = int(box.cls[0])
                    if class_id not in class_map:
                        continue

                    confidence = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2
                    command, category = class_map[class_id]

                    detections.append(
                        {
                            "class_id": class_id,
                            "category": category,
                            "command": command,
                            "confidence": confidence,
                            "box": (x1, y1, x2, y2),
                            "cx": cx,
                            "cy": cy,
                        }
                    )

            detections = tracker.update(detections, frame_number)

            # Duong gui lenh
            cv2.line(frame, (0, line_y), (width, line_y), (0, 180, 255), 2)
            cv2.putText(
                frame,
                "SEND TO STM32",
                (10, max(100, line_y - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (0, 180, 255),
                1,
            )

            for detection in detections:
                x1, y1, x2, y2 = detection["box"]
                category = detection["category"]
                confidence = detection["confidence"]
                track_id = detection["track_id"]

                if category == "GOOD":
                    color = (70, 210, 70)
                else:
                    color = (60, 60, 230)

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                label = (
                    f"{category} {confidence:.2f} "
                    f"[{detection['stable_frames']}]"
                )
                label_y = y1 - 8 if y1 > 24 else y1 + 20
                cv2.putText(
                    frame,
                    label,
                    (x1, label_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    color,
                    2,
                )

                crossed_line = is_crossing_line(
                    detection["previous_y"],
                    detection["cy"],
                    line_y,
                )

                # Mot khi vat da di qua SEND LINE thi ghi nho ID.
                # Neu tai frame cat line chua du stable/cooldown/queue,
                # chuong trinh se tiep tuc cho va gui o frame sau.
                if crossed_line:
                    crossed_track_ids.add(track_id)

                stable_enough = (
                    detection["stable_frames"] >= MIN_STABLE_FRAMES
                )

                cooldown_ok = (
                    time.time() - last_classification_send
                    >= CLASSIFICATION_SEND_COOLDOWN
                )

                queue_ready = (
                    not uart.connected
                    or uart.queue_count < MAX_STM_QUEUE
                )

                if (
                    track_id not in sent_track_ids
                    and track_id in crossed_track_ids
                    and stable_enough
                    and cooldown_ok
                    and queue_ready
                ):
                    if uart.connected:
                        sent_ok = uart.send_classification(
                            detection["command"]
                        )
                    else:
                        sent_ok = True

                    if sent_ok:
                        sent_track_ids.add(track_id)
                        crossed_track_ids.discard(track_id)
                        last_classification_send = time.time()

                        if category == "GOOD":
                            local_good += 1
                        else:
                            local_bad += 1

                        notice_text = f"SENT {category}"
                        notice_until = time.time() + 0.6
                        logging.info(
                            "Sent %s for track %s at y=%s",
                            category,
                            track_id,
                            detection["cy"],
                        )
                    else:
                        notice_text = "UART SEND FAILED"
                        notice_until = time.time() + 1.0

            # Xoa ID cua vat da roi khoi khung hinh.
            active_ids = set(tracker.objects.keys())
            sent_track_ids.intersection_update(active_ids)
            crossed_track_ids.intersection_update(active_ids)

            # Doc ACK/trang thai tu STM32.
            for message, _ in uart.poll():
                if message == "QUEUE_FULL":
                    notice_text = "STM32 QUEUE FULL"
                    notice_until = time.time() + 1.2
                    logging.warning("STM32 queue is full")
                elif message == "G_OK":
                    logging.info("STM32 ACK GOOD")
                elif message == "B_OK":
                    logging.info("STM32 ACK BAD")

            current_time = time.time()
            if uart.connected and current_time - last_query_time >= STATUS_QUERY_INTERVAL:
                uart.request_status()
                last_query_time = current_time

            delta = current_time - last_frame_time
            instant_fps = 1.0 / delta if delta > 0 else 0.0
            smooth_fps = instant_fps if smooth_fps == 0 else (0.85 * smooth_fps + 0.15 * instant_fps)
            last_frame_time = current_time

            draw_panel(frame, uart, smooth_fps, local_good, local_bad)
            if current_time < notice_until:
                draw_notice(frame, notice_text)

            cv2.imshow(window_name, frame)
            key = cv2.waitKey(1) & 0xFF

            if key in (27, ord("q"), ord("Q")):
                break

            if key in (ord("r"), ord("R")):
                reset_ok = uart.reset_system() if uart.connected else True
                local_good = 0
                local_bad = 0
                sent_track_ids.clear()
                crossed_track_ids.clear()
                tracker.reset()

                notice_text = "RESET OK" if reset_ok else "RESET FAILED"
                notice_until = time.time() + 1.0

            elif key in (ord("s"), ord("S")):
                os.makedirs("screenshots", exist_ok=True)
                filename = datetime.now().strftime("screenshots/lemon_%Y%m%d_%H%M%S.jpg")
                cv2.imwrite(filename, frame)
                notice_text = "IMAGE SAVED"
                notice_until = time.time() + 0.8
                logging.info("Saved image: %s", filename)

    finally:
        cap.release()
        uart.close()
        cv2.destroyAllWindows()
        logging.info("Program stopped.")


if __name__ == "__main__":
    main()