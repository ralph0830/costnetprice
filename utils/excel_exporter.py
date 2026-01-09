"""
Excel 출력 모듈

계산 결과를 Excel 템플릿 파일에 기록하고 저장합니다.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from shutil import copyfile
import openpyxl
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from models.constants import FileNames, ExcelCellMapping
from utils.logger import get_logger

logger = get_logger(__name__)


class ExcelExporter:
    """Excel 출력 클래스"""

    def __init__(self, template_file: str = None):
        """
        초기화

        Args:
            template_file: 템플릿 파일 경로 (기본값: FabricCost_Form.xlsx)
        """
        if template_file is None:
            template_file = FileNames.EXCEL_TEMPLATE

        self.template_file = Path(template_file)
        self.mapping = ExcelCellMapping()
        self.logger = logger

    def export(
        self,
        output_file: str,
        inputs: Dict[str, Any],
        base_rate_results: Dict[str, Any],
        all_scenario_results: List[Dict[str, Any]] = None
    ) -> bool:
        """
        계산 결과를 Excel로 출력

        Args:
            output_file: 출력 파일 경로
            inputs: 입력 데이터
            base_rate_results: 기준환율 계산 결과
            all_scenario_results: 전체 시나리오 결과 (선택)

        Returns:
            성공 여부
        """
        try:
            # 1. 템플릿 파일 확인
            if not self.template_file.exists():
                self.logger.error(f"템플릿 파일 없음: {self.template_file}")
                return False

            # 2. 템플릿 복사
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            copyfile(self.template_file, output_path)

            # 3. 워크북 열기
            wb = openpyxl.load_workbook(output_path)
            sheet = wb.active

            # 4. 데이터 입력
            self._fill_basic_info(sheet, inputs)
            self._fill_yarn_info(sheet, inputs)
            self._fill_loss_info(sheet, inputs)
            self._fill_processing_fees(sheet, inputs, base_rate_results)
            self._fill_other_costs(sheet, inputs, base_rate_results)
            self._fill_results(sheet, inputs, base_rate_results, all_scenario_results)

            # 5. 저장
            wb.save(output_path)
            wb.close()

            self.logger.info(f"Excel 저장 완료: {output_path}")
            return True

        except FileNotFoundError as e:
            self.logger.error(f"파일을 찾을 수 없습니다: {e}")
            return False
        except PermissionError as e:
            self.logger.error(f"파일 접근 권한 오류: {e}")
            return False
        except Exception as e:
            self.logger.exception(f"Excel 출력 오류: {e}")
            return False

    def _fill_basic_info(self, sheet: Worksheet, inputs: Dict[str, Any]):
        """기본 정보 입력"""
        try:
            sheet[self.mapping.ITEM_NAME] = inputs.get("item_name", "")
            sheet[self.mapping.FABRIC_WIDTH] = inputs.get("fabric_width_inch", 0)
            sheet[self.mapping.PROC_WEIGHT_VALUE] = inputs.get("proc_weight_input_value", 0)

            self.logger.debug("기본 정보 입력 완료")
        except Exception as e:
            self.logger.error(f"기본 정보 입력 오류: {e}")

    def _fill_yarn_info(self, sheet: Worksheet, inputs: Dict[str, Any]):
        """원사 정보 입력"""
        try:
            yarns = inputs.get("yarns_data", [])

            # 동적 셀 매핑 (최대 3개 원사 지원)
            yarn_rows = [
                (self.mapping.YARN1_NAME, self.mapping.YARN1_RATIO, self.mapping.YARN1_PRICE),
                (self.mapping.YARN2_NAME, self.mapping.YARN2_RATIO, self.mapping.YARN2_PRICE),
                (self.mapping.YARN3_NAME, self.mapping.YARN3_RATIO, self.mapping.YARN3_PRICE)
            ]

            for idx, yarn in enumerate(yarns[:3]):
                name_cell, ratio_cell, price_cell = yarn_rows[idx]

                # 원사명
                sheet[name_cell] = yarn.get("display_name_in_combobox", "")

                # 비율
                sheet[ratio_cell] = yarn.get("ratio_pct", 0)

                # 단가 (통화/단위 포함)
                price_val = yarn.get("price_val", 0)
                currency = yarn.get("price_currency", "$")
                unit = yarn.get("price_unit", "lb")
                sheet[price_cell] = f"{currency}{price_val}/{unit}"

            self.logger.debug(f"원사 정보 입력 완료: {len(yarns)}개")
        except Exception as e:
            self.logger.error(f"원사 정보 입력 오류: {e}")

    def _fill_loss_info(self, sheet: Worksheet, inputs: Dict[str, Any]):
        """손실률 정보 입력"""
        try:
            sheet[self.mapping.WEAVING_LOSS] = inputs.get("weaving_loss_pct", 0)
            sheet[self.mapping.DYEING_LOSS] = inputs.get("dyeing_loss_pct", 0)
            sheet[self.mapping.DELAY_LOSS] = inputs.get("delay_loss_pct", 0)

            self.logger.debug("손실률 정보 입력 완료")
        except Exception as e:
            self.logger.error(f"손실률 정보 입력 오류: {e}")

    def _fill_processing_fees(
        self,
        sheet: Worksheet,
        inputs: Dict[str, Any],
        results: Dict[str, Any]
    ):
        """가공비 정보 입력"""
        try:
            sheet[self.mapping.WEAVING_FEE] = inputs.get("weaving_fee_krw_kg", 0)
            sheet[self.mapping.DYEING_FEE] = inputs.get("dyeing_fee_krw_kg", 0)
            sheet[self.mapping.EXCHANGE_RATE] = inputs.get("base_exchange_rate_krw_usd", 0)

            self.logger.debug("가공비 정보 입력 완료")
        except Exception as e:
            self.logger.error(f"가공비 정보 입력 오류: {e}")

    def _fill_other_costs(
        self,
        sheet: Worksheet,
        inputs: Dict[str, Any],
        results: Dict[str, Any]
    ):
        """기타 비용 정보 입력"""
        try:
            other_costs = inputs.get("other_costs", [])

            # 기타 비용 셀 매핑 (최대 3개)
            cost_cells = [
                (self.mapping.OTHER_COST1_DESC, self.mapping.OTHER_COST1_AMOUNT),
                (self.mapping.OTHER_COST2_DESC, self.mapping.OTHER_COST2_AMOUNT),
                (self.mapping.OTHER_COST3_DESC, self.mapping.OTHER_COST3_AMOUNT)
            ]

            for idx, cost in enumerate(other_costs[:3]):
                desc_cell, amount_cell = cost_cells[idx]

                sheet[desc_cell] = cost.get("description", "")

                # 금액 (USD로 변환된 값 사용)
                amount = cost.get("amount", 0)
                currency = cost.get("currency", "$")

                if currency == "$":
                    sheet[amount_cell] = amount
                else:
                    # 원화는 환율로 나눠서 USD로 변환
                    exchange_rate = inputs.get("base_exchange_rate_krw_usd", 1150)
                    sheet[amount_cell] = amount / exchange_rate if exchange_rate > 0 else 0

            # 빈 셀 처리
            for idx in range(len(other_costs), 3):
                desc_cell, amount_cell = cost_cells[idx]
                sheet[desc_cell] = ""
                sheet[amount_cell] = ""

            self.logger.debug(f"기타 비용 입력 완료: {len(other_costs)}개")
        except Exception as e:
            self.logger.error(f"기타 비용 입력 오류: {e}")

    def _fill_results(
        self,
        sheet: Worksheet,
        inputs: Dict[str, Any],
        base_rate_results: Dict[str, Any],
        all_scenario_results: List[Dict[str, Any]] = None
    ):
        """계산 결과 입력"""
        try:
            # 기준 환율 NET 단가
            net_cost = base_rate_results.get("net_cost_usd_yd", 0)
            sheet[self.mapping.NET_COST_BASE] = net_cost

            # 수주단가
            selling_price = inputs.get("selling_price_usd_yd", 0)
            sheet[self.mapping.SELLING_PRICE] = selling_price

            self.logger.debug(f"결과 입력 완료: NET=${net_cost:.4f}, 수주=${selling_price:.2f}")
        except Exception as e:
            self.logger.error(f"결과 입력 오류: {e}")


class ExcelExportHelper:
    """Excel 출력 헬퍼 함수"""

    @staticmethod
    def generate_output_filename(item_name: str = "원가계산서") -> str:
        """
        출력 파일명 생성

        Args:
            item_name: 아이템 이름

        Returns:
            파일명 (예: "원가계산서_2025-06-05_143022.xlsx")
        """
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        # 파일명에 사용할 수 없는 문자 제거
        safe_name = "".join(c for c in item_name if c.isalnum() or c in (' ', '-', '_'))
        safe_name = safe_name.strip() or "원가계산서"

        return f"{safe_name}_{timestamp}.xlsx"

    @staticmethod
    def get_default_output_dir() -> Path:
        """
        기본 출력 디렉토리 반환

        Returns:
            출력 디렉토리 경로 (예: "./output/")
        """
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        return output_dir


if __name__ == '__main__':
    # 테스트 코드
    print("=== Excel 출력 테스트 ===\n")

    # 테스트 데이터
    test_inputs = {
        "item_name": "TEST-001",
        "fabric_width_inch": 60,
        "proc_weight_input_value": 205,
        "proc_weight_input_unit": "g/yd",
        "yarns_data": [
            {
                "id": 1,
                "display_name_in_combobox": "Polyester(virgin) 150D/72F DTY SD (일반)",
                "ratio_pct": 100.0,
                "price_val": 0.80,
                "price_currency": "$",
                "price_unit": "lb"
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

    test_results = {
        "net_cost_usd_yd": 1.0055,
        "margin_pct": 49.18,
        "details": {
            "total_yarn_cost_usd_yd": 0.4066,
            "cost_weaving_usd_yd": 0.0802,
            "cost_dyeing_usd_yd": 0.3387,
            "total_other_costs_usd_yd": 0.1800
        }
    }

    # 1. 파일명 생성 테스트
    print("1. 파일명 생성:")
    filename = ExcelExportHelper.generate_output_filename("TEST-001")
    print(f"   생성된 파일명: {filename}")

    # 2. 출력 디렉토리 테스트
    print("\n2. 출력 디렉토리:")
    output_dir = ExcelExportHelper.get_default_output_dir()
    print(f"   출력 디렉토리: {output_dir}")

    # 3. Excel 출력 테스트 (템플릿이 있는 경우만)
    print("\n3. Excel 출력 테스트:")
    template_file = "FabricCost_Form.xlsx"

    if Path(template_file).exists():
        exporter = ExcelExporter(template_file)
        output_file = output_dir / filename

        success = exporter.export(
            str(output_file),
            test_inputs,
            test_results
        )

        if success:
            print(f"   ✅ Excel 저장 성공: {output_file}")
            print(f"   파일 크기: {output_file.stat().st_size} bytes")

            # 테스트 파일 삭제
            output_file.unlink()
            print(f"   테스트 파일 삭제 완료")
        else:
            print("   ❌ Excel 저장 실패")
    else:
        print(f"   ⚠️  템플릿 파일 없음: {template_file}")
        print("   Excel 출력 테스트 스킵")

    print("\n테스트 완료!")
