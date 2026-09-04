import streamlit as st

st.set_page_config(page_title="센서 모니터링", layout="wide")

overview_page = st.Page("pages/overview.py", title="대시보드", icon="📊", default=True)
devices_page = st.Page("pages/devices.py", title="디바이스", icon="🖥️")
sensors_page = st.Page("pages/sensors.py", title="센서", icon="📈")
alerts_page = st.Page("pages/alerts.py", title="알림", icon="🔔")
reports_page = st.Page("pages/reports.py", title="리포트", icon="📄")

pg = st.navigation([overview_page, devices_page, sensors_page, alerts_page, reports_page])
pg.run()

