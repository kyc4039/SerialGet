"""공통 UI 컴포넌트 (다크 테마). HTML은 한 줄로 조립한다 (마크다운 들여쓰기 코드블록 오인 방지)."""

from datetime import datetime

import streamlit as st

# 심각도/상태 → (배지 배경, 글자색, 강조색)
STATUS_STYLE = {
    "온라인": ("rgba(34,197,94,.16)", "#4ade80", "#22c55e"),
    "정상": ("rgba(34,197,94,.16)", "#4ade80", "#22c55e"),
    "경고": ("rgba(245,158,11,.18)", "#fbbf24", "#f59e0b"),
    "주의": ("rgba(245,158,11,.18)", "#fbbf24", "#f59e0b"),
    "위험": ("rgba(239,68,68,.2)", "#f87171", "#ef4444"),
    "오프라인": ("rgba(148,163,184,.16)", "#cbd5e1", "#94a3b8"),
    "정보": ("rgba(59,130,246,.2)", "#60a5fa", "#3b82f6"),
    "중립": ("rgba(148,163,184,.14)", "#cbd5e1", "#94a3b8"),  # KPI 정보성 카드 전용 무채색
}

CHART_COLOR = "#60a5fa"
NEUTRAL_CARD_COLOR = "#94a3b8"  # 센서 카드 기본색: 무채색(회색). 경고/위험일 때만 색이 들어와 눈에 잘 띄고, 정상 복귀 시 다시 회색으로.

CSS = (
    "<style>"
    ".block-container{max-width:1240px;padding-top:4rem;padding-bottom:2rem;}"
    ".topbar{display:flex;justify-content:space-between;align-items:flex-end;padding:4px 0 14px;border-bottom:1px solid #1f2a44;margin-bottom:18px;}"
    ".topbar-title{font-size:24px;font-weight:700;color:#f1f5f9;margin:0;line-height:1.3;}"
    ".topbar-sub{font-size:13px;color:#94a3b8;margin-top:2px;}"
    ".topbar-right{font-size:13px;color:#94a3b8;text-align:right;}"
    ".kpi{border:1px solid #1f2a44;border-top:3px solid #334155;border-radius:12px;padding:16px 20px;background:#111a2e;height:100%;}"
    ".kpi-title{font-size:13px;color:#94a3b8;margin-bottom:6px;}"
    ".kpi-value{font-size:30px;font-weight:700;color:#f1f5f9;line-height:1.1;}"
    ".kpi-sub{font-size:12px;color:#94a3b8;margin-top:6px;}"
    ".badge{display:inline-block;padding:2px 10px;border-radius:999px;font-size:12px;font-weight:600;white-space:nowrap;border:1px solid transparent;}"
    ".card-title{font-size:16px;font-weight:600;color:#f1f5f9;margin:0;}"
    ".card-desc{font-size:13px;color:#94a3b8;margin:2px 0 12px;}"
    ".alert{display:flex;flex-direction:column;gap:4px;padding:12px 14px;border:1px solid #1f2a44;border-left:4px solid #334155;border-radius:10px;background:#111a2e;margin-bottom:10px;margin-right:4px;}"
    ".alert-head{display:flex;justify-content:space-between;align-items:center;gap:8px;}"
    ".alert-dev{font-size:14px;font-weight:600;color:#f1f5f9;}"
    ".alert-time{font-size:12px;color:#94a3b8;}"
    ".alert-msg{font-size:13px;color:#cbd5e1;}"
    ".alert-id{font-size:12px;color:#64748b;}"
    ".gauge{border:1px solid #1f2a44;border-radius:12px;padding:14px 16px;background:#111a2e;margin-bottom:18px;min-height:126px;display:flex;flex-direction:column;}"
    ".gauge-label{font-size:16px;font-weight:600;color:#e2e8f0;min-height:24px;display:flex;align-items:center;line-height:1.3;margin-bottom:6px;}"
    ".gauge-val-row{margin-bottom:2px;}"
    ".gauge-val{font-weight:700;color:#f1f5f9;font-size:24px;}"
    ".gauge-bar{background:#1f2a44;height:8px;border-radius:999px;overflow:hidden;margin-top:2px;}"
    ".gauge-fill{height:8px;border-radius:999px;}"
    ".gauge-range{display:flex;justify-content:space-between;font-size:11px;color:#64748b;margin-top:6px;}"
    ".gauge-badge-row{margin-bottom:8px;}"
    ".status-row{display:flex;align-items:center;justify-content:space-between;margin-top:auto;}"
    "div[data-testid='column']{min-width:210px;}"
    "table.dev{width:100%;border-collapse:collapse;font-size:14px;}"
    "table.dev th{text-align:left;padding:10px 12px;color:#94a3b8;font-weight:500;border-bottom:1px solid #1f2a44;font-size:13px;}"
    "table.dev td{padding:12px;border-bottom:1px solid #16213a;color:#e2e8f0;}"
    "table.dev tr:last-child td{border-bottom:none;}"
    "table.dev tr:hover td{background:#16213a;}"
    "div[data-testid='stVerticalBlockBorderWrapper']{border-radius:12px;border-color:#1f2a44 !important;background:#0f172a;}"
    "#MainMenu,footer{visibility:hidden;}"
    "</style>"
)


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def accent(status: str) -> str:
    return STATUS_STYLE.get(status, STATUS_STYLE["오프라인"])[2]


def page_header(title: str, subtitle: str, right_text: str | None = None):
    right = right_text or datetime.now().strftime("%Y년 %m월 %d일 %H:%M:%S")
    st.markdown(
        f"<div class='topbar'><div><div class='topbar-title'>{title}</div><div class='topbar-sub'>{subtitle}</div></div>"
        f"<div class='topbar-right'>{right}</div></div>",
        unsafe_allow_html=True,
    )


def badge(text: str) -> str:
    bg, fg, line = STATUS_STYLE.get(text, STATUS_STYLE["오프라인"])
    return f"<span class='badge' style='background:{bg};color:{fg};border-color:{line}55'>{text}</span>"


def kpi_row(items: list):
    """items: (title, value, sub) 또는 (title, value, sub, status) — status가 있으면 상단 띠와 숫자에 색을 준다."""
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        title, value, sub = item[:3]
        status = item[3] if len(item) > 3 else None
        top = f"border-top-color:{accent(status)}" if status else ""
        val_color = f"color:{STATUS_STYLE[status][1]}" if status else ""
        col.markdown(
            f"<div class='kpi' style='{top}'><div class='kpi-title'>{title}</div>"
            f"<div class='kpi-value' style='{val_color}'>{value}</div><div class='kpi-sub'>{sub}</div></div>",
            unsafe_allow_html=True,
        )


def section_title(title: str, desc: str = ""):
    html = f"<div class='card-title'>{title}</div>"
    if desc:
        html += f"<div class='card-desc'>{desc}</div>"
    st.markdown(html, unsafe_allow_html=True)


def alert_card(a: dict, time_text: str):
    bg, _, line = STATUS_STYLE.get(a["severity"], STATUS_STYLE["정보"])
    st.markdown(
        f"<div class='alert' style='border-left-color:{line};background:linear-gradient(90deg,{bg} 0%,#111a2e 40%)'>"
        f"<div class='alert-head'><span class='alert-dev'>{a['device']}</span>{badge(a['severity'])}</div>"
        f"<div class='alert-time'>{time_text}</div><div class='alert-msg'>{a['message']}</div>"
        f"<div class='alert-id'>ID: {a['id']}</div></div>",
        unsafe_allow_html=True,
    )


def gauge_card(label: str, value_text: str, ratio: float, min_text: str, max_text: str, status: str = "온라인", identity_color: str | None = None):
    # 평상시(온라인)엔 통일 색을 쓰고, 위험/경고일 때만 심각도 색을 씀. identity_color는 카드에는 더 이상 쓰지 않음(차트 색은 별도 유지).
    color = accent(status) if status in ("위험", "경고") else NEUTRAL_CARD_COLOR
    pct = int(max(0, min(1, ratio)) * 100)
    st.markdown(
        f"<div class='gauge' style='border-left:4px solid {color}'>"
        f"<div class='gauge-label'>{label}</div>"
        f"<div class='gauge-val-row'><span class='gauge-val' style='color:{color}'>{value_text}</span></div>"
        f"<div class='gauge-bar'><div class='gauge-fill' style='width:{pct}%;background:{color}'></div></div>"
        f"<div class='gauge-range'><span>{min_text}</span><span>{max_text}</span></div></div>",
        unsafe_allow_html=True,
    )


def status_card(label: str, value_text: str, status: str, identity_color: str | None = None):
    """불리언 센서용 카드: 라벨은 상단, 뱃지와 값은 한 줄에 좌우로 배치."""
    color = accent(status) if status in ("위험", "경고") else NEUTRAL_CARD_COLOR
    st.markdown(
        f"<div class='gauge' style='border-left:4px solid {color}'>"
        f"<div class='gauge-label'>{label}</div>"
        f"<div class='status-row'>{badge(status)}<span class='kpi-value' style='font-size:24px;color:{color}'>{value_text}</span></div></div>",
        unsafe_allow_html=True,
    )


def device_table(rows: list[dict]):
    head = "".join(f"<th>{h}</th>" for h in ["ID", "디바이스명", "상태", "위치", "마지막 활동", "주요 값"])
    body = ""
    for r in rows:
        val_color = STATUS_STYLE.get(r["상태"], STATUS_STYLE["오프라인"])[1] if r["상태"] in ("위험", "경고") else "#f1f5f9"
        body += (
            f"<tr><td style='color:#94a3b8'>{r['ID']}</td><td>{r['디바이스명']}</td><td>{badge(r['상태'])}</td>"
            f"<td>{r['위치']}</td><td style='color:#94a3b8'>{r['마지막 활동']}</td><td style='font-weight:600;color:{val_color}'>{r['주요 값']}</td></tr>"
        )
    st.markdown(f"<table class='dev'><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>", unsafe_allow_html=True)
