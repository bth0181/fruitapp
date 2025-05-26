#!/usr/bin/env python3
# fruit_pay_system.py
# Raspberry Pi 4B – YOLO  + Loadcell HX711  + HTTP POST

import time, json, cv2, os, signal, sys
from collections import Counter

# ─────────  YOLO  ──────────────────────────────────────────────────────────────
YOLO_MODEL_PATH = "./my_model.pt"          # hoặc .onnx, đổi nếu cần
YOLO_CONF_TH = 0.5                         # ngưỡng tin cậy

try:
    from ultralytics import YOLO           # dùng YOLOv8/v5 của Ultralytics
    model = YOLO(YOLO_MODEL_PATH, task="detect")
except Exception as e:
    print("❌ KHÔNG load được mô hình YOLO – kiểm tra đường dẫn & cài đặt ultralytics.")
    raise e
CLASS_NAMES = {v.lower(): v for v in model.names.values()}  # ví dụ {'apple':'Apple', …}

# ─────────  HX711  ─────────────────────────────────────────────────────────────
import RPi.GPIO as GPIO
from hx711v0_5_1 import HX711

HX_DT, HX_SCK = 5, 6                       # chân GPIO (BCM)
REFERENCE_UNIT = -403                      # → Hiệu chuẩn theo cân của bạn!
hx = HX711(HX_DT, HX_SCK)
hx.setReadingFormat("MSB", "MSB")
hx.autosetOffset()
hx.setReferenceUnit(REFERENCE_UNIT)

# ─────────  CAMERA  (Picamera2)  ───────────────────────────────────────────────
from picamera2 import Picamera2
picam = Picamera2()
RES_W, RES_H = 1280, 720
picam.configure(picam.create_video_configuration(
        main={"format": 'RGB888', "size": (RES_W, RES_H)}))
picam.start()
time.sleep(1)  # đợi camera “ấm” một chút

# ─────────  BẢNG GIÁ  ─────────────────────────────────────────────────────────
UNIT_PRICE = {
    "apple": 15,   # 15 k/ quả
    "banana": 8,
    "orange": 12,
    "guava": 20,   # ổi
    "pear": 18,    # lê
    "mango": 25
}

# ─────────  SERVER  ────────────────────────────────────────────────────────────
SERVER_URL = "http://192.168.1.8:5000/product"   # đổi thành API thật của bạn
HEADERS = {"Content-Type": "application/json"}

# ─────────  HÀM TIỆN ÍCH  ─────────────────────────────────────────────────────
def read_weight(num_samples: int = 15) -> float:
    """Đọc N mẫu, lấy trung bình, trả về gram (>=0)."""
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

# ─────────  VÒNG LẶP NHẬN DẠNG  +  GỬI DỮ LIỆU  ───────────────────────────────
def main():
    print("=== Hệ thống nhận diện trái cây + cân nặng + gửi hóa đơn ===")
    DETECT_WINDOW = 5         # giây “quét” để đếm trái cây
    try:
        while True:
            print("\n✋  Bỏ trái cây lên cân, chờ quét...")
            t0 = time.time()
            labels_session = []

            # ----------- 1) QUÉT CAMERA trong DETECT_WINDOW giây -------------
            while time.time() - t0 < DETECT_WINDOW:
                frame = picam.capture_array()
                results = model(frame, conf=YOLO_CONF_TH, verbose=False)
                for box in results[0].boxes:
                    cls_idx = int(box.cls.item())
                    conf    = box.conf.item()
                    if conf < YOLO_CONF_TH:       # phòng hờ
                        continue
                    label = model.names[cls_idx].lower()
                    labels_session.append(label)

                # Hiển thị (tuỳ chọn – tắt nếu chạy Headless)
                cv2.imshow("Detect", results[0].plot(conf=True))
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    raise KeyboardInterrupt

            # ----------- 2) ĐẾM SẢN PHẨM -------------------------------------
            counts = Counter(labels_session)
            if not counts:
                print("⚠️  Không phát hiện trái cây nào. Thử lại.")
                continue
            print("🔎 Đếm được:", dict(counts))

            # ----------- 3) ĐỌC KHỐI LƯỢNG -----------------------------------
            weight = round(read_weight(), 1)
            print("⚖️  Khối lượng tổng:", weight, "gram")

            # ----------- 4) TÍNH TIỀN ---------------------------------------
            products_json = []
            total_money   = 0
            for label, qty in counts.items():
                unit_price = UNIT_PRICE.get(label, 0)
                money      = qty * unit_price
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

            # ----------- 5) GỬI LÊN SERVER ----------------------------------
            post_bill(payload)

            print("✅ Hoàn tất! Gỡ trái cây xuống, hệ thống sẽ chờ cho lô tiếp theo…")
            time.sleep(2)         # đợi người dùng lấy hàng xuống cân

    except KeyboardInterrupt:
        print("\n⏹️  Người dùng kết thúc chương trình.")
    finally:
        picam.stop()
        GPIO.cleanup()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
