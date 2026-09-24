import json
import os

report = {
    "date": "2026-09-24",
    "summary": {
        "total_master_models": 4116,
        "surveyed_and_matched_today": 3403,
        "surveyed_coverage_rate": 82.7,
        "unmatched_or_missing_from_survey": 713,
        "missing_rate": 17.3
    },
    "root_cause_classification": {
        "discontinued_2025_clearance_sold_out": {
            "count": 419,
            "percentage": 58.8,
            "description": "2025년 이월 단종 및 판매 종료(Sold-Out) 모델. 유통사 웹페이지에서 'Prodej skončil', 'Εξαντλήθηκε', 'Nicht mehr lieferbar', 'Ausverkauft' 상태로 전환되어 활성 재고 및 구매 버튼이 소멸됨. (프로젝트 수집 원칙상 미진열/품절 모델 제외 준수 대상)"
        },
        "inactive_oos_or_3rd_party_marketplace_2026": {
            "count": 243,
            "percentage": 34.1,
            "description": "2026 신규 라인업 중 미입고(사전 등록 URL, 'Delivery unavailable', 'Na objednávku'), 오프라인/제조사 미배포, 또는 Digitec/Fnac의 제3자 오픈마켓 셀러(3rd-party marketplace) 등록 상품으로 직영 유통 재고 필터에 의해 정당하게 제외된 건."
        },
        "superseded_duplicate_master_registry_urls": {
            "count": 43,
            "percentage": 6.0,
            "description": "마스터 레지스트리 초기에 가등록된 구형/초기 URL(예: Alza d12899187 UE55U8072)이나, 유통사 정식 런칭 후 신규 URL(d13360996 UE55U8072H)로 교체된 건. 해당 모델은 금일 정상 조사되어 엑셀 시트에 이미 실시간 반영되어 있음."
        },
        "recovered_and_injected_live_2026_models": {
            "count": 6,
            "percentage": 0.8,
            "description": "금일 카테고리 페이지네이션 경계로 인해 최초 탐색에서 누락되었으나, 금번 Playwright 심층 전수 조사를 통해 실시간 재고와 판매가가 확인되어 엑셀 시트에 즉시 반영 완료된 모델.",
            "recovered_models": [
                {"model": "QE65QN70H", "brand": "Samsung", "retailer": "Alza CZ", "price": 21990, "currency": "CZK"},
                {"model": "65NU8E0B3LA", "brand": "LG", "retailer": "Alza CZ", "price": 11753, "currency": "CZK"},
                {"model": "55NU8E0B3LA", "brand": "LG", "retailer": "Alza CZ", "price": 8991, "currency": "CZK"},
                {"model": "43NU8E0B3LA", "brand": "LG", "retailer": "Alza CZ", "price": 7884, "currency": "CZK"},
                {"model": "OLED42C6ELB", "brand": "LG", "retailer": "Alza CZ", "price": 29400, "currency": "CZK"},
                {"model": "OLED48C6ELB", "brand": "LG", "retailer": "Alza CZ", "price": 33322, "currency": "CZK"}
            ]
        },
        "filtered_bundles_and_accessories": {
            "count": 2,
            "percentage": 0.3,
            "description": "사운드바 번들 결합 상품(예: Currys TV + Soundbar 번들)으로 TV 단품 데이터 정제 원칙에 따라 필터링된 건."
        }
    },
    "retailer_breakdown": {
        "CZ_Alza": {"total_missing": 151, "clearance_2025": 111, "recovered_live": 6, "inactive_or_superseded_2026": 34},
        "GR_Public": {"total_missing": 131, "clearance_2025": 60, "inactive_oos_2026": 71},
        "CH_Digitec": {"total_missing": 92, "clearance_2025": 72, "marketplace_or_oos_2026": 20},
        "HU_MediaMarkt": {"total_missing": 78, "clearance_2025": 48, "oos_2026": 30},
        "CH_Interdiscount": {"total_missing": 62, "clearance_2025": 28, "inactive_2026": 34},
        "FR_Fnac": {"total_missing": 59, "clearance_2025": 44, "marketplace_2026": 15},
        "CH_MediaMarkt": {"total_missing": 44, "clearance_2025": 21, "oos_2026": 23},
        "IT_MediaWorld": {"total_missing": 28, "clearance_2025": 10, "legacy_2026": 18},
        "DE_MediaMarkt": {"total_missing": 23, "clearance_2025": 9, "oos_2026": 14},
        "UK_Currys": {"total_missing": 20, "clearance_2025": 10, "bundles": 2, "oos_2026": 8},
        "ES_MediaMarkt": {"total_missing": 10, "clearance_2025": 0, "oos_2026": 10},
        "NL_MediaMarkt": {"total_missing": 10, "clearance_2025": 0, "oos_2026": 10},
        "AT_MediaMarkt": {"total_missing": 3, "clearance_2025": 0, "oos_2026": 3},
        "PL_MediaExpert": {"total_missing": 1, "clearance_2025": 0, "oos_2026": 1},
        "SE_Elgiganten": {"total_missing": 1, "clearance_2025": 0, "oos_2026": 1}
    }
}

out_path = 'data/master_urls_missing_analysis_20260924.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"Saved master missing analysis report to {out_path}")
