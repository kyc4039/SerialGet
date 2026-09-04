import serial
import sqlite3
from datetime import datetime

SERIAL_PORT = "COM5"
BAUD_RATE = 115200
DB_PATH = "console_data.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            cds INTEGER,
            flame INTEGER,
            water INTEGER,
            sound INTEGER,
            reed INTEGER,
            hit INTEGER,
            dist INTEGER,
            temp REAL,
            humidity REAL
        )
    """)
    conn.commit()
    conn.close()


def save_reading(data):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT INTO readings
           (timestamp, cds, flame, water, sound, reed, hit, dist, temp, humidity)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data.get("cds"),
            data.get("flame"),
            data.get("water"),
            data.get("sound"),
            data.get("reed"),
            data.get("hit"),
            data.get("dist"),
            data.get("temp"),
            data.get("hum"),
        ),
    )
    conn.commit()
    conn.close()


def parse_line(line):
    result = {}
    for pair in line.split(","):
        if ":" not in pair:
            continue
        key, value = pair.split(":")
        key = key.strip()
        value = value.strip()

        if value == "NaN":
            result[key] = None
        elif "." in value:
            result[key] = float(value)
        else:
            try:
                result[key] = int(value)
            except ValueError:
                continue
    return result


def serial_check():
    init_db()

    try:
        with serial.Serial(port=SERIAL_PORT, baudrate=BAUD_RATE, timeout=1) as arduino:
            print(f"{SERIAL_PORT} 연결됨, 수집 시작 (Ctrl+C로 종료)")

            while True:
                line = arduino.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                data = parse_line(line)
                if "cds" not in data:
                    continue  # 형식이 깨진 줄은 무시

                save_reading(data)
                print(f"저장됨 → {data}")

    except KeyboardInterrupt:
        print("\n종료합니다.")
    except serial.SerialException as error:
        print(f"시리얼 포트를 열 수 없습니다: {error}")


if __name__ == "__main__":
    serial_check()