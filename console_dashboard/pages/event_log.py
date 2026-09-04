from datetime import datetime

import pandas as pd
import streamlit as st

from src.queries import get_boolean_events, get_readings

st.title("이벤트 로그")

window_label = st.selectbox("조회 범위", ["최근 1시간", "최근 6시간", "최근 24시간"], index=0)
window_minutes = {"최근 1시간": 60, "최근 6시간": 360, "최근 24시간": 1440}[window_label]

df = get_readings(window_minutes)

sensor_filter = st.multiselect(
    "센서 필터",
    ["기울기(Tilt)", "문/자석(Reed)", "충격(Hit)", "터치(Touch)"],
    default=["기울기(Tilt)", "문/자석(Reed)", "충격(Hit)", "터치(Touch)"],
)

events = []
if not df.empty:
    if "기울기(Tilt)" in sensor_filter:
        for _, r in get_boolean_events(df, "tilt", 0).iterrows():
            events.append((r["timestamp"], "기울기", "기울어짐 감지"))
        for _, r in get_boolean_events(df, "tilt", 1).iterrows():
            events.append((r["timestamp"], "기울기", "평평함 복귀"))

    if "문/자석(Reed)" in sensor_filter:
        for _, r in get_boolean_events(df, "reed", 0).iterrows():
            events.append((r["timestamp"], "문/자석", "문 닫힘"))
        for _, r in get_boolean_events(df, "reed", 1).iterrows():
            events.append((r["timestamp"], "문/자석", "문 열림"))

    if "충격(Hit)" in sensor_filter:
        for _, r in get_boolean_events(df, "hit", 0).iterrows():
            events.append((r["timestamp"], "충격", "충격 감지"))

    if "터치(Touch)" in sensor_filter:
        for _, r in get_boolean_events(df, "touch", 1).iterrows():
            events.append((r["timestamp"], "터치", "터치 감지"))

events.sort(key=lambda e: e[0], reverse=True)

st.metric("조회된 이벤트 수", len(events))

if events:
    log_df = pd.DataFrame(events, columns=["시각", "센서", "이벤트"])
    log_df["시각"] = log_df["시각"].dt.strftime("%Y-%m-%d %H:%M:%S")

    st.dataframe(log_df, use_container_width=True, hide_index=True)

    st.download_button(
        "이벤트 로그 CSV 다운로드",
        log_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )
else:
    st.caption("조건에 맞는 이벤트가 없습니다.")

st.divider()

st.subheader("원본 데이터")
if not df.empty:
    st.download_button(
        "전체 원본 데이터 CSV 다운로드",
        df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"readings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )
    st.dataframe(df.tail(100).iloc[::-1], use_container_width=True, hide_index=True)
else:
    st.caption("데이터 없음")
