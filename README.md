# SerialGet

시리얼(아두이노 등) 센서 데이터를 수집해 SQLite에 저장하고, Streamlit 대시보드로 실시간 모니터링하는 미들웨어입니다.

## 구성 요소

| 파일/폴더 | 역할 |
|---|---|
| `sender.py` | 실제 하드웨어 없이 테스트할 수 있도록 랜덤워크 방식으로 센서값을 생성해 COM4로 송신하는 시뮬레이터 |
| `console_bridge.py` | COM5에서 시리얼 라인을 읽어 파싱한 뒤 `console_data.db`(SQLite)에 저장하는 브릿지 |
| `console_data.db` | 수집된 센서 읽기값이 쌓이는 SQLite DB (`readings` 테이블) |
| `console_dashboard/` | Streamlit 멀티페이지 대시보드 앱 |

### 대시보드 페이지 구성 (`console_dashboard/`)

- `main.py` — 대시보드/디바이스/센서/알림/리포트 5개 페이지 네비게이션
- `pages/overview.py`, `devices.py`, `sensors.py`, `alerts.py`, `reports.py` — 각 화면
- `src/db.py` — DB 커넥션 전담
- `src/queries.py` — 조회 전용 쿼리 (최근 데이터, 최신값, 이벤트/구간 전이 기반 알림 피드 생성 등)
- `src/sensors.py` — 센서를 "디바이스"로 취급하는 공통 설정 (임계값, 표시 포맷, 색상)
- `src/ui.py` — 공통 UI 컴포넌트 (다크 테마 카드/뱃지/게이지 등)

## 센서 구성

연속값: 온도, 습도, 조도(CdS), 화염(Flame), 수위(Water), 초음파거리(Dist)
이벤트/상태: 도어(Reed), 진동(Hit), 소음(Sound)

시리얼로 전달되는 데이터 포맷 예시:

```
switch:1,cds:512,flame:900,water:120,sound:0,reed:0,hit:1,dist:45,temp:24.3,hum:52.1
```

## 요구 사항

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) 패키지 매니저

## 설치

```powershell
uv sync
```

## 실행

1. 센서 데이터 수집 브릿지 실행 (실제 장치가 COM5에 연결되어 있어야 함)

   ```powershell
   uv run python console_bridge.py
   ```

   테스트용으로 실제 장치 없이 데이터를 흘려보내고 싶다면, 다른 터미널에서 시뮬레이터를 함께 실행합니다 (COM4 ↔ COM5를 가상 시리얼 포트 페어로 연결한 환경 기준).

   ```powershell
   uv run python sender.py
   ```

2. 대시보드 실행

   ```powershell
   uv run streamlit run console_dashboard/main.py
   ```

## 설정값 변경

- 시리얼 포트/보드레이트: `sender.py`, `console_bridge.py` 상단의 `SERIAL_PORT`, `BAUD_RATE`
- 센서 임계값(정상/경고/위험 구간): `console_dashboard/src/sensors.py`의 `THRESHOLDS`
