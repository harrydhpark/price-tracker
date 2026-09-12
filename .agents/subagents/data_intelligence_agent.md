# 🤖 Subagent Spec: Data Intelligence Agent (Price & Lineup Analyst)

## 1. Role & Mission
- **Role Name**: Data Intelligence Agent (데이터 관리 및 분석 전담 서브에이전트)
- **Primary Mission**:
  - 유럽 11개국(및 향후 확장 국가/지역)의 실시간 수집 가격 데이터를 정규화, 검증 및 시계열 분석.
  - LG vs Samsung 1:1 라인업(OLED, Micro RGB, QNED/QLED, UHD 4K) 가격 갭(Price Gap) 산출 및 포지셔닝 우위 판정.
  - 주간(WoW) 및 일간(DoD) 가격 변동, 프로모션 공세(캐시백, 번들, 회원 쿠폰) 트렌드 자동 추적.
  - C-Level 및 실무진을 위한 종합 경영 브리핑 마크다운 리포트(`Executive_Price_Briefing_{YYYYMMDD}.md`) 발행 및 독립형 웹 대시보드 주입용 데이터(`executive_summary_data.json`) 생성.

---

## 2. Core Architecture & Responsibilities

```
                      +------------------------------------------+
                      |       Master Orchestrator Agent          |
                      |        (scripts/orchestrator.py)         |
                      +--------------------+---------------------+
                                           |
                    +----------------------+----------------------+
                    |                                             |
+-------------------v--------------------+  +---------------------v--------------------+
|  Scraper & Region Specialist Agents    |  |       Data Intelligence Agent            |
|   (DACH, Western EU, Eastern EU)       |  |  (scripts/data_intelligence_engine.py)   |
+-------------------+--------------------+  +---------------------+--------------------+
                    |                                             |
                    | Raw Scrapes                                 | Reads DB & Workbooks
                    v                                             v
        [ data/raw_*.json ]                       [ data/price_history.db ]
        [ 22-Sheet Workbooks ]                    [ config/regions/*.json ]
                                                                  |
                                                                  v
                                              +-------------------+--------------------+
                                              | Output Deliverables:                   |
                                              | 1. Executive_Price_Briefing.md         |
                                              | 2. executive_summary_data.json         |
                                              | 3. Embedded AI Dashboard View          |
                                              +----------------------------------------+
```

---

## 3. Data Inputs & Dependencies
1. **SQLite Database**: `data/price_history.db`
   - Multi-country, currency-neutral table: `daily_prices`.
   - Historical records (31,000+ snapshots) for YoY, WoW, DoD baseline comparison.
2. **Current Survey Workbook**: `data/price tracker_EU_{YYYY MMDD}_v1.xlsx` (22 sheets across 11 countries).
3. **Region & Pairing Configurations**: `config/regions/*.json`
   - `dach.json` (DE, AT, CH)
   - `western_eu.json` (FR, UK, ES, IT, NL)
   - `eastern_eu.json` (CZ, GR, HU)
   - Extensible via `config/regions/region_template.json` for new countries.

---

## 4. Key Analytical Modules
### A. Lineup Gap Analyzer (`analyze_1to1_lineup_gaps`)
- Evaluates 1:1 direct competitive pairs across sizes:
  - **Flagship OLED**: LG G6 vs Samsung S95H (55", 65", 77", 83")
  - **Mainstream OLED**: LG C6 vs Samsung S90H (42", 48", 55", 65", 77", 83")
  - **Entry OLED**: LG B6 vs Samsung S85H (48", 55", 65", 77", 83")
  - **Micro RGB**: LG MRGB87B vs Samsung R85H (55", 65", 75", 86") & MRGB96B vs R95H (100")
  - **Premium QNED/QLED**: LG QNED86B / QNED87 vs Samsung QN80H / QN70H
- Normalizes local currencies (GBP, CHF, CZK, HUF) to EUR.
- Categorizes verdict:
  - `LG Advantage`: Price $\le -2.0\%$ lower than Samsung.
  - `Parity`: Price within $\pm 2.0\%$.
  - `LG Premium`: Price $> +2.0\%$ higher than Samsung.

### B. Time-Series Trend Tracker (`analyze_price_movements`)
- Compares target date prices against baseline prior survey dates.
- Identifies Top 10 aggressive price reductions and price increases.
- Generates brand price change velocity metrics (number of price drops vs hikes).

### C. Promotional Intensity Scanner (`analyze_promotional_campaigns`)
- Scans `promo_text` across all active SKUs.
- Categorizes tactics: Cashback, Direct Cut, Member Voucher, Soundbar Bundle, Instant Rebates.
- Computes brand promo penetration rate (% of active lineup on promotion).

---

## 5. Execution Interface (CLI)

```bash
# Full analysis and report generation for latest survey date
.\python_env\python.exe scripts/data_intelligence_engine.py

# Targeted analysis for specific country
.\python_env\python.exe scripts/data_intelligence_engine.py --country DE

# Analysis for specific historical date
.\python_env\python.exe scripts/data_intelligence_engine.py --date 2026-09-07
```

---

## 6. Zero Historical Price Injection & Guardrails Compliance
- **Zero Fabrication**: The agent only analyzes verified, live-scraped records present in `daily_prices` for the specified survey date.
- **Strict B6 Guard**: Enforces display type verification (`OLED` vs `QNED/UHD`) to avoid misclassifying budget `QNED81B6C` models as OLED flagships.
- **Currency Accuracy**: Strictly uses current real exchange rates (HUF: 398, CZK: 25, GBP: 1.18, CHF: 1.05).
