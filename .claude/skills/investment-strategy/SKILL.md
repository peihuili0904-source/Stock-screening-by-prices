---
name: investment-strategy
description: 자산운용사 주식투자전략 일일 루틴. Drive '신한리서치' 폴더의 회사 리서치(경제·국내주식전략·해외주식전략·ETF·퀀트)로 하우스 뷰 골조를 세우고, '주식전략' 폴더의 타사 시장전략과 외신(FT·WSJ·Economist)으로 검증·보완해, 국가·섹터별 투자의견(OW/N/UW)과 "하우스 리서치가 놓친 부분"을 정리한다. "오늘 하우스 뷰", "투자전략 업데이트", "국가/섹터 뷰" 요청 시 사용.
---

# 주식투자전략 일일 루틴

역할과 정보 위계는 저장소 루트 `CLAUDE.md`를 따른다. 요약: **회사 리서치 = 기본 골조**, 타사 = 검증, 외신 = 누락 지적.

## 0. 입력 수집
| 자료 | 조회 |
|---|---|
| 회사 리서치 | `search_files`: `parentId = '1lwsoUxQnX0LcTWo2lviPLaPKZsToRGvN' and createdTime > '<직전 실행 시각 UTC>'`. 파일명 `신한투자증권_<카테고리>_<제목>_YYYYMMDD.pdf`. ` (1).pdf` 중복본은 제외 |
| 타사 시장전략 | `parentId = '1MgqvsYEPdG05oBmor4DqE-LkrB-M3oay'` 같은 조건. 폴더·신한 파일은 제외 |
| 외신 | ① 예약 작업 `trig_01QAUD51gvmjVVXUxPC2WHRq` → `last_run.session_id` → `list_events(kinds=["result"])` ② `python3 -I .claude/skills/market-research/scripts/fetch_news.py --hours 48 --out data/news/<날짜>.json` |
| 직전 하우스 뷰 | `strategy/house-view.md` |

새 회사 리서치가 0건이면 하우스 뷰는 그대로 두고, 타사·외신으로 "하우스 뷰 점검"만 한다.

## 1. 회사 리서치 분류와 정독
카테고리 → 층:
- **경제**: 경제시황, 해외경제, 금융전략(자산배분), 채권전략/채권시황, 크레딧
- **국내주식전략**: 신한 생각, 주식시황, 주식전략
- **해외주식전략**: 해외주식, 신흥국
- **ETF**: ETF
- **퀀트**: 퀀트분석
- **산업**: 그 외 업종명 카테고리 → 섹터 뷰 근거

리포트가 많으면 층별로 서브에이전트에 나눠 정독시킨다(각 6–7건). 뽑을 것: 결론, 원문 수치(밴드·목표·EPS·금리·환율), 국가·섹터·스타일 의견, 리스크, 리포트가 사실로 제시한 외부 사건, **발간일**.

## 2. 하우스 뷰 골조 (회사 리서치만으로)
1. 매크로: 성장·물가·정책금리·장기금리·달러/원·유가·유동성
2. 자산배분 톤: 주식/채권/현금
3. 국가 뷰: 한국·미국·중국·대만·일본·유럽·인도·기타 신흥국
4. 국내 섹터 뷰 / 미국 섹터 뷰 / 스타일·팩터 뷰
5. 매크로 → 국가·섹터 전달 경로를 한 줄씩 (예: "금리 고원 → 밸류 부담 큰 장기 성장주 중립")

## 3. 검증·보완
- **타사**: 하우스 뷰가 컨센서스 대비 어디에 있는지(동조/역행), 타사만 지적한 논점.
- **외신**: 하우스 리포트 발간일 이후 사건, 리포트가 다루지 않은 리스크·기회. 각 항목에 "영향 받는 국가/섹터"와 "하우스 뷰 조정 여부(유지/조정/관찰)"를 붙인다.
- 리포트끼리, 리포트와 외신 사이 수치가 다르면 표로 남긴다.

## 4. 산출
- `strategy/daily/YYYY-MM-DD.md` (템플릿 `references/daily-template.md`)
- `strategy/house-view.md` 갱신: 상단 현재 뷰 표 교체, 하단 "변경 이력"에 날짜·변경·사유 추가
- 대시보드 갱신: https://claude.ai/artifact/VdyNY9ZkP9n3mYxyfNzSd6 (Dashboard 타입). 원본은 `strategy/dashboard/`.
  - 데이터 JSON 6개(views·bands·macro·gaps·checkpoints·takeaways)를 오늘 내용으로 고친다.
  - 각 파일을 Artifact `asset: true`로 업로드한다.
  - `ArtifactData` update로 `datasets/<id>`의 `source.url`·`updated`·`edit`를 바꾼다(`if_version` 필수).
  - 제목의 날짜가 바뀌면 `files/index.html`의 `<h1>`도 `str_replace`로 고친다.
- 커밋 후 지정 브랜치에 push.

## 원칙
- 하우스 의견과 전략팀 조정을 항상 구분해 쓴다. 조정은 근거 2개 이상(외신·타사·데이터)일 때만.
- 발간 3일 이상 지난 리포트는 "(발간일, 기준 시점 주의)" 표시.
- 짧은 문장, 숫자는 원문 그대로, 범위는 `–`.
