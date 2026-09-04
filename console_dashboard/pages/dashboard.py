import time
from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st

from src.queries import build_alert_feed, get_latest_reading, get_readings, get_record_count, time_ago

THRESHOLDS = {
    "cds_dark": 200,
    "dist_close": 10,
    "temp_high": 30.0,
    "hum_low": 30.0,
    "hum_high": 70.0,
}

SEVERITY_COLOR = {"위험": "🔴", "경고": "🟡", "정보": "🔵"}

st.title("센서 모니터링")
st.caption(datetime.now().strftime("%Y년 %m월 %d일 %H:%M:%S"))

window_label = st.selectbox("조회 범위", ["최근 1시간", "최근 6시간", "최근 24시간"], index=0, label_visibility="collapsed")
window_minutes = {"최근 1시간": 60, "최근 6시간": 360, "최근 24시간": 1440}[window_label]

df = get_readings(window_minutes)
latest = get_latest_reading()
total = get_record_count()
alerts = build_alert_feed(df, THRESHOLDS)

danger_count = sum(1 for a in alerts if a["severity"] == "위험")
warn_count = sum(1 for a in alerts if a["severity"] == "경고")

SENSORS = [
    {"id": "SEN-CDS", "name": "조도 센서", "col": "cds", "unit": "", "min": 0, "max": 1023},
    {"id": "SEN-US", "name": "초음파 센서", "col": "dist", "unit": "cm", "min": 0, "max": 100},
    {"id": "SEN-DHT-T", "name": "온도 센서", "col": "temp", "unit": "°C", "min": 0, "max": 45},
    {"id": "SEN-DHT-H", "name": "습도 센서", "col": "humidity", "unit": "%", "min": 0, "max": 100},
    {"id": "SEN-TILT", "name": "기울기 센서", "col": "tilt", "unit": "", "min": None, "max": None},
    {"id": "SEN-REED", "name": "문/자석 센서", "col": "reed", "unit": "", "min": None, "max": None},
    {"id": "SEN-HIT", "name": "충격 센서", "col": "hit", "unit": "", "min": None, "max": None},
    {"id": "SEN-TOUCH", "name": "터치 센서", "col": "touch", "unit": "", "min": None, "max": None},
]


def sensor_status(sensor, value, seconds_since_update):
    if value is None or seconds_since_update > 30:
        return "오프라인"
    col = sensor["col"]
    if col == "hit" and value == 0:
        return "위험"
    if col == "reed" and value == 1:
        return "경고"
    if col == "tilt" and value == 0:
        return "경고"
    if col == "cds" and value <= THRESHOLDS["cds_dark"]:
        return "경고"
    if col == "dist" and value <= THRESHOLDS["dist_close"]:
        return "위험"
    if col == "temp" and value >= THRESHOLDS["temp_high"]:
        return "경고"
    if col == "humidity" and not (THRESHOLDS["hum_low"] <= value <= THRESHOLDS["hum_high"]):
        return "경고"
    return "온라인"


def display_value(sensor, value):
    col = sensor["col"]
    if value is None:
        return "N/A"
    if col == "tilt":
        return "평평함" if value == 1 else "기울어짐"
    if col == "reed":
        return "닫힘" if value == 0 else "열림"
    if col == "hit":
        return "정상" if value == 1 else "충격"
    if col == "touch":
        return "터치됨" if value == 1 else "IDLE"
    if col in ("temp",):
        return f"{value:.1f}°C"
    if col in ("humidity",):
        return f"{value:.1f}%"
    return f"{int(value)}{sensor['unit']}"


# ── KPI 카드 ────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("총 센서", len(SENSORS))
k2.metric("수집 레코드", f"{total:,}")
k3.metric("활성 알림", len(alerts), f"{warn_count} 경고 / {danger_count} 위험" if alerts else None,
          delta_color="inverse")
system_state = "위험" if danger_count else ("주의" if warn_count else "정상")
k4.metric("시스템 상태", system_state,
          f"마지막 수신: {time_ago(latest['timestamp']) if latest else '-'}")

st.divider()

tab_overview, tab_sensors, tab_alerts = st.tabs(["개요", "센서 상세", "알림"])

# ── 개요 탭 ─────────────────────────────────────────────
with tab_overview:
    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("센서 데이터 추이")
        col_choice = st.selectbox(
            "대상 센서", ["조도(cds)", "거리(dist)", "온도(temp)", "습도(humidity)"], key="trend_sensor"
        )
        chart_type = st.radio("차트 유형", ["라인 차트", "영역 차트"], horizontal=True, key="trend_type")
        col_map = {"조도(cds)": "cds", "거리(dist)": "dist", "온도(temp)": "temp", "습도(humidity)": "humidity"}
        target_col = col_map[col_choice]

        if not df.empty and df[target_col].notna().any():
            mark = "area" if chart_type == "영역 차트" else "line"
            chart = (
                alt.Chart(df)
                .mark_area(opacity=0.35, color="#2f6fed") if mark == "area" else alt.Chart(df).mark_line(color="#2f6fed")
            ).encode(x=alt.X("timestamp:T", title=None), y=alt.Y(f"{target_col}:Q", title=None)).properties(height=280)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.caption("데이터 없음")

    with c2:
        st.subheader("최근 알림")
        if alerts:
            for a in alerts[:5]:
                with st.container(border=True):
                    st.markdown(f"{SEVERITY_COLOR[a['severity']]} **{a['device']}** · {a['severity']}")
                    st.caption(f"{time_ago(a['ts'])} · {a['message']}")
                    st.caption(f"ID: {a['id']}")
        else:
            st.caption("활성 알림 없음")

    st.subheader("주요 센서 상태")
    g1, g2, g3, g4 = st.columns(4)
    for col, sensor in zip((g1, g2, g3, g4), SENSORS[:4]):
        value = latest.get(sensor["col"]) if latest else None
        with col:
            st.caption(sensor["name"])
            if value is not None and sensor["max"]:
                ratio = min(max((value - sensor["min"]) / (sensor["max"] - sensor["min"]), 0), 1)
                st.progress(ratio, text=display_value(sensor, value))
                st.caption(f"{sensor['min']}{sensor['unit']} ~ {sensor['max']}{sensor['unit']}")
            else:
                st.write("N/A")

# ── 센서 상세 탭 ─────────────────────────────────────────
with tab_sensors:
    st.subheader("센서 상태")
    rows = []
    for sensor in SENSORS:
        value = latest.get(sensor["col"]) if latest else None
        seconds_since = (datetime.now() - latest["timestamp"].to_pydatetime()).total_seconds() if latest else 9999
        status = sensor_status(sensor, value, seconds_since)
        rows.append({
            "ID": sensor["id"],
            "센서명": sensor["name"],
            "상태": status,
            "마지막 값": display_value(sensor, value),
            "마지막 업데이트": time_ago(latest["timestamp"]) if latest else "-",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ── 알림 탭 ─────────────────────────────────────────────
with tab_alerts:
    st.subheader(f"전체 알림 ({len(alerts)}건)")
    if alerts:
        for a in alerts:
            with st.container(border=True):
                cols = st.columns([3, 1])
                cols[0].markdown(f"{SEVERITY_COLOR[a['severity']]} **{a['device']}** — {a['severity']}")
                cols[1].caption(time_ago(a["ts"]))
                st.caption(a["message"])
                st.caption(f"ID: {a['id']}")

        alert_df = pd.DataFrame(alerts)
        alert_df["ts"] = alert_df["ts"].astype(str)
        st.download_button(
            "알림 이력 CSV 다운로드",
            alert_df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )
    else:
        st.caption("활성 알림 없음")

time.sleep(2)
st.rerun()
