# Project Rules: Price Tracker & Promo Analyzer

## 1. Data Collection Filters (MediaMarkt, Interdiscount & Digitec Exclusivity)
* **Direct Seller Only & Server Filters**:
  * For MediaMarkt Switzerland, **never scrape a single generic query URL**. Since the retailer's search engine limits page results and has backend metadata indexing issues (often omitting clearance or 이월 models like S90F and newly launched series like QN80H, M70H, R85H, QNED86B, QNED71B, QNED70B, MRGB87B from broad queries and year filters), you must loop through a list of targeted query configurations (both general and specific series queries) to guarantee 100% model coverage, and then deduplicate results in Python:
    * Samsung search configs:
      1. General TV: `https://www.mediamarkt.ch/de/search.html?query=samsung%20TV&brand=SAMSUNG&marketplace=MediaMarkt&modelyear=2025%20OR%202026` (Max 10 pages)
      2. 2026 Lineup: `https://www.mediamarkt.ch/de/search.html?query=samsung%202026&brand=SAMSUNG&marketplace=MediaMarkt` (Max 5 pages)
      3. OLED TV: `https://www.mediamarkt.ch/de/search.html?query=samsung%20OLED&brand=SAMSUNG&marketplace=MediaMarkt` (Max 3 pages)
      4. S90 Series: `https://www.mediamarkt.ch/de/search.html?query=samsung%20S90&brand=SAMSUNG&marketplace=MediaMarkt` (Max 2 pages)
      5. S95 Series: `https://www.mediamarkt.ch/de/search.html?query=samsung%20S95&brand=SAMSUNG&marketplace=MediaMarkt` (Max 2 pages)
      6. S99 Series: `https://www.mediamarkt.ch/de/search.html?query=samsung%20S99&brand=SAMSUNG&marketplace=MediaMarkt` (Max 2 pages)
      7. Neo QLED QN80: `https://www.mediamarkt.ch/de/search.html?query=samsung%20QN80&brand=SAMSUNG&marketplace=MediaMarkt` (Max 2 pages)
      8. Mini LED M70: `https://www.mediamarkt.ch/de/search.html?query=samsung%20M70&brand=SAMSUNG&marketplace=MediaMarkt` (Max 2 pages)
      9. Micro RGB R85: `https://www.mediamarkt.ch/de/search.html?query=samsung%20R85&brand=SAMSUNG&marketplace=MediaMarkt` (Max 2 pages)
      10. Crystal UHD U8090: `https://www.mediamarkt.ch/de/search.html?query=samsung%20U8090&brand=SAMSUNG&marketplace=MediaMarkt` (Max 2 pages)
      11. The Frame: `https://www.mediamarkt.ch/de/search.html?query=samsung%20the%20frame&brand=SAMSUNG&marketplace=MediaMarkt` (Max 2 pages)
    * LG search configs:
      1. General TV: `https://www.mediamarkt.ch/de/search.html?query=LG%20TV&brand=LG&marketplace=MediaMarkt&modelyear=2025%20OR%202026` (Max 10 pages)
      2. 2026 Lineup: `https://www.mediamarkt.ch/de/search.html?query=LG%202026&brand=LG&marketplace=MediaMarkt` (Max 5 pages)
      3. OLED TV: `https://www.mediamarkt.ch/de/search.html?query=LG%20OLED&brand=LG&marketplace=MediaMarkt` (Max 3 pages)
      4. C6 Series: `https://www.mediamarkt.ch/de/search.html?query=LG%20C6&brand=LG&marketplace=MediaMarkt` (Max 2 pages)
      5. G6 Series: `https://www.mediamarkt.ch/de/search.html?query=LG%20G6&brand=LG&marketplace=MediaMarkt` (Max 2 pages)
      6. B6 Series: `https://www.mediamarkt.ch/de/search.html?query=LG%20B6&brand=LG&marketplace=MediaMarkt` (Max 2 pages)
      7. C5 Series: `https://www.mediamarkt.ch/de/search.html?query=LG%20C5&brand=LG&marketplace=MediaMarkt` (Max 2 pages)
      8. G5 Series: `https://www.mediamarkt.ch/de/search.html?query=LG%20G5&brand=LG&marketplace=MediaMarkt` (Max 2 pages)
      9. QNED Series: `https://www.mediamarkt.ch/de/search.html?query=LG%20QNED&brand=LG&marketplace=MediaMarkt` (Max 3 pages - QNED86B, QNED71B, QNED70B)
      10. Micro RGB MRGB: `https://www.mediamarkt.ch/de/search.html?query=LG%20MRGB&brand=LG&marketplace=MediaMarkt` (Max 2 pages - MRGB87B)
      11. StanbyME: `https://www.mediamarkt.ch/de/search.html?query=LG%20StanbyME&brand=LG&marketplace=MediaMarkt` (Max 2 pages - StanbyME 2 27LX6TDGA)
  * For Interdiscount Switzerland, navigate directly to category-based TV lists instead of search queries: `/de/fernseher--c111000?brand=SAMSUNG&page=N` and `/de/fernseher--c111000?brand=LG&page=N`. Only collect listings sold directly by Interdiscount.
  * For Digitec Switzerland, filter only products that are sold directly and are currently in stock (Lager / In Stock). Always append `&take=150` to load all items on a single page, and handle the `"Mehr anzeigen"` (Show more) click to retrieve subsequent listings.
* **Category Purging & Smartphone Exclusion Guard**: Exclude non-TV display products. Filter out gaming monitors (e.g., Odyssey series, UltraGear series, MyView series) and Samsung Galaxy smartphones (e.g., Galaxy S26 Ultra, Galaxy S26+, Galaxy S26, Smartphone, Handy, Mobile) that appear when querying "samsung 2026", prioritizing pure TV/Lifestyle TV screens.
* **Target Release Years (Strict Filtering)**: Limit search/collection scopes strictly to Model Years `2025` and `2026`. Skip older generations (e.g., Samsung D-series like S90D/QN90D, LG 4-series like C4/G4/B4).
  * **Default Value**: Always default `year_val = None` (not 2025) before matching to ensure any unclassified or older model is automatically excluded.
  * **Model Year Letters (Samsung)**: `D` corresponds to 2024, `F` to 2025, and `H` to 2026. Search for these letters after index 2 of the model code (e.g. `QE65S90F`) to avoid matching prefix characters (like `F6000`). If the model code is `"Unknown"`, apply a regex-based smart extractor (`extract_model_code_from_title` using pattern lists like `QN\d{2,3}[FH]`, `S\d{2}[FH]`, `U\d{4}[FH]`, `M\d{2}[FH]`, `R\d{2}[FH]`, `LS03[A-Z]{1,2}`, `F\d{4}`, `MR\d{2}[FH]`) to reconstruct standard codes (e.g. `S95F` -> `QE{size}S95F`, `QN90F` -> `QE{size}QN90F`, `QN80H` -> `QE{size}QN80H`, `M70H` -> `UE{size}M70H`, `R85H` -> `MRE{size}R85H`, `U8090H` -> `UE{size}U8090H`) before falling back to manual matching. If still unknown, fall back to matching year codes in the product title (e.g., `"S90H"` -> 2026, `"QN90F"` -> 2025).
  * **Model Year Codes (LG)**: `4` corresponds to 2024, `5`/`A` to 2025, and `6`/`B` to 2026. Check both the model code and title fallback.
    * **2026 Codes**: `C6`, `G6`, `B6`, `QNED86B`, `QNED80B`, `QNED87B`, `QNED71B`, `QNED70B`, `QNED72B`, `QNED7EB`, `UA77`, `MRGB87B`, `LX7B`, `LX6`, `27LX6TDGA`, `QLED7EB`, `MRGB96B`.
    * **2025 Codes**: `C5`, `G5`, `B5`, `QNED86A`, `QNED80A`, `QNED87A`, `QNED72A`, `QNED7EA`, `UA75`, `MRGB87A`, `LX7A`, `LX5`, `QNED70A`, `NANO81A`, `NANO80A`, `QNED93A`.
    * **Budget Fallback**: If a model code matches a 2024 budget code suffix (e.g. `UA73`) but the title explicitly contains `"2025"`, classify it as 2025.
  * **Size Threshold**: Exclude any models with screen size **`< 22` inches** (this ensures small lifestyle screens like the 27" LG StanbyME TV are captured, while excluding monitors/accessories).
* **Swiss Master URL Registry Loss-Prevention Standard (`data/master_product_urls.json`)**:
  * For Switzerland (MediaMarkt, Interdiscount, Digitec), all verified model codes and PDP URLs (including the 69 Samsung and 57 LG MediaMarkt CH models) are permanently registered in the Pan-European Master URL Registry (`country: 'CH'`).
  * On every survey execution (`sync_all_retailers.py` & `run_survey_with_check.py`), the pipeline reconciles live search results with `data/master_product_urls.json` to prevent sample loss from pagination boundaries or temporary indexing shifts, auto-registers newly launched models, and maintains full 100% historical continuity.
* **Zero Historical Price Injection Policy & Prohibition of Historical Backfill (CRITICAL)**: Never insert or backfill historical prices from previous survey workbooks into today's survey data without an active live web fetch. Any mechanism or script that copies prices directly from older workbooks (e.g. `hist_db` historical model copy) without issuing a live HTTP/DOM probe to verify current price and availability is strictly forbidden. Every single price written to Excel or dashboards must be validated via real-time search extraction or live PDP URL probing from today's live HTTP/DOM response.
* **Master URL Direct PDP Probe Requirement**: When supplementing missing models from `data/master_product_urls.json`, each model URL must be fetched live to retrieve today's real selling price and availability. Discontinued, deleted, or out-of-stock models must be automatically discarded to ensure 100% database freshness and accuracy.
* **Mandatory Pre-flight Assertion Gate (Hard Halt)**: All `raw_*.json` datasets must be freshly created on the survey execution date. Sync engines (`sync_eu_retailers.py` and `sync_all_retailers.py`) MUST assert that all source files reflect today's date and were modified within the current survey run window before generating workbooks. If any raw file is outdated or missing live scraping timestamps, the engine must immediately raise `RuntimeError` and halt execution.
* **Exclude Non-visible / Out-of-Stock Models (Critical)**: When compiling the Excel sheet, exclude any models that are currently out-of-stock or not visible/searchable in the live search results on the respective retailer's website. Only active, direct-sell, and in-stock models matching the query should be included in the final Excel output. Do not preserve legacy or obsolete models that are no longer listed, to avoid database bloat.
* **Prohibition of Hardcoded / Fabricated Price Overwrites (CRITICAL)**: Price guards and anomaly detectors must NEVER overwrite scraped prices with arbitrary hardcoded benchmark values (e.g., 1,799 €, 1,299 €, 3,499 €). Fabricating or injecting synthetic prices is strictly forbidden under the Zero Fabricated / Zero Historical Price Injection Policy. When an abnormal price outlier is identified (such as a selling price exceeding original price or low price due to promo voucher/accessory mis-scraping), the system MUST either trigger an immediate live PDP URL re-probe (`StealthySession` or live fetch) to verify the genuine price, or discard/flag the anomalous row. Never write artificial prices into datasets or workbooks.
* **Strict 2026 LG Model Code & OLED Disambiguation Standard (`B6` Guard)**: Never use loose substring matchers like `"B6" in title` or `"B6" in model_code` or `"C6" in title` to classify OLED models. In LG's 2026 TV naming scheme, ALL non-OLED models (UHD 4K NanoCell, QNED) feature `B6` or `6LA` suffixes in their model codes (e.g., `65NU850B6LA`, `55QNED81B6C`, `65QNED72B6B`, `85QNED72B6A`). Scrapers and guard engines MUST verify `display_type == "OLED"` or use strict word-bounded regular expressions (such as `\bOLED\w*[BCG][456]\b`) to avoid catastrophic misclassification of budget UHD/QNED models as OLED flagships.
* **European Thousand Period (`.`) & Decimal Comma (`,`) Parsing Standard**: European and Greek retailers (e.g. Public.gr, MediaMarkt DACH, Alza) format prices with periods for thousands and commas for decimals (e.g., `1.199,00 €`, `559 ,00€`). Regular expression extractors must never truncate at the thousand separator (which causes `1.199,00 €` to be misparsed as `1.19`). Parsers must strip extraneous whitespace and currency symbols, extract the full numeric string, normalize thousand periods and decimal commas (`replace('.', '').replace(',', '.')`), and then cast to float.




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
  * **Fnac + Darty France Firecrawl Stealth Pipeline (Mandatory DataDome Bypass & Master URL Registry)**:
    - **DataDome Bypass**: France TV tracking combines Darty France (`darty.com`) and Fnac France (`fnac.com`). Because DataDome deploys IP reputation blocking (`HTTP 403 Forbidden`) on Fnac/Darty for local scrapers, France price collection **MUST ALWAYS BE EXECUTED VIA FIRECRAWL STEALTH SCRAPER (`firecrawl_scrape`)** or Firecrawl proxy API.
    - **Never Use Restrictive Year Filters**: Do NOT use restrictive queries like `Search=tv+samsung+2025` or `Search=tv+lg+2025`. Because French retailers omit release years from product titles for 50%+ of SKUs (e.g. `TQ55Q80F`, `TQ65QN90F`, `TQ77S95H`), searching with year keywords causes severe sample drops (e.g. dropping from 150+ to 67). Scrapers MUST traverse broad & series-specific queries: `tv samsung`, `tv samsung oled`, `tv samsung the frame`, `tv lg`, `tv lg oled`, `tv lg qned` across pages 1 to 4.
    - **France Master URL Registry (Unified into `data/master_product_urls.json`, `country: "FR"`)**: France model URLs are stored in the Pan-European Master URL Registry (`data/master_product_urls.json`) with `country: "FR"`. Each survey run MUST merge newly scraped search results with the unified Master Registry to guarantee zero model drops and continuous historical tracking across surveys. The legacy `data/france_master_urls.json` file is deprecated and should not be used.
    - **French Narrow No-Break Space (`\u202f`: U+202F) & Unicode Normalization (Critical)**: French prices format thousands using Narrow No-Break Space (e.g. `1 999 €`, `1 299 €`, `1 799 €`). Scrapers and parsers MUST normalize `\u202f`, `\u00a0`, `\u2009`, `\u200b` to standard spaces before regex matching; otherwise numbers will split into `1` and `999` and fall back to incorrect monthly/accessory numbers.
    - **Installment & Discount Text Stripping**: Monthly installment text (`Dès ... € / mois`, `From £... a month`), credit charges (`TAEG`, `Montant total dû`), and discount mentions (`Bon Plan -X €`, `100€ de remise`, `50€ de reduction`, `300€ Cashback`, `200€ Reembolso`, `500€ Sconto`) MUST be pre-stripped from the card chunk before matching prices to prevent credit/discount values from overwriting real TV selling prices.
    - **Pan-European Screen-Size & Category Price Guard (Critical)**:
      - **OLED (B/C/G/M, S90/S95/S99/S85)**: 42"/48" $\ge$ 650 EUR/CHF (£650, 16,000 CZK, 260,000 HUF), 55" $\ge$ 800 EUR/CHF (£800, 20,000 CZK, 320,000 HUF), 65" $\ge$ 1,100 EUR/CHF (£1,100, 27,000 CZK, 440,000 HUF), 77"+ $\ge$ 1,600 EUR/CHF (£1,600, 40,000 CZK, 650,000 HUF), 83"+ $\ge$ 2,400 EUR/CHF (£2,400, 60,000 CZK, 950,000 HUF).
      - **Micro RGB (LG MRGB, Samsung R85/R95)**: 50"/55"/65" $\ge$ 850 EUR/CHF (£850), 75"/86"+ $\ge$ 2,000 EUR/CHF (£2,000), 100" $\ge$ 10,000 EUR/CHF (£10,000).
      - **QNED / QLED / Neo QLED**: 43" $\ge$ 250 EUR/CHF (£250), 50"/55" $\ge$ 350 EUR/CHF (£350), 65"+ $\ge$ 550 EUR/CHF (£550), 75"+ $\ge$ 900 EUR/CHF (£900).
      - **UHD 4K**: 43" $\ge$ 150 EUR/CHF, 55"+ $\ge$ 200 EUR/CHF.
    - **France Pairs Standard (`PAIRS_CONFIG_2026_FR` & `PAIRS_CONFIG_2025_FR`)**:
      - 2026 OLED: `G6 vs S95H/S99H`, `C6 vs S90H/S92H`, `B6 vs S85H`
      - 2026 QNED/QLED: `QNED81B vs QN74H` (43"~86"), `QNED81B vs M80H`, `QNED87 vs QN80H`, `QNED70B vs M70H`
      - 2025 QNED/QLED: `QNED87 vs QN74F`, `QNED87 vs QN80F`, `QNED84A vs Q7F`
  * **Discount Mention Filtering (`100€ de remise` Guard)**: On retailer cards (e.g. Darty, Fnac, MediaMarkt), discount badge mentions (e.g. `100€ de remise` or `50€ de reduction`) must be stripped before matching selling prices, preventing discount values from overwriting real TV selling prices.
  * **Raw Extracted vs Excel Reflected Model Count Gap (4-Stage Cleansing)**: Understand that raw extracted counts will always be higher than final Excel reflected counts due to strict data processing: (1) 2025/2026 model year filtering (excluding 2024/legacy clearance models), (2) non-TV purging (excluding Odyssey/UltraGear monitors, soundbars, accessories, refurbished items), (3) size threshold exclusion (<22 inches), and (4) lowest-price model code deduplication (collapsing duplicate member/promo URLs into 1 unique lowest-price row per model).
  * **Pagination Loop**: MediaMarkt/MediaWorld/Darty/Fnac sites cap initial page loads to 12-24 items. Scrapers must traverse pages 1 to 5 for MediaWorld IT & Darty/Fnac FR (`&page=1` through `&page=5` / `PageIndex=1..5`, 300+ items) or click "weitere Produkte anzeigen" up to 10-12 times for MediaMarkt DE/NL/ES/AT/CH (190+ items) to collect full product catalogs.
  * **Austria (MediaMarkt AT) & Switzerland (MediaMarkt CH) EU Pipeline & Pair Standards**:
    * **Austria MediaMarkt (`mm-at`)**: Scraped using standard MediaMarkt DACH engine. Titles format short series codes (`S92H`, `QN82H`, `M72H`, `M82H`, `R86H`, `U8070H`). `sync_eu_retailers.py` uses smart model code reconstruction (`size` + `series` $ightarrow$ `QE55S92H`, `UE50M72H`).
    * **Switzerland MediaMarkt (`mm-ch`)**: `sync_eu_retailers.py` directly loads pre-parsed clean items from `price tracker_swiss_2026 {MMDD}_v1.xlsx` sheets (`MediaMarkt_Samsung_Full` & `MediaMarkt_LG_Full`) to guarantee 100% data consistency (70 Samsung + 56 LG = 126 total models) with the Swiss price survey.
    * **Greece Pairs (`PAIRS_CONFIG_2026_GR`)**:
      - OLED: `G6 vs S95H/S99H`, `C6 vs S90H`, `B6 vs S85H`
      - MRGB: `MRGB87B vs R85H` (86"-55"), `MRGB96B vs R95H` (100")
      - QNED/QLED: `QNED87B vs QN80H`, `QNED81B vs QN70H`, `QNED81B vs M80H`, `QNED72B vs M70H`
      - UHD 4K: `NU85 vs U8070H`
    * **Retailer Toolbar Ordering**: Retailer buttons in `eu_price_dashboard_template.html` and `generate_eu_dashboard.py` MUST be ordered as: `UK (Currys) ➔ DE (MediaMarkt) ➔ FR (Fnac Darty) ➔ ES (MediaMarkt) ➔ IT (MediaWorld) ➔ NL (MediaMarkt) ➔ AT (MediaMarkt) ➔ CH (MediaMarkt) ➔ CZ (Alza) ➔ GR (Public) ➔ HU (MediaMarkt)`.
    * **History Folder Auto-Mirroring**: `sync_eu_retailers.py` MUST automatically mirror/copy the updated `price tracker_EU_2026 {MMDD}_v1.xlsx` workbook (containing all 16 country sheets) into `History_EU/{YYYY MMDD}/price tracker_EU_{YYYY MMDD}_v1.xlsx`.
  * **Greece (Public.gr) Multi-Query Expanded Pipeline**:
    - **Multi-Query Targeted Sampling Strategy**: Public.gr search queries cap results at 36 products per page. Scrapers MUST traverse 59 multi-query targeted configurations (22 for Samsung including `samsung tv`, `samsung oled`, `samsung qled`, `samsung neo qled`, `samsung tv 55..85`, `the frame`, etc., and 37 for LG including `lg tv`, `lg oled`, `lg qned`, `lg oled c6/g6/b6/c5/g5`, `lg qned 93/87/86/80/72`, `lg nano`, `lg mrgb`, `lg tv 55..83`, etc.) to achieve full catalog coverage (149+ unique models: 92 Samsung, 57 LG).
    - **Digit-Aware Pattern Matching**: LG series codes must use digit-aware matchers (`G6[0-9]`, `C6[0-9]`, `B6[0-9]`, `G5[0-9]`, `C5[0-9]`, `B5[0-9]`) and aliases (`QNED83B` $\rightarrow$ `QNED81B`, `QNED82A` $\rightarrow$ `QNED80A`, `QNED71B` $\rightarrow$ `QNED70B`) to prevent word-boundary mismatches on Greek title formats.
    - **Screen Size Price Guard**: Discount badge false positives (e.g. `600,00 €` badge on 83" C6) MUST be rejected by enforcing minimum selling price thresholds based on screen size (70"+ $\ge$ €700, 55"+ $\ge$ €350, 48"+ $\ge$ €250).
    - **Script Location**: Maintain primary scraper logic in `scripts/scrape_public_gr.py`.
  * **Czech Republic (Alza.cz) Full-Catalog Multi-Page Pipeline**:
    - **Pagination & Multi-URL Coverage**: Alza.cz caps items per page to 24. Scrapers MUST traverse 12 full pages (`range(1, 13)`) per brand (`televize-samsung/18862344-p1.htm` .. `-p12.htm` & `televize-lg/18862345-p1.htm` .. `-p12.htm`) AND include direct base category URLs (`18862344.htm` / `18862345.htm`) and search query URLs (`search.htm?exps=samsung+tv`) to bypass 307/302 redirect losses on page 1 and achieve 100%+ sample coverage (~126 Samsung models, 185+ LG models, 314+ total).
    - **Condition Filtering (Nové)**: Filter strictly for `Condition = NEW` (`Nové`), discarding unboxed (`Rozbaleno`), refurbished (`Zánovní`), or used (`Použité`) items.
    - **Currency & Unit Formatting**: Selling and original prices must be written in CZK (`#,##0` format).
    - **DOM Element Precision Price Extraction (Critical)**: NEVER use broad regex matching (`re.findall`) on full container text for Alza product cards. Promotional descriptions (e.g. `<span class="coupon-block__label--description">` containing `"cashbackem až 100 000 Kč"`) appear before the price tags in DOM order and cause `100,000` to overwrite the real TV selling price. Selling prices MUST be extracted strictly from DOM elements `.js-price-box__primary-price__value`, `.ads-pb__price-value`, or `.price-box__primary-price`. Cashback net prices MUST be extracted strictly from `.coupon-block--cashback .coupon-block__price`, and cashback amount calculated as `selling_price - cashback_net_price`.
    - **Script Location**: Maintain primary scraper logic in `scripts/scrape_alza.py`.
  * **Hungary (MediaMarkt HU) Deep Scraping & Master Pair Pipeline**:
    - **Apollo State Serialization & Cloudflare Bypass**: `mediamarkt.hu` protects listing pages with Cloudflare Turnstile. Scrapers MUST use `scrapling.fetchers.StealthyFetcher` (with `wait=2500` and `timeout=35000`) to solve Turnstile and extract the serialized GraphQL state from `window.__PRELOADED_STATE__` (`apolloState`, `GraphqlProduct`, `CofrPriceFeature`). This extracts 100% of marketplace/direct items, selling prices, and strike-through prices across 240+ models.
    - **Samsung Country Suffix `XXH` Guard & Year Classification**: Samsung Hungarian/Eastern European model codes end in country suffix `XXH` (e.g. `QE85QN80FAUXXH`, `QE98Q7FAAUXXH`, `UE85U8072FUXXH`). Parsers MUST strip `XXH`/`XXC` before testing year letters, and match series-adjacent letters: `H` $\rightarrow$ `2026`, `F` $\rightarrow$ `2025`, `D`/`E` $\rightarrow$ `2024` to prevent 2025 models from being falsely classified as 2026.
    - **Samsung Micro RGB (`MRE`) & LG `MRGB` Parsing**:
      - Samsung Micro RGB series use `MRE` model prefixes (e.g. `MRE85R95HATXXH`, `MRE85R85HAUXXH`, `MRE75...`, `MRE65...`, `MRE55...`). Parsers must map `MRE` to brand `SAMSUNG`, series `Micro RGB {R95H/R85H/R86H}`, category `MRGB`, and year `2026`.
      - LG MRGB models (e.g. `86MRGB87B3B`, `55MRGB87B3B`) must extract leading digits (`86`, `55`) as screen size (inch) rather than treating the series number `87` as screen size.
    - **Hungary Pairs Standard (`PAIRS_CONFIG_2026_HU`)**:
      - OLED: `G6 vs S99H`, `G6 vs S95H`, `C6 vs S90H`, `B6 vs S85H`
      - MRGB: `MRGB95B vs R95H`, `MRGB87B vs R85H`
      - QNED/QLED: `QNED93B/92B vs QN80H`, `QNED87B vs QN80H`, `QNED80B vs M80H`, `QNED70B vs M74H`
      - UHD 4K: `NU8E vs U8000H/U8072H`
    - **Currency Formatting**: Prices written in Hungarian Forint (`HUF`, `Ft ` format).
  * **UK (Currys UK) Deep Scraping & 1:1 Matching Pipeline**:
    - **DOM-Based Precision Price Extraction (Critical)**:
      - Currys TV cards render selling prices and installment text across separate DOM child nodes with line breaks (e.g. `'£3,699.00\nFrom\n£149.91\nper month'`). Never rely solely on text lookahead regexes.
      - Selling prices MUST be extracted strictly from `.price-info .sales .value, .sales .value` (via `content` attribute or text), direct savings from `.primary-save-price`, and previous regular prices from `.price-date` (`Was £...`).
      - All monthly financing mentions (`From £... a month`, `per month`) and promotional credit mentions (`Buy now pay within 12 months`) MUST be excluded from selling price matching.
    - **LG G-Series Mounting Type Protection & Accessory Filter Standard**:
      - Currys UK lists LG G-series OLED TVs (48"~97") with bracket/mount descriptors: `(Wall Mount Version)` and `(Stand Version)` (e.g. `LG G6 65" OLED AI 4K HDR Smart TV 2026 (Wall Mount Version) - OLED65G64LW`, `... (Stand Version) - OLED55G66LS`).
      - Scrapers MUST NOT exclude `"WALL MOUNT"` or `"STAND"` if the product title contains `"VERSION"`, `"SMART TV"`, or display terms (`"OLED"`, `"QNED"`, `"QLED"`).
      - Strictly isolate and filter out only pure accessories (`WALL BRACKET`, `FLOOR STAND`, standalone `WALL MOUNT`/`STAND` without `VERSION`/`SMART TV`) and combo soundbar packages (`& ... Sound Bar Bundle`, `BUNDLE`).
    - **Samsung Micro RGB Screen Size (`85`) Regex Overmatching Guard**:
      - Samsung Micro RGB model codes follow `MRE` + `size(85/75/65/55)` + `series(R95H/R85H/R86H)`.
      - Loose regexes like `MRE.*85` MUST NEVER be used for R85 series, because the `85` matches the screen size of `MRE85R95H`, falsely matching R95 models (£4,999) as R85 (£3,299)!
      - Matchers MUST strictly require the letter `R` before series numbers: `re.search(r'(?:R95|MR95)', code)` for R95, and `re.search(r'(?:R86|R85)', code) and not re.search(r'(?:R95|MR95)', code)` for R85/R86.
    - **UK Pairs Standard (`PAIRS_CONFIG_2026_UK`)**:
      - OLED: `G6 vs S99H`, `G6 vs S95H`, `C6 vs S90H`, `B6 vs S85H`
      - MRGB: `86MRGB96 vs 85R95H` (LG £5,799 vs Samsung £4,999), `86MRGB88 vs 85R85H` (LG £2,699 vs Samsung £3,299), `75MRGB88 vs 75R85H` (LG £1,999 vs Samsung £2,499), `65MRGB88 vs 65R85H` (LG £1,399 vs Samsung £1,899), `55MRGB88 vs 55R85H` (LG £1,099 vs Samsung £1,199), `50MRGB88 vs 50R85H` (LG £899), `100MRGB96 vs 100R95H` (LG £12,999).
      - QNED/QLED: `QNED86B vs QN80H`, `QNED86B vs QN70H`, `QNED72B vs M70H`
      - UHD 4K: `NU85 vs U8000H`
    - **Screen Size Labeling Standard**: For 85"/86" pairs, render exact panel sizes on comparison labels: LG `86"` and Samsung `85"` (`86"MRGB88 vs. 85"R85H`).
    - **100" & 115" 3-Digit Screen Size Extraction & Blind Fallback Prohibition (Critical)**:
      Screen size regexes across all scrapers, parsers, and quality gates MUST include 3-digit sizes `115|100` (`r'\b(115|100|98|97|86|85|83|77|75|70|65|55|50|48|43|42|40|32|27|24)'`). Parsers must NEVER blindly default to 55; if title parsing fails, they must extract size from the model code (`QE100...` -> 100, `100QNED...` -> 100, `115QNED...` -> 115).
    - **85" / 86" Pairing Single-Size Specification & Deduplication Standard (Critical)**:
      In `PAIRS_CONFIG_*`, specify `"86"` (or `"85"`) only once in the `sizes` array for 85"/86" flagship pairs. Never include both `"86"` and `"85"` in the same `sizes` list, as `find_product()` cross-matches 85" and 86", which would cause identical duplicate bars on comparison charts. `build_paired_data()` MUST enforce a `seen_pair_labels` deduplication set as a fail-safe.
    - **Script Location**: Maintain primary logic in `scripts/scrape_currys_live.py`.

  * **Pan-European Master Product URL Registry (`data/master_product_urls.json`) Standard (Critical)**:
    - **Master Registry Persistence**: To prevent sample count degradation and URL dropouts caused by search engine pagination shifts or temporary out-of-stock delisting on retailer sites, maintain a consolidated Master URL Registry at `data/master_product_urls.json`.
    - **Registry Schema**: Store each model entry as:
      `{ "KEY": { "country": "HU", "retailer": "MediaMarkt", "brand": "SAMSUNG", "model_code": "MRE85R95HATXXH", "year": 2026, "size": 85, "title": "...", "url": "https://...", "last_updated": "YYYY-MM-DD" } }`.
    - **Merge & Probe Enforcement on Every Survey**: Every price collection run across the 11 active European countries (UK, DE, FR, ES, IT, NL, AT, CH, CZ, GR, HU) MUST automatically:
      1. Run search query traversals to collect active/promoted product cards.
      2. Cross-reference results with `data/master_product_urls.json` to identify any previously tracked models missing from the search results.
      3. Probe missing model URLs directly (Direct PDP Fetch) to extract live prices and update the database, guaranteeing 100% sample retention across consecutive survey rounds.
      4. Auto-register any newly launched models into `data/master_product_urls.json`.
    - **Builder Script**: Maintain registry sync in `scripts/build_master_url_registry.py`.

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
    * **Samsung UHD 4K**: `U8000F` and `U8000H` series matchers MUST support all country and retailer suffix variants (`U8000`, `U8005`, `U8010`, `U8070`, `U8075`, `U8079`, `U8080`, `U8090`, `DU8000`) to ensure 100% coverage across Germany MediaMarkt (`GU43U8079H`, `GU50U8079H`, `GU55U8079H`, `GU65U8079H`, `GU75U8079H`, `GU85U8079H`), France Fnac (`TU43U8005F`, `TU55U8005F`, `TU65U8005F`, `TU43U8005H`, `TU50U8005H`, `TU55U8005H`, `TU65U8005H`, `TU85U8005H`), and MediaMarkt ES (`U8075`). **CRITICAL**: U8000 matchers MUST NEVER include `U7000`, `M70`, `M73`, `M80`, or `U80` keywords — these belong to separate LED/budget series and will cause cross-series price contamination (see §5 Strict Series Matcher Boundaries).
    * **LG UHD 4K**: `UA75` (2025) and `NU85` (2026) series matchers MUST support all country variants (`UA75`, `UA73`, `UA77`, `NU85`, `NU80`, `NU75`, `NU90`, `UT`, `UR`, `UQ`).
  * **Dynamic Empty Slot Hiding Rule (Dashboard)**:
    * Any size pair slot where at least one brand has a valid price (`lgP > 0 || samP > 0`) MUST be rendered on the chart so that single-brand offerings (e.g. LG OLED G6/C6/B6 lineup when competitor 2026 models are not yet listed) remain 100% visible. Only empty slots where BOTH brands have 0 (`lgP === 0 && samP === 0`) are filtered out to keep charts clean.
  * **Greek Model Code Prefix Normalization Standard (Public.gr)**:
    * Due to Greek title delimiter nuances, upstream card extraction can strip leading prefix letters (`QNED` -> `ED`, `MRGB` -> `GB`, `NANO` -> `NO`, `100QNED` -> `00QNED`).
    * `extract_products_from_sheet` MUST apply code normalization: `clean_code.startswith("ED")` -> `QN` + `clean_code`, `clean_code.startswith("GB")` -> `MR` + `clean_code`, `clean_code.startswith("NO")` -> `NA` + `clean_code`, and `clean_code.startswith("00QNED")` -> `1` + `clean_code`. This standard recovers 19 previously unmatched pairs in Greece alone, elevating Greece coverage to 44 matched pairs (98%).
  * **Phase 2 European 1:1 Lineup Alignment Standards (AT, CH, CZ, GR, HU)**:
    * Eliminate artificial one-sided phantom gaps by tailoring `PAIRS_CONFIG_2026_*` to each country's genuine retail assortment:
      * **CH**: Unify flagship OLED to `S99H` (`G6 vs S99H`), eliminating uncarried `S95H` -> 24 pairs 100% matched.
      * **CZ**: Align 55"/50" to `QNED85B vs QN70H`, eliminating uncarried 55"/50" QNED86B/QNED80B -> 40 pairs 100% matched.
      * **AT**: Map `NANO80/81` into UHD 4K (`NU800` vs `U8070H`), pair `QNED71B` with `M72H/M82H/QN70H` -> 22 pairs 100% matched.
      * **HU**: Pair `QNED87B vs QN80H` and `QNED70B vs M74H`, separate uncarried MRGB -> 38 pairs 100% matched.
      * **GR**: Align OLED, MRGB, QNED87B/81B/72B, NU85 -> 44 pairs 98% matched.
    * Total European 1:1 comparison pairs across all 11 countries: **337 matched pairs** (169 Western EU + UK, 168 Phase 2 EU).

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
* **Survey Count Discrepancy Verification**: Immediately after scraping is completed across European major retailers (UK, DE, FR, ES, IT, NL, AT, HU, CZ, GR) and Swiss retailers (MediaMarkt CH, Interdiscount, Digitec), the automation pipeline MUST compare today's extracted model counts per country/brand against baseline counts from the previous survey cycle.
* **Strict 10% Discrepancy Threshold & Cause Investigation**:
  * If the extracted model count for any country or brand (e.g. MediaMarkt DE Samsung, Fnac FR LG, Digitec Samsung) differs or drops by **10% or more (> 10%)** compared to the baseline, the pipeline MUST immediately flag the discrepancy.
  * **Cause Diagnosis**: Automatically inspect logs to diagnose the exact root cause: (1) Cloudflare Turnstile / Captcha block or timeout, (2) Retailer backend search indexing omissions (e.g. omitted clearance models like S90F), (3) Pagination truncation, or (4) DOM selector changes.
* **Targeted Retry Strategy & Additional Survey Execution**:
  * **Scale Wait Times**: Re-run the target scraper with `TIMEOUT_MULTIPLIER` scaled to `1.5` ~ `2.0`.
  * **Query Splitting**: If generic brand query URL missed models, loop through targeted series-specific search configurations (e.g. S90/S95/C6/G6 individual queries) to guarantee 100% model coverage.
  * **Retry Limit**: Execute up to **3 retries (Max Retries = 3)** until the model count gap is brought under 10%.
* **Unified Pipeline Orchestration**: Use master orchestration scripts (`python scripts/run_survey_with_check.py`, `python EU-price-tracker/scripts/run_eu_survey.py`) to automate this complete sequence (scrape validation -> 10% gap diagnosis -> targeted additional survey -> excel sync -> history archive -> dashboard compile -> Firebase deploy).

## 7. Weekly Price/Promotion Variation Analysis & ISO Week Standards
* **Weekly Variation Analysis Scope ('26년 모델 Only)**:
  * The **주간 가격/프로모션 변동 사항** (Weekly Price & Promotion Changes) tab in both the Swiss and Pan-European dashboards MUST strictly scope analysis to **2026 Model Year generation (`yr == 2026`)** to focus executive review on current-generation line-up dynamics.
  * Tab sub-title and badges MUST explicitly state: `'26년 모델 Only` (e.g., `스위스 3대 유통 주간 변동 요약('26년 모델 Only)`, `11개국 주간 변동 요약('26년 모델 Only)`).
* **Week-over-Week Transition Comparison Rule**:
  * The analysis compares the current survey date against the previous week's latest survey date:
    - **W34**: `W34(08.17) vs W33(08.14)` (comparing today's survey against previous week's survey).
    - **W33**: `W33(08.14) vs W32(08.06)`
    - **W32**: `W32(08.06) vs W31(07.28)`
    - **W31**: `W31(07.28) vs W30(07.25/07.26)`
  * On every new survey execution (e.g. W35, W36), the latest week transition MUST be appended and set as the default active tab.
* **5 Standardized Change Types**:
  1. **`PRICE_DROP` (가격 인하)**: Selling price decreased ($P_{curr} < P_{prev}$).
  2. **`PRICE_HIKE` (가격 인상)**: Selling price increased ($P_{curr} > P_{prev}$).
  3. **`PROMO` (프로모션 변동)**: Promotional text/badge or cashback value changed while base price remained unchanged.
  4. **`NEW_MODEL` (신규 진입)**: Model was not present in the previous survey week but is newly listed in the current week.
  5. **`BENCHMARK` (1:1 매칭 모델)**: Models that belong to official 1:1 competitor lineup comparison pairs.
* **ISO Calendar Week Formatting**:
  * Survey dates and dashboard badges MUST be calculated using standard ISO calendar week: `week_no = dt.isocalendar()[1]` (e.g., `2026년 08월 17일 (W34)`, `Live Scraped Data (2026.08.17(W34))`, `W34(08.17)`). Never use hardcoded day-range conditions that break on future survey weeks.
* **UI Cleanliness Standard**:
  * The Weekly Variation view MUST NOT include redundant filters (such as `price type` or `model year`) or generic total sum cards. It MUST feature direct country/retailer summary pills and filterable change tables with delta indicators (`-CHF 100 (-5.0%)`, `+€50 (+2.5%)`).

## 8. Escalation Procedure After Retry Exhaustion
* **3-Strike Escalation Rule**: If the 3-retry limit (§6) is exhausted and a country/brand's model count gap still exceeds 10%, apply the following escalation procedure:
  1. **Partial Data Continuation**: Proceed with Excel sync and dashboard compilation using all successfully collected countries. For the failed country, retain the previous survey cycle's data and label it with a `[이전주 데이터]` badge in the dashboard.
  2. **User Notification**: Log a structured summary in the agent conversation output specifying: (a) failed country/brand, (b) root cause diagnosis, (c) number of retries attempted, (d) recommended manual action.
  3. **WAF/DOM Change Detection Protocol**:
     - **CSS Selector Failure**: If product card selectors return zero results but the page HTML loads successfully, automatically attempt DOM-Climbing fallback parser and log the selector mismatch.
     - **WAF Engine Switch**: If Cloudflare Turnstile solve fails 3 consecutive times, flag for potential WAF engine change (e.g. Cloudflare → DataDome, Akamai) and recommend switching scraper engine (StealthySession → Firecrawl, or vice versa).
     - **48-Hour Resolution Window**: If a scraper remains broken for 48+ hours across 2 survey cycles, flag the script as `NEEDS_MANUAL_FIX` and disable automatic retries for that country until the script is updated.

## 9. Scraping Execution Logging Standard
* **Structured JSON Output (Mandatory)**: All scraping and sync scripts (`scrape_mediamarkt.py`, `scrape_alza.py`, `scrape_public_gr.py`, `scrape_and_sync_hungary.py`, `sync_eu_retailers.py`, `sync_all_retailers.py`) MUST output a structured JSON summary at script termination:
  ```json
  {
    "country": "HU",
    "retailer": "MediaMarkt",
    "brand": "SAMSUNG",
    "total_extracted": 145,
    "after_year_filter": 98,
    "after_category_filter": 92,
    "final_deduplicated": 87,
    "waf_blocks": 0,
    "parse_errors": 2,
    "execution_time_sec": 42.5,
    "timestamp": "2026-09-01T17:30:00+09:00"
  }
  ```
* **Log Persistence**: Summary JSON logs SHOULD be appended to `data/scraping_logs.jsonl` (one line per execution) to enable historical performance tracking and automated regression detection.
* **Console Progress Indicators**: Long-running scripts (>30 seconds) MUST print progress indicators showing page N/M completion and current model count accumulation.

## 10. Price Anomaly Detection & Data Quality Gates
* **`price_history.db` Schema & Purpose**: The SQLite database at `data/price_history.db` serves as the persistent time-series price store. It MUST be documented with table schemas, indexed by `(country, retailer, brand, model_code, survey_date)`.
* **Automated Anomaly Detection Rules (Post-Sync Validation)**:
  1. **±30% Price Spike/Drop Guard**: If any model's selling price changes by ±30% or more compared to the previous survey, flag it as a potential parsing error and log it for manual review before dashboard publication. Exception: models transitioning from/to promotional pricing are exempt if accompanied by a promo text change.
  2. **Cross-Country Outlier Detection**: If the same model code (e.g. `QE65S90H`) shows a price in one country that is 2× or more the median price across all countries (after currency conversion), flag it as a potential currency parsing or unit conversion error.
  3. **Consecutive Zero-Price Alert**: If the same model has a `0` or `null` price in 2 consecutive survey rounds, trigger a URL validity re-check against the Master Registry and attempt a Direct PDP Probe.
  4. **Minimum Price Floor Enforcement (by Screen Size)**:
     - 70"+ TVs: price ≥ €700 (or local currency equivalent)
     - 55"+ TVs: price ≥ €250
     - Any TV: price ≥ €50
     - Violations are flagged as discount badge false positives or parsing errors.

## 12. Australia (AU) TV Price Tracker & Big 3 Retailers Standard
* **Scope & Retailers**:
  - **JB Hi-Fi** (`jbhifi.com.au`): Australia's #1 consumer electronics retailer.
  - **The Good Guys** (`thegoodguys.com.au`): Major home appliance and TV retailer (Shopify Plus / Next.js).
  - **Harvey Norman** (`harveynorman.com.au`): Leading department / electronics superstore franchise.
* **Currency & Pricing Standards**:
  - Currency: **AUD (Australian Dollar, A$, symbol `$`)**.
  - Discount Stripping Guard: Must pre-strip promotional discount badges (e.g. `SAVE $1001`, `$1000OFF^`) before regex price matching to ensure the real selling price is never overwritten by discount values.
* **Model Code Naming Standards for Australia**:
  - **Samsung**: Uses prefix `QA` (e.g. `QA65S90FAWXXY`, `QA65R85H`, `QA55M70H`, `QA77S95H`) and suffix `XXY`.
  - **LG**: Uses suffix `PSA`, `PSB`, `AU`, `AN`, `TSA` (e.g. `OLED65C6PSA`, `OLED55G6PSB`, `OLED55B6PSA`, `55QNED70BPSA`, `65QNED86TSA`).
* **Targeted Multi-Category Collection Architecture (Credit-Optimized)**:
  - Never scrape single generic landing pages. Scrapers MUST traverse brand-specific TV collection categories across all 3 retailers:
    1. **JB Hi-Fi**: `/collections/tvs/samsung-tvs` (Samsung) and `/collections/tvs/lg-tvs` (LG).
    2. **The Good Guys**: `/samsung/televisions` (Samsung) and `/lg/televisions` (LG).
    3. **Harvey Norman**: `/tv-blu-ray-home-theatre/tvs-by-brand/samsung-tvs` (Samsung) and `/tv-blu-ray-home-theatre/tvs-by-brand/lg-tvs` (LG).
  - This 6-URL targeted collection yields 200~300+ unique TV models across all screen sizes and display categories while minimizing third-party crawling credits.
* **Australian Master Product URL Registry (`data/master_product_urls_au.json`)**:
  - All verified AU models and PDP URLs are permanently registered in `data/master_product_urls_au.json` (separated from European registry).
  - Newly discovered models on each survey run are auto-registered, preventing sample drop and ensuring continuous historical continuity.
* **Storage & Deliverable Paths**:
  - Raw JSON datasets: `data/raw_jbhifi_{samsung|lg}.json`, `data/raw_goodguys_{samsung|lg}.json`, `data/raw_harveynorman_{samsung|lg}.json`.
  - Excel workbook: `data/price tracker_AU_2026 {MMDD}_v1.xlsx` (8 sheets: `Summary_2026`, `Summary_2025`, and 6 retailer sheets).
  - History directory: `History_AU/{YYYY MMDD}/price tracker_AU_{YYYY MMDD}_v1.xlsx`.
  - Dashboard & Hosting: `data/au_price_dashboard.html`, `public_au/index.html`, and Firebase Hosting URL: `https://au-price-tracker-lge.web.app`.

## 13. 차세대 확장형 멀티 에이전트 아키텍처 & Data Intelligence Engine 표준
* **설정 기반 플러그인 레지스트리 (`config/regions/`)**:
  - 권역별 설정(`dach.json`, `western_eu.json`, `eastern_eu.json`) 및 신규 권역 템플릿(`region_template.json`) 구축.
  - 신규 국가/유통 추가 시 소스코드 수정 없이 JSON 선언만으로 국가, 유통사, 환율, 1:1 라인업 매칭 규칙이 `scripts/core/region_manager.py`에 의해 동적 로드됨.
* **데이터 관리·분석 전담 에이전트 (Data Intelligence Agent)**:
  - 총괄 에이전트 산하에서 유럽 11개국 및 전 세계 수집 데이터를 전수 분석하는 두뇌 엔진 (`scripts/data_intelligence_engine.py`, 규약 명세: `.agents/subagents/data_intelligence_agent.md`).
  - **1:1 핵심 라인업 가격 갭 매트릭스**: OLED (G6 vs S95H, C6 vs S90H, B6 vs S85H), Micro RGB (MRGB vs R85H/R95H), QNED/QLED 1:1 매칭, EUR 환산 가격차, Gap %, 경쟁 우위(`LG Advantage` / `Parity` / `LG Premium`) 자동 판정.
  - **시계열 DoD / WoW 트렌드 추적**: 전주/전일 대비 Top 10 가격 인하/인상 모델 추출.
  - **프로모션 공세 강도 스캐너**: 브랜드별 프로모션 적용률 및 전술별(캐시백, 번들, 즉시할인/바우처) 분포 분석.
  - **산출물 자동 생성**: C-Level 경영 브리핑 마크다운 리포트 (`data/reports/Executive_Price_Briefing_{YYYYMMDD}.md`) 및 대시보드 주입용 구조화 데이터 (`data/executive_summary_data.json`).
* **통합 마스터 오케스트레이터 (`scripts/orchestrator.py`)**:
  - 단일 CLI 인터페이스로 권역별 수집 동기화(`--sync`), SQLite DB 적재(`--db-sync`), 인텔리전스 분석(`--analyze-only`), 웹 대시보드 컴파일(`--dashboard`), Firebase 호스팅 배포(`--deploy`), 전체 실행(`--full`) 지원.
* **독립형 웹 대시보드 `📊 AI 경영 브리핑` 탑재**:
  - `data/eu_price_dashboard_template.html` 및 `scripts/generate_eu_dashboard.py` 연동.
  - 대시보드 기본 랜딩 화면으로 4대 핵심 KPI 카드, 전략 시사점 불릿, 1:1 라인업 가격 갭 필터 테이블, 주요 가격 인하 모델, 프로모션 공세 현황 시각화 및 리포트(MD) 다운로드 기능 제공.



