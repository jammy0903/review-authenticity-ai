# CSV Schema

## Purpose
이 문서는 라벨링용 CSV와 모델 입력용 CSV의 기본 컬럼 구조를 정의한다.

초기에는 사람이 직접 정리하기 쉬운 형태로 시작하고, 나중에 전처리 단계에서 학습용 컬럼으로 변환한다.

## Recommended File Split
권장 파일은 아래와 같다.

- `raw_reviews.csv`: 원본 수집 데이터
- `labeled_reviews.csv`: 사람이 라벨링한 데이터
- `model_input.csv`: 전처리 후 모델 학습용 데이터

## `raw_reviews.csv`
원본 데이터를 최대한 손대지 않고 저장한다.

### Columns
- `review_id`
  - 각 리뷰의 고유 ID
  - 플랫폼 내 ID가 있으면 사용하고, 없으면 직접 생성
- `platform`
  - 예: `coupang`, `coupang_eats`, `kakaomap`, `naver`
- `store_or_product_name`
  - 가게명 또는 상품명
- `review_text_raw`
  - 원문 리뷰 텍스트
- `rating`
  - 별점 또는 평점
- `has_photo`
  - 사진 첨부 여부, `0` 또는 `1`
- `event_flag_raw`
  - 리뷰이벤트 관련 표시가 원본상 보였는지, 없으면 비움
- `reorder_count_raw`
  - 재주문 횟수 표시가 있으면 기록, 없으면 비움
- `collected_at`
  - 수집 날짜, 예: `2026-03-11`
- `source_note`
  - 수집 방식 메모

## `labeled_reviews.csv`
라벨링과 간단한 메모를 추가한 버전이다.

### Required Columns
- `review_id`
- `platform`
- `review_text_raw`
- `label`
  - `genuine`, `promotion`, `uncertain`
- `label_reason`
  - 짧은 라벨링 이유
- `annotator`
  - 누가 라벨링했는지
- `annotated_at`
  - 라벨링 날짜

### Optional Columns
- `store_or_product_name`
- `rating`
- `has_photo`
- `event_flag_raw`
- `reorder_count_raw`
- `notes`

## `model_input.csv`
학습에 바로 투입하기 위한 정리된 데이터다.

### Required Columns
- `review_id`
- `platform`
- `review_text`
  - 전처리 후 텍스트
- `label_binary`
  - `0 = genuine`, `1 = good`

### Optional Feature Columns
- `text_length_chars`
- `text_length_words`
- `has_event_phrase`
- `has_photo`
- `rating`
- `reorder_count`
- `contains_menu_keyword`
- `contains_delivery_keyword`
- `contains_taste_keyword`

## Label Mapping Rule
모델 학습용 2분류에서는 아래처럼 매핑한다.

- `genuine -> 0`
- `good -> 1`
- `uncertain -> 학습셋에서 제외`

## Example Row: `labeled_reviews.csv`
```csv
review_id,platform,review_text_raw,label,label_reason,annotator,annotated_at,rating,has_photo,event_flag_raw,reorder_count_raw
ce_0001,coupang_eats,"리뷰이벤트 참여합니다. 잘 먹었습니다.",promotion,event_phrase_only,user,2026-03-11,5,0,1,3
ce_0002,coupang_eats,"배송은 빨랐고 국물이 진한 편인데 면은 조금 불었어요.",genuine,specific_delivery,user,2026-03-11,4,0,0,1
km_0001,kakaomap,"양은 적당했고 고기는 부드러웠는데 반찬은 조금 짰어요.",genuine,specific_taste,user,2026-03-11,4,1,,
```

## Data Entry Rules
- 빈값은 임의 문구 대신 빈칸으로 둔다.
- `0/1` 컬럼은 일관되게 숫자로 넣는다.
- 날짜 형식은 `YYYY-MM-DD`로 통일한다.
- 플랫폼명은 소문자 snake_case 또는 소문자 단일 토큰으로 통일한다.
- 같은 리뷰가 중복 수집되지 않도록 `review_id`를 관리한다.

## Minimum Starter Schema
처음 시작할 때 너무 많은 컬럼이 부담되면 아래 최소 구조로 시작해도 된다.

```csv
review_id,platform,review_text_raw,label,label_reason
```

이후 필요할 때 `rating`, `has_photo`, `event_flag_raw`, `reorder_count_raw`를 추가한다.

## Practical Recommendation
처음에는 `labeled_reviews.csv` 중심으로 진행하는 것이 가장 좋다.

이유:
- 사람이 검토하기 쉽다.
- baseline 모델에 바로 연결하기 쉽다.
- 나중에 feature를 추가하기도 쉽다.
