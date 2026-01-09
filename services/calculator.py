"""
원가 계산 모듈

원단 원가 계산의 핵심 비즈니스 로직을 처리합니다.
UI에서 분리된 순수한 계산 로직을 제공합니다.
"""

from typing import Dict, Any, List
from models.yarn import YarnCostComponent, CalculationResult
from models.constants import ValidationRules
from services.converter import UnitConverter, CurrencyConverter, LossCalculator
from utils.logger import get_logger

logger = get_logger(__name__)


class CostCalculator:
    """원가 계산 클래스"""

    def __init__(self):
        """초기화"""
        self.logger = logger

    def calculate_single_scenario(
        self,
        inputs: Dict[str, Any],
        exchange_rate: float
    ) -> CalculationResult:
        """
        단일 환율 시나리오에 대한 원가 계산

        Args:
            inputs: 계산 입력 데이터
                {
                    "fabric_width_inch": 60,
                    "proc_weight_input_value": 205,
                    "proc_weight_input_unit": "g/yd",
                    "yarns_data": [...],
                    "weaving_loss_pct": 2,
                    "dyeing_loss_pct": 4,
                    "delay_loss_pct": 6,
                    "weaving_fee_krw_kg": 450,
                    "dyeing_fee_krw_kg": 1900,
                    "other_costs": [...],
                    "selling_price_usd_yd": 1.50
                }
            exchange_rate: 적용할 환율 (원/$)

        Returns:
            CalculationResult 객체

        Raises:
            ValueError: 계산 중 오류 발생
        """
        try:
            self.logger.info(f"계산 시작: 환율={exchange_rate:.0f}원")

            # 1. 원단 중량 변환 (g/yd)
            proc_weight_gyd = UnitConverter.weight_to_gyd(
                inputs["proc_weight_input_value"],
                inputs["proc_weight_input_unit"],
                inputs.get("fabric_width_inch")
            )
            self.logger.debug(f"원단 중량: {proc_weight_gyd:.2f} g/yd")

            # 2. kg/yd로 변환
            proc_weight_kg_yd = UnitConverter.weight_to_kg_per_yd(proc_weight_gyd)

            # 3. 손실률 계산
            loss_multiplier = LossCalculator.calculate_loss_multiplier(
                inputs["weaving_loss_pct"],
                inputs["dyeing_loss_pct"],
                inputs["delay_loss_pct"]
            )
            self.logger.debug(f"손실률 승수: {loss_multiplier:.4f}")

            # 4. 원사 비용 계산
            yarn_components, total_yarn_cost_usd_yd = self._calculate_yarn_costs(
                inputs["yarns_data"],
                proc_weight_kg_yd,
                loss_multiplier,
                exchange_rate
            )
            self.logger.debug(f"총 원사비용: ${total_yarn_cost_usd_yd:.4f}/yd")

            # 5. 가공비 계산
            cost_weaving_usd_yd = self._calculate_processing_cost(
                inputs["weaving_fee_krw_kg"],
                proc_weight_kg_yd,
                exchange_rate
            )
            cost_dyeing_usd_yd = self._calculate_processing_cost(
                inputs["dyeing_fee_krw_kg"],
                proc_weight_kg_yd,
                exchange_rate
            )
            self.logger.debug(f"제직료: ${cost_weaving_usd_yd:.4f}/yd, 염색료: ${cost_dyeing_usd_yd:.4f}/yd")

            # 6. 기타 비용 계산
            total_other_costs_usd_yd = self._calculate_other_costs(
                inputs.get("other_costs", []),
                exchange_rate
            )
            self.logger.debug(f"기타 비용: ${total_other_costs_usd_yd:.4f}/yd")

            # 7. NET 단가 계산
            net_cost_usd_yd = (
                total_yarn_cost_usd_yd +
                cost_weaving_usd_yd +
                cost_dyeing_usd_yd +
                total_other_costs_usd_yd
            )

            # 8. 마진 계산
            margin_pct = self._calculate_margin(
                net_cost_usd_yd,
                inputs.get("selling_price_usd_yd", 0)
            )

            self.logger.info(f"계산 완료: NET=${net_cost_usd_yd:.4f}/yd, 마진={margin_pct:.2f}%")

            # 9. 결과 반환
            return CalculationResult(
                net_cost_usd_yd=net_cost_usd_yd,
                margin_pct=margin_pct,
                total_yarn_cost_usd_yd=total_yarn_cost_usd_yd,
                cost_weaving_usd_yd=cost_weaving_usd_yd,
                cost_dyeing_usd_yd=cost_dyeing_usd_yd,
                total_other_costs_usd_yd=total_other_costs_usd_yd,
                yarn_components=yarn_components,
                proc_weight_gyd=proc_weight_gyd
            )

        except ValueError as e:
            self.logger.error(f"계산 오류: {e}")
            raise
        except Exception as e:
            self.logger.exception(f"예상치 못한 오류: {e}")
            raise ValueError(f"계산 중 오류가 발생했습니다: {e}")

    def _calculate_yarn_costs(
        self,
        yarns_data: List[Dict[str, Any]],
        proc_weight_kg_yd: float,
        loss_multiplier: float,
        exchange_rate: float
    ) -> tuple:
        """
        원사 비용 계산

        Args:
            yarns_data: 원사 정보 리스트
            proc_weight_kg_yd: 원단 중량 (kg/yd)
            loss_multiplier: 손실률 승수
            exchange_rate: 환율 (원/$)

        Returns:
            (yarn_components, total_cost) 튜플
        """
        total_yarn_cost_usd_yd = 0.0
        yarn_components = []

        for yarn_input in yarns_data:
            # 원사 단가를 $/kg로 변환
            yarn_price_usd_kg = UnitConverter.price_to_usd_per_kg(
                yarn_input["price_val"],
                yarn_input["price_currency"],
                yarn_input["price_unit"],
                exchange_rate
            )

            # 100% 사용 시 비용
            cost_if_100pct = yarn_price_usd_kg * proc_weight_kg_yd * loss_multiplier

            # 실제 비율 적용
            yarn_ratio_pct = yarn_input["ratio_pct"]
            weighted_cost = cost_if_100pct * (yarn_ratio_pct / 100.0)

            total_yarn_cost_usd_yd += weighted_cost

            # 구성 요소 저장
            component = YarnCostComponent(
                yarn_id=yarn_input.get("id", 0),
                name=yarn_input.get("display_name_in_combobox", "N/A"),
                ratio_pct=yarn_ratio_pct,
                price_value=yarn_input["price_val"],
                currency=yarn_input["price_currency"],
                unit=yarn_input["price_unit"],
                cost_if_100pct_usd_yd=cost_if_100pct,
                cost_contrib_usd_yd=weighted_cost
            )
            yarn_components.append(component)

            self.logger.debug(
                f"원사 [{component.name}]: "
                f"{yarn_ratio_pct}% × ${cost_if_100pct:.4f} = ${weighted_cost:.4f}/yd"
            )

        return yarn_components, total_yarn_cost_usd_yd

    def _calculate_processing_cost(
        self,
        fee_krw_kg: float,
        proc_weight_kg_yd: float,
        exchange_rate: float
    ) -> float:
        """
        가공비 계산 (제직료 또는 염색료)

        Args:
            fee_krw_kg: 가공비 (원화/kg)
            proc_weight_kg_yd: 원단 중량 (kg/yd)
            exchange_rate: 환율 (원/$)

        Returns:
            가공비 ($/yd)
        """
        if exchange_rate <= 0:
            raise ValueError("유효하지 않은 환율입니다.")

        cost_krw_yd = fee_krw_kg * proc_weight_kg_yd
        cost_usd_yd = CurrencyConverter.to_usd(cost_krw_yd, "원화", exchange_rate)

        return cost_usd_yd

    def _calculate_other_costs(
        self,
        other_costs: List[Dict[str, Any]],
        exchange_rate: float
    ) -> float:
        """
        기타 비용 계산

        Args:
            other_costs: 기타 비용 리스트
                [{"description": "...", "amount": 0.15, "currency": "$"}, ...]
            exchange_rate: 환율 (원/$)

        Returns:
            기타 비용 합계 ($/yd)
        """
        total = 0.0

        for cost in other_costs:
            amount = cost["amount"]
            currency = cost["currency"]

            amount_usd = CurrencyConverter.to_usd(amount, currency, exchange_rate)
            total += amount_usd

            self.logger.debug(
                f"기타 비용 [{cost.get('description', 'N/A')}]: "
                f"{currency}{amount} = ${amount_usd:.4f}/yd"
            )

        return total

    def _calculate_margin(
        self,
        net_cost: float,
        selling_price: float
    ) -> float:
        """
        마진율 계산

        Args:
            net_cost: NET 단가 ($/yd)
            selling_price: 수주단가 ($/yd)

        Returns:
            마진율 (%)
        """
        if selling_price is None or selling_price == 0:
            return 0.0

        if net_cost == 0:
            if selling_price > 0:
                return float('inf')
            return 0.0

        margin = ((selling_price - net_cost) / net_cost) * 100
        return margin

    def calculate_multiple_scenarios(
        self,
        inputs: Dict[str, Any],
        exchange_rates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        다중 환율 시나리오 계산

        Args:
            inputs: 계산 입력 데이터
            exchange_rates: 환율 시나리오 리스트
                [{"label": "낮은 환율", "rate": 1100}, ...]

        Returns:
            계산 결과 리스트
                [{"scenario": "...", "rate_used": 1100, "result": CalculationResult}, ...]
        """
        results = []

        for scenario in exchange_rates:
            label = scenario["label"]
            rate = scenario["rate"]

            try:
                result = self.calculate_single_scenario(inputs, rate)
                results.append({
                    "scenario": label,
                    "rate_used": rate,
                    "result": result,
                    "success": True
                })
            except Exception as e:
                self.logger.error(f"시나리오 [{label}] 계산 실패: {e}")
                results.append({
                    "scenario": label,
                    "rate_used": rate,
                    "result": None,
                    "success": False,
                    "error": str(e)
                })

        return results


if __name__ == '__main__':
    # 테스트 코드
    print("=== 원가 계산 테스트 ===\n")

    # 테스트 입력 데이터
    test_inputs = {
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
                "display_name_in_combobox": "Polyester(virgin) 150D/72F DTY SD (일반)"
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

    calculator = CostCalculator()

    # 1. 단일 시나리오 계산
    print("1. 단일 시나리오 계산 (환율 1150원):")
    result = calculator.calculate_single_scenario(test_inputs, 1150)
    print(f"   NET 단가: ${result.net_cost_usd_yd:.4f}/yd")
    print(f"   마진: {result.margin_pct:.2f}%")
    print(f"\n   비용 구성:")
    print(f"      원사: ${result.total_yarn_cost_usd_yd:.4f}/yd")
    print(f"      제직: ${result.cost_weaving_usd_yd:.4f}/yd")
    print(f"      염색: ${result.cost_dyeing_usd_yd:.4f}/yd")
    print(f"      기타: ${result.total_other_costs_usd_yd:.4f}/yd")

    breakdown = result.get_cost_breakdown()
    print(f"\n   비율:")
    print(f"      원사: {breakdown['yarn']:.1f}%")
    print(f"      제직: {breakdown['weaving']:.1f}%")
    print(f"      염색: {breakdown['dyeing']:.1f}%")
    print(f"      기타: {breakdown['other']:.1f}%")

    # 2. 다중 시나리오 계산
    print("\n2. 다중 시나리오 계산:")
    scenarios = [
        {"label": "낮은 환율", "rate": 1100},
        {"label": "기준 환율", "rate": 1150},
        {"label": "높은 환율", "rate": 1200}
    ]
    results = calculator.calculate_multiple_scenarios(test_inputs, scenarios)

    for item in results:
        if item["success"]:
            res = item["result"]
            print(f"   {item['scenario']} ({item['rate_used']:.0f}원): "
                  f"NET=${res.net_cost_usd_yd:.4f}/yd, 마진={res.margin_pct:.2f}%")
        else:
            print(f"   {item['scenario']}: 계산 실패 - {item['error']}")

    # 3. 혼용 원사 테스트
    print("\n3. 혼용 원사 테스트 (Polyester 60% + Nylon 40%):")
    test_inputs_mixed = test_inputs.copy()
    test_inputs_mixed["yarns_data"] = [
        {
            "id": 1,
            "price_val": 0.80,
            "price_currency": "$",
            "price_unit": "lb",
            "ratio_pct": 60.0,
            "display_name_in_combobox": "Polyester(virgin) 150D/72F DTY SD"
        },
        {
            "id": 2,
            "price_val": 2500,
            "price_currency": "원화",
            "price_unit": "kg",
            "ratio_pct": 40.0,
            "display_name_in_combobox": "Nylon(virgin) 70D/68F ATY SD"
        }
    ]

    result = calculator.calculate_single_scenario(test_inputs_mixed, 1150)
    print(f"   NET 단가: ${result.net_cost_usd_yd:.4f}/yd")
    print(f"   마진: {result.margin_pct:.2f}%")
    print(f"\n   원사 구성:")
    for comp in result.yarn_components:
        print(f"      {comp.name}: {comp.ratio_pct}% → ${comp.cost_contrib_usd_yd:.4f}/yd")

    print("\n테스트 완료!")
