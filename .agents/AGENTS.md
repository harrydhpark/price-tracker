# Project Rules: Price Tracker & Promo Analyzer

## 1. Data Collection Filters (MediaMarkt, Interdiscount & Digitec Exclusivity)
* **Direct Seller Only & Server Filters**:
  * For MediaMarkt Switzerland, **never scrape a single generic query URL**. Since the retailer's search engine limits page results and has backend metadata indexing issues (often omitting clearance or 이월 models like S90F from broad queries and year filters), you must loop through a list of targeted query configurations (both general and specific series queries) to guarantee 100% model coverage, and then deduplicate results in Python:
    * Samsung search configs:
      1. General TV: `https://www.mediamarkt.ch/de/search.html?query=samsung%20TV&brand=SAMSUNG&marketplace=MediaMarkt&modelyear=2025%20OR%202026` (Max 10 pages)
      2. OLED TV: `https://www.mediamarkt.ch/de/search.html?query=samsung%20OLED&brand=SAMSUNG&marketplace=MediaMarkt` (Max 3 pages)
      3. S90 Series: `https://www.mediamarkt.ch/de/search.html?query=samsung%20S90&brand=SAMSUNG&marketplace=MediaMarkt` (Max 2 pages)
      4. S95 Series: `https://www.mediamarkt.ch/de/search.html?query=samsung%20S95&brand=SAMSUNG&marketplace=MediaMarkt` (Max 2 pages)
      5. S99 Series: `https://www.mediamarkt.ch/de/search.html?query=samsung%20S99&brand=SAMSUNG&marketplace=MediaMarkt` (Max 2 pages)
    * LG search configs:
      1. General TV: `https://www.mediamarkt.ch/de/search.html?query=LG%20TV&brand=LG&marketplace=MediaMarkt&modelyear=2025%20OR%202026` (Max 10 pages)
      2. OLED TV: `https://www.mediamarkt.ch/de/search.html?query=LG%20OLED&brand=LG&marketplace=MediaMarkt` (Max 3 pages)
      3. C6 Series: `https://www.mediamarkt.ch/de/search.html?query=LG%20C6&brand=LG&marketplace=MediaMarkt` (Max 2 pages)
      4. G6 Series: `https://www.mediamarkt.ch/de/search.html?query=LG%20G6&brand=LG&marketplace=MediaMarkt` (Max 2 pages)
      5. C5 Series: `https://www.mediamarkt.ch/de/search.html?query=LG%20C5&brand=LG&marketplace=MediaMarkt` (Max 2 pages)
      6. G5 Series: `https://www.mediamarkt.ch/de/search.html?query=LG%20G5&brand=LG&marketplace=MediaMarkt` (Max 2 pages)
  * For Interdiscount Switzerland, navigate directly to category-based TV lists instead of search queries: `/de/fernseher--c111000?brand=SAMSUNG&page=N` and `/de/fernseher--c111000?brand=LG&page=N`. Only collect listings sold directly by Interdiscount.
  * For Digitec Switzerland, filter only products that are sold directly and are currently in stock (Lager / In Stock). Always append `&take=150` to load all items on a single page, and handle the `"Mehr anzeigen"` (Show more) click to retrieve subsequent listings.
* **Category Purging**: Exclude non-TV display products. Filter out gaming monitors (e.g., Odyssey series, UltraGear series, MyView series) and prioritize pure TV/Lifestyle TV screens.
* **Target Release Years (Strict Filtering)**: Limit search/collection scopes strictly to Model Years `2025` and `2026`. Skip older generations (e.g., Samsung D-series like S90D/QN90D, LG 4-series like C4/G4/B4).
  * **Default Value**: Always default `year_val = None` (not 2025) before matching to ensure any unclassified or older model is automatically excluded.
  * **Model Year Letters (Samsung)**: `D` corresponds to 2024, `F` to 2025, and `H` to 2026. Search for these letters after index 2 of the model code (e.g. `QE65S90F`) to avoid matching prefix characters (like `F6000`). If the model code is `"Unknown"`, apply a regex-based smart extractor (`extract_model_code_from_title` using pattern lists like `QN\d{2,3}[FH]`, `S\d{2}[FH]`, `U\d{4}[FH]`, `M\d{2}[FH]`, `R\d{2}[FH]`, `LS03[A-Z]{1,2}`, `F\d{4}`, `MR\d{2}[FH]`) to reconstruct standard codes (e.g. `S95F` -> `QE{size}S95F`, `QN90F` -> `QE{size}QN90F`) before falling back to manual matching. If still unknown, fall back to matching year codes in the product title (e.g., `"S90H"` -> 2026, `"QN90F"` -> 2025).
  * **Model Year Codes (LG)**: `4`/`A` corresponds to 2024, `5`/`A`/`7` to 2025, and `6`/`B` to 2026. Check both the model code and title fallback.
    * **2026 Codes**: `C6`, `G6`, `B6`, `QNED86B`, `QNED80B`, `QNED87B`, `QNED72B`, `QNED7EB`, `UA77`, `MRGB87B`, `LX7B`, `LX6`, `QLED7EB`, `MRGB96B`.
    * **2025 Codes**: `C5`, `G5`, `B5`, `QNED86A`, `QNED80A`, `QNED87A`, `QNED72A`, `QNED7EA`, `UA75`, `MRGB87A`, `LX7A`, `LX5`, `QNED70A`, `NANO81A`, `NANO80A`, `QNED93A`.
    * **Budget Fallback**: If a model code matches a 2024 budget code suffix (e.g. `UA73`) but the title explicitly contains `"2025"`, classify it as 2025.
  * **Size Threshold**: Exclude any models with screen size **`< 22` inches** (this ensures small lifestyle screens like the 27" LG StanbyME TV are captured, while excluding monitors/accessories).
* **Exclude Non-visible / Out-of-Stock Models (Critical)**: When compiling the Excel sheet, exclude any models that are currently out-of-stock or not visible/searchable in the live search results on the respective retailer's website (MediaMarkt, Interdiscount, Digitec). Only active, direct-sell, and in-stock models matching the query should be included in the final Excel output. Do not preserve legacy or obsolete models that are no longer listed, to avoid database bloat.



## 2. Technical Execution Standards (Anti-Scraping & Browser Contexts)
* **Node.js Playwright API Conventions (Critical)**: When executing browser evaluation loops via Playwright MCP server RCE, do not mix Python's snake_case / property style (e.g. `.first` or `is_visible()`). Always use Node.js Playwright API camelCase methods:
  * First element: **`locator.first()`** (with parentheses).
  * Visibility check: **`await locator.isVisible()`** (async camelCase method).
* **JSON-Escaped HTML Source Handling**: The raw page source returned by Playwright MCP RCE dumps (`page.content()`) is typically output as a single JSON-escaped string. You must completely decode the escapes (e.g. using `json.loads` or replacing `\\"` with `"` and `\\\\` with `\\`) before loading it into BeautifulSoup. Otherwise, the parser will fail to build the DOM tree.
* **Viewport Scrolling & Dynamic Loading (Digitec)**: Always scroll the page down (`window.scrollTo` or `scrollIntoView`) to trigger infinite scroll/AJAX loading elements. Allow a minimum of 2.0 - 2.5 seconds after each scroll/click for elements to render.
* **Headed Browser Requirement & Playwright MCP Bypass (Interdiscount)**: For Interdiscount Switzerland, always run Playwright in headed mode (`headless: false`) and disable automation flags (`--disable-blink-features=AutomationControlled`). If headed execution gets blocked by Cloudflare in the background, utilize the agent-controlled Playwright MCP server's browser session (`browser_tabs` and `browser_run_code_unsafe` with a custom Javascript evaluation block) to perform the scraping.
  * **MCP High-Speed Bypass Execution**: When using the Playwright MCP server bypass, run a unified javascript script using `browser_run_code_unsafe` to loop through Samsung (pages 1 to 5) and LG (pages 1 to 5) in a clean, non-blocked sandbox profile. This cuts scraper execution time down from 15+ minutes (under local captcha loop delays) to less than 50 seconds.
  * **Local Data Synchronizer**: Process the saved raw text dump of the MCP output using the helper script: `python scripts/fast_interdiscount_sync.py <path_to_mcp_output_txt>` to cleanly parse, filter, and write outputs to `data/raw_interdiscount_samsung.json` and `data/raw_interdiscount_lg.json`.
* **Scrapling StealthySession for MediaMarkt (Critical)**: For MediaMarkt Switzerland, utilize Scrapling's `StealthySession` context manager (`with StealthySession(headless=True) as session:`) to solve the Cloudflare Turnstile captcha automatically and reuse cookies across page requests, preventing pagination timeouts and blockages.
  * **Omit `network_idle=True`**: Do **not** use the `network_idle=True` parameter in `StealthySession.fetch()`. Because commercial sites continuously run background analytics, ads, and websocket connections, the network never becomes fully idle, causing requests to hang until the maximum 60-second timeout. Rely instead on default DOM load events combined with a render sleep (`wait=3000 * TIMEOUT_MULTIPLIER`).
  * **Accurate Block Detection**: When validating whether a fetch was blocked by Cloudflare, do **not** check for the generic word `"blocked"` inside the HTML body, as legitimate product listings often contain this string. Check only for `"Verification Required" in html` or non-200 HTTP statuses.
* **Usercentrics CMP Cookie Banner Piercing (Critical)**: MediaMarkt/MediaWorld privacy banners (`Wir respektieren Ihre Privatsphäre`, `Aceptar todo`, `Accetta tutto`) are encapsulated inside `#usercentrics-root.shadowRoot`. Scrapers must query `shadowRoot.querySelector('#uc-btn-accept-banner')` or `button[data-testid="uc-accept-all"]` to click the accept button and prevent page blockages.
* **MediaWorld IT & MediaMarkt DE Multi-Page Pagination & Attribute Matching**:
  * **Attribute Matching**: MediaWorld IT product cards format product type as `Tipo di dispositivo` (instead of `Tipo di producto`). Parsers must include `Tipo di dispositivo` along with `OLED`, `QNED`, `Hz`, `pollici`, `Classe` in `PRODUCT_MARKER`.
  * **Fnac + Darty France Combined Multi-Page Search Pipeline (137 Active Excel Rows)**: France TV tracking combines Darty France (`darty.com`) and Fnac France (`fnac.com`, `https://www.fnac.com/SearchResult/ResultList.aspx?Search=tv+{brand}&PageIndex=N`). Multi-page search scraping across pages 1 to 5 yields **333 raw extracted cards** (168 Samsung, 165 LG) and **137 active 2025/2026 TV rows** in Excel (72 Samsung, 65 LG), completely matching DE, NL, ES, IT volume standards.
  * **Discount Mention Filtering (`100€ de remise` Guard)**: On retailer cards (e.g. Darty, Fnac, MediaMarkt), discount badge mentions (e.g. `100€ de remise` or `50€ de reduction`) must be stripped before matching selling prices, preventing discount values from overwriting real TV selling prices.
  * **Raw Extracted vs Excel Reflected Model Count Gap (4-Stage Cleansing)**: Understand that raw extracted counts will always be higher than final Excel reflected counts due to strict data processing: (1) 2025/2026 model year filtering (excluding 2024/legacy clearance models), (2) non-TV purging (excluding Odyssey/UltraGear monitors, soundbars, accessories, refurbished items), (3) size threshold exclusion (<22 inches), and (4) lowest-price model code deduplication (collapsing duplicate member/promo URLs into 1 unique lowest-price row per model).
  * **Pagination Loop**: MediaMarkt/MediaWorld/Darty/Fnac sites cap initial page loads to 12-24 items. Scrapers must traverse pages 1 to 5 for MediaWorld IT & Darty/Fnac FR (`&page=1` through `&page=5` / `PageIndex=1..5`, 300+ items) or click "weitere Produkte anzeigen" up to 10-12 times for MediaMarkt DE/NL/ES (190+ items) to collect full product catalogs.
* **DOM-Climbing Parser**: Avoid relying solely on unstable CSS class names. Locate key text nodes (like brand names or product links) and programmatically climb up parent nodes (`parentElement` in JS or `.parent` in BeautifulSoup) to extract prices, promotions, and shipping details.
* **Aria-Label Attribute Extraction (Interdiscount & Digitec)**: Both Interdiscount and Digitec product titles are kept inside the `aria-label` attribute of the product anchor (`a[href*="/product/"]`), leaving the inner text empty. Programmers must extract titles via `link.getAttribute('aria-label')`.
* **Translation-Tolerant Matchers**: Since local agent environments may trigger browser-level Korean machine translation (e.g., converting "CHF" to "스위스 프랑", "Cashback" to "캐시백", "Discount" to "할인/혜택"), use flexible regex for decimal parsing (`/(\d[\d\s’\x27\x60,.]*[,.]\d{2})/`) and allow both German/English and Korean translation terms.

## 3. Excel Output & File Integrity Rules
* **Dynamic Excel Lock Bypass Loop (Critical)**: When exporting results using `pandas` and `openpyxl`, always anticipate that the target Excel workbook might be opened in Excel by the user (generating `PermissionError [Errno 13]`). Wrap file writing in a dynamic loop that auto-increments the file version suffix (e.g., `_v3`, `_v4`, `_v5`) continuously until a free path is found. Never abort execution on permission errors.
* **European Thousand Separator & Abnormal Price Guard Rules (Critical)**:
  * **European Format Parsing (`1.799 €` $\rightarrow$ `1799.0`)**: In European notation (DE, NL, ES, IT, FR), dots are used as thousand separators (e.g. `1.799 €` = €1,799). String-to-number parsers MUST check for `^\d{1,3}\.\d{3}$` or `^\d{1,3},\d{3}$` and strip thousands dots before converting to float, preventing `1.799 €` from being parsed as `1.799` float (which rounds to `€2` on charts).
  * **Screen Size Price Threshold Guard (Prevention of `100€ d'économie` False Positives)**: Promotional badges (e.g., `100€ de remise`, `100€ d'économie`, `50€ de réduction`) MUST be pre-stripped using comprehensive regex (`d'économie`, `de remise`, `réduction`, `remise immédiate`, `d'avantage`). Furthermore, screen size price threshold guards MUST be enforced: 70"+ TVs must be `>= €1,000`, 60"+ TVs must be `>= €500`, 50"+ TVs must be `>= €300`, and any TV price `< €150` MUST be rejected to prevent discount badge numbers (e.g. `100`) from overwriting real TV selling prices.
  * **Threshold Guard (`price < 50.0` Purging)**: TV prices must be `>= 50.0`. Any price extraction resulting in `< 50.0` or negative values MUST be flagged as an invalid extraction and sanitized to `0` or `None`.
  * **Cashback Single-Digit False Positive Guard**: Cashback numeric extraction must reject values `< 10` (e.g. `2` from "2 years warranty" or "2% discount") to prevent single-digit numbers from being written into the Cashback column.
  * **Case-Insensitive Sheet Row Deletion**: When syncing retailer sheets, string comparisons for brand row deletion (e.g., `sheet.cell(row=r, column=1).value`) MUST be case-insensitive (`str(brand_val).upper() == str(brand).upper()`) to prevent stale rows from accumulating across syncs.
* **Strict Promotion Column Separation**: Always split promotional metadata into two separate columns:
  * `Cashback (CHF)`: Keep as a clean integer numeric column. **CRITICAL**: Only map a cashback value if the raw scraped promotion text explicitly contains a clear numeric cashback value alongside the word "Cashback" or "캐시백" (e.g. "CHF 150 Cashback"). If the cashback amount is not explicitly specified on the website for that model, you MUST write `0`. Never auto-inject, estimate, or derive cashback values based on panel type, sizes, or standard tables.
  * `General Promotions`: Keep as text for bundles, free gifts, and club member voucher specifications.
* **Promotion Text Standardization**: Raw German/French promotional texts must be mapped to their clean English equivalents:
  * `"mit kostenlosem Zusatzprodukt"` / `"Zusatzprodukt"` $\rightarrow$ `"Free Promotional Product (Sound Device)"`
  * `"RESTPOSTEN"` / `"Restposten"` $\rightarrow$ `"Clearance (Restposten)"`
  * `"Outlet"` $\rightarrow$ `"Outlet (Clearance)"`
  * `"SoundSuite/Soundbar"` / `"SoundSuite"` $\rightarrow$ `"Free SoundSuite/Soundbar with LG OLED TV 2026 Purchase"` (LG 2026 only)
  * `"Sound Device geschenkt"` $\rightarrow$ `"Free Sound Device with 2026 TV Purchase"` (2026 TVs only)
  * `"Music Studio 5"` $\rightarrow$ `"Free Music Studio 5 Soundbar (HW-LS50H/EN)"`
  * `"Cashback und oder 26% Rabatt auf Soundbar QS700F"` $\rightarrow$ `"Samsung Cashback and/or 26% Off Soundbar QS700F"`
  * `"Aus unserer Werbung"` / `"Werbung"` $\rightarrow$ `"Featured in Weekly Ad (Aus unserer Werbung)"`
  * `"Online Only"` $\rightarrow$ `"Online Only"`
  * Discount badges (e.g., `CHF 299.– statt CHF 349.–` / `14% Rabatt`) $\rightarrow$ `"Sale N%; was CHF X"`
* **Direct Cashback Sync Retrieval**: When syncing data from the price tracker Excel sheet to the comparative analysis sheet, the script must load the cashback value directly from the `Cashback (CHF)` column (Column 9) of the price tracker sheet instead of parsing it from the promotion text. This preserves manually inputted or adjusted cashback amounts.
* **Excel Source Sync Command**: To rebuild or sync comparison sheets for historical dates or manually reviewed price trackers, execute `python scripts/sync_all_retailers.py --excel-source <path_to_price_tracker>`. The script dynamically resolves the output comparison file path in the same directory.
* **Excel Color Verification**: Note that 6-digit RGB colors (e.g. `002060`) written via openpyxl are automatically converted internally to 8-digit aRGB values (e.g. `00002060` with a leading `00` alpha channel). When writing test or verification scripts, always check that the color value matches either format (e.g. `val in ["002060", "00002060"]`) to avoid false verification failures.

## 4. Swiss ATA Comparison Report Format Rules
* **Golden Template Standard (Strict)**:
  * **`Swiss_ATA_Comparison_2026_0705_v2.xlsx`** (stored in `History/2026 0705`) is the official golden standard layout and template for all comparative analysis outputs.
  * You must strictly replicate the styling, borders, colors, font families, and formula configurations of this golden template.
  * **NO CHANGES** to the structure, colors, headers, formulas, sheet naming, or formatting are permitted without the user's explicit permission. If you think a modification is needed, you **MUST stop and ask the user for permission** first.
* **Header and Cell Shift**:
  * Keep cell `B2` completely empty.
  * Cell `B3` must be formatted in bold and contain the label `'Series'`.
* **B-Column Series Code Refactoring (Clean Series)**:
  * Strip minor generation/region suffix digits:
    * LG OLED G: `G57`/`G67` -> `G5`/`G6`
    * LG OLED C: `C57`/`C67` -> `C5`/`C6`
    * LG OLED B: `B59`/`B69` -> `B5`/`B6`
    * Samsung OLED S90: `S905` -> `S90F` (2025) and `S90H` (2026)
    * Samsung OLED S85: `S855` -> `S85F` (2025) and `S85H` (2026)
    * Samsung QN70: `QN70f` -> `QN70F` (2025) and `QN70H` (2026)
  * **Precise Series Matching (OLED vs QNED & Generation Boundaries)**:
    * When matching LG series codes, ensure generic suffixes like `G5`, `C5`, `B5`, `G6`, `C6`, `B6` do not falsely match QNED or other model types (e.g., `QNED86B6B` contains `B6` and must not be mapped into OLED `B6` series). Add checks that exclude `QNED` or verify `OLED` prefix when mapping OLED series.
    * **Generation Boundary Separation**: Ensure the matching algorithm filters products strictly by year (`p.get("year") == year`) and uses generation-specific conditions (e.g., `family == "G5"` checks only `"G5" in code`, and does not match `G6` models), preventing cross-generation mismatches (e.g., mapping `G6` to `G5` rows).
  * **QNED/QLED 2025 Comparison Pairs & Sub-Model Alias Fallback Rules**:
    * **2025 QNED/QLED Pairing Set**:
      1. `QNED86A vs QN80F` (LG QNED86A/85A/87A vs Samsung QN80F/QN8xF)
      2. `QNED86A vs QN70F` (LG QNED86A/85A/87A vs Samsung QN70F/QN7xF)
      3. `QNED80A vs Q8F` (LG QNED80A/82A/84A vs Samsung Q8F/Q80F)
      4. `QNED80A vs Q7F` (LG QNED80A/82A/84A vs Samsung Q7F/Q70F)
    * **Germany-Specific 2025 & 2026 QNED/QLED Pairs**:
      * 2026 DE: Declare `PAIRS_CONFIG_2026_DE` with 4 exclusive pairs (`QNED93 vs QN80H`, `QNED86B vs QN70H`, `QNED72B vs M80H`, `QNED72B vs M70H`).
      * 2025 DE: Declare `PAIRS_CONFIG_2025_DE` with 3 exclusive pairs (`QNED86A vs QN80F` 100-55" excluding 50/43", `QNED86A vs QN70F` 85-43" excluding 100", `QNED70A vs Q7F` 85-43" replacing QNED84A).
    * **LG Sub-Model Fallback Rules**:
      * `QNED86A`: If `QNED86A` / `QNED86` is absent, fall back to `QNED85A` / `QNED85` or `QNED87A` / `QNED87`.
      * `QNED80A`: If `QNED80A` / `QNED80` is absent, fall back to `QNED82A` / `QNED82` or `QNED84A` / `QNED84`.
    * **Samsung Sub-Model Fallback Rules**:
      * `QN70F` (`QN7xF`): Match `QN70F`/`QN70` or region variants `QN71F`, `QN72F`, `QN73F`, `QN74F`, `QN75F`.
      * `QN80F` (`QN8xF`): Match `QN80F`/`QN80` or region variants `QN81F`, `QN82F`, `QN83F`, `QN84F`, `QN85F`, `QN88F`.
      * `Q8F`: Match `Q80F`/`Q8F`/`Q80`.
      * `Q7F`: Match `Q70F`/`Q7F`/`Q70`.
  * **UHD 4K Model Variant Matching Rules (2025 & 2026)**:
    * **Samsung UHD 4K**: `U8000F` and `U8000H` series matchers MUST support all country and retailer suffix variants (`U8000`, `U8005`, `U8010`, `U8070`, `U8075`, `U8079`, `U8080`, `U8090`, `U7000`, `DU8000`, `CU8000`, `M70`, `M73`, `M80`, `U80`) to ensure 100% coverage across Germany MediaMarkt (`GU43U8079H`, `GU50U8079H`, `GU55U8079H`, `GU65U8079H`, `GU75U8079H`, `GU85U8079H`), France Fnac (`TU43U8005F`, `TU55U8005F`, `TU65U8005F`, `TU43U8005H`, `TU50U8005H`, `TU55U8005H`, `TU65U8005H`, `TU85U8005H`), MediaMarkt ES (`U8075`), and MediaWorld IT (`U7000`, `M70`, `M80`).
    * **LG UHD 4K**: `UA75` (2025) and `NU85` (2026) series matchers MUST support all country variants (`UA75`, `UA73`, `UA77`, `NU85`, `NU80`, `NU75`, `NU90`, `UT`, `UR`, `UQ`).
  * **Dynamic Empty Slot Hiding Rule (Dashboard)**:
    * Any size pair slot where at least one brand has a valid price (`lgP > 0 || samP > 0`) MUST be rendered on the chart so that single-brand offerings (e.g. LG OLED G6/C6/B6 lineup when competitor 2026 models are not yet listed) remain 100% visible. Only empty slots where BOTH brands have 0 (`lgP === 0 && samP === 0`) are filtered out to keep charts clean.

* **Model Sorting Order (Strict TV Segment Matching)**:
  * LG: OLED G -> OLED C -> OLED B -> QNED86 -> QNED80 -> UA.
  * Samsung: OLED S95 -> OLED S90 -> OLED S85 -> QN70 (Neo QLED) -> Q8 (QLED) -> Q7 (QLED) -> U8000.
* **Hidden Gridlines**:
  * Set `showGridLines = False` for both `Swiss_2025` and `Swiss_2026` worksheets to provide a clean visual presentation.
* **Clean Empty Cells (No 'N/A' or '0')**:
  * For missing/unmatched model slots, do not display `'N/A'`. Leave the cells blank (`""`).
  * In the bottom VLOOKUP summary table, wrap detailed model lookups in an `IF` statement: `=IF(VLOOKUP(...) = 0, "", VLOOKUP(...))` to prevent displaying `0` for empty text columns.
* **Integer Percentage Formatting**:
  * Format all ATA columns in both the upper matrices and lower VLOOKUP summaries as clean integer percentages using the `"0%"` format (no decimals).
* **Samsung Blue Styling & ATA Removal**:
  * Style all Samsung series codes (Column B) in bold Dark Blue font (`color="002060"`).
  * Style all Samsung detailed model name VLOOKUP outputs (Columns C, H, M) in regular Dark Blue font (`color="002060"`).
  * Clear all ATA cells for Samsung rows to keep them blank.
* **Row 87 / 133 Summary Layout**:
  * For `Swiss_2025` sheet: upper matrix runs from Row 4 to Row 83. The summary header begins at Row 86, and data rows start at Row 87.
  * For `Swiss_2026` sheet: upper matrix runs from Row 4 to Row 131. The summary header begins at Row 132, and data rows start at Row 133.
  * Group models by brand (LG first, then Samsung) and size groups (55", 65", 77/75") with spacer rows in between.
* **Q8H and Q7H Search Key Mapping**:
  * In the 2026 sheet's bottom VLOOKUP Summary Table, since `Q8H` and `Q7H` do not exist in the upper matrix, their VLOOKUP formulas must search for `"R95H"` and `"R85H"` keys respectively (e.g. `VLOOKUP("55R95H", ...)` for `55Q8H`).
* **Display Type Col A Mapping**:
  * Any series code containing `MRGB`, `R95`, or `R85` must be assigned the display type `"MRGB"`.
  * Series code `QNED93` must be assigned the display type `"QNED"`.
* **Dynamic Row Limit Scanning (No Hardcoded Offsets)**:
  * When populating, polishing, or parsing comparison sheets, do not use hardcoded offsets (such as `last_row = summary_start - 3`) to calculate the end of the upper matrix. Instead, calculate it dynamically by scanning Column 2 upwards from `summary_hdr_row - 1` until finding the first non-empty cell. This ensures that inserting rows or varying the number of blank spacer rows does not cause data lines to be skipped.

## 5. Price Survey Dashboard & History Archive Rules
* **Sub-Agent Role for HTML Dashboard**: Creating and compiling the interactive HTML Price Comparison Dashboard (`swiss_price_dashboard.html`) is explicitly designated as a sub-agent execution task.
* **Global Price Type Slicer**: The dashboard must feature a Price Type Slicer in the header allowing users to toggle between `"판매가"` (Raw Price) and `"실질가 (캐시백반영)"` (Net Value = Price - Cashback) across all views.
* **Interactive Bar Chart Tooltips (Model Name & Promotion Display)**:
  * When a user hovers over a price bar, the Chart.js tooltip must display the exact model code (e.g. "Model: QE83S90FAE" or "Model: OLED83C57LA") extracted from Columns 3, 8, and 13 of the comparative analysis sheet. Pass these model codes from the python dashboard builder in the JSON payload (`lg_model_msh`, `sam_model_msh`, etc.) and format them in the tooltip `afterLabel` callback alongside the parsed General Promotion details.
* **Sidebar Historical Price Slicer**:
  * Add a third menu item: **`일자별 가격비교`** (Historical Price Comparison).
  * This view must show a dropdown select for all surveyed model series (dynamically updated by year).
  * Display a **line chart (Line Chart)** showing price trends for MediaMarkt, Interdiscount, and Digitec across different survey dates, alongside a detailed data table.
* **Dynamic Display Slices Buttons**:
  * The display type slices tab buttons must be rendered dynamically based on the active year (2026 includes `OLED`, `MRGB`, `QNED/QLED`, `UHD 4K`; 2025 includes `OLED`, `QNED/QLED`, `UHD 4K`).
  * If a user is viewing `MRGB` in 2026 and switches to 2025, the view must automatically fallback to `OLED`.
* **Chart Text Styling and Formatting**:
  * Set x-axis tick labels for model codes to `size: 8` with `maxRotation: 45` to prevent text overlapping or cutting off in crowded charts.
  * Enable `offset: true` on the chart X-axis and define a `grace: '5%'` on the Y-axis.
  * Define `datalabels` configurations individually within each dataset object (MediaMarkt: `align: 'top'`, Interdiscount: `align: 'bottom'`, Digitec: `align: 'right'`) rather than globally, resolving label overlapping and visual clipping issues.
  * Sidebar logo subtitle must be set to `"LGE SWISS MARKET PRICE TRACKING"`.
* **History Pre-Archive Requirement (Critical for Trend Chart)**:
  To ensure the current day's price data is correctly scanned and included in the "Historical Price Comparison" (일자별 가격비교) trend line, you **must create the date-specific History folder and copy the two Excel files before compiling the dashboard**:
  1. Create a date-specific directory (e.g., `2026 0707` for July 7th, 2026) inside the `History` archive folder: `D:\TV 유럽영업\15. AX Task\2026 AX 실행과제\Price Tracker\History`.
  2. Copy and store the two compiled Excel workbooks into this newly created folder:
     * Scraped Raw Price Data: `price tracker_swiss_2026 [MMDD]_v*.xlsx`
     * Comparative Analysis Report: `Swiss_ATA_Comparison_2026_[MMDD]_v*.xlsx`
* **Dynamic Dashboard Update Trigger**:
  After pre-archiving the Excel files, automatically trigger `generate_dashboard.py` to rebuild and update the HTML dashboard template. The script will scan the History folder (now containing today's folder) and correctly include today's prices in the historical chart.
* **Firebase Hosting Deployment**:
  * The project utilizes Firebase multisite hosting under the project ID `fx-tracker-4f44c`.
  * The target site is **`swiss-price-tracker-lge`** (configured as hosting target `swiss-price-tracker` in `.firebaserc` and `firebase.json`).
  * The script `generate_dashboard.py` automatically outputs to the `public/index.html` directory.
  * To deploy the dashboard live, execute: `firebase deploy --only hosting:swiss-price-tracker`.
  * Deployed Web App URL: **`https://swiss-price-tracker-lge.web.app`**.
* **Final Dashboard Archiving (Backup)**:
  Once the deployment is successfully completed, copy and store the final compiled web dashboard (`swiss_price_dashboard.html`) into the same date-specific History folder to complete the archive.

* **Strict Series Matcher Boundaries (Prevention of Over-matching in Dashboards - Critical)**:
  * When mapping raw scraped products from Excel sheets into comparison paired JSON structures for dashboards (e.g. `generate_eu_dashboard.py`, `generate_dashboard.py`, `sync_all_retailers.py`, `sync_eu_retailers.py`), series matchers MUST enforce strict boundary rules to prevent missing/unlisted models from inheriting prices of other series:
    * **LG Micro RGB (`MRGB95` vs `MRGB85`)**: `MRGB95` must ONLY match 9-series codes (e.g. `MRGB95`, `MRGB96`, `MRGB9`, `MR95`). `MRGB85` must ONLY match 8-series codes (e.g. `MRGB85`, `MRGB87`, `MRGB8`, `MR85`). Never use generic prefix checks like `"MRGB" in code` that cause 8-series models (`75MRGB87`) to fill `75MRGB95` slots.
    * **Samsung Micro RGB / MiniLED (`R95H` vs `R85H`)**: `R95H` must ONLY match `R95` / `MRE95`. `R85H` must ONLY match `R85` / `MRE85`. **CRITICAL**: Never include generic QNED/Neo QLED search terms (such as `or "QN" in code`) in Samsung `R` series matcher conditions, as this causes unlisted `R85H` slots to falsely match normal Neo QLED models (e.g., `QN74H`) and inject invalid prices into the dashboard.
    * **Samsung UHD 4K `U8000H` Scope Boundary**: `U8000H` / `U8005H` matchers MUST NOT contain `M80`, `M70` or LED M-series keywords, ensuring true `U8005H` prices (`450`, `550`, `580`, `750`, `1,199`) are not overridden by `M80H` LED models.
    * **Model Code Size Extraction Priority**: When parsing raw screen size, parsers MUST prioritize valid 2-digit screen sizes embedded inside model codes (e.g. `TQ65S92H` -> 65, `55QNED81B` -> 55) over title cm-to-inch conversions (e.g. 163cm / 164cm -> 64), preventing size truncation errors from dropping models from comparison slots.
    * **Sub-model Alias Pair Label Sync Rule**: When mapping sub-model aliases (e.g. `QNED84A` -> `QNED80A` family or `QNED81B` -> `QNED80B` family), the dashboard configuration (`PAIRS_CONFIG`) MUST explicitly update the series label (`lg` or `sam` key) to match the exact alias code (e.g. `"lg": "QNED84A"`) so that X-axis chart labels dynamically display the exact target series name (`65"QNED84A vs. 65"Q7F`) instead of stale fallback family labels.
    * **Country-Specific Dashboard Pair Isolation**: When updating retailer comparison pairs for a specific country/retailer (e.g. Italy MediaWorld `QNED87B vs QN70H` & `QNED70B vs M70H`), declare an isolated country configuration variable (e.g. `PAIRS_CONFIG_2026_IT`) and apply it conditionally for that country, ensuring other countries maintain standard global pair configurations without side effects.
    * **86/85 Inch Flagship Tolerance & Distinct Pair Labeling**: When comparing LG 86-inch models against Samsung 85-inch models (e.g. `86MRGB95 vs 85R95H`, `86MRGB85 vs 85R85H`, `86QNED70B vs 85M70H`), allow `85` and `86` inch sizes to match flexibly in `find_product` while explicitly formatting `pair_label` as `86"<LG> vs. 85"<SAM>` so both brand screen sizes are correctly and distinctly labeled on chart X-axes.
    * **OLED Series Code Requirement (Prevention of Year-Suffix Collisions)**: When matching LG OLED series (`B6`, `B5`, `C6`, `C5`, `G6`, `G5`), parsers MUST require `"OLED" in code` or explicit OLED prefixes. Never match solely on year-suffix strings like `"B6" in code`, which wrongly classifies 2026 QNED/Micro RGB/UHD 4K models (e.g. `43QNED87B6A`, `86MRGB87B6B`, `65NU850B6LA`) as OLED.
    * **Official Sub-model Priority Selection Rule**: When an Excel sheet contains both official country sub-models (e.g. Italian official OLED `OLED65G56LS`, `C55`, `G66`, or Samsung `U8000F` series) and parallel/lower sub-models (`OLED65G54LW`, `U7000F`), `find_product` MUST apply priority weighted sorting (`get_priority`) so official country sub-models are matched with highest 0-priority over lower/parallel variants.
    * **Strict U8000F Exclusion of U7000 Series**: Samsung `U8000F` / `U8000H` series matchers MUST NEVER include `"U7000"` keywords in their matching arrays. `U8000F` comparison slots must exclusively match true U8000 series (`U8000`, `U8005`, `U8070`, `U8075`, `U8090`, `DU8000`), preventing lower U7000 models from polluting U8000F chart slots.
    * **UK-Specific QNED Pair Order & 100-inch QNED87B Rule**: For UK Currys dashboard, declare `PAIRS_CONFIG_2026_UK` in exact order (`QNED86B vs QN80H`, `QNED86B vs QN70H`, `QNED72B vs M70H`). For the 100-inch slot under `QNED86B vs QN80H`, allow LG `100QNED87B` (`100QNED87B6`) to be matched flexibly while auto-converting the pair label to `100"QNED87B vs. 100"QN80H`.
    * **LG NU800B/NU850B UHD 4K Fixed Categorization**: LG 2026 `NU800B` / `NU850B` / `NU80` / `NU85` models MUST be strictly categorized under `UHD 4K`. Never allow year-suffix `B6` to misclassify them into OLED.
    * **Size-Prefixed LG OLED Matcher Rule**: LG OLED matchers (`G6`, `G5`, `C6`, `C5`, `B6`, `B5`) MUST support size-prefixed model codes (e.g. `42C67LA`, `48G69LS`, `55B68LA`, `77C67LA`, `97G67LW` where `OLED` prefix is absent) via `^\d{2}(G6|G5|C6|C5|B6|B5)` regex pattern matching, preventing country-specific OLED codes from being dropped from dashboards.
    * **NL-Specific QNED Pair Configuration & Single 85-inch Rule**: For Netherlands MediaMarkt dashboard, declare `PAIRS_CONFIG_2026_NL` with 3 exclusive pairs (`QNED86B vs QN80H`, `QNED82B vs M80H`, `QNED70B vs M70H`) and `PAIRS_CONFIG_2025_NL` with 2 exclusive pairs (`QNED86A vs QN74F`, `QNED70A vs Q7F`). Omit `"86"` from the `sizes` array and include only `"85"` to display a single merged `86"<LG> vs. 85"<SAM>` bar, preventing duplicate `86 vs 86` bars.
    * **QNED70 Series & QN74F Sub-model Matcher Boundary**: `QNED70` matchers MUST explicitly accept both `QNED70A` and `QNED70B` via `any(x in code for x in ["QNED70", "QNED72", "QNED7E"])`. Samsung `QN70F` matchers MUST accept regional sub-models like `QN74F` (`QE55QN74FATXXN`) via `any(x in code for x in ["QN70", "QN71", "QN72", "QN73", "QN74", "QN75"])`.
    * **Retailer Menu Button Order & Custom Badge/Label Standard**: `allRetailersList` array MUST be ordered as `UK` (Currys) $\rightarrow$ `DE` (MediaMarkt) $\rightarrow$ `FR` (Fnac) $\rightarrow$ `ES` (MediaMarkt) $\rightarrow$ `IT` (MediaWorld) $\rightarrow$ `NL` (MediaMarkt). Buttons MUST render badge text spans (`UK`, `DG`, `FS`, `ES`, `IS`, `BN`) and labels (`Currys (UK)`, `MediaMarkt (DG)`, `Fnac Darty (FS)`, `MediaMarkt (ES)`, `MediaWorld (IS)`, `MediaMarkt (NL)`). Initial active country MUST default to `UK` (`Currys`).
    * **Historical Price Table UK Priority & Multi-currency Rendering**: In `renderHistoryTable`, representative prices on main parent rows MUST prioritize `UK` Currys (`£`) as rank 1. If UK price is absent, fall back to `DE` $\rightarrow$ `ES` $\rightarrow$ `IT` $\rightarrow$ `FR` $\rightarrow$ `NL` priority order while dynamically formatting values with exact local currency symbols (`£` vs `€`). Child rows MUST be strictly sorted in `UK` $\rightarrow$ `DE` $\rightarrow$ `ES` $\rightarrow$ `IT` $\rightarrow$ `FR` $\rightarrow$ `NL` order.
    * **Chart Title Safe String Guard (`undefined` Prevention)**: Chart title generators MUST safely handle missing `flag` properties (e.g. `flag = item.flag ? (item.flag + ' ') : ''`) to prevent raw `undefined` strings from being injected into chart headers (e.g. `Currys (UK) 유통 분석`).

## 6. Automated Survey Verification, 10% Discrepancy Investigation & Rerun Policy
* **Survey Count Discrepancy Verification**: Immediately after scraping is completed across European major retailers (UK, DE, FR, ES, IT, NL, SE) and Swiss retailers (MediaMarkt CH, Interdiscount, Digitec), the automation pipeline MUST compare today's extracted model counts per country/brand against baseline counts from the previous survey cycle.
* **Strict 10% Discrepancy Threshold & Cause Investigation**:
  * If the extracted model count for any country or brand (e.g. MediaMarkt DE Samsung, Fnac FR LG, Digitec Samsung) differs or drops by **10% or more (> 10%)** compared to the baseline, the pipeline MUST immediately flag the discrepancy.
  * **Cause Diagnosis**: Automatically inspect logs to diagnose the exact root cause: (1) Cloudflare Turnstile / Captcha block or timeout, (2) Retailer backend search indexing omissions (e.g. omitted clearance models like S90F), (3) Pagination truncation, or (4) DOM selector changes.
* **Targeted Retry Strategy & Additional Survey Execution**:
  * **Scale Wait Times**: Re-run the target scraper with `TIMEOUT_MULTIPLIER` scaled to `1.5` ~ `2.0`.
  * **Query Splitting**: If generic brand query URL missed models, loop through targeted series-specific search configurations (e.g. S90/S95/C6/G6 individual queries) to guarantee 100% model coverage.
  * **Retry Limit**: Execute up to **3 retries (Max Retries = 3)** until the model count gap is brought under 10%.
* **Unified Pipeline Orchestration**: Use master orchestration scripts (`python scripts/run_survey_with_check.py`, `python EU-price-tracker/scripts/run_eu_survey.py`) to automate this complete sequence (scrape validation -> 10% gap diagnosis -> targeted additional survey -> excel sync -> history archive -> dashboard compile -> Firebase deploy).

