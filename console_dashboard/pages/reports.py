from datetime import datetime

import altair as alt
import streamlit as st

from src.queries import get_readings
from src.sensors import sensor_color
from src.ui import inject_css, kpi_row, page_header, section_title

inject_css()
page_header("리포트", "시스템 데이터 분석 및 리포트를 생성합니다.")

p1, p2 = st.columns([3, 1])
period = p1.radio("기간", ["일간", "주간", "월간"], horizontal=True, label_visibility="collapsed")
period_minutes = {"일간": 1440, "주간": 1440 * 7, "월간": 1440 * 30}[period]
report_df = get_readings(period_minutes)
p2.download_button(
    "리포트 다운로드",
    report_df.to_csv(index=False).encode("utf-8-sig") if not report_df.empty else b"",
    file_name=f"report_{period}_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv",
    disabled=report_df.empty,
    use_container_width=True,
)

if not report_df.empty:
    t = report_df["temp"].dropna()
    h = report_df["humidity"].dropna()
    kpi_row([
        ("수집 건수", f"{len(report_df):,}", f"{period} 기준", "중립"),
        ("평균 온도", f"{t.mean():.1f}°C" if not t.empty else "N/A", f"최고 {t.max():.1f} / 최저 {t.min():.1f}" if not t.empty else "", "중립"),
        ("평균 습도", f"{h.mean():.1f}%" if not h.empty else "N/A", f"최고 {h.max():.0f} / 최저 {h.min():.0f}" if not h.empty else "", "중립"),
        ("충격 감지", str(int(((report_df["hit"] == 0) & (report_df["hit"].shift(1) != 0)).sum())), "이벤트 횟수", "중립"),
    ])
    st.write("")

with st.container(border=True):
    section_title(f"{period} 온도 데이터", "선택한 기간 동안의 온도 데이터 추이를 확인합니다.")
    range_choice = st.radio("범위", ["1시간", "6시간", "24시간"], horizontal=True, label_visibility="collapsed", key="rp_range")
    minutes = {"1시간": 60, "6시간": 360, "24시간": 1440}[range_choice]
    chart_df = get_readings(minutes)
    if not chart_df.empty and chart_df["temp"].notna().any():
        temp_c = sensor_color("temp")
        chart = alt.Chart(chart_df).mark_line(color=temp_c, strokeWidth=2).encode(
            x=alt.X("timestamp:T", title=None), y=alt.Y("temp:Q", title="°C", scale=alt.Scale(zero=False))
        )
        st.altair_chart(chart.properties(height=300).configure_view(strokeWidth=0).configure_axis(gridColor="#1f2a44", domainColor="#1f2a44", labelColor="#94a3b8"), use_container_width=True)
    else:
        st.caption("데이터 없음")
