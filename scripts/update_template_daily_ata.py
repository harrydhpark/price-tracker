import os
import re

template_path = 'data/eu_price_dashboard_template.html'
with open(template_path, 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add CSS rules in <style>
css_target = """.sticky-table-container::-webkit-scrollbar-thumb:hover {
            background: #94a3b8;
        }"""
css_replacement = """.sticky-table-container::-webkit-scrollbar-thumb:hover {
            background: #94a3b8;
        }
        .sub-pill {
            transition: all 0.15s ease-in-out;
        }
        .sub-pill.active {
            background-color: #a50034 !important;
            color: #ffffff !important;
            border-color: #a50034 !important;
            box-shadow: 0 2px 6px rgba(165,0,52,0.22);
        }"""

if css_target in c:
    c = c.replace(css_target, css_replacement, 1)
    print("1. CSS added.")
else:
    print("Warning: CSS target not found.")

# 2. Add Exec Pills bar
exec_old = '<div id="top_scroll_exec_ata_matrix_table_wrapper" class="top-scrollbar-wrapper overflow-x-auto overflow-y-hidden mb-1 hidden">'
exec_new = """<!-- Interactive Subsidiary Quick Pill Selector Bar for Daily ATA (Exec View) -->
                    <div id="exec_daily_ata_pills_bar" class="hidden bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-2 mb-3">
                        <div class="flex items-center justify-between">
                            <span class="text-[11px] font-bold text-slate-500">📌 법인 빠른 선택 메뉴 (클릭 시 해당 법인 일별 ATA 매트릭스로 전환)</span>
                            <span class="text-[11px] font-bold" id="exec_daily_ata_active_sub_status" style="color: #a50034;">현재 선택 법인: 🇩🇪 DE 독일 (DG · MediaMarkt)</span>
                        </div>
                        <div class="flex flex-wrap items-center gap-1.5" id="exec_daily_ata_sub_pills_container"></div>
                    </div>
                    <div id="top_scroll_exec_ata_matrix_table_wrapper" class="top-scrollbar-wrapper overflow-x-auto overflow-y-hidden mb-1 hidden">"""

if exec_old in c:
    c = c.replace(exec_old, exec_new, 1)
    print("2. Exec pills bar added.")
else:
    print("Warning: Exec target not found.")

# 3. Remove daily_ata_controls in standalone header
c = re.sub(r'<!-- 일별 조사 전용: 법인/지점 선택 셀렉터 -->\s*<div id="daily_ata_controls"[\s\S]*?</div>\s*</div>', '', c)
print("3. Standalone daily_ata_controls removed.")

# 4. Add Standalone Pills bar
standalone_old = '<div id="top_scroll_standalone_ata_matrix_table_wrapper" class="top-scrollbar-wrapper overflow-x-auto overflow-y-hidden mb-1 hidden">'
standalone_new = """<!-- Interactive Subsidiary Quick Pill Selector Bar for Daily ATA (Matches Leaflet Dashboard UI) -->
                    <div id="daily_ata_pills_bar" class="hidden bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-2 mb-3">
                        <div class="flex items-center justify-between">
                            <span class="text-[11px] font-bold text-slate-500">📌 법인 빠른 선택 메뉴 (클릭 시 해당 법인 일별 ATA 매트릭스로 전환)</span>
                            <span class="text-[11px] font-bold" id="daily_ata_active_sub_status" style="color: #a50034;">현재 선택 법인: 🇩🇪 DE 독일 (DG · MediaMarkt)</span>
                        </div>
                        <div class="flex flex-wrap items-center gap-1.5" id="daily_ata_sub_pills_container"></div>
                    </div>
                    <div id="top_scroll_standalone_ata_matrix_table_wrapper" class="top-scrollbar-wrapper overflow-x-auto overflow-y-hidden mb-1 hidden">"""

if standalone_old in c:
    c = c.replace(standalone_old, standalone_new, 1)
    print("4. Standalone pills bar added.")
else:
    print("Warning: Standalone target not found.")

# 5. Update alignAtaMatrixStickyHeader
align_old = """        function alignAtaMatrixStickyHeader(wrapperId) {
            const tableContainer = document.getElementById(wrapperId);
            if (!tableContainer) return;
            const thead = tableContainer.querySelector('thead');
            if (!thead || thead.rows.length < 3) return;

            const r0 = thead.rows[0];
            const r1 = thead.rows[1];
            const r2 = thead.rows[2];

            const h0 = Math.floor(r0.getBoundingClientRect().height) || 26;
            const h1 = Math.floor(r1.getBoundingClientRect().height) || 26;
            const h2 = Math.floor(r2.getBoundingClientRect().height) || 26;
            const totalHdrHeight = h0 + h1 + h2;

            Array.from(r1.cells).forEach(th => {
                th.style.top = h0 + 'px';
                th.style.boxShadow = '0 -1px 0 #6b7280';
            });
            Array.from(r2.cells).forEach(th => {
                th.style.top = (h0 + h1) + 'px';
                th.style.boxShadow = '0 -1px 0 #6b7280';
            });
            Array.from(r0.querySelectorAll('th[rowspan="3"]')).forEach(th => {
                th.style.height = totalHdrHeight + 'px';
            });

            tableContainer.querySelectorAll('.ata-sticky-cell-label').forEach(lbl => {
                lbl.style.top = (totalHdrHeight + 4) + 'px';
            });
        }"""

align_new = """        function alignAtaMatrixStickyHeader(wrapperId) {
            const tableContainer = document.getElementById(wrapperId);
            if (!tableContainer) return;
            const thead = tableContainer.querySelector('thead');
            if (!thead || thead.rows.length < 2) return;

            if (thead.rows.length === 2) {
                // Daily ATA: 2-row thead
                const r0 = thead.rows[0];
                const r1 = thead.rows[1];
                const h0 = Math.floor(r0.getBoundingClientRect().height) || 28;
                const h1 = Math.floor(r1.getBoundingClientRect().height) || 28;
                const totalHdrHeight = h0 + h1;

                Array.from(r1.cells).forEach(th => {
                    th.style.top = h0 + 'px';
                    th.style.boxShadow = '0 -1px 0 #6b7280';
                });
                Array.from(r0.querySelectorAll('th[rowspan="2"]')).forEach(th => {
                    th.style.height = totalHdrHeight + 'px';
                });
                tableContainer.querySelectorAll('.ata-sticky-cell-label').forEach(lbl => {
                    lbl.style.top = (totalHdrHeight + 4) + 'px';
                });
            } else if (thead.rows.length >= 3) {
                // Weekly ATA: 3-row thead
                const r0 = thead.rows[0];
                const r1 = thead.rows[1];
                const r2 = thead.rows[2];
                const h0 = Math.floor(r0.getBoundingClientRect().height) || 26;
                const h1 = Math.floor(r1.getBoundingClientRect().height) || 26;
                const h2 = Math.floor(r2.getBoundingClientRect().height) || 26;
                const totalHdrHeight = h0 + h1 + h2;

                Array.from(r1.cells).forEach(th => {
                    th.style.top = h0 + 'px';
                    th.style.boxShadow = '0 -1px 0 #6b7280';
                });
                Array.from(r2.cells).forEach(th => {
                    th.style.top = (h0 + h1) + 'px';
                    th.style.boxShadow = '0 -1px 0 #6b7280';
                });
                Array.from(r0.querySelectorAll('th[rowspan="3"]')).forEach(th => {
                    th.style.height = totalHdrHeight + 'px';
                });
                tableContainer.querySelectorAll('.ata-sticky-cell-label').forEach(lbl => {
                    lbl.style.top = (totalHdrHeight + 4) + 'px';
                });
            }
        }"""

if align_old in c:
    c = c.replace(align_old, align_new, 1)
    print("5. alignAtaMatrixStickyHeader updated.")
else:
    print("Warning: alignAtaMatrixStickyHeader target not found.")

# 6. Replace Daily ATA JS Block (Pills logic + Daily ATA Table with 4 columns matching Weekly ATA & Image 2)
daily_block_regex = r'// =========================================================================\s*// Corporate Subsidiary x Product DAILY ATA Matrix[\s\S]*?function renderExecutiveGapTable'

daily_block_new = """// =========================================================================
        // Corporate Subsidiary x Product DAILY ATA Matrix (November 1~30) Logic
        // =========================================================================
        let currentAtaViewMode = 'weekly'; // 'weekly' or 'daily'
        let currentDailySub = 'DG';       // Default to DG (Germany)

        // 15 Subsidiaries in ABC Order matching Promotion Leaflet Dashboard
        const DAILY_ATA_SUB_LIST = [
            { code: "AT", sub: "AG", flag: "🇦🇹", name: "AT 오스트리아", retailer: "MediaMarkt" },
            { code: "CH", sub: "SWISS", flag: "🇨🇭", name: "CH 스위스", retailer: "MediaMarkt" },
            { code: "CZ", sub: "CK", flag: "🇨🇿", name: "CZ 체코", retailer: "Alza" },
            { code: "DE", sub: "DG", flag: "🇩🇪", name: "DE 독일", retailer: "MediaMarkt" },
            { code: "ES", sub: "ES", flag: "🇪🇸", name: "ES 스페인", retailer: "MediaMarkt" },
            { code: "FR", sub: "FS", flag: "🇫🇷", name: "FR 프랑스", retailer: "Boulanger" },
            { code: "GR", sub: "HS", flag: "🇬🇷", name: "GR 그리스", retailer: "Kotsovolos" },
            { code: "HU", sub: "MK", flag: "🇭🇺", name: "HU 헝가리", retailer: "MediaMarkt" },
            { code: "IT", sub: "IS", flag: "🇮🇹", name: "IT 이탈리아", retailer: "MediaWorld" },
            { code: "NL", sub: "BN", flag: "🇳🇱", name: "NL 네덜란드", retailer: "MediaMarkt" },
            { code: "PL", sub: "PL", flag: "🇵🇱", name: "PL 폴란드", retailer: "MediaExpert" },
            { code: "PT", sub: "PT", flag: "🇵🇹", name: "PT 포르투갈", retailer: "Worten" },
            { code: "RO", sub: "RO", flag: "🇷🇴", name: "RO 루마니아", retailer: "eMAG" },
            { code: "SE", sub: "SW", flag: "🇸🇪", name: "SE 스웨덴", retailer: "Elgiganten" },
            { code: "UK", sub: "UK", flag: "🇬🇧", name: "GB UK 영국", retailer: "Currys" }
        ];

        function renderDailyAtaPills() {
            const containers = [
                document.getElementById('daily_ata_sub_pills_container'),
                document.getElementById('exec_daily_ata_sub_pills_container')
            ];
            const statusEls = [
                document.getElementById('daily_ata_active_sub_status'),
                document.getElementById('exec_daily_ata_active_sub_status')
            ];

            const currentItem = DAILY_ATA_SUB_LIST.find(item => item.sub === currentDailySub) || DAILY_ATA_SUB_LIST[3];

            statusEls.forEach(el => {
                if (el) {
                    el.innerHTML = `현재 선택 법인: <span class="font-extrabold">${currentItem.flag} ${currentItem.code} ${currentItem.name.replace(/^[A-Z]+\\s*/, '')} (${currentItem.sub} · ${currentItem.retailer})</span>`;
                }
            });

            containers.forEach(container => {
                if (!container) return;
                let html = '';
                DAILY_ATA_SUB_LIST.forEach(item => {
                    const isActive = (item.sub === currentDailySub);
                    const activeClass = isActive
                        ? 'active bg-[#a50034] text-white border-[#a50034] shadow-sm'
                        : 'bg-white text-slate-700 hover:bg-slate-100 border-slate-200';
                    const korShort = item.name.replace(/^[A-Z]+\\s*/, '');
                    html += `<button type="button" onclick="selectDailyAtaSub('${item.sub}')" class="sub-pill ${activeClass} px-2.5 py-1.5 rounded-lg text-xs font-bold border transition-all cursor-pointer flex items-center gap-1">
                        <span>${item.flag} ${item.code} ${korShort}</span>
                    </button>`;
                });
                container.innerHTML = html;
            });
        }

        function selectDailyAtaSub(newSub) {
            currentDailySub = newSub;
            renderDailyAtaPills();
            renderCorporateDailyAtaMatrix('standalone_ata_matrix_table_wrapper');
            renderCorporateDailyAtaMatrix('exec_ata_matrix_table_wrapper');
        }

        function switchAtaViewMode(mode) {
            currentAtaViewMode = mode;
            const btnWeekly = document.getElementById('btn_ata_mode_weekly');
            const btnDaily = document.getElementById('btn_ata_mode_daily');
            const titleEl = document.getElementById('ata_matrix_main_title');
            const badgeEl = document.getElementById('standalone_ata_matrix_basis_badge');
            const pillsBar = document.getElementById('daily_ata_pills_bar');
            const execPillsBar = document.getElementById('exec_daily_ata_pills_bar');

            if (mode === 'daily') {
                if (btnWeekly) btnWeekly.className = 'px-3 py-1 text-xs font-bold rounded-md transition-all text-slate-500 hover:text-slate-800';
                if (btnDaily) btnDaily.className = 'px-3 py-1 text-xs font-bold rounded-md transition-all bg-white text-primary shadow-xs';
                if (pillsBar) pillsBar.classList.remove('hidden');
                if (execPillsBar) execPillsBar.classList.remove('hidden');
                if (titleEl) titleEl.innerText = '유럽 법인/지점별 일별 ATA 비교 매트릭스 (11월)';
                if (badgeEl) badgeEl.innerText = '15개 법인 개별 · 11월 일별 조사(11/1~11/30) · 판매가 기준';
                renderDailyAtaPills();
            } else {
                if (btnWeekly) btnWeekly.className = 'px-3 py-1 text-xs font-bold rounded-md transition-all bg-white text-primary shadow-xs';
                if (btnDaily) btnDaily.className = 'px-3 py-1 text-xs font-bold rounded-md transition-all text-slate-500 hover:text-slate-800';
                if (pillsBar) pillsBar.classList.add('hidden');
                if (execPillsBar) execPillsBar.classList.add('hidden');
                if (titleEl) titleEl.innerText = '유럽 법인/지점별 주간 ATA 비교 매트릭스';
                if (badgeEl) badgeEl.innerText = '15개 법인 · 최근 3주 · 판매가 기준';
            }

            renderCorporateAtaMatrixOrDaily('standalone_ata_matrix_table_wrapper');
            renderCorporateAtaMatrixOrDaily('exec_ata_matrix_table_wrapper');
        }

        function renderCorporateAtaMatrixOrDaily(wrapperId) {
            if (currentAtaViewMode === 'daily') {
                renderCorporateDailyAtaMatrix(wrapperId);
            } else {
                renderCorporateAtaMatrix(wrapperId);
            }
        }

        function downloadDailyAtaMatrixExcel() {
            if (typeof dailyAtaMatrixExcelBase64 !== 'undefined' && dailyAtaMatrixExcelBase64) {
                const byteCharacters = atob(dailyAtaMatrixExcelBase64);
                const byteNumbers = new Array(byteCharacters.length);
                for (let i = 0; i < byteCharacters.length; i++) {
                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                }
                const byteArray = new Uint8Array(byteNumbers);
                const blob = new Blob([byteArray], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
                const link = document.createElement('a');
                link.href = window.URL.createObjectURL(blob);
                link.download = (typeof dailyAtaMatrixExcelFilename !== 'undefined' && dailyAtaMatrixExcelFilename) ? dailyAtaMatrixExcelFilename : 'EU_Daily_ATA_Matrix_2026_11.xlsx';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            } else {
                window.location.href = 'data/EU_Daily_ATA_Matrix_2026_11.xlsx';
            }
        }

        function downloadWeeklyAtaMatrixExcel() {
            if (typeof ataMatrixExcelBase64 !== 'undefined' && ataMatrixExcelBase64) {
                const byteCharacters = atob(ataMatrixExcelBase64);
                const byteNumbers = new Array(byteCharacters.length);
                for (let i = 0; i < byteCharacters.length; i++) {
                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                }
                const byteArray = new Uint8Array(byteNumbers);
                const blob = new Blob([byteArray], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
                const link = document.createElement('a');
                link.href = window.URL.createObjectURL(blob);
                link.download = (typeof ataMatrixExcelFilename !== 'undefined' && ataMatrixExcelFilename) ? ataMatrixExcelFilename : 'EU_Weekly_ATA_Matrix_2026.xlsx';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            } else {
                window.location.href = 'data/EU_Weekly_ATA_Matrix_2026_1102.xlsx';
            }
        }

        function renderCorporateDailyAtaMatrix(wrapperId) {
            const wrapper = document.getElementById(wrapperId);
            if (!wrapper) return;

            const dData = (typeof priceData !== 'undefined' && priceData.daily_ata_matrix_2026_11) ? priceData.daily_ata_matrix_2026_11 : null;
            if (!dData || !dData.rows || !dData.subsidiaries) {
                wrapper.innerHTML = `
                    <div class="p-8 text-center bg-slate-50 rounded-lg border border-dashed border-slate-300 text-slate-500">
                        <svg class="w-12 h-12 mx-auto mb-3 text-slate-400 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                        </svg>
                        <p class="font-bold text-slate-700">11월 일별 ATA 매트릭스 데이터 준비 중</p>
                        <p class="text-xs text-slate-500 mt-1">11/01~11/30 일별 비교 데이터를 로드하고 있습니다.</p>
                    </div>`;
                return;
            }

            const allRows = dData.rows;
            const days = dData.days || [];
            const activeDays = new Set(dData.active_days || ['11/01', '11/02', '11/03']);
            const sub = currentDailySub || 'DG';

            // Find current subsidiary metadata
            const subInfo = dData.subsidiaries.find(s => s.sub === sub) || dData.subsidiaries[0];
            const currSym = (typeof CURRENCY_SYMBOLS !== 'undefined' && typeof COUNTRY_CURRENCIES !== 'undefined')
                ? (CURRENCY_SYMBOLS[COUNTRY_CURRENCIES[subInfo.cc]] || '€') : '€';

            // Filter out G6 vs S99H, MRGB8 vs R85H, and 83" S95H
            const rows = allRows.filter(r => !(
                (r.lg_series === 'G6' && r.sam_label === 'S99H') ||
                (r.lg_series === 'MRGB8' && r.sam_label === 'R85H') ||
                (r.lg_series === 'G6' && r.sam_label === 'S95H' && String(r.inch) === '83')
            ));

            // Compute category rowspans, pair rowspans, and category break rows dynamically (Exact match with Weekly ATA & Image 2)
            const catSpans = {};
            const catBreakRows = new Set();
            for (let i = 0; i < rows.length; ) {
                const c = rows[i].cat;
                let j = i;
                while (j < rows.length && rows[j].cat === c) j++;
                catSpans[i] = j - i;
                catBreakRows.add(j - 1);
                i = j;
            }

            const pairSpans = {};
            const pairBreakRows = new Set();
            for (let i = 0; i < rows.length; ) {
                const lgS = rows[i].lg_series;
                const samS = rows[i].sam_label;
                let j = i;
                while (j < rows.length && rows[j].lg_series === lgS && rows[j].sam_label === samS) j++;
                pairSpans[i] = j - i;
                pairBreakRows.add(j - 1);
                i = j;
            }

            let html = `<table class="w-full text-center text-[11px] font-sans select-text" style="min-width: 2500px; border-collapse: separate; border-spacing: 0;">`;
            // Header Row 1: Category, Inch, LG, Samsung + 3 Main Section Banners
            html += `<thead class="sticky top-0 z-30 bg-[#F2F2F2]">`;
            html += `<tr class="bg-[#D9D9D9] text-black font-bold">`;
            html += `<th rowspan="2" class="px-2 py-1 border-r border-b-2 border-r-gray-500 border-b-black sticky top-0 left-0 z-40 bg-[#D9D9D9] whitespace-nowrap" style="min-width:68px;width:68px;height:56px;">Category</th>`;
            html += `<th rowspan="2" class="px-1.5 py-1 border-r border-b-2 border-r-gray-500 border-b-black sticky top-0 left-[68px] z-40 bg-[#D9D9D9] whitespace-nowrap" style="min-width:38px;width:38px;height:56px;">Inch</th>`;
            html += `<th rowspan="2" class="px-2 py-1 border-r border-b-2 border-r-gray-500 border-b-black sticky top-0 left-[106px] z-40 bg-[#D9D9D9] whitespace-nowrap" style="min-width:66px;width:66px;height:56px;">LG</th>`;
            html += `<th rowspan="2" class="px-2 py-1 border-r-2 border-b-2 border-r-black border-b-black sticky top-0 left-[172px] z-40 bg-[#D9D9D9] whitespace-nowrap" style="min-width:66px;width:66px;height:56px;">Samsung</th>`;
            
            // Section 1: ATA Index
            html += `<th colspan="${days.length}" class="bg-[#1E3A8A] text-white px-3 py-1.5 border-r-2 border-b border-slate-600 tracking-wider text-center text-xs font-extrabold sticky top-0 z-30 whitespace-nowrap" style="height:28px;">`;
            html += `📊 1. ATA 지수 (${subInfo.sub} · ${subInfo.country_ko || subInfo.cc} | LG 실판매가 / SEC 실판매가 * 100) [Guide 105는 100 기준 정규화]</th>`;
            
            // Section 2: LG Price
            html += `<th colspan="${days.length}" class="bg-[#991B1B] text-white px-3 py-1.5 border-r-2 border-b border-slate-600 tracking-wider text-center text-xs font-extrabold sticky top-0 z-30 whitespace-nowrap" style="height:28px;">`;
            html += `🔴 2. LG 실판매가 [${currSym}]</th>`;
            
            // Section 3: Samsung Price
            html += `<th colspan="${days.length}" class="bg-[#065F46] text-white px-3 py-1.5 border-b border-slate-600 tracking-wider text-center text-xs font-extrabold sticky top-0 z-30 whitespace-nowrap" style="height:28px;">`;
            html += `🟢 3. Samsung 실판매가 [${currSym}]</th>`;
            html += `</tr>`;

            // Header Row 2: Sub-headers for Days (11/01 ~ 11/30)
            html += `<tr class="bg-[#F2F2F2] text-black font-bold">`;
            // ATA Days
            days.forEach((day, idx) => {
                const isActive = activeDays.has(day);
                const isBorder = (idx === days.length - 1) ? 'border-r-2 border-r-black' : 'border-r border-r-gray-300';
                const bgClass = isActive ? 'bg-blue-100 text-blue-900 font-extrabold' : 'bg-blue-50/50 text-slate-400 font-normal';
                html += `<th class="px-1 py-1 ${bgClass} ${isBorder} border-b-2 border-b-black text-center sticky top-[28px] z-30 whitespace-nowrap text-[10px]" style="min-width:42px;height:28px;">${day}</th>`;
            });
            // LG Price Days
            days.forEach((day, idx) => {
                const isActive = activeDays.has(day);
                const isBorder = (idx === days.length - 1) ? 'border-r-2 border-r-black' : 'border-r border-r-gray-300';
                const bgClass = isActive ? 'bg-rose-100 text-rose-900 font-extrabold' : 'bg-rose-50/50 text-slate-400 font-normal';
                html += `<th class="px-1 py-1 ${bgClass} ${isBorder} border-b-2 border-b-black text-center sticky top-[28px] z-30 whitespace-nowrap text-[10px]" style="min-width:54px;height:28px;">${day}</th>`;
            });
            // Samsung Price Days
            days.forEach((day, idx) => {
                const isActive = activeDays.has(day);
                const isBorder = (idx === days.length - 1) ? 'border-r border-slate-300' : 'border-r border-r-gray-300';
                const bgClass = isActive ? 'bg-emerald-100 text-emerald-900 font-extrabold' : 'bg-emerald-50/50 text-slate-400 font-normal';
                html += `<th class="px-1 py-1 ${bgClass} ${isBorder} border-b-2 border-b-black text-center sticky top-[28px] z-30 whitespace-nowrap text-[10px]" style="min-width:54px;height:28px;">${day}</th>`;
            });
            html += `</tr>`;
            html += `</thead><tbody>`;

            // Product Rows (Category, Inch, LG, Samsung formatted 100% identically with Weekly ATA & Image 2)
            rows.forEach((r, rIdx) => {
                const isCatBreak = catBreakRows.has(rIdx);
                const isPairBreak = pairBreakRows.has(rIdx);
                const cellBorderBottom = isCatBreak
                    ? 'border-b-2 border-b-black'
                    : (isPairBreak ? 'border-b border-b-gray-400' : 'border-b border-b-gray-300');
                const subData = (r.subsidiaries && r.subsidiaries[sub]) ? r.subsidiaries[sub] : {};

                html += `<tr class="hover:brightness-95 transition-all">`;

                // Col 1: Category (merged)
                if (catSpans[rIdx]) {
                    html += `<td rowspan="${catSpans[rIdx]}" class="px-1.5 py-1 font-bold text-black bg-white border-r border-r-gray-400 border-b-2 border-b-black sticky left-0 z-20" style="min-width:68px;width:68px;"><div class="ata-sticky-cell-label sticky py-0.5" style="top:58px;">${r.cat}</div></td>`;
                }

                // Col 2: Inch
                html += `<td class="px-1 py-0.5 text-black bg-white border-r border-r-gray-400 ${cellBorderBottom} sticky left-[68px] z-20" style="min-width:38px;width:38px;">${r.inch}</td>`;

                // Col 3 & Col 4: LG Series & Samsung Series (merged per pair block)
                if (pairSpans[rIdx]) {
                    const endIdx = rIdx + pairSpans[rIdx] - 1;
                    const pairBottomBorder = catBreakRows.has(endIdx) ? 'border-b-2 border-b-black' : 'border-b border-b-gray-400';
                    let lgCellHtml = `<div class="font-bold text-[11px] leading-tight">${r.lg_series}</div>`;
                    if (r.lg_guide) {
                        lgCellHtml += `<div class="text-[9px] text-slate-500 font-medium leading-tight mt-0.5">${r.lg_guide}</div>`;
                    }
                    html += `<td rowspan="${pairSpans[rIdx]}" class="px-1 py-0.5 text-black bg-white border-r border-r-gray-400 ${pairBottomBorder} sticky left-[106px] z-20 whitespace-nowrap" style="min-width:66px;width:66px;"><div class="ata-sticky-cell-label sticky py-0.5" style="top:58px;">${lgCellHtml}</div></td>`;
                    html += `<td rowspan="${pairSpans[rIdx]}" class="px-1.5 py-0.5 font-semibold text-black bg-white border-r-2 border-r-black ${pairBottomBorder} sticky left-[172px] z-20 whitespace-nowrap" style="min-width:66px;width:66px;"><div class="ata-sticky-cell-label sticky py-0.5" style="top:58px;">${r.sam_label}</div></td>`;
                }

                // 1. ATA Block (30 cols)
                days.forEach((day, dIdx) => {
                    const rec = subData[day];
                    const isLast = (dIdx === days.length - 1);
                    const bRight = isLast ? 'border-r-2 border-r-black' : 'border-r border-r-gray-300';
                    if (rec && rec.ata !== null && typeof rec.ata !== 'undefined') {
                        const ataVal = rec.ata;
                        let guideTh = 100;
                        if (r.lg_guide) {
                            if (r.lg_guide.includes('105')) {
                                guideTh = 100; // Normalized 105 to 100
                            } else {
                                const m = String(r.lg_guide).match(/\\d+/);
                                if (m) guideTh = parseInt(m[0], 10);
                            }
                        }
                        const isGreen = ataVal >= guideTh;
                        const bgStyle = isGreen ? 'background-color:#D9EAD3;color:#1E4620;' : 'background-color:#F4CCCC;color:#9C0006;';
                        const tip = `[${subInfo.sub} · ${subInfo.banner} | ${day}]\\nLG: ${rec.lg_code || '-'} (${currSym}${rec.lg_price ? rec.lg_price.toLocaleString() : '-'})${r.lg_guide ? ' [' + r.lg_guide + ']' : ''}\\nSEC: ${rec.sam_code || '-'} (${currSym}${rec.sam_price ? rec.sam_price.toLocaleString() : '-'})\\nATA: ${ataVal}%`;
                        html += `<td class="px-0.5 py-0.5 font-bold ${bRight} ${cellBorderBottom} cursor-help" style="${bgStyle}" title="${tip.replace(/"/g, '&quot;')}">${ataVal}</td>`;
                    } else {
                        html += `<td class="px-0.5 py-0.5 text-gray-400 bg-white ${bRight} ${cellBorderBottom}">-</td>`;
                    }
                });

                // 2. LG Price Block (30 cols)
                days.forEach((day, dIdx) => {
                    const rec = subData[day];
                    const isLast = (dIdx === days.length - 1);
                    const bRight = isLast ? 'border-r-2 border-r-black' : 'border-r border-r-gray-300';
                    const p = rec ? (rec.lg_net || rec.lg_price || 0) : 0;
                    if (p > 0) {
                        const tip = `[${subInfo.sub} | ${day}] LG: ${rec.lg_code || r.lg_series} (${currSym}${p.toLocaleString()})`;
                        html += `<td class="px-1 py-0.5 text-right font-medium text-slate-800 bg-white ${bRight} ${cellBorderBottom} cursor-help" title="${tip.replace(/"/g, '&quot;')}">${p.toLocaleString()}</td>`;
                    } else {
                        html += `<td class="px-1 py-0.5 text-center text-gray-400 bg-white ${bRight} ${cellBorderBottom}">-</td>`;
                    }
                });

                // 3. Samsung Price Block (30 cols)
                days.forEach((day, dIdx) => {
                    const rec = subData[day];
                    const isLast = (dIdx === days.length - 1);
                    const bRight = isLast ? 'border-r border-slate-300' : 'border-r border-r-gray-300';
                    const p = rec ? (rec.sam_net || rec.sam_price || 0) : 0;
                    if (p > 0) {
                        const tip = `[${subInfo.sub} | ${day}] SEC: ${rec.sam_code || r.sam_label} (${currSym}${p.toLocaleString()})`;
                        html += `<td class="px-1 py-0.5 text-right font-medium text-slate-800 bg-white ${bRight} ${cellBorderBottom} cursor-help" title="${tip.replace(/"/g, '&quot;')}">${p.toLocaleString()}</td>`;
                    } else {
                        html += `<td class="px-1 py-0.5 text-center text-gray-400 bg-white ${bRight} ${cellBorderBottom}">-</td>`;
                    }
                });

                html += `</tr>`;
            });

            html += `</tbody></table>`;
            wrapper.innerHTML = html;

            alignAtaMatrixStickyHeader(wrapperId);
            setTimeout(() => syncAtaMatrixTopScroll(wrapperId), 30);
        }

        function renderExecutiveGapTable"""

if re.search(daily_block_regex, c):
    c = re.sub(daily_block_regex, lambda m: daily_block_new, c)
    print("6. Daily ATA JS block updated.")
else:
    print("Warning: Daily ATA JS block regex did not match.")

# 7. Update downloadAtaMatrixExcel to support daily matrix download
download_old = """        function downloadAtaMatrixExcel(event) {
            if (typeof ataMatrixExcelBase64 !== 'undefined' && ataMatrixExcelBase64) {"""

download_new = """        function downloadAtaMatrixExcel(event) {
            if (currentAtaViewMode === 'daily') {
                if (typeof dailyAtaMatrixExcelBase64 !== 'undefined' && dailyAtaMatrixExcelBase64) {
                    if (event) event.preventDefault();
                    try {
                        const byteChars = atob(dailyAtaMatrixExcelBase64);
                        const byteNumbers = new Array(byteChars.length);
                        for (let i = 0; i < byteChars.length; i++) {
                            byteNumbers[i] = byteChars.charCodeAt(i);
                        }
                        const byteArray = new Uint8Array(byteNumbers);
                        const blob = new Blob([byteArray], {
                            type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                        });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = (typeof dailyAtaMatrixExcelFilename !== 'undefined' && dailyAtaMatrixExcelFilename)
                            ? dailyAtaMatrixExcelFilename
                            : 'EU_Daily_ATA_Matrix_2026_11.xlsx';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        setTimeout(() => URL.revokeObjectURL(url), 3000);
                        return false;
                    } catch (err) {
                        console.error('Daily Excel download fallback:', err);
                    }
                }
            } else {
                if (typeof ataMatrixExcelBase64 !== 'undefined' && ataMatrixExcelBase64) {"""

if download_old in c:
    c = c.replace(download_old, download_new, 1)
    # also add closing brace before return true
    c = c.replace("""                    setTimeout(() => URL.revokeObjectURL(url), 3000);
                    return false;
                } catch (err) {
                    console.error('Base64 Excel download fallback:', err);
                }
            }
            return true;""", """                    setTimeout(() => URL.revokeObjectURL(url), 3000);
                    return false;
                } catch (err) {
                    console.error('Base64 Excel download fallback:', err);
                }
                }
            }
            return true;""")
    print("7. downloadAtaMatrixExcel updated.")
else:
    print("Warning: downloadAtaMatrixExcel target not found.")

with open(template_path, 'w', encoding='utf-8') as f:
    f.write(c)

print("ALL TEMPLATE UPDATES COMPLETED SUCCESSFULLY!")
