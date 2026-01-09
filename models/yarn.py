"""
원사 데이터 모델

원사(Yarn) 관련 데이터 클래스를 정의합니다.
딕셔너리 대신 타입 안정성을 제공하는 데이터 클래스를 사용합니다.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class Yarn:
    """원사 데이터 클래스"""

    id: int
    yarn_type: str
    denier: float
    filament: float
    processing_type: str
    luster: str
    recycle_status: str
    price_value: float
    price_currency: str
    price_unit: str
    quality: str
    created_at: str
    updated_at: str

    def get_display_name(self) -> str:
        """
        표시용 원사 이름 생성

        예: "Polyester(virgin) 150D/72F DTY SD (일반)"

        Returns:
            포맷된 원사 이름
        """
        desc = f"{self.yarn_type}({self.recycle_status})"

        # Denier/Filament 추가 (0이 아닌 경우만)
        if self.denier or self.filament:
            denier_str = int(self.denier) if self.denier else ''
            filament_str = int(self.filament) if self.filament else ''
            desc += f" {denier_str}D/{filament_str}F"

        # 사가공 및 광택
        desc += f" {self.processing_type} {self.luster}"

        # 불필요한 문자열 제거
        desc = desc.replace("0D/0F ", "").replace(" D/ F", "")
        desc = desc.replace("N/A(N/A) ", "").replace("N/A N/A", "")
        desc = desc.strip()

        # 품질 등급 추가
        desc += f" ({self.quality})"

        return desc

    def get_price_display(self) -> str:
        """
        단가 표시 문자열 생성

        예: "$0.80/lb"

        Returns:
            포맷된 단가 문자열
        """
        return f"{self.price_currency}{self.price_value:.2f}/{self.price_unit}"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Yarn':
        """
        딕셔너리에서 Yarn 객체 생성

        Args:
            data: 원사 데이터 딕셔너리

        Returns:
            Yarn 객체
        """
        # created_at, updated_at이 datetime 객체인 경우 문자열로 변환
        created_at = data.get("created_at", "")
        updated_at = data.get("updated_at", "")

        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        if isinstance(updated_at, datetime):
            updated_at = updated_at.isoformat()

        return cls(
            id=data.get("id", 0),
            yarn_type=data.get("yarn_type", ""),
            denier=data.get("denier", 0.0),
            filament=data.get("filament", 0.0),
            processing_type=data.get("processing_type", ""),
            luster=data.get("luster", ""),
            recycle_status=data.get("recycle_status", ""),
            price_value=data.get("price_value", 0.0),
            price_currency=data.get("price_currency", "$"),
            price_unit=data.get("price_unit", "lb"),
            quality=data.get("quality", "일반"),
            created_at=created_at,
            updated_at=updated_at
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        딕셔너리로 변환 (JSON 저장용)

        Returns:
            원사 데이터 딕셔너리
        """
        return asdict(self)

    def update_timestamp(self):
        """updated_at을 현재 시간으로 갱신"""
        self.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def __str__(self):
        """문자열 표현"""
        return f"Yarn(id={self.id}, name={self.get_display_name()}, price={self.get_price_display()})"


@dataclass
class YarnCostComponent:
    """원사 비용 구성 요소"""

    yarn_id: int
    name: str
    ratio_pct: float
    price_value: float
    currency: str
    unit: str
    cost_if_100pct_usd_yd: float
    cost_contrib_usd_yd: float

    def get_contribution_percentage(self, total_cost: float) -> float:
        """
        전체 원가에서 이 원사가 차지하는 비율 계산

        Args:
            total_cost: 전체 원사 비용 ($/yd)

        Returns:
            비율 (%)
        """
        if total_cost == 0:
            return 0.0
        return (self.cost_contrib_usd_yd / total_cost) * 100

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'YarnCostComponent':
        """딕셔너리에서 객체 생성"""
        return cls(
            yarn_id=data.get("id", 0),
            name=data.get("name", ""),
            ratio_pct=data.get("ratio", 0.0),
            price_value=data.get("price_val_live", 0.0),
            currency=data.get("currency_from_db", "$"),
            unit=data.get("unit_from_db", "lb"),
            cost_if_100pct_usd_yd=data.get("cost_if_100pct_usd_yd", 0.0),
            cost_contrib_usd_yd=data.get("cost_contrib_usd_yd", 0.0)
        )

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "id": self.yarn_id,
            "name": self.name,
            "ratio": self.ratio_pct,
            "price_val_live": self.price_value,
            "currency_from_db": self.currency,
            "unit_from_db": self.unit,
            "cost_if_100pct_usd_yd": self.cost_if_100pct_usd_yd,
            "cost_contrib_usd_yd": self.cost_contrib_usd_yd
        }


@dataclass
class CalculationInput:
    """계산 입력 데이터"""

    item_name: str
    fabric_width_inch: float
    proc_weight_input_value: float
    proc_weight_input_unit: str
    yarns_data: list
    weaving_loss_pct: float
    dyeing_loss_pct: float
    delay_loss_pct: float
    weaving_fee_krw_kg: float
    dyeing_fee_krw_kg: float
    base_exchange_rate_krw_usd: float
    other_costs: list
    selling_price_usd_yd: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CalculationInput':
        """딕셔너리에서 객체 생성"""
        return cls(
            item_name=data.get("item_name", ""),
            fabric_width_inch=data.get("fabric_width_inch", 0.0),
            proc_weight_input_value=data.get("proc_weight_input_value", 0.0),
            proc_weight_input_unit=data.get("proc_weight_input_unit", "g/yd"),
            yarns_data=data.get("yarns_data", []),
            weaving_loss_pct=data.get("weaving_loss_pct", 0.0),
            dyeing_loss_pct=data.get("dyeing_loss_pct", 0.0),
            delay_loss_pct=data.get("delay_loss_pct", 0.0),
            weaving_fee_krw_kg=data.get("weaving_fee_krw_kg", 0.0),
            dyeing_fee_krw_kg=data.get("dyeing_fee_krw_kg", 0.0),
            base_exchange_rate_krw_usd=data.get("base_exchange_rate_krw_usd", 0.0),
            other_costs=data.get("other_costs", []),
            selling_price_usd_yd=data.get("selling_price_usd_yd", 0.0)
        )

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)


@dataclass
class CalculationResult:
    """계산 결과 데이터"""

    net_cost_usd_yd: float
    margin_pct: float
    total_yarn_cost_usd_yd: float
    cost_weaving_usd_yd: float
    cost_dyeing_usd_yd: float
    total_other_costs_usd_yd: float
    yarn_components: list  # List[YarnCostComponent]
    proc_weight_gyd: float = 0.0

    def get_total_processing_cost(self) -> float:
        """가공비 합계 (제직 + 염색)"""
        return self.cost_weaving_usd_yd + self.cost_dyeing_usd_yd

    def get_cost_breakdown(self) -> Dict[str, float]:
        """비용 구성 비율 (%)"""
        total = self.net_cost_usd_yd
        if total == 0:
            return {
                "yarn": 0.0,
                "weaving": 0.0,
                "dyeing": 0.0,
                "other": 0.0
            }

        return {
            "yarn": (self.total_yarn_cost_usd_yd / total) * 100,
            "weaving": (self.cost_weaving_usd_yd / total) * 100,
            "dyeing": (self.cost_dyeing_usd_yd / total) * 100,
            "other": (self.total_other_costs_usd_yd / total) * 100
        }

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (Excel 출력용)"""
        return {
            "net_cost_usd_yd": self.net_cost_usd_yd,
            "margin_pct": self.margin_pct,
            "details": {
                "total_yarn_cost_usd_yd": self.total_yarn_cost_usd_yd,
                "cost_weaving_usd_yd": self.cost_weaving_usd_yd,
                "cost_dyeing_usd_yd": self.cost_dyeing_usd_yd,
                "total_other_costs_usd_yd": self.total_other_costs_usd_yd,
                "final_proc_weight_gyd_used": self.proc_weight_gyd,
                "yarn_cost_components_usd_yd": [
                    {
                        "name": c.name,
                        "ratio": c.ratio_pct,
                        "cost_contrib_usd_yd": c.cost_contrib_usd_yd
                    }
                    for c in self.yarn_components
                ]
            }
        }


if __name__ == '__main__':
    # 테스트 코드
    print("=== Yarn 데이터 클래스 테스트 ===\n")

    # 1. Yarn 객체 생성
    print("1. Yarn 객체 생성:")
    yarn_dict = {
        "id": 1,
        "yarn_type": "Polyester",
        "denier": 150,
        "filament": 72,
        "processing_type": "DTY",
        "luster": "SD",
        "recycle_status": "virgin",
        "price_value": 0.80,
        "price_currency": "$",
        "price_unit": "lb",
        "quality": "일반",
        "created_at": "2025-06-05 18:38:15",
        "updated_at": "2025-06-05 18:38:15"
    }

    yarn = Yarn.from_dict(yarn_dict)
    print(f"   {yarn}")
    print(f"   표시명: {yarn.get_display_name()}")
    print(f"   단가: {yarn.get_price_display()}")

    # 2. YarnCostComponent 테스트
    print("\n2. YarnCostComponent 테스트:")
    component = YarnCostComponent(
        yarn_id=1,
        name="Polyester(virgin) 150D/72F DTY SD (일반)",
        ratio_pct=100.0,
        price_value=0.80,
        currency="$",
        unit="lb",
        cost_if_100pct_usd_yd=0.42,
        cost_contrib_usd_yd=0.42
    )
    print(f"   원사 비용 기여도: ${component.cost_contrib_usd_yd:.2f}/yd")
    print(f"   비율: {component.ratio_pct}%")

    # 3. CalculationResult 테스트
    print("\n3. CalculationResult 테스트:")
    result = CalculationResult(
        net_cost_usd_yd=1.35,
        margin_pct=11.11,
        total_yarn_cost_usd_yd=0.42,
        cost_weaving_usd_yd=0.35,
        cost_dyeing_usd_yd=0.40,
        total_other_costs_usd_yd=0.18,
        yarn_components=[component],
        proc_weight_gyd=205.0
    )
    print(f"   NET 단가: ${result.net_cost_usd_yd:.2f}/yd")
    print(f"   마진: {result.margin_pct:.2f}%")
    print(f"   가공비 합계: ${result.get_total_processing_cost():.2f}/yd")

    breakdown = result.get_cost_breakdown()
    print(f"\n   비용 구성:")
    print(f"      원사: {breakdown['yarn']:.1f}%")
    print(f"      제직: {breakdown['weaving']:.1f}%")
    print(f"      염색: {breakdown['dyeing']:.1f}%")
    print(f"      기타: {breakdown['other']:.1f}%")

    # 4. 딕셔너리 변환 테스트
    print("\n4. 딕셔너리 변환 테스트:")
    result_dict = result.to_dict()
    print(f"   딕셔너리 키: {list(result_dict.keys())}")
    print(f"   details 키: {list(result_dict['details'].keys())}")

    print("\n테스트 완료!")
