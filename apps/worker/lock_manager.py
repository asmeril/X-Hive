import json
import os
import time
import random
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class LockTimeoutError(Exception):
    """Lock acquisition timed out"""
    pass


class LockStaleButBusyError(Exception):
    """Lock is stale but process still running"""
    pass


class LockOwnedByAnotherProcessError(Exception):
    """Lock is owned by another process"""
    pass


class LockManager:
    """
    X-HIVE Lock Manager (v1.1 standard).
    Prevents concurrent execution with XiDeAI_Pro.
    
    Lock file format (JSON):
    {
        "pid": 1234,
        "process_name": "x-hive-worker",
        "created_at_utc": "2026-01-18T10:30:45.123456Z"
    }
    """

    def __init__(self, lock_path: str, timeout: int = 180, stale: int = 600):
        """
        Initialize lock manager.
        
        Args:
            lock_path: Full path to lock file
            timeout: Acquisition timeout in seconds (default: 180)
            stale: Lock stale timeout in seconds (default: 600)
        """
        self.lock_path = Path(lock_path)
        self.timeout = timeout
        self.stale = stale
        self._lock_acquired = False

    def _get_current_pid(self) -> int:
        """Get current process ID"""
        return os.getpid()

    def _create_lock_data(self) -> dict:
        """Create lock data structure"""
        return {
            "pid": self._get_current_pid(),
            "process_name": "x-hive-worker",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
        }

    def _read_lock_file(self) -> Optional[dict]:
        """Read lock file content"""
        try:
            if not self.lock_path.exists():
                return None
            with open(self.lock_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to read lock file: {e}")
            return None

    def _is_lock_stale(self, lock_data: dict) -> bool:
        """Check if lock is stale (older than stale timeout)"""
        try:
            created_at_str = lock_data.get("created_at_utc", "")
            created_at = datetime.fromisoformat(created_at_str)
            age_seconds = (datetime.now(timezone.utc) - created_at).total_seconds()
            return age_seconds > self.stale
        except (ValueError, KeyError):
            logger.warning("Could not parse lock creation time; assuming stale")
            return True

    def _is_process_running(self, pid: int) -> bool:
        """Check if process with given PID is running (Windows-specific)"""
        try:
            import subprocess
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            return str(pid) in result.stdout
        except Exception as e:
            logger.debug(f"Could not check process status: {e}")
            return True

    def _remove_lock_file_with_retry(self, max_retries: int = 10) -> bool:
        """
        Remove lock file with exponential backoff retry logic.
        
        Args:
            max_retries: Maximum number of removal attempts
            
        Returns:
            True if successfully removed; False otherwise
        """
        for attempt in range(max_retries):
            try:
                if self.lock_path.exists():
                    self.lock_path.unlink()
                    logger.info(f"Lock file removed (attempt {attempt + 1})")
                    return True
            except PermissionError:
                backoff = random.uniform(0.2, 0.6)
                logger.debug(f"Lock file busy; retrying in {backoff:.2f}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(backoff)
            except Exception as e:
                logger.error(f"Unexpected error removing lock: {e}")
                return False

        logger.error(f"Failed to remove lock file after {max_retries} attempts")
        return False

    def acquire_lock(self) -> bool:
        """
        Acquire lock with timeout.
        
        Returns:
            True if lock acquired; False otherwise
            
        Raises:
            LockTimeoutError: If timeout exceeded
            LockStaleButBusyError: If lock is stale but process still running
            LockOwnedByAnotherProcessError: If lock owned by another process
        """
        start_time = time.time()
        attempt = 0

        while time.time() - start_time < self.timeout:
            attempt += 1

            if self.lock_path.exists():
                existing_lock = self._read_lock_file()

                if existing_lock:
                    existing_pid = existing_lock.get("pid")
                    is_stale = self._is_lock_stale(existing_lock)

                    if is_stale:
                        if self._is_process_running(existing_pid):
                            raise LockStaleButBusyError(
                                f"Lock is stale but process {existing_pid} still running"
                            )
                        logger.info(f"Removing stale lock (age > {self.stale}s)")
                        if not self._remove_lock_file_with_retry():
                            raise LockTimeoutError("Could not remove stale lock")
                        continue
                    else:
                        current_pid = self._get_current_pid()
                        if existing_pid != current_pid:
                            raise LockOwnedByAnotherProcessError(
                                f"Lock owned by PID {existing_pid} (current: {current_pid})"
                            )

                break

            try:
                self.lock_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.lock_path, "w") as f:
                    json.dump(self._create_lock_data(), f)
                self._lock_acquired = True
                logger.info(f"Lock acquired on attempt {attempt}")
                return True
            except Exception as e:
                logger.debug(f"Failed to create lock (attempt {attempt}): {e}")
                time.sleep(0.1)

        raise LockTimeoutError(f"Failed to acquire lock within {self.timeout}s")

    def release_lock(self) -> bool:
        """
        Release lock.
        
        Returns:
            True if released; False otherwise
        """
        if not self._lock_acquired:
            logger.warning("Lock not acquired by this instance; skipping release")
            return False

        if not self.lock_path.exists():
            logger.warning("Lock file does not exist; nothing to release")
            return False

        lock_data = self._read_lock_file()
        if lock_data and lock_data.get("pid") != self._get_current_pid():
            logger.error(f"Lock owned by PID {lock_data.get('pid')}; cannot release")
            return False

        success = self._remove_lock_file_with_retry()
        if success:
            self._lock_acquired = False
            logger.info("Lock released successfully")
        return success
