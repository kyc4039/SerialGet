import streamlit as st

from src.queries import get_latest_reading, time_ago
from src.sensors import SENSORS, display_value, seconds_since, sensor_status
from src.ui import device_table, inject_css, kpi_row, page_header, section_title

inject_css()
page_header("디바이스 관리", "모든 등록된 디바이스의 상태를 확인하고 관리합니다.")

latest = get_latest_reading()
since = seconds_since(latest)

rows = []
for s in SENSORS:
    value = latest.get(s["col"]) if latest else None
    rows.append({
        "ID": s["id"],
        "디바이스명": s["name"],
        "상태": sensor_status(s, value, since),
        "위치": s["location"],
        "마지막 활동": time_ago(latest["timestamp"]) if latest else "-",
        "주요 값": display_value(s, value),
    })

counts = {k: sum(1 for r in rows if r["상태"] == k) for k in ["온라인", "경고", "위험", "오프라인"]}
kpi_row([
    ("온라인", str(counts["온라인"]), "정상 동작 중", "온라인"),
    ("경고", str(counts["경고"]), "임계값 접근", "경고"),
    ("위험", str(counts["위험"]), "즉시 확인 필요", "위험"),
    ("오프라인", str(counts["오프라인"]), "30초 이상 미수신", "오프라인"),
])

st.write("")

with st.container(border=True, height=520):
    section_title("디바이스 목록", "모든 등록된 디바이스의 상태를 확인합니다.")
    status_filter = st.selectbox("상태 필터", ["전체", "온라인", "경고", "위험", "오프라인"], label_visibility="collapsed")
    filtered = rows if status_filter == "전체" else [r for r in rows if r["상태"] == status_filter]
    if filtered:
        device_table(filtered)
    else:
        st.caption("조건에 맞는 디바이스가 없습니다.")
