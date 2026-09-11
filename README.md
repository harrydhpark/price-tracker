# Pan-European TV Price Tracker & Promo Analyzer

유럽 주요 11개국(스위스, 독일, 프랑스, 영국, 이탈리아, 스페인, 네덜란드, 오스트리아, 체코, 그리스, 헝가리)의 리테일러 웹사이트로부터 2025/2026 라인업 TV 가격 및 프로모션 데이터를 수집하고, 품질 검증, 엑셀 분석 리포트, 인터랙티브 웹 대시보드 생성 및 Firebase 호스팅 배포를 자동화하는 전사 파이프라인 시스템입니다.

---

## 1. 주요 기능 및 아키텍처

- **WAF/Anti-Bot 우회 수집 엔진**:
  - Scrapling StealthySession (MediaMarkt DACH/스위스 Cloudflare Turnstile 자동 해결)
  - Playwright sandboxed headless context (Interdiscount, Digitec 등)
  - Curl_cffi / Firecrawl stealth pipeline (Fnac/Darty DataDome 우회)
- **Pan-European Master URL Registry (data/master_product_urls.json)**:
  - 유럽 전 국가의 검증된 모델 PDP URL 영구 등록 및 누락 방지
  - 매 조사마다 신규 모델 자동 등록 및 비활성/단종 모델 검증
- **시계열 가격 데이터베이스 (data/price_history.db)**:
  - SQLite 기반 통화 중립 시계열 데이터 저장 (일자, 국가, 리테일러, 브랜드, 모델, 화면크기, 출시년도, 판매가, 정가, 통화, 프로모션 텍스트)
  - 과거 수집 이력(History, History_EU, History_AU) 전수 백필 및 조사 완료 시 자동 동기화
- **구조화 로깅 (data/scraping_logs.jsonl)**:
  - 스크래퍼 실행별 JSON Lines 형식 로그 기록 (시작/종료 시각, HTTP 상태, 추출/필터링 건수, 에러 내역)
  - 파일 크기 10MB 도달 시 자동 롤오버 관리
- **품질 게이트 및 가격 이상탐지 (scripts/quality_gates.py)**:
  - **R1 (급격한 가격 변동)**: 직전 조사 대비 ±30% 변동 감지 (프로모션 문구 동시 변경 시 정당한 할인으로 면제)
  - **R2 (국가 간 이상치)**: 동일 모델 EUR 환산 후 전 국가 중앙값 대비 2.0배 이상 편차 차단 (CRITICAL)
  - **R3 (가격 결측/0원)**: 2회 연속 0원 또는 결측 시 경고 (WARN)
  - **R4 (카테고리/화면크기별 가격 플로어)**: OLED, Micro RGB, QNED, UHD 4K 패널 및 화면 크기별 최저 하한선 미달 차단 (CRITICAL)
  - 이상치 비율 5% 초과 또는 CRITICAL 룰 위반 시 **배포 즉시 차단 (exit 2)**
- **실패 안전 전파 (Fail-Safe Pipeline)**:
  - 수집 실패 또는 데이터 누락 시 무음 통과 방지 (하위 동기화, 대시보드 생성, Firebase 배포 단계 자동 차단)
  - 전일 대비 모델 수 10% 이상 변동 시 재조사 검증

---

## 2. 환경 요구사항 및 설치

### 요구 환경
- **운영체제**: Windows 10/11
- **Python**: 3.10 이상 (프로젝트 내 가상환경: .\python_env\python.exe)
- **Node.js**: Firebase CLI (irebase-tools) 설치 필요

### 의존성 설치
`powershell
# 가상환경 파이썬 확인
.\python_env\python.exe --version

# 의존성 패키지 설치 (버전 핀 고정)
.\python_env\python.exe -m pip install -r requirements.txt

# Playwright 브라우저 바이너리 설치 (최초 1회)
.\python_env\python.exe -m playwright install chromium
`

---

## 3. 실행 방법 (Usage)

### 전체 조사 및 자동 배포 (권장)
스위스 및 유럽 리테일러 수집, 동기화, 품질 게이트, 대시보드 생성, Firebase 배포까지 원스톱 실행:
`powershell
.\python_env\python.exe scripts/run_survey_with_check.py
`

### 특정 리테일러 장애 시 부분 수집 허용
수집 실패한 리테일러가 있더라도 나머지 정상 수집된 데이터로 파이프라인을 계속 진행할 경우:
`powershell
.\python_env\python.exe scripts/run_survey_with_check.py --allow-partial
`

### 품질 게이트 단독 실행 (데이터 검증)
수집된 엑셀 파일 또는 최근 데이터의 무결성 및 가격 이상치 검사:
`powershell
.\python_env\python.exe scripts/quality_gates.py
`

### 시계열 DB 수동 동기화 및 백필
과거 워크북 파일들을 SQLite DB로 백필하거나 재구축할 때:
`powershell
.\python_env\python.exe scripts/price_history.py --backfill
`

### 개별 스크래퍼 실행
`powershell
# 스위스 MediaMarkt
.\python_env\python.exe scripts/scrape_mediamarkt_ch.py

# 스위스 Interdiscount
.\python_env\python.exe scripts/scrape_interdiscount.py

# 그리스 Public.gr
.\python_env\python.exe scripts/scrape_public_gr.py

# 체코 Alza.cz
.\python_env\python.exe scripts/scrape_alza_cz.py
`

---

## 4. 디렉터리 구조

`	ext
├── data/
│   ├── master_product_urls.json    # 유럽 통합 마스터 PDP URL 레지스트리
│   ├── price_history.db            # SQLite 시계열 가격 DB
│   ├── scraping_logs.jsonl         # 구조화 수집 로그
│   ├── anomaly_report_*.json       # 품질 게이트 이상탐지 보고서
│   └── raw_*.json                  # 일자별 실시간 원천 수집 데이터
├── dashboard/                      # 배포용 웹 대시보드 (Firebase Hosting 타겟)
│   ├── index.html
│   ├── dashboard.js
│   └── data/
├── scripts/
│   ├── run_survey_with_check.py    # 메인 파이프라인 오케스트레이터
│   ├── quality_gates.py            # 가격 이상탐지 및 품질 게이트
│   ├── price_history.py            # 시계열 DB 모델 및 백필 엔진
│   ├── scrape_logger.py            # JSON Lines 수집 로깅 엔진
│   ├── sync_all_retailers.py       # 스위스 3대 리테일러 동기화 및 엑셀 생성
│   ├── sync_eu_retailers.py        # 유럽 11개국 동기화 및 마스터 엑셀 생성
│   ├── build_master_url_registry.py# 마스터 URL 레지스트리 빌더
│   └── scrape_*.py                 # 국가별/리테일러별 수집 스크립트
├── tests/
│   └── test_parsers.py             # 파서 회귀 테스트 슈트
├── requirements.txt                # 핀 고정 의존성 목록
└── README.md                       # 본 문서
`

---

## 5. 핵심 운영 원칙 (Rules & Best Practices)

1. **Zero Historical Price Injection Policy (과거 가격 주입 절대 금지)**:
   - 과거 조사 엑셀에서 가격을 복사하거나 임의의 기준 가격을 덮어쓰는 행위는 엄격히 금지됩니다.
   - 모든 가격은 당일 실시간 수집 또는 당일 유효한 PDP URL 라이브 프로브 결과만을 반영합니다.
2. **Bulk Excel Data Operations**:
   - 대용량 데이터 전송 시 셀 단위(Cell-by-cell) COM/openpyxl 반복 루프를 금지하고, pandas.ExcelWriter(mode='a', if_sheet_exists='overlay')를 통해 일괄 오버레이합니다.
3. **Strict 2026 Model Naming & OLED Disambiguation (B6 Guard)**:
   - LG 2026 라인업에서 UHD/QNED 모델에 포함된 B6 접미사(65NU850B6LA, 55QNED81B6C 등)가 플래그십 OLED B6로 오분류되지 않도록 패널 타입 및 정규식 경계를 엄격히 검증합니다.
4. **유럽 통화 및 숫자 표기 파싱 표준**:
   - 유럽 대륙의 천단위 마침표(.) 및 소수점 쉼표(,), 프랑스의 Narrow No-Break Space(\u202f), 할부/할인 텍스트 스트리핑 규격을 준수합니다.
