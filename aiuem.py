#!/usr/bin/env python3
# fruit_pay_system.py
# Raspberry Pi 4B – YOLO + Loadcell HX711 + HTTP POST

import time, json, cv2, os, sys
from collections import Counter

# ───────── YOLO ──────────────────────────────────────────────────────────────
YOLO_MODEL_PATH = "./my_model.pt"
YOLO_CONF_TH = 0.5

try:
    from ultralytics import YOLO
    model = YOLO(YOLO_MODEL_PATH, task="detect")
except Exception as e:
    print("❌ Không load được mô hình YOLO.")
    raise e

CLASS_NAMES = {v.lower(): v for v in model.names.values()}

# ───────── HX711 ─────────────────────────────────────────────────────────────
import RPi.GPIO as GPIO
from hx711v0_5_1 import HX711

HX_DT, HX_SCK = 5, 6
REFERENCE_UNIT = -403
hx = HX711(HX_DT, HX_SCK)
hx.setReadingFormat("MSB", "MSB")
hx.autosetOffset()
hx.setReferenceUnit(REFERENCE_UNIT)

# ───────── CAMERA (Picamera2) ────────────────────────────────────────────────
from picamera2 import Picamera2
picam = Picamera2()
RES_W, RES_H = 1280, 720
picam.configure(picam.create_video_configuration(
    main={"format": 'RGB888', "size": (RES_W, RES_H)}))
picam.start()
time.sleep(1)

# ───────── BẢNG GIÁ ──────────────────────────────────────────────────────────
UNIT_PRICE = {
    "apple": 15,
    "banana": 8,
    "orange": 12,
    "guava": 20,
    "pear": 18,
    "mango": 25
}

# ───────── SERVER ────────────────────────────────────────────────────────────
SERVER_URL = "https://fruit-api-server.onrender.com/product"
HEADERS = {"Content-Type": "application/json"}

# ───────── HÀM TIỆN ÍCH ──────────────────────────────────────────────────────
def read_weight(num_samples: int = 15) -> float:
    w = [hx.getWeight() for _ in range(num_samples)]
    gram = sum(w) / len(w)
    return 0 if gram < 0 else gram

def post_bill(payload: dict):
    import requests
    try:
        resp = requests.post(SERVER_URL, headers=HEADERS, data=json.dumps(payload), timeout=5)
        print(f"➡️  POST {resp.status_code}: {resp.text}")
    except Exception as e:
        print("❌ Gửi dữ liệu thất bại:", e)

# ───────── CHƯƠNG TRÌNH CHÍNH ────────────────────────────────────────────────
def main():
    print("=== Hệ thống nhận diện trái cây + cân nặng + gửi hóa đơn ===")
    DETECT_WINDOW = 5
    prev_counts = None
    prev_weight = 0

    try:
        while True:
            print("\n✋ Đặt trái cây lên cân, hệ thống đang quét...")
            t0 = time.time()
            labels_session = []

            while time.time() - t0 < DETECT_WINDOW:
                frame = picam.capture_array()
                results = model(frame, conf=YOLO_CONF_TH, verbose=False)
                for box in results[0].boxes:
                    cls_idx = int(box.cls.item())
                    conf = box.conf.item()
                    if conf < YOLO_CONF_TH:
                        continue
                    label = model.names[cls_idx].lower()
                    labels_session.append(label)

                cv2.imshow("Detect", results[0].plot(conf=True))
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    raise KeyboardInterrupt

            counts = Counter(labels_session)
            if not counts:
                print("⚠️ Không phát hiện trái cây.")
                continue

            weight = round(read_weight(), 1)
            print("🔎 Đếm được:", dict(counts))
            print("⚖️  Khối lượng:", weight, "gram")

            # ❗ Kiểm tra nếu không có thay đổi thì bỏ qua
            if counts == prev_counts and abs(weight - prev_weight) < 5:
                print("↪️  Không thay đổi, bỏ qua lần này.")
                continue

            prev_counts = counts
            prev_weight = weight

            # Tính tiền và gửi
            products_json = []
            total_money = 0
            for label, qty in counts.items():
                unit_price = UNIT_PRICE.get(label, 0)
                money = qty * unit_price
                total_money += money
                products_json.append({
                    "name": CLASS_NAMES.get(label, label.title()),
                    "quantity": qty,
                    "unit_price": unit_price,
                    "total_price": money
                })

            payload = {
                "products": products_json,
                "total_weight": weight,
                "total_amount": total_money
            }

            print("💰 Tổng tiền:", total_money, "k – gửi lên server…")
            post_bill(payload)

            print("✅ Gửi xong. Gỡ trái cây xuống nếu muốn quét đơn mới.")
            time.sleep(2)

    except KeyboardInterrupt:
        print("\n⏹️ Kết thúc bởi người dùng.")
    finally:
        picam.stop()
        GPIO.cleanup()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
