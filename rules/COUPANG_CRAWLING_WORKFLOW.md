# Coupang Crawling Workflow

## Purpose
이 문서는 이 프로젝트에서 쿠팡 리뷰를 수집할 때 사용할 표준 방식을 고정한다.

현재 결론은 아래와 같다.
- 직접 HTTP 요청: `403` 또는 차단 페이지로 실패
- 독립 Playwright/Docker 접속: `Access Denied` 페이지로 실패 가능성 높음
- 로그인된 실제 크롬 세션에 CDP로 연결: 현재 가장 안정적

따라서 앞으로 쿠팡 크롤링은 기본적으로
`로그인된 원격 디버깅 크롬 탭 -> HTML 저장 -> 파싱 -> raw_reviews.csv 생성`
흐름으로 진행한다.

## Standard Flow
1. Windows에서 크롬을 원격 디버깅 모드로 실행한다.
2. 그 크롬에서 쿠팡 로그인 상태를 만든다.
3. 수집할 상품 페이지를 탭으로 연다.
4. Codex/WSL에서 CDP로 해당 탭에 연결해 HTML을 저장한다.
5. 저장된 HTML을 `src.collect_reviews`로 파싱한다.
6. 결과를 `data/raw/raw_reviews.csv`로 만든다.

## Why This Is The Default
- 실제 사용자 세션을 그대로 재사용할 수 있다.
- 쿠팡 차단 페이지 대신 실제 렌더링된 DOM을 받을 가능성이 높다.
- 리뷰 영역이 브라우저에서 이미 열린 상태이므로 동적 로딩에 대응하기 쉽다.
- 수집과 파싱을 분리할 수 있어 디버깅이 쉽다.

## Required Browser Launch
Windows에서 아래처럼 크롬을 실행한다.

```bat
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chrome-cdp-review"
```

중요:
- 기존 크롬이 아니라 새 프로필 창으로 띄우는 것이 안전하다.
- 이 창에서 쿠팡 로그인과 상품 페이지 열기를 해야 한다.

## Current Scripts
- [fetch_coupang_from_cdp.js](/home/jammy/projects/review-authenticity-ai/scripts/fetch_coupang_from_cdp.js)
  - 이미 열려 있는 쿠팡 상품 탭 하나에 붙어서 DOM을 저장한다.
- [fetch_coupang_pages_from_cdp.js](/home/jammy/projects/review-authenticity-ai/scripts/fetch_coupang_pages_from_cdp.js)
  - 리뷰 페이지를 자동으로 넘기면서 각 페이지 HTML을 저장한다.
- [fetch_coupang_urls_from_cdp.js](/home/jammy/projects/review-authenticity-ai/scripts/fetch_coupang_urls_from_cdp.js)
  - URL 목록을 순회하면서 상품별 멀티페이지 HTML 수집을 실행한다.
- [merge_coupang_raw.py](/home/jammy/projects/review-authenticity-ai/scripts/merge_coupang_raw.py)
  - 수집된 HTML 묶음을 기존 `data/raw/raw_reviews.csv`에 누적 병합한다.
- [collect_reviews.py](/home/jammy/projects/review-authenticity-ai/src/collect_reviews.py)
  - 저장된 HTML 파일을 파싱해서 raw CSV를 만든다.

## Single-Page Collection Example
1. 크롬 원격 디버깅 창에서 쿠팡 상품 페이지를 연다.
2. 아래처럼 HTML을 저장한다.

```bash
PATH=/home/jammy/.nvm/versions/node/v22.22.0/bin:$PATH \
node scripts/fetch_coupang_from_cdp.js \
  'https://www.coupang.com/vp/products/8926187693?itemId=26089853240&vendorItemId=93070652313&sourceType=cmgoms&subSourceType=cmgoms&omsPageId=165341&omsPageUrl=165341' \
  'data/raw/coupang_saved_html/coupang_8926187693_cdp.html'
```

3. 저장된 HTML을 파싱한다.

```bash
python3 -m src.collect_reviews \
  --platform coupang \
  --html-file data/raw/coupang_saved_html/coupang_8926187693_cdp.html \
  --output data/raw/raw_reviews.csv
```

## Multi-Page Collection Example
리뷰 페이지가 여러 장이면 아래 스크립트를 우선 사용한다.

```bash
PATH=/home/jammy/.nvm/versions/node/v22.22.0/bin:$PATH \
node scripts/fetch_coupang_pages_from_cdp.js \
  'https://www.coupang.com/vp/products/8926187693?itemId=26089853240&vendorItemId=93070652313&sourceType=cmgoms&subSourceType=cmgoms&omsPageId=165341&omsPageUrl=165341' \
  'data/raw/coupang_saved_html'
```

위 스크립트는 아래처럼 페이지별 HTML을 저장한다.
- `coupang_<product_id>_cdp_page_001.html`
- `coupang_<product_id>_cdp_page_002.html`
- `coupang_<product_id>_cdp_page_003.html`

그 다음 배치 파싱:

```bash
python3 -m src.collect_reviews \
  --platform coupang \
  --html-dir data/raw/coupang_saved_html \
  --html-glob 'coupang_8926187693_cdp_page_*.html' \
  --output data/raw/raw_reviews.csv
```

필요하면 마지막 인자로 최대 페이지 수를 줄 수 있다.

```bash
PATH=/home/jammy/.nvm/versions/node/v22.22.0/bin:$PATH \
node scripts/fetch_coupang_pages_from_cdp.js \
  '<product_url>' \
  'data/raw/coupang_saved_html' \
  'http://127.0.0.1:9222' \
  3
```

## Multi-Product Collection Example
여러 상품을 한 번에 수집할 때는 URL 파일을 사용한다.

```bash
PATH=/home/jammy/.nvm/versions/node/v22.22.0/bin:$PATH \
node scripts/fetch_coupang_urls_from_cdp.js \
  'data/raw/coupang_seed_urls.txt' \
  'data/raw/coupang_saved_html' \
  'http://127.0.0.1:9222' \
  10
```

그 다음 저장된 HTML 전체를 기존 raw CSV에 누적 병합한다.

```bash
python3 scripts/merge_coupang_raw.py \
  --html-dir data/raw/coupang_saved_html \
  --html-glob 'coupang_*_cdp_page_*.html' \
  --output data/raw/raw_reviews.csv
```

## Operational Rules
- Docker Playwright 직접 접속 결과가 `Access Denied`면 기본 경로로 돌아간다.
- `document.cookie`로 추출한 쿠키만으로 해결하려고 오래 끌지 않는다.
- 실제 HTML이 확보되면 파싱 로직 수정은 저장 HTML 기준으로 진행한다.
- 원본 HTML은 가능하면 `data/raw/coupang_saved_html/`에 보존한다.
- root 소유 파일이 생기면 덮어쓰기 대신 새 파일명 저장을 우선한다.
- 멀티페이지 수집이 가능하면 단일 페이지 저장보다 `fetch_coupang_pages_from_cdp.js`를 우선한다.
- 여러 상품을 누적할 때는 `merge_coupang_raw.py`로 기존 raw CSV에 append+dedupe 한다.
- 상품명/옵션/수량만 반복된 비리뷰 문장은 제거한다.

## What To Check After Collection
- HTML 제목이 `Access Denied`가 아닌가
- HTML 길이가 비정상적으로 짧지 않은가
- 저장본 안에 `상품 리뷰`, `상품평`, `data-review-id` 같은 문자열이 있는가
- 파서가 최소 몇 건의 리뷰를 추출하는가

## Non-Default Paths
아래 방식은 보조 수단이다.
- Docker Playwright 직접 수집
- 쿠키 JSON 주입
- 수동 DevTools Console 저장

이 방법들은 필요하면 쓸 수 있지만,
현재 프로젝트의 기본 운영 방식은 `CDP 연결 방식`이다.
