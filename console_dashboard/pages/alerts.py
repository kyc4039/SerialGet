from datetime import datetime

import pandas as pd
import streamlit as st

from src.queries import build_alert_feed, get_readings, time_ago
from src.ui import alert_card, inject_css, kpi_row, page_header, section_title

inject_css()
page_header("알림 관리", "시스템에서 발생한 모든 알림을 확인하고 관리합니다.")

f1, f2 = st.columns(2)
severity_filter = f1.selectbox("심각도 필터", ["전체", "위험", "경고", "정보"])
range_choice = f2.selectbox("조회 범위", ["최근 1시간", "최근 6시간", "최근 24시간"])
minutes = {"최근 1시간": 60, "최근 6시간": 360, "최근 24시간": 1440}[range_choice]

df = get_readings(minutes)
all_alerts = build_alert_feed(df)

kpi_row([
    ("전체", str(len(all_alerts)), range_choice, "중립"),
    ("위험", str(sum(1 for a in all_alerts if a["severity"] == "위험")), "즉시 확인 필요", "위험"),
    ("경고", str(sum(1 for a in all_alerts if a["severity"] == "경고")), "임계값 접근", "경고"),
    ("정보", str(sum(1 for a in all_alerts if a["severity"] == "정보")), "정상 복귀 등", "정보"),
])

st.write("")

alerts = all_alerts if severity_filter == "전체" else [a for a in all_alerts if a["severity"] == severity_filter]

with st.container(border=True, height=600):
    section_title(f"알림 목록 ({len(alerts)}건)", "시스템에서 발생한 모든 알림을 확인합니다.")
    if alerts:
        for a in alerts:
            alert_card(a, time_ago(a["ts"]))
    else:
        st.caption("조건에 맞는 알림이 없습니다.")

if alerts:
    alert_df = pd.DataFrame(alerts)
    alert_df["ts"] = alert_df["ts"].astype(str)
    st.download_button(
        "알림 이력 CSV 다운로드",
        alert_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )
