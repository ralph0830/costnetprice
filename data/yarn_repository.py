"""
원사 데이터 저장소 모듈

yarn_db.json 파일을 관리하고 원사 데이터 CRUD 작업을 수행합니다.
"""

import json
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from models.yarn import Yarn
from models.constants import FileNames, DEFAULT_YARNS
from utils.logger import get_logger

logger = get_logger(__name__)


class YarnRepository:
    """원사 데이터 저장소 클래스"""

    def __init__(self, db_file: str = None):
        """
        초기화

        Args:
            db_file: JSON 파일 경로 (기본값: yarn_db.json)
        """
        if db_file is None:
            db_file = FileNames.YARN_DB_JSON

        self.db_file = Path(db_file)
        self.logger = logger

        # 파일이 없으면 초기화
        if not self.db_file.exists() or self.db_file.stat().st_size == 0:
            self.logger.info(f"원사 DB 파일이 없습니다. 초기화합니다: {self.db_file}")
            self._initialize_with_defaults()

    def _initialize_with_defaults(self):
        """기본 원사 데이터로 초기화"""
        default_yarns = []
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for yarn_data in DEFAULT_YARNS:
            yarn_data = yarn_data.copy()
            yarn_data["created_at"] = current_time
            yarn_data["updated_at"] = current_time
            default_yarns.append(yarn_data)

        self._save_to_file(default_yarns)
        self.logger.info(f"기본 원사 {len(default_yarns)}개 생성 완료")

    def _load_from_file(self) -> List[dict]:
        """
        JSON 파일에서 데이터 로드

        Returns:
            원사 데이터 리스트 (딕셔너리)
        """
        if not self.db_file.exists():
            self.logger.warning(f"파일이 존재하지 않습니다: {self.db_file}")
            return []

        try:
            # 파일 크기 확인
            if self.db_file.stat().st_size == 0:
                self.logger.warning(f"파일이 비어있습니다: {self.db_file}")
                return []

            # JSON 파일 읽기
            with open(self.db_file, 'r', encoding='utf-8') as f:
                content = f.read()

                if not content or not content.strip():
                    self.logger.warning("파일 내용이 비어있습니다")
                    return []

                data = json.loads(content)

                if not isinstance(data, list):
                    self.logger.error(f"잘못된 데이터 형식: {type(data)}")
                    return []

                return data

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON 디코딩 오류: {e}")
            return []
        except OSError as e:
            self.logger.error(f"파일 읽기 오류: {e}")
            return []
        except Exception as e:
            self.logger.exception(f"예상치 못한 오류: {e}")
            return []

    def _save_to_file(self, yarns_data: List[dict]):
        """
        JSON 파일에 데이터 저장

        Args:
            yarns_data: 원사 데이터 리스트
        """
        try:
            # 디렉토리 생성
            self.db_file.parent.mkdir(parents=True, exist_ok=True)

            # JSON 파일 저장
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(yarns_data, f, ensure_ascii=False, indent=4)

            self.logger.debug(f"파일 저장 완료: {self.db_file}")

        except IOError as e:
            self.logger.error(f"파일 저장 오류: {e}")
            raise
        except Exception as e:
            self.logger.exception(f"예상치 못한 오류: {e}")
            raise

    def get_all(self) -> List[Yarn]:
        """
        모든 원사 조회

        Returns:
            Yarn 객체 리스트
        """
        yarns_data = self._load_from_file()
        return [Yarn.from_dict(data) for data in yarns_data]

    def get_by_id(self, yarn_id: int) -> Optional[Yarn]:
        """
        ID로 원사 조회

        Args:
            yarn_id: 원사 ID

        Returns:
            Yarn 객체 또는 None
        """
        yarns = self.get_all()
        for yarn in yarns:
            if yarn.id == yarn_id:
                return yarn
        return None

    def add(self, yarn: Yarn) -> Yarn:
        """
        원사 추가

        Args:
            yarn: Yarn 객체

        Returns:
            추가된 Yarn 객체 (ID가 자동 할당됨)
        """
        yarns_data = self._load_from_file()

        # ID 자동 생성
        if yarns_data:
            max_id = max(y["id"] for y in yarns_data)
            yarn.id = max_id + 1
        else:
            yarn.id = 1

        # 타임스탬프 설정
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        yarn.created_at = current_time
        yarn.updated_at = current_time

        # 추가 및 저장
        yarns_data.append(yarn.to_dict())
        self._save_to_file(yarns_data)

        self.logger.info(f"원사 추가: ID={yarn.id}, {yarn.get_display_name()}")
        return yarn

    def update(self, yarn: Yarn) -> bool:
        """
        원사 수정

        Args:
            yarn: 수정할 Yarn 객체

        Returns:
            성공 여부
        """
        yarns_data = self._load_from_file()

        # ID로 찾기
        found = False
        for i, yarn_data in enumerate(yarns_data):
            if yarn_data["id"] == yarn.id:
                # updated_at 갱신
                yarn.update_timestamp()
                yarns_data[i] = yarn.to_dict()
                found = True
                break

        if not found:
            self.logger.warning(f"원사를 찾을 수 없습니다: ID={yarn.id}")
            return False

        # 저장
        self._save_to_file(yarns_data)
        self.logger.info(f"원사 수정: ID={yarn.id}, {yarn.get_display_name()}")
        return True

    def delete(self, yarn_id: int) -> bool:
        """
        원사 삭제

        Args:
            yarn_id: 삭제할 원사 ID

        Returns:
            성공 여부
        """
        yarns_data = self._load_from_file()
        initial_count = len(yarns_data)

        # ID로 필터링
        yarns_data = [y for y in yarns_data if y["id"] != yarn_id]

        if len(yarns_data) == initial_count:
            self.logger.warning(f"원사를 찾을 수 없습니다: ID={yarn_id}")
            return False

        # 저장
        self._save_to_file(yarns_data)
        self.logger.info(f"원사 삭제: ID={yarn_id}")
        return True

    def search(self, keyword: str) -> List[Yarn]:
        """
        키워드로 원사 검색

        Args:
            keyword: 검색 키워드

        Returns:
            검색된 Yarn 객체 리스트
        """
        all_yarns = self.get_all()
        keyword_lower = keyword.lower()

        results = []
        for yarn in all_yarns:
            # 원사 타입, 사가공, 광택에서 검색
            if (
                keyword_lower in yarn.yarn_type.lower() or
                keyword_lower in yarn.processing_type.lower() or
                keyword_lower in yarn.luster.lower() or
                keyword_lower in yarn.recycle_status.lower()
            ):
                results.append(yarn)

        self.logger.debug(f"검색 결과: '{keyword}' → {len(results)}개")
        return results

    def get_count(self) -> int:
        """
        전체 원사 개수 조회

        Returns:
            원사 개수
        """
        yarns_data = self._load_from_file()
        return len(yarns_data)


if __name__ == '__main__':
    # 테스트 코드
    print("=== 원사 저장소 테스트 ===\n")

    # 임시 테스트 파일 사용
    test_db_file = "test_yarn_db.json"

    # 1. 저장소 초기화
    print("1. 저장소 초기화:")
    repo = YarnRepository(test_db_file)
    print(f"   기본 원사 개수: {repo.get_count()}개")

    # 2. 전체 조회
    print("\n2. 전체 조회:")
    yarns = repo.get_all()
    for yarn in yarns[:3]:  # 처음 3개만 출력
        print(f"   - {yarn}")

    # 3. ID로 조회
    print("\n3. ID로 조회 (ID=1):")
    yarn = repo.get_by_id(1)
    if yarn:
        print(f"   {yarn.get_display_name()}")
        print(f"   단가: {yarn.get_price_display()}")

    # 4. 원사 추가
    print("\n4. 원사 추가:")
    new_yarn = Yarn(
        id=0,  # 자동 할당됨
        yarn_type="Spandex",
        denier=40,
        filament=1,
        processing_type="FY",
        luster="BRT",
        recycle_status="virgin",
        price_value=5.50,
        price_currency="$",
        price_unit="lb",
        quality="AAA",
        created_at="",
        updated_at=""
    )
    added_yarn = repo.add(new_yarn)
    print(f"   추가됨: ID={added_yarn.id}, {added_yarn.get_display_name()}")
    print(f"   전체 개수: {repo.get_count()}개")

    # 5. 원사 수정
    print("\n5. 원사 수정 (ID=1의 단가 변경):")
    yarn = repo.get_by_id(1)
    if yarn:
        old_price = yarn.price_value
        yarn.price_value = 0.90
        repo.update(yarn)
        print(f"   단가: ${old_price} → ${yarn.price_value}")

    # 6. 검색
    print("\n6. 검색 (Polyester):")
    results = repo.search("Polyester")
    print(f"   검색 결과: {len(results)}개")
    for yarn in results[:2]:
        print(f"   - {yarn.get_display_name()}")

    # 7. 삭제
    print("\n7. 원사 삭제 (마지막 추가한 원사):")
    success = repo.delete(added_yarn.id)
    print(f"   삭제 성공: {success}")
    print(f"   전체 개수: {repo.get_count()}개")

    # 8. 정리
    print("\n8. 테스트 파일 삭제:")
    Path(test_db_file).unlink()
    print("   완료")

    print("\n테스트 완료!")
