# KakaoMap Review Collection Plan

## Why Switch
쿠팡 상품 리뷰는 현재 데이터 특성상 `promotion` 쪽 비율이 지나치게 높다.

그래서 다음 수집원은 아래 조건을 더 잘 만족해야 한다.

- 실제 사용 경험이 드러나는 리뷰 비율이 높을 것
- 웹에서 접근 가능할 것
- 장소/매장 중심이라 음식, 서비스, 분위기, 가격, 재방문 의사 같은 정보가 들어갈 가능성이 높을 것

카카오맵 리뷰는 이 조건에 비교적 잘 맞는다.

## Goal
카카오맵 장소 리뷰를 수집해서 아래 목적에 맞는 raw/labeled 데이터셋을 만든다.

- `genuine` vs `promotion` 분류
- 음식/매장 경험 중심 한국어 리뷰 확보
- 쿠팡 대비 더 다양한 실제 경험 문장 확보

## Collection Strategy
카카오맵 리뷰 수집은 아래 2단계로 나눈다.

1. 장소 URL 또는 장소 ID 수집
2. 각 장소 페이지에서 리뷰 텍스트와 메타데이터 수집

## Input Unit
초기 입력 단위는 `장소 URL 목록`으로 잡는 것이 가장 현실적이다.

이유:
- 장소 ID를 직접 찾는 단계보다 단순하다.
- 사람이 수집 대상을 검토하기 쉽다.
- 지역/카테고리별로 seed를 관리하기 쉽다.

추천 seed 파일:
- `data/raw/kakaomap_place_urls.txt`

각 줄 예시:
- `https://place.map.kakao.com/123456789`

## What To Collect
리뷰 단위로 아래 정보를 저장한다.

### Required Columns
- `review_id`
- `platform`
- `place_id`
- `place_name`
- `review_text_raw`
- `rating`
- `collected_at`
- `source_note`

### Optional Columns
- `reviewer_name`
- `review_date`
- `has_photo`
- `visit_count_raw`
- `menu_context`
- `place_url`

## Output Files
### Raw
- `data/raw/kakaomap_reviews_raw.csv`

### Blank labeling file
- `data/labeled/kakaomap_reviews_blank.csv`

### Final labeled file
- `data/labeled/kakaomap_reviews_labeled.csv`

## Browser Automation Plan
카카오맵은 정적 HTML 파싱보다 브라우저 자동화가 더 현실적이다.

권장 도구:
- Playwright 우선
- Selenium은 대안

이유:
- 동적 렌더링 대응이 편하다.
- iframe/탭 전환/더보기 클릭 자동화가 상대적으로 안정적이다.
- 기존 프로젝트도 브라우저 자동화 흐름과 잘 맞는다.

## Recommended Flow
1. seed 장소 URL 열기
2. 리뷰 탭 또는 리뷰 섹션 찾기
3. 리뷰가 로드될 때까지 대기
4. 더보기 버튼 반복 클릭
5. 현재 화면의 리뷰 카드들을 파싱
6. 텍스트/평점/날짜/사진 여부 추출
7. 중복 리뷰 제거
8. CSV append 또는 최종 저장

## Deduplication Rule
리뷰 중복 제거는 아래 우선순위로 한다.

1. `review_id`가 있으면 `review_id` 기준
2. 없으면 아래 조합 기준
- `place_id`
- `review_text_raw`
- `review_date`
- `reviewer_name`

## Stop Conditions
한 장소당 무한 수집하지 않도록 제한을 둔다.

권장 제한:
- 장소당 최대 리뷰 100~200개
- 더보기 클릭 최대 20회
- 새 리뷰 증가가 2회 연속 0이면 중단

## Quality Filter
수집 직후 아래 필터는 별도 컬럼으로 표시만 하고 바로 삭제하지 않는다.

- 텍스트 길이 0
- 텍스트 길이 5자 이하
- 이모지/감탄사 위주
- 메뉴/서비스 정보 없음

삭제보다 `후보 필터`로만 남겨야 나중에 라벨링 판단이 가능하다.

## Labeling Fit
카카오맵 리뷰는 아래 이유로 `genuine` 데이터 확보에 유리하다.

- 음식 맛, 양, 가격, 친절도, 대기시간, 분위기 언급이 많다.
- 실제 방문 경험 기반 표현이 자주 나온다.
- 재방문, 위치, 주차, 포장, 배달 등 구체 경험이 포함되기 쉽다.

## Risks
- DOM 구조 변경 가능성
- iframe 구조 가능성
- 무한스크롤 또는 더보기 버튼 구조 변경
- 로그인/차단/속도 제한
- 리뷰 탭 렌더 지연

## First Small Experiment
처음부터 대규모 수집하지 않는다.

1. 장소 5개만 seed로 준비
2. 장소당 최대 리뷰 30개 수집
3. raw CSV 확인
4. blank labeling CSV 생성
5. 라벨링 후 genuine/promotion 분포 확인

## Recommended Initial Categories
처음에는 아래처럼 범위를 좁게 잡는 것이 좋다.

- 카페
- 분식
- 치킨
- 디저트
- 한식

이유:
- 리뷰 스타일 비교가 쉽다.
- 장소 리뷰 문장 패턴을 빨리 파악할 수 있다.

## Recommended Next Files
이 설계 다음에 만들 파일은 아래 순서가 좋다.

1. `data/raw/kakaomap_place_urls.txt`
2. `scripts/fetch_kakaomap_reviews_playwright.js` 또는 `scripts/fetch_kakaomap_reviews.py`
3. `scripts/derive_kakaomap_blank_labels.py`
4. 필요 시 `rules/KAKAOMAP_LABELING_NOTES.md`
