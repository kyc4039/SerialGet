import time

import altair as alt
import streamlit as st

from src.queries import build_alert_feed, get_latest_reading, get_readings, get_record_count, time_ago
from src.sensors import SENSORS, display_value, seconds_since, sensor_color, sensor_status, zone_series
from src.ui import accent, alert_card, device_table, gauge_card, inject_css, kpi_row, page_header, section_title, status_card

inject_css()
page_header("통합 모니터링 대시보드", "실시간 센서 데이터 및 디바이스 상태를 모니터링합니다.")

df = get_readings(60)
latest = get_latest_reading()
total = get_record_count()
alerts = build_alert_feed(df)
danger_n = sum(1 for a in alerts if a["severity"] == "위험")
warn_n = sum(1 for a in alerts if a["severity"] == "경고")
since = seconds_since(latest)
statuses = {s["id"]: sensor_status(s, latest.get(s["col"]) if latest else None, since) for s in SENSORS}
online_n = sum(1 for v in statuses.values() if v != "오프라인")
system_state = "위험" if danger_n else ("주의" if warn_n else "정상")

kpi_row([
    ("총 디바이스", str(len(SENSORS)), f"{online_n} 온라인 / {len(SENSORS) - online_n} 오프라인", "중립"),
    ("수집 레코드", f"{total:,}", "누적 저장 건수", "중립"),
    ("활성 알림", str(len(alerts)), f"{warn_n} 경고 / {danger_n} 위험" if alerts else "최근 1시간 알림 없음",
     "위험" if danger_n else ("경고" if warn_n else "정상")),
    ("시스템 상태", system_state, f"마지막 수신: {time_ago(latest['timestamp'])}" if latest else "데이터 없음", system_state),
])

st.write("")

CONTINUOUS = [s for s in SENSORS if s["max"] is not None]
TARGET_OPTIONS = {s["name"]: s for s in CONTINUOUS}

col_main, col_side = st.columns([2, 1])

with col_main:
    with st.container(border=True, height=470):
        section_title("센서 데이터 추이", "시간에 따른 센서 데이터 변화를 확인합니다.")
        c0, c1 = st.columns([1, 1])
        target_name = c0.selectbox("대상", list(TARGET_OPTIONS.keys()), label_visibility="collapsed", key="ov_target")
        range_choice = c1.radio("범위", ["1시간", "6시간", "24시간"], horizontal=True, label_visibility="collapsed", key="ov_range")
        target = TARGET_OPTIONS[target_name]
        target_col, unit = target["col"], target["unit"]
        minutes = {"1시간": 60, "6시간": 360, "24시간": 1440}[range_choice]
        trend_df = get_readings(minutes)
        if not trend_df.empty and trend_df[target_col].notna().any():
            interpolate = target.get("interpolate", "linear")
            sc = sensor_color(target_col)
            line = alt.Chart(trend_df).mark_line(color=sc, strokeWidth=2, interpolate=interpolate).encode(
                x=alt.X("timestamp:T", title=None), y=alt.Y(f"{target_col}:Q", title=unit or None, scale=alt.Scale(zero=False))
            )
            layers = [line]
            if interpolate == "step-after":
                zone = zone_series(target_col, trend_df[target_col])
                anomalies = trend_df[zone != "정상"].copy()
                if not anomalies.empty:
                    anomalies["zone"] = zone[zone != "정상"]
                    points = alt.Chart(anomalies).mark_point(filled=True, size=70).encode(
                        x="timestamp:T", y=f"{target_col}:Q",
                        color=alt.Color("zone:N", scale=alt.Scale(domain=["경고", "위험"], range=[accent("경고"), accent("위험")]), legend=None),
                    )
                    layers.append(points)
            chart = alt.layer(*layers)
            st.altair_chart(chart.properties(height=260).configure_view(strokeWidth=0).configure_axis(gridColor="#1f2a44", domainColor="#1f2a44", labelColor="#94a3b8"), use_container_width=True)
        else:
            st.caption("데이터 없음")

with col_side:
    with st.container(border=True, height=470):
        section_title("최근 알림", "최근 발생한 알림 5건")
        if alerts:
            for a in alerts[:5]:
                alert_card(a, time_ago(a["ts"]))
        else:
            st.caption("활성 알림 없음")

st.write("")

with st.container(border=True):
    section_title("센서 상태", "모든 센서의 현재 값과 상태를 한눈에 확인합니다.")
    rows = [st.columns(3), st.columns(3), st.columns(3)]
    flat_cols = rows[0] + rows[1] + rows[2]
    for col, s in zip(flat_cols, SENSORS):
        value = latest.get(s["col"]) if latest else None
        status = statuses[s["id"]]
        with col:
            if s["max"] is not None:
                if value is None:
                    gauge_card(f"{s['icon']} {s['name']}", "N/A", 0, str(s["min"]), str(s["max"]), "오프라인", s["color"])
                else:
                    ratio = (value - s["min"]) / (s["max"] - s["min"])
                    unit = s["unit"]
                    gauge_card(f"{s['icon']} {s['name']}", display_value(s, value), ratio, f"{s['min']}{unit}", f"{s['max']}{unit}", status, s["color"])
            else:
                status_card(f"{s['icon']} {s['name']}", display_value(s, value), status, s["color"])
    st.write("")

st.write("")

with st.container(border=True, height=420):
    section_title("디바이스 상태", "모든 등록된 디바이스의 상태를 확인합니다.")
    device_rows = [{
        "ID": s["id"],
        "디바이스명": s["name"],
        "상태": statuses[s["id"]],
        "위치": s["location"],
        "마지막 활동": time_ago(latest["timestamp"]) if latest else "-",
        "주요 값": display_value(s, latest.get(s["col"]) if latest else None),
    } for s in SENSORS]
    device_table(device_rows)

time.sleep(2)
st.rerun()
