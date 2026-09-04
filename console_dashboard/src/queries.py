"""조회 전용 쿼리 모음. 저장/쓰기 로직은 여기 두지 않는다."""

from datetime import datetime, timedelta

import pandas as pd

from src.db import get_connection
from src.sensors import THRESHOLDS


def get_readings(window_minutes: int) -> pd.DataFrame:
    """최근 window_minutes 분간의 센서 원본 데이터를 시간순으로 반환한다."""
    conn = get_connection()
    since = (datetime.now() - timedelta(minutes=window_minutes)).strftime("%Y-%m-%d %H:%M:%S")
    df = pd.read_sql_query(
        "SELECT * FROM readings WHERE timestamp >= ? ORDER BY id ASC",
        conn,
        params=(since,),
    )
    conn.close()
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def get_record_count() -> int:
    conn = get_connection()
    try:
        count = conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
    except Exception:
        count = 0
    conn.close()
    return count


def get_latest_reading() -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM readings ORDER BY id DESC LIMIT 1").fetchone()
        columns = [d[0] for d in conn.execute("SELECT * FROM readings LIMIT 1").description]
    except Exception:
        conn.close()
        return None
    conn.close()
    if row is None:
        return None
    result = dict(zip(columns, row))
    if "timestamp" in result and result["timestamp"] is not None:
        result["timestamp"] = pd.Timestamp(result["timestamp"])
    return result


def get_boolean_events(df: pd.DataFrame, column: str, active_value) -> pd.DataFrame:
    """지정한 불리언 컬럼이 active_value로 바뀌는 시점만 추출한다 (이벤트 로그용)."""
    if df.empty or column not in df:
        return df.iloc[0:0] if not df.empty else df
    mask = (df[column] == active_value) & (df[column].shift(1) != active_value)
    return df[mask]


def time_ago(ts: pd.Timestamp) -> str:
    delta = datetime.now() - ts.to_pydatetime()
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return f"{seconds}초 전"
    if seconds < 3600:
        return f"{seconds // 60}분 전"
    if seconds < 86400:
        return f"{seconds // 3600}시간 전"
    return f"{seconds // 86400}일 전"


def _zone_series(series: pd.Series, warn: float, danger: float, direction: str) -> pd.Series:
    """값 시계열을 정상/경고/위험 구간으로 분류한다. direction: 'low'=낮을수록 위험, 'high'=높을수록 위험."""
    zone = pd.Series("정상", index=series.index)
    if direction == "low":
        zone[series <= warn] = "경고"
        zone[series <= danger] = "위험"
    else:
        zone[series >= warn] = "경고"
        zone[series >= danger] = "위험"
    return zone


def _zone_alerts(df: pd.DataFrame, col: str, device: str, sensor_id: str,
                  warn: float, danger: float, direction: str, unit: str = "") -> list[dict]:
    if col not in df or not df[col].notna().any():
        return []
    zone = _zone_series(df[col], warn, danger, direction)
    changed = zone != zone.shift(1)
    changed.iloc[0] = False  # 첫 행은 비교 대상이 없어 항상 True로 뜨는 것 방지

    out = []
    for idx in df.index[changed]:
        z = zone.loc[idx]
        val = df.loc[idx, col]
        val_text = f"{val:.1f}{unit}" if isinstance(val, float) else f"{int(val)}{unit}"
        if z == "정상":
            out.append({"device": device, "severity": "정보", "ts": df.loc[idx, "timestamp"],
                        "message": f"정상 범위로 복귀했습니다 ({val_text}).", "id": sensor_id})
        else:
            out.append({"device": device, "severity": z, "ts": df.loc[idx, "timestamp"],
                        "message": f"{z} 구간 진입 ({val_text}).", "id": sensor_id})
    return out


def _humidity_alerts(df: pd.DataFrame) -> list[dict]:
    if "humidity" not in df or not df["humidity"].notna().any():
        return []
    t = THRESHOLDS
    h = df["humidity"]
    zone = pd.Series("정상", index=h.index)
    zone[(h <= t["hum_warn_low"]) | (h >= t["hum_warn_high"])] = "경고"
    zone[(h <= t["hum_danger_low"]) | (h >= t["hum_danger_high"])] = "위험"
    changed = zone != zone.shift(1)
    changed.iloc[0] = False

    out = []
    for idx in df.index[changed]:
        z = zone.loc[idx]
        val = h.loc[idx]
        if z == "정상":
            out.append({"device": "습도 센서", "severity": "정보", "ts": df.loc[idx, "timestamp"],
                        "message": f"습도가 정상 범위로 복귀했습니다 ({val:.1f}%).", "id": "DEV002"})
        else:
            out.append({"device": "습도 센서", "severity": z, "ts": df.loc[idx, "timestamp"],
                        "message": f"습도 {z} 구간 진입 ({val:.1f}%).", "id": "DEV002"})
    return out


def build_alert_feed(df: pd.DataFrame) -> list[dict]:
    """불리언 상태 전이 + 연속값 구간 전이를 하나의 알림 피드로 합친다."""
    if df.empty:
        return []

    t = THRESHOLDS
    feed = []

    # ── 이벤트/불리언 센서 ──
    for _, r in get_boolean_events(df, "hit", 0).iterrows():
        feed.append({"device": "진동 감지 센서", "severity": "위험", "ts": r["timestamp"],
                     "message": "충격이 감지되었습니다. 즉시 확인이 필요합니다.", "id": "DEV008"})

    for _, r in get_boolean_events(df, "reed", 1).iterrows():
        feed.append({"device": "도어/자석 센서", "severity": "경고", "ts": r["timestamp"],
                     "message": "제어반 도어가 열렸습니다.", "id": "DEV007"})
    for _, r in get_boolean_events(df, "reed", 0).iterrows():
        feed.append({"device": "도어/자석 센서", "severity": "정보", "ts": r["timestamp"],
                     "message": "제어반 도어가 닫혔습니다.", "id": "DEV007"})

    for _, r in get_boolean_events(df, "sound", 1).iterrows():
        feed.append({"device": "소음 감지 센서", "severity": "경고", "ts": r["timestamp"],
                     "message": "이상 소음이 감지되었습니다.", "id": "DEV009"})

    # ── 연속값 센서 (구간 전이 기반) ──
    feed += _zone_alerts(df, "cds", "조도 센서", "DEV003", t["cds_warn"], t["cds_danger"], "low")
    feed += _zone_alerts(df, "flame", "화염 센서", "DEV004", t["flame_warn"], t["flame_danger"], "low")
    feed += _zone_alerts(df, "water", "수위 센서", "DEV005", t["water_warn"], t["water_danger"], "high")
    feed += _zone_alerts(df, "dist", "초음파 거리 센서", "DEV006", t["dist_warn"], t["dist_danger"], "low", unit="cm")
    feed += _zone_alerts(df, "temp", "온도 센서", "DEV001", t["temp_warn"], t["temp_danger"], "high", unit="°C")
    feed += _humidity_alerts(df)

    feed.sort(key=lambda e: e["ts"], reverse=True)
    return feed
