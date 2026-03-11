# Review Authenticity AI

한국어 리뷰를 대상으로 `진심 리뷰 (`genuine`)`와 `좋아요성 리뷰 (`promotion`)`를 분류하는 NLP 포트폴리오 프로젝트.

## Project Goal
이 프로젝트의 목표는 단순히 "리뷰이벤트 문구가 있는지"를 찾는 것이 아니라,
실제 경험 정보가 담긴 리뷰와 형식적이고 정보가 빈약한 리뷰를 구분하는 것이다.

## Core Principles
- 라벨은 플랫폼이 아니라 리뷰 내용 기준으로 정한다.
- 메타데이터는 보조 feature 후보로만 사용한다.
- 작은 단위의 코드와 문서로 진행한다.
- 사용자가 모든 파일과 함수를 직접 리뷰하고 이해할 수 있게 만든다.

## Current Status
현재까지 준비된 문서:
- `rules/CODEX_COLLAB_RULES.md`
- `rules/LABELING_GUIDE.md`
- `rules/CSV_SCHEMA.md`
- `rules/PROJECT_STRUCTURE.md`

현재 기본 라벨링 파일:
- `data/labeled/coupang_multiproduct_labeled.csv`

현재 기본 raw 파일:
- `data/raw/raw_reviews.csv`

## Recommended Workflow
1. 라벨링 기준 확정
2. 라벨링 데이터 수집 및 정리
3. baseline 모델 구현
4. 평가 지표 계산
5. 오분류 분석
6. 고급 모델 실험

## Directory Overview
- `rules/`: 프로젝트 운영 규칙과 기준 문서
- `data/raw/`: 원본 데이터
- `data/labeled/`: 사람이 라벨링한 데이터
- `data/processed/`: 전처리 후 학습용 데이터
- `src/`: 핵심 파이썬 코드
- `outputs/`: 모델, 지표, 그림 등 결과물
- `tests/`: 테스트 코드

## First Build Order
처음에는 아래 순서로 구현한다.

1. `data/labeled/labeled_reviews_template.csv`
2. `src/config.py`
3. `src/data_loader.py`
4. `src/preprocess.py`
5. `src/train_baseline.py`
6. `src/evaluate.py`
7. `src/error_analysis.py`

## Labels
- `genuine`: 구체적인 경험 정보가 있는 리뷰
- `promotion`: 이벤트 중심, 형식적, 정보가 빈약한 리뷰
- `uncertain`: 애매해서 학습셋에서 제외할 리뷰

## Baseline Run Guide
아래 패키지가 설치된 Python 환경이 필요하다.

- `pandas`
- `scikit-learn`

설치 예시:

```bash
pip install -r requirements.txt
```

baseline 실행:

```bash
cd ~/projects/review-authenticity-ai
python3 -m src.run_baseline
```

성공적으로 실행되면 아래 결과 파일이 생성된다.

- `outputs/metrics/baseline_metrics.json`
- `outputs/metrics/misclassified_reviews.csv`

## Current Limitation
현재 라벨 수가 적으면 baseline은 실행 가능해도 결과 해석 신뢰도는 낮다.

- 소량 라벨링 데이터는 파이프라인 검증용으로 먼저 사용한다.
- 성능 비교나 결론 도출은 라벨 수를 더 늘린 뒤 진행한다.
