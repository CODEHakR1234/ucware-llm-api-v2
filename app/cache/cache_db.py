
import os
import redis
from functools import lru_cache
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import json
from zoneinfo import ZoneInfo

class RedisCacheDB:
    def __init__(
        self,
        host: str = os.getenv("REDIS_HOST", "localhost"),
        port: int = int(os.getenv("REDIS_PORT", "6379")),
        db: int = int(os.getenv("REDIS_DB", "0")),
        ttl_days: int = int(os.getenv("REDIS_TTL_DAYS", "7"))
    ):
        self.r = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.ttl_days = ttl_days
        
    def _get_date_key(self, date: datetime = None) -> str:
        """날짜를 기준으로 HSET key 생성"""
        if date is None:
            date = datetime.now(ZoneInfo("Asia/Seoul"))
        return f"pdf:summaries:{date.strftime('%Y-%m-%d')}"
    
    def _get_metadata_key(self, file_id: str) -> str:
        """파일 메타데이터용 key"""
        return f"pdf:metadata:{file_id}"

    def get_pdf(self, fid: str) -> Optional[str]:
        """file_id로 요약본 조회 (모든 날짜에서 검색)"""
        # 1. 먼저 메타데이터에서 저장된 날짜 확인
        metadata_key = self._get_metadata_key(fid)
        metadata = self.r.get(metadata_key)

        if metadata:
            self.r.expire(metadata_key, self.ttl_days * 86400)
            meta = json.loads(metadata)
            date_key = f"pdf:summaries:{meta['date']}"
            summary = self.r.hget(date_key, fid)
            if summary:
                return summary
        
        # 2. 메타데이터가 없으면 최근 7일간의 모든 날짜 검색
        for i in range(self.ttl_days):
            date = datetime.now(ZoneInfo("Asia/Seoul")) - timedelta(days=i)
            date_key = self._get_date_key(date)
            summary = self.r.hget(date_key, fid)
            if summary:
                return summary
        
        return None

    def exists_pdf(self, fid: str) -> bool:
        """해당 file_id 에 대한 요약이 **어디**에든 존재하는지 빠르게 확인."""
        # 1) 메타데이터 키가 있으면 바로 True
        metadata_key = self._get_metadata_key(fid)
        if self.r.exists(metadata_key):
            # 접근 시 TTL 갱신
            self.r.expire(metadata_key, self.ttl_days * 86400)
            return True

        # 2) 최근 ttl_days 동안 날짜별 HSET 조회
        now = datetime.now(ZoneInfo("Asia/Seoul"))
        for i in range(self.ttl_days):
            date_key = self._get_date_key(now - timedelta(days=i))
            if self.r.hexists(date_key, fid):
                return True

        return False

    def set_pdf(self, fid: str, s: str):
        """날짜별 HSET에 요약본 저장"""
        now = datetime.now(ZoneInfo("Asia/Seoul"))
        date_key = self._get_date_key(now)
        
        # 1. HSET에 요약본 저장
        self.r.hset(date_key, fid, s)
        
        # 2. 메타데이터 저장 (조회 성능 향상용)
        metadata = {
            'date': now.strftime('%Y-%m-%d'),
            'timestamp': now.isoformat(),
            'ttl_days': self.ttl_days
        }
        self.r.setex(
            self._get_metadata_key(fid), 
            self.ttl_days * 86400,  # TTL in seconds
            json.dumps(metadata)
        )
        
        # 3. 날짜별 HSET에도 TTL 설정 (8일로 설정해서 여유 확보)
        self.r.expire(date_key, (self.ttl_days + 1) * 86400)

    def get_summaries_by_date(self, date: datetime) -> Dict[str, str]:
        """특정 날짜의 모든 요약본 조회"""
        date_key = self._get_date_key(date)
        return self.r.hgetall(date_key)

    def get_summary_count_by_date(self, date: datetime) -> int:
        """특정 날짜의 요약본 개수 조회"""
        date_key = self._get_date_key(date)
        return self.r.hlen(date_key)

    def delete_pdf(self, fid: str) -> bool:
        metadata_key = self._get_metadata_key(fid)
        metadata = self.r.get(metadata_key)
        deleted = False

        if metadata:
            meta = json.loads(metadata)
            date_key = f"pdf:summaries:{meta['date']}"
            deleted = bool(self.r.hdel(date_key, fid))
            self.r.delete(metadata_key)
        else:
        # 메타데이터가 없으면 최근 날짜 중 찾아서 삭제
            for i in range(self.ttl_days):
                date = datetime.now(ZoneInfo("Asia/Seoul")) - timedelta(days=i)
                date_key = self._get_date_key(date)
                if self.r.hexists(date_key, fid):
                    deleted = bool(self.r.hdel(date_key, fid))
                    break

    # ✅ 삭제 성공했으면 무조건 로그 남기기
        if deleted:
            self._log_cache_deletion(fid)

        return deleted

    def get_all_file_ids(self) -> List[str]:
        """현재 저장된 모든 file_id 조회"""
        file_ids = []
        pattern = "pdf:summaries:*"
        
        for key in self.r.scan_iter(match=pattern):
            file_ids.extend(self.r.hkeys(key))
        
        return list(set(file_ids))  # 중복 제거

    def cleanup_expired_summaries(self):
        """수동으로 만료된 요약본 정리 (백업용)"""
        cutoff_date = datetime.now(ZoneInfo("Asia/Seoul")) - timedelta(days=self.ttl_days)
        
        # TTL이 지난 날짜의 key들 삭제
        for i in range(30):  # 최대 30일 전까지 확인
            check_date = cutoff_date - timedelta(days=i)
            date_key = self._get_date_key(check_date)
            
            if self.r.exists(date_key):
                self.r.delete(date_key)
                print(f"Deleted expired summaries for {check_date.strftime('%Y-%m-%d')}")

    def get_statistics(self) -> Dict:
        """캐시 통계 정보 조회"""
        stats = {
            'total_summaries': 0,
            'summaries_by_date': {},
            'memory_usage': {},
            'total_memory_bytes': 0
        }
        
        # 날짜별 요약본 개수 집계
        pattern = "pdf:summaries:*"
        for key in self.r.scan_iter(match=pattern):
            date_str = key.split(':')[-1]
            count = self.r.hlen(key)
            stats['summaries_by_date'][date_str] = count
            stats['total_summaries'] += count
            
            # 메모리 사용량 추정
            memory_info = self.r.memory_usage(key)
            if memory_info:
                stats['memory_usage'][date_str] = memory_info
                stats['total_memory_bytes'] += memory_info
        for key in self.r.scan_iter(match="pdf:metadata:*"):
            mem = self.r.memory_usage(key)
            if mem:
                stats['total_memory_bytes'] += mem
                stats['memory_usage'][key] = mem
        return stats

    # 기존 메서드는 비활성화 유지
    def get_chat(self, cid: str) -> Optional[str]:
        return None

    def set_chat(self, cid, s: str):
        pass

    def _log_cache_deletion(self, file_id: str):
        now = datetime.now(ZoneInfo("Asia/Seoul"))
        date_str = now.strftime('%Y-%m-%d')
        date_key = f"cache:deleted:{date_str}"
        entry = f"{file_id}|{now.isoformat()}"
        self.r.rpush(date_key, entry)
        print(f"[LOG] Deleted cache entry for {file_id} → {date_key} / {entry}")

    def delete_all_summaries(self) -> int:
        deleted_count = 0
        for key in self.r.scan_iter(match="pdf:summaries:*"):
            file_ids = self.r.hkeys(key)
            for fid in file_ids:
                self._log_cache_deletion(fid)
            
            deleted_count += self.r.hlen(key)
            self.r.delete(key)

        for key in self.r.scan_iter(match="pdf:metadata:*"):
            self.r.delete(key)
            
        return deleted_count

@lru_cache(maxsize=1)
def get_cache_db() -> "RedisCacheDB":
    return RedisCacheDB()
