"""
새 모듈 사용 예제

모듈화된 코드를 사용하는 방법을 보여줍니다.
GUI 없이 순수 계산만 수행합니다.
"""

from config import get_config
from data.yarn_repository import YarnRepository
from data.history_repository import HistoryRepository
from services.calculator import CostCalculator
from services.validator import InputValidator
from utils.logger import setup_logger
from utils.excel_exporter import ExcelExporter, ExcelExportHelper

# 로거 설정
logger = setup_logger('example')


def example_basic_calculation():
    """기본 계산 예제"""
    print("\n" + "=" * 60)
    print("예제 1: 기본 원가 계산")
    print("=" * 60)

    # 1. 설정 로드
    config = get_config()
    logger.info(f"설정 로드 완료: 기본 환율 {config.default_exchange_rate}원")

    # 2. 계산 입력 데이터 준비
    inputs = {
        "item_name": "EXAMPLE-001",
        "fabric_width_inch": 60,
        "proc_weight_input_value": 205,
        "proc_weight_input_unit": "g/yd",
        "yarns_data": [
            {
                "id": 1,
                "price_val": 0.80,
                "price_currency": "$",
                "price_unit": "lb",
                "ratio_pct": 100.0,
                "display_name_in_combobox": "Polyester(virgin) 150D/72F DTY SD"
            }
        ],
        "weaving_loss_pct": 2,
        "dyeing_loss_pct": 4,
        "delay_loss_pct": 6,
        "weaving_fee_krw_kg": 450,
        "dyeing_fee_krw_kg": 1900,
        "base_exchange_rate_krw_usd": 1150,
        "other_costs": [
            {"description": "검사비", "amount": 0.15, "currency": "$"},
            {"description": "부대비용", "amount": 0.03, "currency": "$"}
        ],
        "selling_price_usd_yd": 1.50
    }

    # 3. 입력 검증
    print("\n1. 입력 검증:")
    validation_result = InputValidator.validate_all_inputs(inputs)
    if validation_result.is_valid():
        print("   ✅ 입력 검증 통과")
    else:
        print("   ❌ 입력 오류:")
        for error in validation_result.errors:
            print(f"      - {error}")
        return

    # 4. 계산 수행
    print("\n2. 원가 계산:")
    calculator = CostCalculator()
    result = calculator.calculate_single_scenario(inputs, 1150)

    print(f"   NET 단가: ${result.net_cost_usd_yd:.4f}/yd")
    print(f"   마진: {result.margin_pct:.2f}%")
    print(f"\n   비용 구성:")
    print(f"      원사: ${result.total_yarn_cost_usd_yd:.4f}/yd ({result.get_cost_breakdown()['yarn']:.1f}%)")
    print(f"      제직: ${result.cost_weaving_usd_yd:.4f}/yd ({result.get_cost_breakdown()['weaving']:.1f}%)")
    print(f"      염색: ${result.cost_dyeing_usd_yd:.4f}/yd ({result.get_cost_breakdown()['dyeing']:.1f}%)")
    print(f"      기타: ${result.total_other_costs_usd_yd:.4f}/yd ({result.get_cost_breakdown()['other']:.1f}%)")

    # 5. 이력 저장
    print("\n3. 계산 이력 저장:")
    history_repo = HistoryRepository()
    history_id = history_repo.add(
        inputs["item_name"],
        inputs,
        result.to_dict()
    )
    print(f"   ✅ 이력 저장 완료: ID={history_id}")

    return result, inputs


def example_multiple_scenarios():
    """다중 시나리오 계산 예제"""
    print("\n" + "=" * 60)
    print("예제 2: 다중 환율 시나리오 계산")
    print("=" * 60)

    # 설정 로드
    config = get_config()

    # 입력 데이터 (example_basic_calculation과 동일)
    inputs = {
        "item_name": "EXAMPLE-002",
        "fabric_width_inch": 60,
        "proc_weight_input_value": 205,
        "proc_weight_input_unit": "g/yd",
        "yarns_data": [
            {
                "id": 1,
                "price_val": 0.80,
                "price_currency": "$",
                "price_unit": "lb",
                "ratio_pct": 100.0,
                "display_name_in_combobox": "Polyester(virgin) 150D/72F DTY SD"
            }
        ],
        "weaving_loss_pct": 2,
        "dyeing_loss_pct": 4,
        "delay_loss_pct": 6,
        "weaving_fee_krw_kg": 450,
        "dyeing_fee_krw_kg": 1900,
        "base_exchange_rate_krw_usd": 1150,
        "other_costs": [
            {"description": "검사비", "amount": 0.15, "currency": "$"}
        ],
        "selling_price_usd_yd": 1.50
    }

    # 환율 시나리오 생성
    scenarios = config.get_exchange_scenarios(inputs["base_exchange_rate_krw_usd"])

    print(f"\n환율 시나리오 {len(scenarios)}개:")
    for scenario in scenarios:
        print(f"   - {scenario['label']}: {scenario['rate']:.0f}원")

    # 다중 시나리오 계산
    print("\n계산 결과:")
    calculator = CostCalculator()
    results = calculator.calculate_multiple_scenarios(inputs, scenarios)

    for item in results:
        if item["success"]:
            res = item["result"]
            print(f"   {item['scenario']}: NET=${res.net_cost_usd_yd:.4f}/yd, 마진={res.margin_pct:.2f}%")
        else:
            print(f"   {item['scenario']}: 실패 - {item['error']}")


def example_yarn_management():
    """원사 관리 예제"""
    print("\n" + "=" * 60)
    print("예제 3: 원사 데이터 관리")
    print("=" * 60)

    # 원사 저장소
    yarn_repo = YarnRepository()

    print(f"\n1. 전체 원사 조회:")
    yarns = yarn_repo.get_all()
    print(f"   총 {len(yarns)}개 원사")
    for yarn in yarns[:3]:  # 처음 3개만
        print(f"      - {yarn.get_display_name()}: {yarn.get_price_display()}")

    print(f"\n2. 검색 (Polyester):")
    results = yarn_repo.search("Polyester")
    print(f"   검색 결과: {len(results)}개")
    for yarn in results:
        print(f"      - {yarn.get_display_name()}")

    print(f"\n3. ID로 조회 (ID=1):")
    yarn = yarn_repo.get_by_id(1)
    if yarn:
        print(f"   {yarn.get_display_name()}")
        print(f"   단가: {yarn.get_price_display()}")


def example_history_management():
    """이력 관리 예제"""
    print("\n" + "=" * 60)
    print("예제 4: 계산 이력 관리")
    print("=" * 60)

    history_repo = HistoryRepository()

    print(f"\n1. 이력 요약 조회:")
    summary = history_repo.get_summary_list(limit=5)
    print(f"   최근 {len(summary)}개 이력:")
    for history_id, calc_date, item_name in summary:
        print(f"      - ID={history_id}, {calc_date}, {item_name}")

    if summary:
        print(f"\n2. 상세 조회 (최근 이력):")
        history_id = summary[0][0]
        detail = history_repo.get_by_id(history_id)
        if detail:
            inputs, results = detail
            print(f"   아이템: {inputs.get('item_name')}")
            print(f"   NET 단가: ${results.get('net_cost_usd_yd', 0):.4f}/yd")


def example_excel_export(result, inputs):
    """Excel 출력 예제"""
    print("\n" + "=" * 60)
    print("예제 5: Excel 파일 출력")
    print("=" * 60)

    # 템플릿 파일 확인
    from pathlib import Path
    template_file = "FabricCost_Form.xlsx"

    if not Path(template_file).exists():
        print(f"   ⚠️  템플릿 파일 없음: {template_file}")
        print("   Excel 출력 예제 스킵")
        return

    # Excel 출력
    exporter = ExcelExporter(template_file)
    output_dir = ExcelExportHelper.get_default_output_dir()
    filename = ExcelExportHelper.generate_output_filename(inputs["item_name"])
    output_file = output_dir / filename

    success = exporter.export(
        str(output_file),
        inputs,
        result.to_dict()
    )

    if success:
        print(f"   ✅ Excel 저장 완료:")
        print(f"      {output_file}")
        print(f"      크기: {output_file.stat().st_size} bytes")
    else:
        print(f"   ❌ Excel 저장 실패")


def main():
    """메인 함수"""
    print("\n" + "=" * 60)
    print("새 모듈 사용 예제")
    print("=" * 60)

    try:
        # 예제 1: 기본 계산
        result, inputs = example_basic_calculation()

        # 예제 2: 다중 시나리오
        example_multiple_scenarios()

        # 예제 3: 원사 관리
        example_yarn_management()

        # 예제 4: 이력 관리
        example_history_management()

        # 예제 5: Excel 출력
        example_excel_export(result, inputs)

        print("\n" + "=" * 60)
        print("모든 예제 완료!")
        print("=" * 60)

    except Exception as e:
        logger.exception(f"오류 발생: {e}")
        print(f"\n❌ 오류: {e}")


if __name__ == '__main__':
    main()
