# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

원단(Fabric) 원가 계산기 - 원사 배합, 가공비, 손실률 등을 고려하여 원단의 NET 단가를 계산하고 Excel로 출력하는 Tkinter GUI 애플리케이션입니다.

## 실행 방법

```bash
python calculate_net_price.py
```

애플리케이션이 실행되면 Tkinter GUI 창이 열립니다.

## 핵심 아키텍처

### 3-Tier 구조

1. **Data Layer (데이터 계층)**
   - `yarn_db.json`: 원사(yarn) 마스터 데이터 저장 (JSON 형식)
   - `calculation_history.db`: 계산 이력 저장 (SQLite 형식)
   - 원사 데이터는 JSON으로, 계산 이력은 SQLite로 분리하여 관리

2. **Business Logic Layer (계산 로직 계층)**
   - `calculate_single_scenario()`: 단일 환율 시나리오에 대한 원가 계산
   - `get_all_inputs()`: UI로부터 모든 입력값 수집 및 검증
   - 원사 혼용 계산, 손실률 적용, 가공비 계산 등의 복잡한 로직 처리

3. **Presentation Layer (UI 계층)**
   - `FabricCostCalculatorApp`: 메인 계산기 GUI (메인 윈도우)
   - `YarnManagementWindow`: 원사 DB 관리 GUI (팝업 윈도우)
   - `HistoryWindow`: 계산 이력 조회 GUI (팝업 윈도우)

### 주요 클래스 구조

```
calculate_net_price.py (단일 파일 구조)
├── Utility Functions (유틸리티 함수)
│   ├── JSON DB Utils: load_yarns_from_json(), save_yarns_to_json()
│   ├── History DB Utils: init_history_db(), save_calculation_to_history()
│   └── Display Utils: generate_yarn_display_description()
│
├── YarnManagementWindow (원사 DB 관리, line 152)
│   ├── Treeview로 원사 목록 표시 및 정렬 기능
│   ├── 원사 추가/수정/삭제 기능
│   └── yarn_db.json 파일 직접 조작
│
├── HistoryWindow (계산 이력 조회, line 427)
│   ├── Treeview로 이력 목록 표시
│   ├── 선택한 이력 상세 내역 표시
│   └── calculation_history.db 에서 데이터 조회
│
└── FabricCostCalculatorApp (메인 계산기, line 551)
    ├── setup_ui(): 복잡한 입력 폼 구성
    ├── calculate_all(): 3개 환율 시나리오 계산 (기준, 기준-50, 기준+50)
    ├── calculate_single_scenario(): 단일 시나리오 계산 엔진
    ├── trigger_excel_save(): Excel 템플릿 기반 결과 출력
    └── 원사 혼용 기능: 동적으로 원사 입력 행 추가 가능
```

## 데이터 구조

### 원사(Yarn) 데이터 스키마 (yarn_db.json)

```json
{
  "id": 1,
  "yarn_type": "Polyester",
  "denier": 150,
  "filament": 72,
  "processing_type": "DTY",
  "luster": "SD",
  "recycle_status": "virgin",
  "price_value": 0.8,
  "price_currency": "$",
  "price_unit": "lb",
  "quality": "일반",
  "created_at": "2025-06-05 18:38:15",
  "updated_at": "2025-06-05 18:38:15"
}
```

### 계산 이력 데이터베이스 (calculation_history.db)

```sql
CREATE TABLE calculation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    calculation_date TEXT NOT NULL,
    item_name TEXT,
    inputs_json TEXT,  -- 입력값 전체를 JSON으로 직렬화
    base_rate_results_json TEXT  -- 기준환율 계산 결과를 JSON으로 직렬화
)
```

## 계산 로직 흐름

1. **입력 수집**: `get_all_inputs()` → 원단 정보, 원사 구성(혼용 가능), 손실률, 가공비, 환율 등
2. **3개 환율 시나리오 계산**: 기준환율, 기준-50원, 기준+50원
3. **각 시나리오별 계산**: `calculate_single_scenario(inputs, rate_value)`
   - 원사 단가 환산 (통화/단위 고려)
   - 혼용 비율 적용하여 원사비 계산
   - 손실률 적용 (제직, 염색, 지연)
   - 가공비 추가 (제직료, 염색료)
   - 기타 비용 추가
   - NET 단가 산출
   - 마진 계산 (수주단가 기준)
4. **결과 표시**: Treeview에 3개 시나리오 결과 표시, 상세 내역 Text 위젯에 표시
5. **이력 저장**: 기준환율 계산 결과를 SQLite에 저장
6. **Excel 출력**: `FabricCost_Form.xlsx` 템플릿에 결과 기록

## Excel 템플릿 연동

- **템플릿 파일**: `FabricCost_Form.xlsx`
- **출력 메서드**: `fill_cost_sheet(workbook, sheet_name, inputs, base_rate_results, all_scenario_results)`
- **작동 방식**:
  - 템플릿 파일을 복사하여 새 파일 생성
  - `openpyxl`로 특정 셀에 계산 결과 기록
  - 원사 정보, 가공비, NET 단가 등을 미리 정의된 셀 위치에 입력

## 주요 특징

### 원사 혼용 기능
- `_add_yarn_input_row()`: 동적으로 원사 입력 행 추가
- 여러 원사를 비율(%)로 혼합하여 원가 계산 가능
- 각 원사의 단가, 통화, 단위가 다를 수 있어 환산 로직 필요

### 환율/통화/단위 처리
- 원사 단가: `$`, `원화` × `lb`, `kg` 조합 가능
- 가공비: 원화/kg 기준
- 최종 출력: $/yd 단위로 통일
- 환산 상수:
  - 1 lb = 0.453592 kg
  - 1 yd = 0.9144 m

### 손실률 체계
- 제직 Loss (%)
- 염색 Loss (%)
- 지연 Loss (%)
- 각 단계별 손실이 누적 적용됨

## 파일 구조

```
/mnt/c/project/python/costNETprice/
├── calculate_net_price.py          # 메인 애플리케이션 (1303 lines, 단일 파일)
├── calculate_net_price.py.bak      # 백업 파일
├── calculate_net_price copy.py     # 복사본
├── yarn_db.json                     # 원사 마스터 데이터
├── calculation_history.db           # 계산 이력 (SQLite)
└── FabricCost_Form.xlsx            # Excel 출력 템플릿
```

## 코드 수정 시 주의사항

### 계산 로직 변경
- `calculate_single_scenario()` 메서드는 핵심 계산 엔진입니다.
- 원사 혼용 로직, 환율 환산, 손실률 적용 순서를 정확히 파악하고 수정하세요.
- 계산 결과는 반드시 `details` 딕셔너리에 상세 내역을 포함해야 합니다.

### UI 레이아웃 변경
- `setup_ui()` 메서드에서 모든 위젯을 구성합니다.
- 스크롤 가능한 입력 영역: `scrollable_input_frame` (Canvas + Scrollbar)
- 고정된 출력 영역: `output_frame` (Treeview + Text)
- 위젯 추가 시 `row_idx` 변수를 올바르게 증가시켜야 레이아웃이 깨지지 않습니다.

### 데이터베이스 스키마 변경
- `yarn_db.json`: 수동으로 구조 변경 가능, `load_yarns_from_json()` 로직 확인
- `calculation_history.db`: 스키마 변경 시 `init_history_db()` 수정 필요
- 기존 데이터 마이그레이션 계획을 세우세요.

### Excel 출력 변경
- `fill_cost_sheet()` 메서드에서 셀 매핑 수정
- 템플릿 파일(`FabricCost_Form.xlsx`)의 레이아웃과 정확히 일치해야 함
- 디버깅용 print 문이 많이 남아있으니 참고하세요.

## 의존성

```
tkinter      # GUI (Python 표준 라이브러리)
json         # JSON 파일 처리
sqlite3      # SQLite 데이터베이스
openpyxl     # Excel 파일 읽기/쓰기
datetime     # 타임스탬프 생성
shutil       # 파일 복사
os           # 파일 시스템 접근
sys          # PyInstaller 경로 감지
```

## 일반적인 작업 패턴

### 새로운 입력 필드 추가
1. `setup_ui()`에서 위젯 추가
2. 해당 필드의 `tk.Variable` 생성
3. `get_all_inputs()`에서 입력값 수집 로직 추가
4. `calculate_single_scenario()`에서 계산 로직에 반영
5. `fill_cost_sheet()`에서 Excel 출력 로직 추가

### 새로운 원사 속성 추가
1. `yarn_db.json` 스키마에 필드 추가
2. `YarnManagementWindow`의 `yarn_fields_config_for_form`에 설정 추가
3. `generate_yarn_display_description()` 함수에서 표시 로직 추가 (선택사항)
4. 기존 원사 데이터에 기본값 추가 필요

### 새로운 손실 단계 추가
1. `setup_ui()`의 `loss_frame`에 입력 필드 추가
2. `get_all_inputs()`에서 해당 값 수집
3. `calculate_single_scenario()`에서 손실 적용 로직 추가

## 알려진 제약사항

- 단일 Python 파일로 구성되어 있어 코드가 길고 복잡함 (1303 lines)
- 에러 처리가 `messagebox.showerror()`에 의존하여 CLI 환경에서 디버깅 어려움
- Excel 템플릿 의존성: 템플릿 파일이 없으면 Excel 출력 불가
- 환율 시나리오가 하드코딩됨 (기준±50원)
