---
name: swiss_tv_tracker
description: A skill for programmatically collecting year-filtered TV prices and promotional data from MediaMarkt, Interdiscount, and Digitec Switzerland and outputting formatted Excel sheets.
---

# Skill: Swiss TV Price & Promotion Collection

This skill details the exact procedures for a sub-agent to navigate, filter, paginate, scrape, and export Samsung and LG TV data from MediaMarkt, Interdiscount, and Digitec Switzerland.

---

## Part A: MediaMarkt Switzerland Collection

### Step A1: Navigating with Multiple Targeted Query Configurations and Scrapling StealthySession
1. **Never scrape a single generic query URL** (which often misses clearance or 이월 models like S90F due to search ranking limits and year-filter metadata mapping issues).
2. **Multiple Query Configuration Rule (Critical)**: Loop through a list of targeted query configurations (both general and specific series queries) for each brand to guarantee 100% model coverage (recovering clearance models and newly launched series like QN80H, M70H, R85H, QNED86B, QNED71B, QNED70B, MRGB87B omitted by basic filters), and merge/deduplicate results in Python:
   * **Samsung queries**:
     - General TV: `https://www.mediamarkt.ch/de/search.html?query=samsung%20TV&brand=SAMSUNG&marketplace=MediaMarkt&modelyear=2025%20OR%202026` (Max 10 pages)
     - 2026 Lineup: `https://www.mediamarkt.ch/de/search.html?query=samsung%202026&brand=SAMSUNG&marketplace=MediaMarkt` (Max 5 pages)
     - OLED TV: `https://www.mediamarkt.ch/de/search.html?query=samsung%20OLED&brand=SAMSUNG&marketplace=MediaMarkt` (Max 3 pages)
     - S90 Series: `https://www.mediamarkt.ch/de/search.html?query=samsung%20S90&brand=SAMSUNG&marketplace=MediaMarkt` (Max 2 pages)
     - S95 Series: `https://www.mediamarkt.ch/de/search.html?query=samsung%20S95&brand=SAMSUNG&marketplace=MediaMarkt` (Max 2 pages)
     - S99 Series: `https://www.mediamarkt.ch/de/search.html?query=samsung%20S99&brand=SAMSUNG&marketplace=MediaMarkt` (Max 2 pages)
     - Neo QLED QN80: `https://www.mediamarkt.ch/de/search.html?query=samsung%20QN80&brand=SAMSUNG&marketplace=MediaMarkt` (Max 2 pages)
     - Mini LED M70: `https://www.mediamarkt.ch/de/search.html?query=samsung%20M70&brand=SAMSUNG&marketplace=MediaMarkt` (Max 2 pages)
     - Micro RGB R85: `https://www.mediamarkt.ch/de/search.html?query=samsung%20R85&brand=SAMSUNG&marketplace=MediaMarkt` (Max 2 pages)
     - Crystal UHD U8090: `https://www.mediamarkt.ch/de/search.html?query=samsung%20U8090&brand=SAMSUNG&marketplace=MediaMarkt` (Max 2 pages)
     - The Frame: `https://www.mediamarkt.ch/de/search.html?query=samsung%20the%20frame&brand=SAMSUNG&marketplace=MediaMarkt` (Max 2 pages)
   * **LG queries**:
     - General TV: `https://www.mediamarkt.ch/de/search.html?query=LG%20TV&brand=LG&marketplace=MediaMarkt&modelyear=2025%20OR%202026` (Max 10 pages)
     - 2026 Lineup: `https://www.mediamarkt.ch/de/search.html?query=LG%202026&brand=LG&marketplace=MediaMarkt` (Max 5 pages)
     - OLED TV: `https://www.mediamarkt.ch/de/search.html?query=LG%20OLED&brand=LG&marketplace=MediaMarkt` (Max 3 pages)
     - C6 Series: `https://www.mediamarkt.ch/de/search.html?query=LG%20C6&brand=LG&marketplace=MediaMarkt` (Max 2 pages)
     - G6 Series: `https://www.mediamarkt.ch/de/search.html?query=LG%20G6&brand=LG&marketplace=MediaMarkt` (Max 2 pages)
     - B6 Series: `https://www.mediamarkt.ch/de/search.html?query=LG%20B6&brand=LG&marketplace=MediaMarkt` (Max 2 pages)
     - C5 Series: `https://www.mediamarkt.ch/de/search.html?query=LG%20C5&brand=LG&marketplace=MediaMarkt` (Max 2 pages)
     - G5 Series: `https://www.mediamarkt.ch/de/search.html?query=LG%20G5&brand=LG&marketplace=MediaMarkt` (Max 2 pages)
     - QNED Series: `https://www.mediamarkt.ch/de/search.html?query=LG%20QNED&brand=LG&marketplace=MediaMarkt` (Max 3 pages - QNED86B, QNED71B, QNED70B)
     - Micro RGB MRGB: `https://www.mediamarkt.ch/de/search.html?query=LG%20MRGB&brand=LG&marketplace=MediaMarkt` (Max 2 pages - MRGB87B)
     - StanbyME: `https://www.mediamarkt.ch/de/search.html?query=LG%20StanbyME&brand=LG&marketplace=MediaMarkt` (Max 2 pages - StanbyME 2 27LX6TDGA)
3. Use Scrapling's `StealthySession` context manager in Python (`with StealthySession(headless=True) as session:`) to fetch pages. This solves the Cloudflare captcha automatically on the first page, and reuses cookies to bypass Cloudflare completely on subsequent pages.
4. **Omit `network_idle=True`**: Do **not** use the `network_idle=True` parameter in Scrapling's `session.fetch()` call. Commercial sites continuously run analytics, ads, and telemetry scripts, preventing network idle and causing 60-second timeouts. Instead, rely on default DOM load events combined with `wait=3000 * TIMEOUT_MULTIPLIER`.
5. **Block Detection**: If validation is needed, only check for `"Verification Required" in html` or non-200 HTTP statuses. Do **not** search for the generic string `"blocked"`, as it matches normal elements in legitimate search results.

### Step A2: Page Iteration Loop
1. MediaMarkt uses url-based pagination. Loop from page 1 to 10 by constructing URLs: `{base_url}&page={page_num}`.
2. Call `session.fetch(url, solve_cloudflare=True, wait=3000 * TIMEOUT_MULTIPLIER)`.
3. If the page returns a status other than 200 or contains `"Verification Required"`, stop the loop (this signifies either the end of results or a permanent block).

### Step A3: Python BeautifulSoup DOM-Climbing Parser
1. Parse the page's HTML content in Python using `BeautifulSoup(html, 'html.parser')`.
2. Locate all anchors (`a`) containing `href` with `/product/`. Deduplicate titles to prevent processing multiple links referencing the same product card.
3. For each anchor, climb up to **8 parent levels** (`parent = link.parent` in a loop):
   * **Price Extraction**: Use regex `re.search(r'CHF\s*([\d\s’\'\x27\x60,.]*(?:[.–]|,\d{2}|\.\d{2}))', text)` to match prices. Replace symbols (`.–`, spaces, apostrophes) to parse numeric floats.
   * **Direct Seller Verification**: Match `Verkauft durch` or `Sold by`. If the seller name contains `Partner` or is not `MediaMarkt`, discard the product card.
   * **Promotion Extraction**: Look for promotional keywords ("Cashback", "Rabatt", "Geschenk", "Aktion") and extract corresponding badge element text if present.

### Step A4: Parsing & Card Filtering
* Locate product card anchors matching `a[href*="/de/product/"]`.
* Programmatically climb up the parent nodes to find the price and promotion details container.
* **Exclude Non-TV Cards & Galaxy Smartphone Guard**: Exclude any cards that do not contain the text `Produkttyp` (this filters out recommendation carousels, mobile phones, and accessories that get mixed into the search results). When querying `samsung 2026`, explicitly filter out Samsung Galaxy smartphones (`Galaxy S26 Ultra`, `Galaxy S26+`, `Galaxy S26`, `Smartphone`, `Handy`, `Mobile`) and enforce `size >= 22` inches.
* **Smart Regex Code Restoration (Samsung)**: If the parsed model code is `"Unknown"`, apply a regex-based smart extractor (`extract_model_code_from_title` using pattern lists like `QN\d{2,3}[FH]`, `S\d{2}[FH]`, `U\d{4}[FH]`, `M\d{2}[FH]`, `R\d{2}[FH]`, `LS03[A-Z]{1,2}`, `F\d{4}`, `MR\d{2}[FH]`) to reconstruct standard codes (e.g. `S95F` -> `QE{size}S95F`, `QN90F` -> `QE{size}QN90F`, `QN80H` -> `QE{size}QN80H`, `M70H` -> `UE{size}M70H`, `R85H` -> `MRE{size}R85H`, `U8090H` -> `UE{size}U8090H`, `S85F` -> `QE{size}S85F`, `Frame Pro 2025` -> `QE{size}LS03FW`) before checking hardcoded fallbacks.
* **Model Code Derivation**:
  * For 2025 models, extract the exact code from the URL slug (e.g., `_samsung-qe55q8faau-...` $\rightarrow$ `QE55Q8FAAU`).
  * For 2026 models, derive codes from the title size and family name:
    * `U8090H` $\rightarrow$ `UE{size}U8090H`
    * `M70H` $\rightarrow$ `UE{size}M70H`
    * `QN80H` $\rightarrow$ `QE{size}QN80H`
    * `S90H` / `S99H` $\rightarrow$ `QE{size}S9xH`
    * `R85H` $\rightarrow$ `MRE{size}R85H`
    * `LS03HE` $\rightarrow$ `QE{size}LS03HE`
    * `QNED86B` / `QNED71B` / `QNED70B` $\rightarrow$ `{size}QNEDxxB`
    * `MRGB87B` $\rightarrow$ `{size}MRGB87B`
    * `27LX6TDGA` $\rightarrow$ `27LX6TDGA` (StanbyME 2)

---

## Part B: Interdiscount Switzerland Collection

### Step B1: Navigation URL
1. Always run Playwright in headed mode (`headless: false`) and accept the cookie banner (`uc-accept-all-button`) to maintain the session.
2. **Category-Based Filtering (Critical)**: Do not scrape the generic search query URL. Instead, navigate to the specific TV category list filtered by brand to ensure no accessories or non-TV products are collected:
   * **Samsung**: `https://www.interdiscount.ch/de/fernseher--c111000?brand=SAMSUNG&page=N`
   * **LG**: `https://www.interdiscount.ch/de/fernseher--c111000?brand=LG&page=N`

### Step B2: Pagination Loop (Pages 1 to ceil(N/24))
1. Get the total number of products from the header (e.g., "NN Produkte"). Calculate total pages as `ceil(N / 24)`.
2. Construct the URL dynamically: `...&page={p}`.
3. Wait 4 seconds for page renders before parsing.
4. **Card Extraction**: Locate card elements matching `main article`. Exclude any articles listed after the "Zuletzt angesehene Produkte" (Recently viewed products) section.

### Step B3: Detail Scraping & Model Code Retrieval
* Extract titles via `a[href*="/product/"]`'s `aria-label` attribute.
* Extract prices from `.sr-only` tags (e.g., "1'299.95 CHF").
* Extract promotions from `.font-semibold.line-clamp-1` tags.
* **Model Codes**: Extract model code from the title word structure. If only marketing codes are visible (e.g., `LG C6`), check the detailed page's `"Hersteller-Nr."` parameter (e.g., Interdiscount LG C6 matches the `OLED{size}C68LA` pattern).

### Step B4: Playwright MCP High-Speed Bypass (Alternative)
1. If headed browser execution gets blocked by Cloudflare in the background, causing continuous timeouts or captcha blockades, utilize the agent-controlled Playwright MCP server's browser session with RCE equivalent tool (`browser_run_code_unsafe`) to bypass Cloudflare.
2. Run a custom JavaScript block that iterates through pages 1 to 5 for Samsung and LG respectively. Use a clean browser environment to avoid triggering Cloudflare Turnstile:
   ```javascript
   async (page) => {
     const results = { samsung: [], lg: [] };
     for (let p = 1; p <= 5; p++) {
       await page.goto(`https://www.interdiscount.ch/de/fernseher--c111000?brand=SAMSUNG&page=${p}`, { timeout: 30000 });
       await page.waitForTimeout(4000);
       const arts = await page.evaluate(() => {
         return Array.from(document.querySelectorAll('main article')).map(a => {
           const link = a.querySelector('a[href*="/product/"]');
           return {
             name: link ? link.getAttribute('aria-label') : null,
             href: link ? link.getAttribute('href') : null,
             price: a.querySelector('.sr-only') ? a.querySelector('.sr-only').textContent : null,
             promo: a.querySelector('.font-semibold.line-clamp-1') ? a.querySelector('.font-semibold.line-clamp-1').textContent : null
           };
         });
       });
       results.samsung.push(...arts);
     }
     // Repeat loop for LG ...
     return results;
   }
   ```
3. Save the returned JSON dump output, then run the local synchronization/parsing helper script (`python scripts/fast_interdiscount_sync.py <output_txt_path>`).
4. **1:1 Card-Specific Price Extraction & OLED Screen-Size Price Guard (Critical)**:
   - **Preceding Price Matching**: When parsing card text, extract the price located immediately preceding the product title (`(\d[\d’\']*(?:\.\d{2}|.–|\.95))\s*(?:CHF)?\s*\n+\s* + title`) rather than taking `min(nums)` across the container, preventing promo cashback values (e.g. `600 CHF Cashback`) or cheaper accessories from overwriting TV selling prices.
   - **OLED Screen-Size Price Guard**: Enforce minimum price thresholds for OLED screens to automatically reject false-positive discount badges or small LCD prices:
     - `83"+ OLED`: $\ge$ 2,000 CHF
     - `77"+ OLED`: $\ge$ 1,500 CHF
     - `65"+ OLED`: $\ge$ 1,000 CHF
     - `55"+ OLED`: $\ge$ 800 CHF
     - `42"/48" OLED`: $\ge$ 650 CHF

---

## Part C: Digitec Switzerland Collection

### Step C1: Direct URL Navigation
1. Navigate directly to the filtered category URL:
   * **Samsung**: `https://www.digitec.ch/de/s1/producttype/tv-4?filter=bra%3D422%2C5778%3D2025%7C2026%2Coff%3DInStock&take=150`
   * **LG**: `https://www.digitec.ch/de/s1/producttype/tv-4?filter=bra%3D284%2C5778%3D2025%7C2026%2Coff%3DInStock&take=150`
2. **take=150 Parameter**: Always append `&take=150` to load all products on a single page instead of the default 24.
3. **Chunking Rule**: If total products exceed 35 and scraping experiences timeouts, divide the query into chunks using the display technology filter (`748` filter parameter: OLED=790, QNED=7193255, LED=180833, QLED=10667980, etc.).

### Step C2: Infinite Scroll & Show More Loop
1. Scroll down the page 15 times dynamically to trigger lazy loading.
2. Locate the `"Mehr anzeigen"` (Show more) anchor tag (`a:has-text('Mehr anzeigen')`).
3. If visible, scroll to it, click it, wait 4 seconds, and scroll down another 5 times.

### Step C3: Deduplication & Lowest Price
* Because Digitec lists import versions (CH/DE/EU) and multiple merchant offers, identical model codes will appear multiple times.
* **Deduplication Rule**: Group the final list by `model_code` and **keep only the entry with the lowest price**. Store any "Returned & Tested" tags in the promotions column.

---

## Part D: Parsing, Formatting, and Excel Syncing

### Step D1: Release Year Classification
* **Samsung**: `F` corresponds to 2025, `H` to 2026 (e.g. `QE65S90F` $\rightarrow$ 2025, `QE65S90H` $\rightarrow$ 2026).
* **LG**:
  * **2026 Models**: `C6`, `G6`, `B6`, `QNED86B`, `QNED80B`, `QNED87B`, `QNED71B`, `QNED70B`, `QNED72B`, `QNED7EB`, `UA77`, `MRGB87B`, `LX7B`, `LX6`, `27LX6TDGA`, `QLED7EB`, `MRGB96B`.
  * **2025 Models**: `C5`, `G5`, `B5`, `QNED86A`, `QNED80A`, `QNED87A`, `QNED72A`, `QNED7EA`, `UA75`, `MRGB87A`, `LX7A`, `LX5`, `QNED70A`, `NANO81A`, `NANO80A`, `QNED93A`.
  * **대시보드 UI/정렬/표기 표준 규칙**:
    * **유통 메뉴 순서 및 뱃지 표기 표준**: `allRetailersList` 순서는 `UK` (Currys) $\rightarrow$ `DE` (MediaMarkt) $\rightarrow$ `FR` (Fnac) $\rightarrow$ `ES` (MediaMarkt) $\rightarrow$ `IT` (MediaWorld) $\rightarrow$ `NL` (MediaMarkt) 로 고정하며, 각 버튼은 약어 뱃지(`UK`, `DG`, `FS`, `ES`, `IS`, `BN`)와 라벨(`Currys (UK)`, `MediaMarkt (DG)`, `Fnac Darty (FS)`, `MediaMarkt (ES)`, `MediaWorld (IS)`, `MediaMarkt (NL)`)을 표기함. 대시보드 진입 시 **초기 활성화 국가**: `UK` (Currys).
    * **일자별 가격비교 테이블 UK 우선순위 정렬**: `renderHistoryTable`에서 메인 대표가(Parent Row)는 **영국(UK / Currys / `£`)을 최우선 1순위**로 노출하고, 영국 미수집 시 `DE` $\rightarrow$ `ES` $\rightarrow$ `IT` $\rightarrow$ `FR` $\rightarrow$ `NL` 순서로 대표가 및 통화 기호(`£` / `€`)를 표기함. 하위 자식 행(Child Rows) 또한 `UK` $\rightarrow$ `DE` $\rightarrow$ `ES` $\rightarrow$ `IT` $\rightarrow$ `FR` $\rightarrow$ `NL` 순서로 차례대로 정렬함.
    * **차트 타이틀 Safe String Guard (`undefined` 방지)**: 차트 카드 타이틀 파싱 시 `flag` 속성이 비어있는 경우 `${item.flag}` 직접 출력을 금지하고 `flag = item.badge ? '' : (item.flag || '')` 와 같이 예외 처리하여 `undefined` 키워드가 유통명 앞에 절대 출력되지 않도록 방어함.
  * **Edge Case Fallback**: If a model has a budget suffix corresponding to 2024 (like `UA73`) but the title explicitly contains `"2025"`, classify it as `2025`.

### Step D2: Screen Size Filtering
* Extract size from the title (`"(\d+)\s*\""`) or the model code.
* **Size Threshold**: Exclude products with screen size **`< 22` inches** (this preserves the 27" LG StanbyME TV, while filtering out monitors and small accessories).

### Step D3: Promotion Cleaning, Cashback Restrictions, & Translation Dictionary (Critical)
1. **Strict Cashback Policy (Prohibit Estimates)**: Only extract cashback amount if it is explicitly specified with a clear numeric value on the website (e.g. "CHF 150 Cashback"). If no numeric value is explicitly written on the page for that model, you MUST write `0`. Never estimate, auto-inject, or derive cashback values based on panel technology, sizes, or standard tables.
2. **Promotion Text Translation Mapping**: Map all raw German/French/Korean promotional texts to their standardized English equivalents before writing to the sheet:
   * `"mit kostenlosem Zusatzprodukt"` / `"Zusatzprodukt"` $\rightarrow$ `"Free Promotional Product (Sound Device)"`
   * `"RESTPOSTEN"` / `"Restposten"` $\rightarrow$ `"Clearance (Restposten)"`
   * `"Outlet"` $\rightarrow$ `"Outlet (Clearance)"`
   * `"SoundSuite/Soundbar"` / `"SoundSuite"` $\rightarrow$ `"Free SoundSuite/Soundbar with LG OLED TV 2026 Purchase"` (LG 2026 only)
   * `"Sound Device geschenkt"` $\rightarrow$ `"Free Sound Device with 2026 TV Purchase"` (2026 TVs only)
   * `"Music Studio 5"` $\rightarrow$ `"Free Music Studio 5 Soundbar (HW-LS50H/EN)"`
   * `"Cashback und oder 26% Rabatt auf Soundbar QS700F"` $\rightarrow$ `"Samsung Cashback and/or 26% Off Soundbar QS700F"`
   * `"Aus unserer Werbung"` / `"Werbung"` $\rightarrow$ `"Featured in Weekly Ad (Aus unserer Werbung)"`
   * `"Online Only"` $\rightarrow$ `"Online Only"`
   * **Discount Badges**: If a card has discount texts like `CHF 299.– statt CHF 349.–` or `14% Rabatt`, map it to: `"Sale N%; was CHF X"` (e.g. `Sale 14%; was CHF 349`).

### Step D4: Excel Writing & File Locks
* **Exclude Out-of-Stock**: Only write active, direct-sell, in-stock products matching the query to avoid bloated files.
* **Lock Bypass**: If writing to the Excel file returns a `PermissionError` (Errno 13), auto-increment the filename suffix (e.g., `_v2`, `_v3`) in a loop until saving succeeds.
* **Reassign Filename**: Always reassign the target filename variable returned by the sync function after every update (e.g., `pt_file = sync_retailer_sheet(pt_file, ...)`).
* **Direct Cashback sync mapping**: When syncing data from the price tracker Excel sheet to the comparison sheets, load the cashback value directly from the `Cashback (CHF)` column (Column 9) of the price tracker sheet instead of parsing it from the promo text.
* **Excel Source command execution**: When updating historical or manual data, run `python scripts/sync_all_retailers.py --excel-source <path_to_price_tracker_file>` to load and sync all data directly from that file.

---

## Part E: Swiss ATA Comparison Report Generation (July 5th Revision)
When creating the final compiled comparative analysis report (e.g., `Swiss_ATA_Comparison_2026_0705.xlsx`), implement the following architectural rules:
1. **Official Golden Template Requirement (Strict)**:
   * **`Swiss_ATA_Comparison_2026_0705_v2.xlsx`** (located in the `History/2026 0705` directory) is the official standard golden template for the comparison report.
   * Every future survey update must strictly replicate the format, headers, fonts, column ranges, and formulas of this file.
   * **NO CHANGES** to the layout, styling, colors, formula structures, or row/column configurations are allowed without the user's explicit permission. If you believe a modification is necessary, you **MUST stop and ask the user for permission** before proceeding.
2. **Header Layout**:
   * Keep cell `B2` completely empty.
   * Cell `B3` contains the label `'Series'` (bold).
   * Merge columns `C1` to `Q1` for the report date header (e.g., `July(3rd)`).
3. **Column B Series Naming**:
   * Refactor detailed codes to clean series codes:
     * LG OLED G: `G57`/`G67` -> `G5`/`G6`
     * LG OLED C: `C57`/`C67` -> `C5`/`C6`
     * LG OLED B: `B59`/`B69` -> `B5`/`B6`
     * Samsung OLED S90: `S905` -> `S90F` (2025) and `S90H` (2026)
     * Samsung OLED S85: `S855` -> `S85F` (2025) and `S85H` (2026)
     * Samsung QN70: `QN70f` -> `QN70F` (2025) and `QN70H` (2026)
    * **Precise Series Matching (OLED vs QNED & Generation Boundaries)**:
      * Ensure that generic substrings (like `B6`, `B5`, `G6`, `G5`) do not falsely match QNED or other model types (e.g., `QNED86B6B` contains `B6` and must not be mapped into OLED `B6` series). Exclude `QNED` or verify `OLED` prefix when mapping OLED series.
      * **Generation Boundary Separation**: Ensure the matching algorithm filters products strictly by year (`p.get("year") == year`) and uses generation-specific conditions (e.g., `family == "G5"` checks only `"G5" in code`, and does not match `G6` models), preventing cross-generation mismatches.
    * **Strict Series Matcher Boundaries (Over-matching Prevention)**:
      * **LG Micro RGB (`MRGB95` vs `MRGB85`)**: `MRGB95` must ONLY match 9-series codes (`MRGB95`, `MRGB96`, `MRGB9`, `MR95`). `MRGB85` must ONLY match 8-series codes (`MRGB85`, `MRGB87`, `MRGB8`, `MR85`). Never use generic prefix checks like `"MRGB" in code` that cause 8-series models (`75MRGB87`) to fill `75MRGB95` slots.
      * **Samsung Micro RGB / MiniLED (`R95H` vs `R85H`)**: `R95H` must ONLY match `R95` / `MRE95`. `R85H` must ONLY match `R85` / `MRE85`. **CRITICAL**: Never include generic QNED/Neo QLED search terms (such as `or "QN" in code`) in Samsung `R` series matcher conditions, as this causes unlisted `R85H` slots to falsely match normal Neo QLED models (e.g., `QN74H`) and inject invalid prices into the dashboard.
      * **Samsung UHD 4K `U8000H` Scope Boundary**: `U8000H` / `U8005H` matchers MUST NOT contain `M80`, `M70` or LED M-series keywords, ensuring true `U8005H` prices (`450`, `550`, `580`, `750`, `1,199`) are not overridden by `M80H` LED models.
      * **Model Code Size Extraction Priority**: When parsing raw screen size, parsers MUST prioritize valid 2-digit screen sizes embedded inside model codes (e.g. `TQ65S92H` -> 65, `55QNED81B` -> 55) over title cm-to-inch conversions (e.g. 163cm / 164cm -> 64), preventing size truncation errors from dropping models from comparison slots.
      * **Sub-model Alias Pair Label Sync Rule**: When mapping sub-model aliases (e.g. `QNED84A` -> `QNED80A` family or `QNED81B` -> `QNED80B` family), the dashboard configuration (`PAIRS_CONFIG`) MUST explicitly update the series label (`lg` or `sam` key) to match the exact alias code (e.g. `"lg": "QNED84A"`) so that X-axis chart labels dynamically display the exact target series name (`65"QNED84A vs. 65"Q7F`) instead of stale fallback family labels.
      * **Country-Specific Dashboard Pair Isolation**: When updating retailer comparison pairs for a specific country/retailer (e.g. Italy MediaWorld `QNED87B vs QN70H` & `QNED70B vs M70H`), declare an isolated country configuration variable (e.g. `PAIRS_CONFIG_2026_IT`) and apply it conditionally for that country, ensuring other countries maintain standard global pair configurations without side effects.
      * **86/85 Inch Flagship Tolerance & Distinct Pair Labeling**: When comparing LG 86-inch models against Samsung 85-inch models (e.g. `86MRGB95 vs 85R95H`, `86MRGB85 vs 85R85H`, `86QNED70B vs 85M70H`), allow `85` and `86` inch sizes to match flexibly in `find_product` while explicitly formatting `pair_label` as `86"<LG> vs. 85"<SAM>` so both brand screen sizes are correctly and distinctly labeled on chart X-axes.
      * **OLED Series Code Requirement (Prevention of Year-Suffix Collisions)**: When matching LG OLED series (`B6`, `B5`, `C6`, `C5`, `G6`, `G5`), parsers MUST require `"OLED" in code` or explicit OLED prefixes. Never match solely on year-suffix strings like `"B6" in code`, which wrongly classifies 2026 QNED/Micro RGB/UHD 4K models (e.g. `43QNED87B6A`, `86MRGB87B6B`, `65NU850B6LA`) as OLED.
      * **Official Sub-model Priority Selection Rule**: When an Excel sheet contains both official country sub-models (e.g. Italian official OLED `OLED65G56LS`, `C55`, `G66`, or Samsung `U8000F` series) and parallel/lower sub-models (`OLED65G54LW`, `U7000F`), `find_product` MUST apply priority weighted sorting (`get_priority`) so official country sub-models are matched with highest 0-priority over lower/parallel variants.
      * **Strict U8000F Exclusion of U7000 Series**: Samsung `U8000F` / `U8000H` series matchers MUST NEVER include `"U7000"` keywords in their matching arrays. `U8000F` comparison slots must exclusively match true U8000 series (`U8000`, `U8005`, `U8010`, `U8070`, `U8075`, `U8079`, `U8080`, `U8090`, `DU8000`), preventing lower U7000 models from polluting U8000F chart slots while covering country-specific variants like German `U8079` (`GU43U8079H`, `GU50U8079H`, `GU55U8079H`, `GU65U8079H`, `GU75U8079H`, `GU85U8079H`).
      * **UK-Specific QNED Pair Order & 100-inch QNED87B Rule**: For UK Currys dashboard, declare `PAIRS_CONFIG_2026_UK` in exact order (`QNED86B vs QN80H`, `QNED86B vs QN70H`, `QNED72B vs M70H`). For the 100-inch slot under `QNED86B vs QN80H`, allow LG `100QNED87B` (`100QNED87B6`) to be matched flexibly while auto-converting the pair label to `100"QNED87B vs. 100"QN80H`.
      * **LG NU800B/NU850B UHD 4K Fixed Categorization**: LG 2026 `NU800B` / `NU850B` / `NU80` / `NU85` models MUST be strictly categorized under `UHD 4K`. Never allow year-suffix `B6` to misclassify them into OLED.
      * **Size-Prefixed LG OLED Matcher Rule**: LG OLED matchers (`G6`, `G5`, `C6`, `C5`, `B6`, `B5`) MUST support size-prefixed model codes (e.g. `42C67LA`, `48G69LS`, `55B68LA`, `77C67LA`, `97G67LW` where `OLED` prefix is absent) via `^\d{2}(G6|G5|C6|C5|B6|B5)` regex pattern matching, preventing country-specific OLED codes from being dropped from dashboards.
      * **NL-Specific QNED Pair Configuration & Single 85-inch Rule**: For Netherlands MediaMarkt dashboard, declare `PAIRS_CONFIG_2026_NL` with 3 exclusive pairs (`QNED86B vs QN80H`, `QNED82B vs M80H`, `QNED70B vs M70H`) and `PAIRS_CONFIG_2025_NL` with 2 exclusive pairs (`QNED86A vs QN74F`, `QNED70A vs Q7F`). Omit `"86"` from the `sizes` array and include only `"85"` to display a single merged `86"<LG> vs. 85"<SAM>` bar, preventing duplicate `86 vs 86` bars.
      * **DE-Specific QNED Pair Configuration Rule**: For Germany MediaMarkt dashboard, declare `PAIRS_CONFIG_2026_DE` with 4 exclusive pairs (`QNED93 vs QN80H`, `QNED86B vs QN70H`, `QNED72B vs M80H`, `QNED72B vs M70H`) and `PAIRS_CONFIG_2025_DE` with 3 exclusive pairs (`QNED86A vs QN80F` 100-55", `QNED86A vs QN70F` 85-43", `QNED70A vs Q7F` 85-43" replacing QNED84A).
4. **TV Sorting Hierarchy**:
   * Sort LG models as: `OLED G` -> `OLED C` -> `OLED B` -> `QNED86` -> `QNED80` -> `UA`.
   * Sort Samsung models as: `OLED S95` -> `OLED S90` -> `OLED S85` -> `QN70` -> `Q8` -> `Q7` -> `U8000`.
5. **Samsung Blue Styling & ATA Removal**:
   * Apply Dark Blue (`#002060`) bold fonts to Samsung series codes (Col B) and regular fonts to Samsung detailed model names (Cols C, H, M).
   * Clear ATA cell values for all Samsung models (leave them blank).
6. **Clean Empty Cells & VLOOKUP Wrapping**:
   * Set `m_cell.value = ""` for missing detailed models (do not output `'N/A'`).
   * Wrap the VLOOKUP formulas for text columns in the bottom summary table in an `IF` statement:
     `=IF(VLOOKUP($B[row], $B$4:$Q$85, col_idx-1, FALSE)=0, "", VLOOKUP(...))`
     This prevents the formula from rendering `0` when pulling blank model cells.
7. **VLOOKUP Summary Table Row Positioning & Redirections**:
   * For `Swiss_2025` sheet: upper matrix runs from Row 4 to Row 83. The summary header begins at Row 86, and data rows start at Row 87.
   * For `Swiss_2026` sheet: upper matrix runs from Row 4 to Row 131. The summary header begins at Row 132, and data rows start at Row 133.
   * In the 2026 sheet's bottom VLOOKUP Summary Table, since `Q8H` and `Q7H` do not exist in the upper matrix, their VLOOKUP formulas must search for `"R95H"` and `"R85H"` keys respectively (e.g. `VLOOKUP("55R95H", ...)` for `55Q8H`).
8. **Display Type Col A Mapping**:
   * Any series code containing `MRGB`, `R95`, or `R85` must be assigned the display type `"MRGB"`.
   * Series code `QNED93` must be assigned the display type `"QNED"`.
9. **No Gridlines**:
   * Set `showGridLines = False` on the worksheet view settings of the openpyxl object to hide default background lines.
10. **Dynamic Row Scanning (No Hardcoded Offsets)**:
    * When populating, polishing, or parsing comparison sheets, calculate `last_row` dynamically by scanning Column 2 upwards from `summary_hdr_row - 1` until finding the first non-empty cell. Never use hardcoded offsets (e.g., `summary_hdr_row - 3`) as they fail when row spacing changes or new models are inserted (such as U8000 series).

---

## Part F: Price Survey Dashboard & History Archive Procedures (July 5th Revision)
Once price trackers and comparison sheets are processed:
1. **Pre-Archive Processed Files in History (Critical for Trend Chart)**:
   * Create a subfolder with date naming convention (e.g. `2026 0707` for July 7th, 2026) under the `History/` path: `D:\TV 유럽영업\15. AX Task\2026 AX 실행과제\Price Tracker\History`.
   * Copy the two compiled Excel workbooks into this newly created folder before compiling the dashboard. This ensures the dashboard generator can scan this folder and include today's prices in the trend line chart:
     * Raw Tracker: `data/price tracker_swiss_2026_[MMDD]_v*.xlsx`
     * Analysis Report: `data/Swiss_ATA_Comparison_2026_[MMDD]_v*.xlsx`
2. **Initialize and Build Dashboard**:
   * Ensure `generate_dashboard.py` is present in the `scripts` folder.
   * Verify that the master template `swiss_price_dashboard_template.html` is safely stored in the `.agents/` customizations or sub-agent artifacts.
3. **Execute HTML Compilation**:
   * Run the builder script: `python scripts/generate_dashboard.py`.
   * This parses the latest Excel workbook prices, rounds decimals to integers, structures 1:1 LG vs. Samsung pairs, and writes the output dashboard to `data/swiss_price_dashboard.html`.
4. **Price Type Slicer and Sidebar History Navigation**:
   * The dashboard must feature a global Price Type Slicer toggle (`"판매가"` vs `"실질가"`) to switch between raw prices and net values across all views.
   * Sidebar navigation must include a third category: **`일자별 가격비교`** (Historical Price Comparison). When clicked, it renders a dropdown to select a model series, drawing a line chart of historical price trends for the three retailers (MediaMarkt, Interdiscount, Digitec) and a details table.
   * Category tab buttons for the display view are rendered dynamically based on the active year (2026 includes `OLED`, `MRGB`, `QNED/QLED`, `UHD 4K`; 2025 includes `OLED`, `QNED/QLED`, `UHD 4K`).
   * If the user selects the `MRGB` tab in 2026 and switches to 2025, the system falls back to `OLED` automatically.
   * X-axis tick labels for model codes must be set to `size: 8` with `maxRotation: 45` to prevent text overlapping or truncation when there are many model pairs (e.g. QNED/QLED category).
   * **Interactive Bar Chart Tooltips (Model Name & Promotion)**: The generated HTML dashboard must extract and pass exact model names (from Columns 3, 8, and 13 of the comparison sheets) in the paired JSON data payload. Format these inside the Chart.js hover tooltip callback `afterLabel` as `Model: <ModelCode>` along with any General Promotion text, so users can see which exact model is priced when hovering.
   * The dashboard logo subtitle must be set to `"LGE SWISS MARKET PRICE TRACKING"`.
5. **Firebase Hosting Deployment**:
   * The project utilizes Firebase multisite hosting under the project ID `fx-tracker-4f44c`.
   * The target site is **`swiss-price-tracker-lge`** (configured as hosting target `swiss-price-tracker` in `.firebaserc` and `firebase.json`).
   * The script `generate_dashboard.py` automatically outputs to the `public/index.html` directory.
   * To deploy the dashboard live, execute: `firebase deploy --only hosting:swiss-price-tracker`.
   * Deployed Web App URL: **`https://swiss-price-tracker-lge.web.app`**.
6. **Final Archive Backup (Dashboard)**:
   * Once the deployment is successfully completed, copy the compiled web dashboard (`data/swiss_price_dashboard.html`) into the same date-specific History folder to complete the archive.

---

## Part G: Automated Survey Verification & Rerun Procedure (July 10th Revision)

### Step G1: Automatic Validation Run & Mandatory Pre-flight Assertion Gate
1. **Zero Historical Price Injection Prohibition (CRITICAL)**: Never copy, backfill, or inject prices from older survey workbooks into today's raw JSON datasets. Every model and price MUST be captured from real-time live search queries or validated via live PDP URL probes.
2. **Mandatory Pre-flight Assertion Gate**: `sync_all_retailers.py` and `sync_eu_retailers.py` must verify that each `raw_{retailer}_{brand}.json` was created or updated on the survey execution date (`YYYY-MM-DD`). If any file is stale, missing, or was not scraped today, the script MUST raise `RuntimeError` and halt immediately.
3. Run the unified orchestration runner: `python scripts/run_survey_with_check.py`.
4. The script dynamically extracts row counts from the previous survey's price tracker file inside `History/`.
5. It maps each sheet (e.g. `MediaMarkt_Samsung_Full`) and compares the item count with the corresponding today's raw json file under `data/`.

### Step G2: 10% Discrepancy Action, Cause Investigation & Retries
1. If the difference in product counts for any retailer's specific brand is **10% or more (> 10%)**, the script immediately flags a discrepancy alert.
2. **Cause Diagnosis**: The pipeline automatically inspects scraper execution logs to diagnose root causes (e.g. Captcha challenge block, backend search indexing omissions, missing clearance models, or DOM selector changes).
3. **Targeted Retry Execution**: The rerun sets `TIMEOUT_MULTIPLIER=1.5` ~ `2.0` and executes targeted series-specific search queries (S90/S95/C6/G6) or Playwright MCP sessions to ensure 100% model coverage.
4. The process retries up to **3 times** until counts are aligned within the acceptable threshold.

### Step G3: Final Synchronization & Deployment
Once verified, the script automatically proceeds with:
* Syncing to Excel files via `sync_all_retailers.py`.
* Copying files to the date-specific `History/` folder.
* Compiling the price survey dashboard HTML via `generate_dashboard.py`.
* Deploying the new dashboard live to Firebase Hosting.
* Copying the final HTML dashboard to the date-specific `History/` folder.

---

## Part H: Czech Republic Alza (alza.cz) Collection & Deployment Procedure

### Step H1: Execution & Multi-Page Coverage
1. Execute the dedicated Alza collector script: `python scripts/scrape_alza.py`.
2. **Multi-Page Loop (12 Pages)**: Alza.cz caps items per page to 24. The script iterates through pages 1 to 12 (`range(1, 13)`) per brand (`televize-samsung/18862344-p1.htm` .. `-p12.htm` & `televize-lg/18862345-p1.htm` .. `-p12.htm`) and includes direct base category URLs (`18862344.htm` / `18862345.htm`) and search query URLs (`search.htm?exps=samsung+tv`) to bypass 307/302 redirect losses on page 1.
3. **Filtering Rules**:
   - `Condition`: NEW (`Nové`) only (exclude `Rozbaleno`, `Zánovní`, `Použité`).
   - `Screen Size`: Screen size $\ge 22$ inches (purging gaming monitors, UltraGear, Odyssey, MyView, StandbyME, soundbars, accessories).
   - `Target Years`: 2025 and 2026 model years.
   - `Currency`: CZK (`#,##0` format).

### Step H2: DOM Precision Price Extraction & Series Classification
1. **DOM Element Precision Price Extraction (Critical)**:
   - Primary selling price MUST be extracted strictly from DOM elements `.js-price-box__primary-price__value`, `.ads-pb__price-value`, or `.price-box__primary-price`.
   - Cashback net price MUST be extracted strictly from `.coupon-block--cashback .coupon-block__price` and net cashback amount calculated as `selling_price - cashback_net_price`.
   - NEVER scan full card text with broad regex (`re.findall`), to prevent promotional banner descriptions (e.g. `<span class="coupon-block__label--description">` containing `"cashbackem až 100 000 Kč"`) from overwriting selling prices with campaign numbers (`100,000`).
2. **Series Code Classifier Priority**:
   - For LG 2026 models: QNED series patterns (`QNED93B`, `QNED87B`, `QNED86B`, `QNED85B`, `QNED80B`, `QNED70B`, `QNED7EB`) MUST be evaluated BEFORE loose OLED `G6`/`C6`/`B6` matchers, preventing model code suffixes like `85QNED93B6A` from being misclassified as `OLED B6`.
   - For Samsung 2026 models: Eastern European model codes ending in `H` (e.g. `U8072H`, `U8092H`, `U8070H`) MUST be recognized as Model Year **`2026`** and mapped to `U8000H` series.

### Step H3: Output & Excel Workbook Sync
* Raw JSON outputs are saved to `data/raw_alza_lg.json` and `data/raw_alza_samsung.json`.
* Results are appended/updated into `Alza_CZ_Samsung` and `Alza_CZ_LG` sheets of `price tracker_EU_2026 {MMDD}_v1.xlsx`.
* Automatically mirrored to `History_EU/{YYYY MMDD}/price tracker_EU_2026 {MMDD}_v1.xlsx`.

### Step H4: EU Dashboard Compilation, 1:1 Pairing & Firebase Deployment
1. **Czech Republic Pairs (`PAIRS_CONFIG_2026_CZ`)**:
   - OLED: `G6 vs S99H/S95H`, `C6 vs S90H`, `B6 vs S85H`
   - QNED/QLED: `QNED93B vs QN80H`, `QNED86B vs QN80H`, `QNED85B vs QN70H`, `QNED80B vs M80H`, `QNED70B vs M70H`
   - UHD 4K: `NU85 vs U8070H` (matches `U8072H`, `U8070H`, `U8092H`, `U8000H`)
2. **Currency Formatting**: Czech Republic MUST render prices in Koruna (`Kč ` / `CZK`).
3. **HTML Compilation & Firebase Deployment**:
   - Execute builder script: `python scripts/generate_eu_dashboard.py`.
   - Deploy live via Firebase CLI / MCP: `npx firebase-tools deploy --only hosting:eu-price-tracker`.
   - Endpoint: **`https://eu-price-tracker-lge.web.app`**.

---

## Part I: Greece (Public.gr) Multi-Query Expanded TV Price Survey Pipeline

### Step I1: Multi-Query Targeted Sampling Configuration
Public.gr search queries cap results at 36 products per page. Scrapers MUST traverse 59 multi-query targeted configurations to achieve full catalog coverage:
- **Samsung (22 queries)**: `samsung tv`, `samsung oled`, `samsung qled`, `samsung neo qled`, `samsung 4k`, `samsung tv 2026`, `samsung tv 2025`, `samsung tv oled/qled/4k`, `samsung tv 55/65/75/77/83/85`, `samsung mini led`, `samsung micro`, `samsung the frame`, `tileoraseis samsung`, `samsung smart tv`, `cat/tileoraseis/tileoraseis/`.
- **LG (37 queries)**: `lg tv`, `lg oled`, `lg qned`, `lg 4k`, `lg oled c6/g6/b6/c5`, `lg c5/g5/b5/b6/c6/g6`, `lg qned 93/87/86/80/72`, `lg nano`, `lg nu85`, `lg mrgb`, `lg micro`, `lg ua`, `lg tv 2026/2025`, `lg tv oled/qned/4k`, `lg tv 55/65/75/77/83`, `tileoraseis lg`, `lg smart tv`, `cat/tileoraseis/tileoraseis/`.
- **Deduplication**: Python in-memory deduplication via unique product URL paths.

### Step I2: Digit-Aware Pattern Matching & Guard Rules
1. **Digit-Aware Series Matching**: LG series codes must use digit-aware matchers (`G6[0-9]`, `C6[0-9]`, `B6[0-9]`, `G5[0-9]`, `C5[0-9]`, `B5[0-9]`) and sub-model aliases (`QNED83B` $\rightarrow$ `QNED81B`, `QNED82A` $\rightarrow$ `QNED80A`, `QNED71B` $\rightarrow$ `QNED70B`) to prevent word-boundary mismatches.
2. **Screen Size Price Threshold Guard**: Enforce minimum price thresholds per screen size (70"+ $\ge$ €700, 55"+ $\ge$ €350, 48"+ $\ge$ €250) to reject discount badge false positives (e.g. `600,00 €` badge).

### Step I3: Output & Excel Workbook Sync
- Raw JSON saved to `data/raw_public_gr_samsung.json` (92 items) and `data/raw_public_gr_lg.json` (57 items).
- Appended/updated to `Public_GR_Samsung` and `Public_GR_LG` sheets in `data/price tracker_EU_2026 {MMDD}_v1.xlsx` in standard EU column format.

### Step I4: 1:1 Pairing & Dashboard Deployment
1. **Greece Pairs (`PAIRS_CONFIG_2026_GR`)**:
   - OLED: `G6 vs S95H/S99H`, `C6 vs S90H`, `B6 vs S85H`
   - MRGB: `MRGB87B vs R85H` (86"-55"), `MRGB96B vs R95H` (100")
   - QNED/QLED: `QNED87B vs QN80H`, `QNED81B vs QN70H`, `QNED81B vs M80H`, `QNED72B vs M70H`
   - UHD 4K: `NU85 vs U8070H` (matches `75NU8E0B3LA`, `65NU850B6LA`, `UE65U8072H`, `UE55U8072H`, `50U8072F`, `UE43U8072H`)
2. **Currency**: Euro (`€` / `EUR`).
3. **Build & Deploy**: `python scripts/generate_eu_dashboard.py` $\rightarrow$ `firebase deploy --only hosting:eu-price-tracker`.

---

## Part J: Swiss Master URL Registry Loss-Prevention & Auto-Registration Engine

### Step J1: Master Registry Integration (`data/master_product_urls.json`)
1. **Swiss Scope (`country == 'CH'`)**:
   - Permanent registry contains **911+ verified Swiss model URLs** across MediaMarkt, Interdiscount, and Digitec.
   - Automatically scanned from all historical subdirectories (`History/*/price tracker_swiss_*.xlsx`) via `scripts/build_master_url_registry.py`.
2. **On Every Survey Execution (`sync_all_retailers.py`)**:
   - Executes `sync_with_swiss_master_registry()` for all 6 retailer/brand groups (`MediaMarkt`, `Interdiscount`, `Digitec` $\times$ `Samsung`, `LG`).
   - Cross-references live search results with `data/master_product_urls.json`.
   - Auto-registers newly launched models into `data/master_product_urls.json` with verified PDP URLs and timestamps.
   - Prevents sample dropouts from pagination boundaries or temporary ranking shifts.
3. **Automated Pipeline Trigger**:
   - `scripts/run_survey_with_check.py` invokes `build_master_url_registry.py` immediately after Excel sheet synchronization.

---

## Part K: Weekly Price & Promotion Variation Analysis Standards ('26년 모델 Only)

### Step K1: Weekly Transition & Dynamic ISO Week Calculation
1. **Scope**: Strictly limited to **2026 Model Year (`year == 2026`)**.
2. **Week Transitions**:
   - **W34**: `W34(08.17) vs W33(08.14)`
   - **W33**: `W33(08.14) vs W32(08.06)`
   - **W32**: `W32(08.06) vs W31(07.28)`
   - **W31**: `W31(07.28) vs W30(07.25)`
   - On future survey rounds (e.g. W35, W36), append the new transition and set it as the default active tab.
3. **ISO Calendar Week Formatting**:
   - Python date injection uses `now_dt.isocalendar()[1]` to generate `2026년 08월 17일 (W34)` and `2026.08.17(W34)`.
   - UI displays clean retailer breakdown pills (MediaMarkt / Interdiscount / Digitec) and filterable change tables.

---

## Part L: Price Guard Integrity & Anomaly Disambiguation Standards

### 1) Zero Fabricated / Zero Historical Price Injection Standard (CRITICAL)
- Price guards and cleansing scripts must **NEVER fabricate or overwrite prices with arbitrary hardcoded benchmark values** (e.g. 1,799 €, 1,299 €, 3,499 €).
- Outliers or anomalies (such as prices lower than normal thresholds or promo vouchers) must trigger live PDP URL re-probing or be discarded/flagged. Never insert artificial numbers into datasets or workbooks.

### 2) 2026 LG Model Code (`B6`/`6LA`) OLED Disambiguation
- In LG's 2026 naming scheme, **all non-OLED models (UHD 4K NanoCell, QNED) feature `B6` or `6LA` in their model codes** (e.g. `65NU850B6LA`, `55QNED81B6C`).
- Loose substring checks like `"B6" in title` or `"C6" in title` are strictly forbidden for OLED classification.
- Always require `display_type == "OLED"` or use strict word-bounded regex `\bOLED\w*[BCG][456]\b`.

### 3) European Thousand Separator (`.`) & Decimal (`,`) Parsing Standard
- In European and Greek formats (`1.199,00 €`, `559 ,00€`), parsers must normalize thousand periods and decimal commas (`replace('.', '').replace(',', '.')`) before float conversion to avoid truncating thousands (e.g. `1.199,00 €` -> `1.19`).





