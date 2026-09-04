import random
import time

import serial

SERIAL_PORT = "COM4"
BAUD_RATE = 115200

ser = serial.Serial(SERIAL_PORT, BAUD_RATE)


class RandomWalkSensor:
    """정상 구간에서 서서히 흔들리다가, 낮은 확률로 경고/위험 구간을 잠깐 방문하는 시뮬레이터."""

    def __init__(self, normal_range, warning_range, danger_range,
                 step=1.0, excursion_chance=0.01, is_int=True):
        self.normal_range = normal_range
        self.warning_range = warning_range
        self.danger_range = danger_range
        self.step = step
        self.excursion_chance = excursion_chance
        self.is_int = is_int
        self.value = (normal_range[0] + normal_range[1]) / 2
        self.target = None  # 이상치로 튈 때 목표값

    def next(self):
        if self.target is None:
            center = (self.normal_range[0] + self.normal_range[1]) / 2
            self.value += (center - self.value) * 0.05 + random.uniform(-self.step, self.step)

            if random.random() < self.excursion_chance:
                pool = self.warning_range if random.random() < 0.7 else self.danger_range
                self.target = random.uniform(*pool)
        else:
            self.value += (self.target - self.value) * 0.15 + random.uniform(-self.step * 0.3, self.step * 0.3)
            if abs(self.value - self.target) < self.step:
                self.target = None

        lo = min(self.normal_range[0], self.warning_range[0], self.danger_range[0])
        hi = max(self.normal_range[1], self.warning_range[1], self.danger_range[1])
        self.value = max(lo, min(hi, self.value))

        return int(round(self.value)) if self.is_int else round(self.value, 1)


class EventSensor:
    """평소 0(정상), 낮은 확률로 짧게 1(감지)이 되는 이벤트성 센서."""

    def __init__(self, trigger_chance=0.02, active_ticks=3, active_value=1, idle_value=0):
        self.trigger_chance = trigger_chance
        self.active_ticks = active_ticks
        self.active_value = active_value
        self.idle_value = idle_value
        self.remaining = 0

    def next(self):
        if self.remaining > 0:
            self.remaining -= 1
            return self.active_value
        if random.random() < self.trigger_chance:
            self.remaining = self.active_ticks
            return self.active_value
        return self.idle_value


# ── 센서별 정상/경고/위험 구간 정의 ──────────────────────
temp_sensor = RandomWalkSensor((18, 26), (26, 30), (30, 38), step=0.3, is_int=False)
hum_sensor = RandomWalkSensor((40, 60), (30, 40), (10, 30), step=1.0, is_int=False)
cds_sensor = RandomWalkSensor((400, 1023), (200, 400), (0, 200), step=15)
flame_sensor = RandomWalkSensor((800, 1023), (400, 800), (0, 400), step=10, excursion_chance=0.003)
water_sensor = RandomWalkSensor((0, 300), (300, 600), (600, 1023), step=8, excursion_chance=0.005)
dist_sensor = RandomWalkSensor((30, 100), (10, 30), (0, 10), step=3)

sound_sensor = EventSensor(trigger_chance=0.03, active_ticks=2)
reed_sensor = EventSensor(trigger_chance=0.01, active_ticks=8)
hit_sensor = EventSensor(trigger_chance=0.008, active_ticks=1, active_value=0, idle_value=1)

print(f"{SERIAL_PORT} 시뮬레이터 시작 (Ctrl+C로 종료)")

try:
    while True:
        temp = temp_sensor.next()
        hum = hum_sensor.next()
        cds = cds_sensor.next()
        flame = flame_sensor.next()
        water = water_sensor.next()
        dist = dist_sensor.next()
        sound = sound_sensor.next()
        reed = reed_sensor.next()
        hit = hit_sensor.next()

        line = (
            f"switch:1,cds:{cds},flame:{flame},water:{water},"
            f"sound:{sound},reed:{reed},hit:{hit},dist:{dist},"
            f"temp:{temp},hum:{hum}\n"
        )
        ser.write(line.encode())
        print("TX:", line.strip())
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n종료합니다.")
    ser.close()