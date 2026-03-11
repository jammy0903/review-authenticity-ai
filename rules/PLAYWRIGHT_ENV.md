# Playwright Environment

## Why This Exists
현재 Codex 실행 환경은 `Ubuntu Core 24`라서 `apt` 기반 시스템 라이브러리 설치가 안 된다.
그래서 쿠팡 브라우저 자동화를 여기서 직접 돌리기 어렵다.

다만 이 문서의 Docker 방식은 보조 경로다.
쿠팡 기본 수집 방식은 [COUPANG_CRAWLING_WORKFLOW.md](/home/jammy/projects/review-authenticity-ai/rules/COUPANG_CRAWLING_WORKFLOW.md)의
`CDP 연결 방식`을 우선한다.

이 문서는 일반 `Docker` 또는 일반 `Ubuntu/WSL` 환경에서
Playwright를 실행하기 위한 최소 구성을 설명한다.

## Files
- [package.json](/home/jammy/projects/review-authenticity-ai/package.json)
- [playwright.Dockerfile](/home/jammy/projects/review-authenticity-ai/docker/playwright.Dockerfile)
- [fetch_coupang_urls_playwright.js](/home/jammy/projects/review-authenticity-ai/scripts/fetch_coupang_urls_playwright.js)
- [run_coupang_playwright_docker.sh](/home/jammy/projects/review-authenticity-ai/scripts/run_coupang_playwright_docker.sh)

## Docker Workflow
아래 명령은 쿠팡 URL 목록 파일을 읽어서 상품 페이지 HTML을 저장한다.

```bash
bash scripts/run_coupang_playwright_docker.sh
```

기본 입력:
- `data/raw/coupang_seed_urls.txt`

기본 출력:
- `data/raw/coupang_saved_html/coupang_<product_id>.html`

## With Session Files
쿠팡이 차단 페이지를 주면 세션 파일을 같이 넣어본다.

```bash
bash scripts/run_coupang_playwright_docker.sh \
  data/raw/coupang_seed_urls.txt \
  data/raw/coupang_saved_html \
  data/raw/cookies/coupang_cookies.json \
  data/raw/cookies/coupang_storage_state.json
```

둘 중 하나만 있어도 된다.
- `coupang_cookies.json`: Playwright `context.addCookies()` 형식의 배열
- `coupang_storage_state.json`: Playwright `storageState` 형식

## After HTML Collection
HTML 저장이 끝나면 아래 명령으로 raw CSV를 만든다.

```bash
python3 -m src.collect_reviews --platform coupang --html-dir data/raw/coupang_saved_html --output data/raw/raw_reviews.csv
```

## Important Limitation
쿠팡이 로그인, 봇 차단, 동적 로딩 정책을 바꾸면
Playwright 성공 여부가 달라질 수 있다.
그래서 HTML 저장 성공 여부와 저장된 HTML 안의 리뷰 텍스트 존재를 항상 같이 확인해야 한다.

특히 Docker Playwright 직접 접속은 `Access Denied`가 자주 발생할 수 있다.
