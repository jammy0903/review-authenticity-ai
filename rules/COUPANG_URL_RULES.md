# Coupang URL Rules

## Purpose
이 문서는 쿠팡 상품 seed URL의 구조, 핵심 식별자, 자동 추출 규칙, 중복 정리 기준을 정의한다.

목표는 쿠팡 상품 URL에서 안정적으로 아래 3개를 추출하는 것이다.

- `product_id`
- `item_id`
- `vendor_item_id`

## Core Pattern
쿠팡 상품 URL의 기본 패턴은 아래와 같다.

```text
https://www.coupang.com/vp/products/{product_id}?itemId={item_id}&vendorItemId={vendor_item_id}&...
```

예시:

```text
https://www.coupang.com/vp/products/8316673793?itemId=24002154096&vendorItemId=91022914050&sourceType=cmgoms
```

## Important Identifiers

### `product_id`
- 경로 `/vp/products/{product_id}` 에 들어간다.
- 상품 페이지 자체를 식별하는 핵심 값이다.
- 자동 추출 시 필수다.

### `item_id`
- 쿼리 파라미터 `itemId` 값이다.
- 상품 옵션/구성 맥락을 구분하는 데 도움이 된다.
- 가능한 경우 같이 저장한다.

### `vendor_item_id`
- 쿼리 파라미터 `vendorItemId` 값이다.
- 판매자 기준 상품 엔트리를 구분하는 데 도움이 된다.
- 가능한 경우 같이 저장한다.

## Non-Core Query Parameters
아래 파라미터는 주로 유입/추적/광고/페이지 문맥 정보다.

- `sourceType`
- `subSourceType`
- `omsPageId`
- `omsPageUrl`
- `clickEventId`
- `templateId`
- `searchId`

이 값들은 참고용으로 보관할 수는 있지만, seed URL의 고유 식별 기준으로는 사용하지 않는다.

## Canonical URL Rule
seed URL 정규화 시 canonical URL은 아래처럼 만든다.

```text
https://www.coupang.com/vp/products/{product_id}?itemId={item_id}&vendorItemId={vendor_item_id}
```

규칙:
- `product_id`는 항상 포함한다.
- `item_id`, `vendor_item_id`가 있으면 canonical URL에 유지한다.
- 나머지 추적성 파라미터는 제거한다.

예시:

원본:
```text
https://www.coupang.com/vp/products/5757045623?itemId=9738974748&vendorItemId=77022731922&sourceType=SDP_MID_CAROUSEL_2&clickEventId=db19fe90-1d02-11f1-93d6-fcdcd2f3ae2a&templateId=7132
```

정규화:
```text
https://www.coupang.com/vp/products/5757045623?itemId=9738974748&vendorItemId=77022731922
```

## Extraction Rule
권장 정규식:

```regex
^https://www\.coupang\.com/vp/products/(?P<product_id>\d+)(?:\?(?P<query>.*))?$ 
```

실제 추출 순서:
1. URL path에서 `product_id` 추출
2. query string에서 `itemId` 추출
3. query string에서 `vendorItemId` 추출
4. canonical URL 생성

## Duplicate Cleanup Rules
중복 정리는 아래 우선순위로 한다.

### Rule 1. Exact URL duplicates
- 문자열이 완전히 동일한 URL은 1개만 남긴다.

### Rule 2. Same canonical URL duplicates
- 추적 파라미터만 다른 URL은 같은 상품 seed로 본다.
- canonical URL이 같으면 1개만 남긴다.

예:
- `sourceType`만 다른 경우
- `clickEventId`만 다른 경우
- `searchId`만 다른 경우

### Rule 3. Same `product_id + item_id + vendor_item_id`
- canonical URL이 같지 않아도, 위 3개가 같으면 같은 엔트리로 본다.

### Rule 4. Missing query params
- `item_id` 또는 `vendor_item_id`가 없는 URL은 보조 seed로 간주한다.
- 같은 `product_id`의 더 완전한 URL이 있으면, 쿼리 파라미터가 더 많은 URL을 우선한다.

## Recommended Storage
seed URL 정리 결과는 아래 두 파일로 관리하는 것을 권장한다.

- `data/raw/coupang_seed_urls_parsed.csv`
- `data/raw/coupang_seed_urls_deduped.txt`

### Parsed CSV columns
- `seed_url`
- `canonical_url`
- `product_id`
- `item_id`
- `vendor_item_id`
- `has_item_id`
- `has_vendor_item_id`

### Deduped TXT
- crawler 입력용 최종 seed URL 목록
- 줄마다 canonical URL 하나

## Operational Guidance
- seed URL을 새로 추가할 때는 먼저 정규화한다.
- crawler에는 deduped TXT를 우선 사용한다.
- 원본 수집 URL은 필요하면 별도 보관하되, 중복 비교 기준은 canonical URL로 통일한다.
