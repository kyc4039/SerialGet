import altair as alt
import streamlit as st

from src.queries import get_latest_reading, get_readings
from src.sensors import SENSORS, display_value, seconds_since, sensor_color, sensor_status, zone_series
from src.ui import accent, gauge_card, inject_css, page_header, section_title, status_card

inject_css()
page_header("센서 데이터", "모든 센서의 실시간 데이터를 확인하고 분석합니다.")

latest = get_latest_reading()
since = seconds_since(latest)

CONTINUOUS = [s for s in SENSORS if s["max"] is not None]
CATEGORIES = list(dict.fromkeys(s["category"] for s in SENSORS))  # 등장 순서 유지, 중복 제거


def mini_chart(sensor: dict, df):
    col, unit = sensor["col"], sensor["unit"]
    if df.empty or not df[col].notna().any():
        st.caption(f"{sensor['icon']} {sensor['name']} — 데이터 없음")
        return
    interpolate = sensor.get("interpolate", "linear")
    sc = sensor_color(col)

    line = (
        alt.Chart(df)
        .mark_line(color=sc, strokeWidth=2, interpolate=interpolate)
        .encode(x=alt.X("timestamp:T", title=None), y=alt.Y(f"{col}:Q", title=unit or None, scale=alt.Scale(zero=False)))
    )
    layers = [line]

    # 계단형(급변 민감) 센서는 경고/위험 구간에 든 지점에만 점을 찍어 이상치를 강조
    if interpolate == "step-after":
        zone = zone_series(col, df[col])
        anomalies = df[zone != "정상"].copy()
        if not anomalies.empty:
            anomalies["zone"] = zone[zone != "정상"]
            points = (
                alt.Chart(anomalies)
                .mark_point(filled=True, size=70)
                .encode(
                    x="timestamp:T", y=f"{col}:Q",
                    color=alt.Color("zone:N", scale=alt.Scale(domain=["경고", "위험"], range=[accent("경고"), accent("위험")]), legend=None),
                )
            )
            layers.append(points)

    chart = (
        alt.layer(*layers)
        .properties(height=180, title=f"{sensor['icon']} {sensor['name']}")
        .configure_view(strokeWidth=0)
        .configure_axis(gridColor="#1f2a44", domainColor="#1f2a44", labelColor="#94a3b8")
        .configure_title(color="#e2e8f0", fontSize=13, anchor="start")
    )
    st.altair_chart(chart, use_container_width=True)


with st.container(border=True):
    section_title("센서 데이터 추이", "센서마다 값 특성에 맞는 차트로 표시합니다 (연속값은 라인, 급격한 변화는 계단형).")
    range_choice = st.radio("범위", ["1시간", "6시간", "24시간"], horizontal=True, label_visibility="collapsed", key="sn_range")
    minutes = {"1시간": 60, "6시간": 360, "24시간": 1440}[range_choice]
    df = get_readings(minutes)

    row1 = st.columns(3)
    row2 = st.columns(3)
    for col, sensor in zip(row1 + row2, CONTINUOUS):
        with col:
            mini_chart(sensor, df)

st.write("")

with st.container(border=True):
    section_title("센서 상태", "모든 센서의 실시간 데이터를 확인합니다.")
    tabs = st.tabs(CATEGORIES)
    for tab, category in zip(tabs, CATEGORIES):
        with tab:
            matched = [s for s in SENSORS if s["category"] == category]
            cols = st.columns(min(len(matched), 3))
            for i, s in enumerate(matched):
                value = latest.get(s["col"]) if latest else None
                status = sensor_status(s, value, since)
                with cols[i % len(cols)]:
                    if s["max"] is not None:
                        if value is None:
                            gauge_card(f"{s['icon']} {s['name']}", "N/A", 0, str(s["min"]), str(s["max"]), "오프라인", s["color"])
                        else:
                            ratio = (value - s["min"]) / (s["max"] - s["min"])
                            gauge_card(f"{s['icon']} {s['name']}", display_value(s, value), ratio, f"{s['min']}{s['unit']}", f"{s['max']}{s['unit']}", status, s["color"])
                    else:
                        status_card(f"{s['icon']} {s['name']}", display_value(s, value), status, s["color"])
