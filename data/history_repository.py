"""
계산 이력 저장소 모듈

calculation_history.db (SQLite) 파일을 관리하고
계산 이력 데이터 CRUD 작업을 수행합니다.
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime

from models.constants import FileNames, DatabaseConfig
from utils.logger import get_logger

logger = get_logger(__name__)


class HistoryRepository:
    """계산 이력 저장소 클래스"""

    def __init__(self, db_file: str = None):
        """
        초기화

        Args:
            db_file: SQLite 파일 경로 (기본값: calculation_history.db)
        """
        if db_file is None:
            db_file = FileNames.HISTORY_DB

        self.db_file = Path(db_file)
        self.logger = logger

        # 데이터베이스 초기화
        self._initialize_database()

    def _initialize_database(self):
        """데이터베이스 테이블 생성"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            # 테이블 생성
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {DatabaseConfig.TABLE_CALCULATION_HISTORY} (
                    {DatabaseConfig.COL_ID} INTEGER PRIMARY KEY AUTOINCREMENT,
                    {DatabaseConfig.COL_CALCULATION_DATE} TEXT NOT NULL,
                    {DatabaseConfig.COL_ITEM_NAME} TEXT,
                    {DatabaseConfig.COL_INPUTS_JSON} TEXT,
                    {DatabaseConfig.COL_BASE_RATE_RESULTS_JSON} TEXT
                )
            """)

            conn.commit()
            conn.close()

            self.logger.debug(f"데이터베이스 초기화 완료: {self.db_file}")

        except sqlite3.Error as e:
            self.logger.error(f"데이터베이스 초기화 오류: {e}")
            raise

    def add(
        self,
        item_name: str,
        inputs: Dict[str, Any],
        base_rate_results: Dict[str, Any]
    ) -> int:
        """
        계산 이력 추가

        Args:
            item_name: 아이템 이름
            inputs: 입력 데이터 딕셔너리
            base_rate_results: 기준환율 계산 결과 딕셔너리

        Returns:
            생성된 이력 ID

        Raises:
            sqlite3.Error: DB 오류
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            # 현재 시각
            calc_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # JSON 직렬화
            inputs_str = json.dumps(inputs, ensure_ascii=False)
            results_str = json.dumps(base_rate_results, ensure_ascii=False)

            # 삽입
            cursor.execute(f"""
                INSERT INTO {DatabaseConfig.TABLE_CALCULATION_HISTORY}
                ({DatabaseConfig.COL_CALCULATION_DATE}, {DatabaseConfig.COL_ITEM_NAME},
                 {DatabaseConfig.COL_INPUTS_JSON}, {DatabaseConfig.COL_BASE_RATE_RESULTS_JSON})
                VALUES (?, ?, ?, ?)
            """, (calc_date, item_name, inputs_str, results_str))

            history_id = cursor.lastrowid
            conn.commit()
            conn.close()

            self.logger.info(f"이력 추가: ID={history_id}, {item_name}")
            return history_id

        except sqlite3.Error as e:
            self.logger.error(f"이력 추가 오류: {e}")
            raise
        except json.JSONEncodeError as e:
            self.logger.error(f"JSON 인코딩 오류: {e}")
            raise

    def get_summary_list(self, limit: int = 100) -> List[Tuple]:
        """
        이력 요약 목록 조회 (최신순)

        Args:
            limit: 조회 개수

        Returns:
            (id, calculation_date, item_name) 튜플 리스트
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute(f"""
                SELECT {DatabaseConfig.COL_ID},
                       {DatabaseConfig.COL_CALCULATION_DATE},
                       {DatabaseConfig.COL_ITEM_NAME}
                FROM {DatabaseConfig.TABLE_CALCULATION_HISTORY}
                ORDER BY {DatabaseConfig.COL_CALCULATION_DATE} DESC
                LIMIT ?
            """, (limit,))

            results = cursor.fetchall()
            conn.close()

            self.logger.debug(f"이력 요약 조회: {len(results)}개")
            return results

        except sqlite3.Error as e:
            self.logger.error(f"이력 조회 오류: {e}")
            return []

    def get_by_id(self, history_id: int) -> Optional[Tuple[Dict, Dict]]:
        """
        ID로 이력 상세 조회

        Args:
            history_id: 이력 ID

        Returns:
            (inputs_dict, results_dict) 튜플 또는 None
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute(f"""
                SELECT {DatabaseConfig.COL_INPUTS_JSON},
                       {DatabaseConfig.COL_BASE_RATE_RESULTS_JSON}
                FROM {DatabaseConfig.TABLE_CALCULATION_HISTORY}
                WHERE {DatabaseConfig.COL_ID} = ?
            """, (history_id,))

            row = cursor.fetchone()
            conn.close()

            if row:
                inputs = json.loads(row[0])
                results = json.loads(row[1])
                self.logger.debug(f"이력 상세 조회: ID={history_id}")
                return (inputs, results)

            self.logger.warning(f"이력을 찾을 수 없습니다: ID={history_id}")
            return None

        except sqlite3.Error as e:
            self.logger.error(f"이력 조회 오류: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON 디코딩 오류: {e}")
            return None

    def delete(self, history_id: int) -> bool:
        """
        이력 삭제

        Args:
            history_id: 삭제할 이력 ID

        Returns:
            성공 여부
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute(f"""
                DELETE FROM {DatabaseConfig.TABLE_CALCULATION_HISTORY}
                WHERE {DatabaseConfig.COL_ID} = ?
            """, (history_id,))

            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()

            if rows_affected > 0:
                self.logger.info(f"이력 삭제: ID={history_id}")
                return True
            else:
                self.logger.warning(f"이력을 찾을 수 없습니다: ID={history_id}")
                return False

        except sqlite3.Error as e:
            self.logger.error(f"이력 삭제 오류: {e}")
            return False

    def search_by_item_name(self, keyword: str, limit: int = 50) -> List[Tuple]:
        """
        아이템 이름으로 검색

        Args:
            keyword: 검색 키워드
            limit: 조회 개수

        Returns:
            (id, calculation_date, item_name) 튜플 리스트
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute(f"""
                SELECT {DatabaseConfig.COL_ID},
                       {DatabaseConfig.COL_CALCULATION_DATE},
                       {DatabaseConfig.COL_ITEM_NAME}
                FROM {DatabaseConfig.TABLE_CALCULATION_HISTORY}
                WHERE {DatabaseConfig.COL_ITEM_NAME} LIKE ?
                ORDER BY {DatabaseConfig.COL_CALCULATION_DATE} DESC
                LIMIT ?
            """, (f"%{keyword}%", limit))

            results = cursor.fetchall()
            conn.close()

            self.logger.debug(f"검색 결과: '{keyword}' → {len(results)}개")
            return results

        except sqlite3.Error as e:
            self.logger.error(f"검색 오류: {e}")
            return []

    def get_count(self) -> int:
        """
        전체 이력 개수 조회

        Returns:
            이력 개수
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute(f"""
                SELECT COUNT(*)
                FROM {DatabaseConfig.TABLE_CALCULATION_HISTORY}
            """)

            count = cursor.fetchone()[0]
            conn.close()

            return count

        except sqlite3.Error as e:
            self.logger.error(f"개수 조회 오류: {e}")
            return 0

    def clear_all(self) -> bool:
        """
        모든 이력 삭제 (주의: 복구 불가)

        Returns:
            성공 여부
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute(f"""
                DELETE FROM {DatabaseConfig.TABLE_CALCULATION_HISTORY}
            """)

            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()

            self.logger.warning(f"모든 이력 삭제: {rows_affected}개")
            return True

        except sqlite3.Error as e:
            self.logger.error(f"전체 삭제 오류: {e}")
            return False


if __name__ == '__main__':
    # 테스트 코드
    print("=== 계산 이력 저장소 테스트 ===\n")

    # 임시 테스트 파일 사용
    test_db_file = "test_history.db"

    # 1. 저장소 초기화
    print("1. 저장소 초기화:")
    repo = HistoryRepository(test_db_file)
    print(f"   초기 이력 개수: {repo.get_count()}개")

    # 2. 이력 추가
    print("\n2. 이력 추가:")
    test_inputs = {
        "item_name": "TEST-001",
        "fabric_width_inch": 60,
        "proc_weight_input_value": 205
    }
    test_results = {
        "net_cost_usd_yd": 1.35,
        "margin_pct": 11.11
    }

    id1 = repo.add("TEST-001", test_inputs, test_results)
    print(f"   추가됨: ID={id1}")

    id2 = repo.add("TEST-002", test_inputs, test_results)
    print(f"   추가됨: ID={id2}")

    id3 = repo.add("CPEM(60-147M)", test_inputs, test_results)
    print(f"   추가됨: ID={id3}")

    print(f"   전체 개수: {repo.get_count()}개")

    # 3. 요약 목록 조회
    print("\n3. 요약 목록 조회:")
    summary_list = repo.get_summary_list(limit=10)
    for history_id, calc_date, item_name in summary_list:
        print(f"   - ID={history_id}, {calc_date}, {item_name}")

    # 4. 상세 조회
    print("\n4. 상세 조회 (ID=1):")
    detail = repo.get_by_id(id1)
    if detail:
        inputs, results = detail
        print(f"   입력: {list(inputs.keys())}")
        print(f"   결과: NET=${results['net_cost_usd_yd']}/yd, 마진={results['margin_pct']}%")

    # 5. 검색
    print("\n5. 검색 (TEST):")
    search_results = repo.search_by_item_name("TEST")
    print(f"   검색 결과: {len(search_results)}개")
    for history_id, calc_date, item_name in search_results:
        print(f"   - {item_name}")

    # 6. 삭제
    print("\n6. 이력 삭제 (ID=1):")
    success = repo.delete(id1)
    print(f"   삭제 성공: {success}")
    print(f"   전체 개수: {repo.get_count()}개")

    # 7. 전체 삭제
    print("\n7. 전체 이력 삭제:")
    repo.clear_all()
    print(f"   전체 개수: {repo.get_count()}개")

    # 8. 정리
    print("\n8. 테스트 파일 삭제:")
    Path(test_db_file).unlink()
    print("   완료")

    print("\n테스트 완료!")
