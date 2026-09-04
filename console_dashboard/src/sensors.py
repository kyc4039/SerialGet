"""센서를 '디바이스'로 취급하는 공통 설정. 여러 페이지에서 공유한다.

현재 센서 구성 (LCD/RTC/Tilt/Touch/로터리엔코더/IR 제거, flame/water/sound 신규):
  연속값: 온도, 습도, 조도(CdS), 화염(Flame), 수위(Water), 초음파거리(Dist)
  이벤트/상태: 도어(Reed), 진동(Hit), 소음(Sound)
"""

from datetime import datetime

import pandas as pd

THRESHOLDS = {
    "cds_warn": 400, "cds_danger": 200,          # 낮을수록 위험(어두움)
    "flame_warn": 800, "flame_danger": 400,      # 낮을수록 위험(불꽃 근접)
    "water_warn": 300, "water_danger": 600,      # 높을수록 위험(범람)
    "dist_warn": 30, "dist_danger": 10,          # 낮을수록 위험(근접)
    "temp_warn": 26.0, "temp_danger": 30.0,      # 높을수록 위험
    "hum_warn_low": 40.0, "hum_danger_low": 30.0,
    "hum_warn_high": 60.0, "hum_danger_high": 70.0,
}

SENSORS = [
    {"id": "DEV001", "name": "온도 센서", "col": "temp", "location": "메인 콘솔", "category": "온도",
     "min": 0, "max": 45, "unit": "°C", "color": "#fb923c", "icon": "🌡️", "interpolate": "linear"},
    {"id": "DEV002", "name": "습도 센서", "col": "humidity", "location": "메인 콘솔", "category": "습도",
     "min": 0, "max": 100, "unit": "%", "color": "#2dd4bf", "icon": "💧", "interpolate": "linear"},
    {"id": "DEV003", "name": "조도 센서", "col": "cds", "location": "메인 콘솔", "category": "조도",
     "min": 0, "max": 1023, "unit": "", "color": "#facc15", "icon": "💡", "interpolate": "linear"},
    {"id": "DEV004", "name": "화염 센서", "col": "flame", "location": "메인 콘솔", "category": "화재",
     "min": 0, "max": 1023, "unit": "", "color": "#fb7185", "icon": "🔥", "interpolate": "step-after"},
    {"id": "DEV005", "name": "수위 센서", "col": "water", "location": "저장탱크", "category": "수위",
     "min": 0, "max": 1023, "unit": "", "color": "#22d3ee", "icon": "🌊", "interpolate": "linear"},
    {"id": "DEV006", "name": "초음파 거리 센서", "col": "dist", "location": "컨베이어", "category": "근접",
     "min": 0, "max": 100, "unit": "cm", "color": "#818cf8", "icon": "📏", "interpolate": "step-after"},
    {"id": "DEV007", "name": "도어/자석 센서", "col": "reed", "location": "제어반", "category": "출입",
     "min": None, "max": None, "unit": "", "color": "#e879f9", "icon": "🚪"},
    {"id": "DEV008", "name": "진동 감지 센서", "col": "hit", "location": "메인 콘솔", "category": "진동",
     "min": None, "max": None, "unit": "", "color": "#a3e635", "icon": "📳"},
    {"id": "DEV009", "name": "소음 감지 센서", "col": "sound", "location": "메인 콘솔", "category": "소음",
     "min": None, "max": None, "unit": "", "color": "#f472b6", "icon": "🔊"},
]


def sensor_color(col: str) -> str:
    for s in SENSORS:
        if s["col"] == col:
            return s["color"]
    return "#60a5fa"


def sensor_status(sensor: dict, value, seconds_since_update: float) -> str:
    if value is None or seconds_since_update > 30:
        return "오프라인"
    col = sensor["col"]
    t = THRESHOLDS

    if col == "hit":
        return "위험" if value == 0 else "온라인"
    if col == "reed":
        return "경고" if value == 1 else "온라인"
    if col == "sound":
        return "경고" if value == 1 else "온라인"
    if col == "dist":
        if value <= t["dist_danger"]:
            return "위험"
        if value <= t["dist_warn"]:
            return "경고"
        return "온라인"
    if col == "cds":
        if value <= t["cds_danger"]:
            return "위험"
        if value <= t["cds_warn"]:
            return "경고"
        return "온라인"
    if col == "flame":
        if value <= t["flame_danger"]:
            return "위험"
        if value <= t["flame_warn"]:
            return "경고"
        return "온라인"
    if col == "water":
        if value >= t["water_danger"]:
            return "위험"
        if value >= t["water_warn"]:
            return "경고"
        return "온라인"
    if col == "temp":
        if value >= t["temp_danger"]:
            return "위험"
        if value >= t["temp_warn"]:
            return "경고"
        return "온라인"
    if col == "humidity":
        if value <= t["hum_danger_low"] or value >= t["hum_danger_high"]:
            return "위험"
        if value <= t["hum_warn_low"] or value >= t["hum_warn_high"]:
            return "경고"
        return "온라인"
    return "온라인"


def display_value(sensor: dict, value) -> str:
    col = sensor["col"]
    if value is None:
        return "N/A"
    if col == "reed":
        return "열림" if value == 1 else "닫힘"
    if col == "hit":
        return "충격" if value == 0 else "정상"
    if col == "sound":
        return "감지됨" if value == 1 else "조용함"
    if col == "temp":
        return f"{value:.1f}°C"
    if col == "humidity":
        return f"{value:.1f}%"
    unit = sensor.get("unit", "")
    return f"{int(value)}{unit}"


def seconds_since(latest: dict | None) -> float:
    if latest is None or latest.get("timestamp") is None:
        return 9999
    return (datetime.now() - latest["timestamp"].to_pydatetime()).total_seconds()


def zone_series(col: str, values: pd.Series) -> pd.Series:
    """연속값 시계열을 정상/경고/위험 구간으로 분류한다 (차트에서 이상치 표시용). 습도(양방향)는 미지원."""
    t = THRESHOLDS
    zone = pd.Series("정상", index=values.index)
    if col == "cds":
        zone[values <= t["cds_warn"]] = "경고"
        zone[values <= t["cds_danger"]] = "위험"
    elif col == "flame":
        zone[values <= t["flame_warn"]] = "경고"
        zone[values <= t["flame_danger"]] = "위험"
    elif col == "water":
        zone[values >= t["water_warn"]] = "경고"
        zone[values >= t["water_danger"]] = "위험"
    elif col == "dist":
        zone[values <= t["dist_warn"]] = "경고"
        zone[values <= t["dist_danger"]] = "위험"
    elif col == "temp":
        zone[values >= t["temp_warn"]] = "경고"
        zone[values >= t["temp_danger"]] = "위험"
    return zone
