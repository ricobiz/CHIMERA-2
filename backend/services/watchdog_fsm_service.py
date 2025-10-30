"""
Watchdog FSM - Finite State Machine for automation execution
Tracks state transitions and prevents infinite loops
"""
import logging
import time
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class FSMState(str, Enum):
    IDLE = "Idle"
    SNAPSHOT = "Snapshot"
    PLAN = "Plan"
    EXECUTE = "Execute"
    VERIFY = "Verify"
    DONE = "Done"
    REPAIR = "Repair"
    ABORT = "Abort"

class WatchdogFSM:
    """
    Watchdog: FSM controller with loop detection
    """
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
        # Thresholds
        self.max_same_scene_hash = 3
        self.max_same_error = 2
        self.hard_timeout_ms = 120000  # 2 minutes
    
    def init_session(self, session_id: str, goal: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize watchdog session"""
        self.sessions[session_id] = {
            "state": FSMState.IDLE,
            "goal": goal,
            "start_time": int(time.time() * 1000),
            "scene_hash_count": {},
            "error_count": {},
            "steps": [],
            "last_scene_hash": None,
            "abort_reason": None
        }
        
        logger.info(f"🐕 Watchdog session {session_id} initialized")
        
        return {
            "session_id": session_id,
            "state": FSMState.IDLE,
            "initialized": True
        }
    
    def transition(
        self,
        session_id: str,
        next_state: FSMState,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transition to next state with validation
        Returns: {ok, state, should_abort, abort_reason}
        """
        if session_id not in self.sessions:
            return {
                "ok": False,
                "error": f"Session {session_id} not initialized in watchdog"
            }
        
        session = self.sessions[session_id]
        current_state = session["state"]
        
        # Check timeout
        elapsed = int(time.time() * 1000) - session["start_time"]
        if elapsed > self.hard_timeout_ms:
            session["state"] = FSMState.ABORT
            session["abort_reason"] = "hard_timeout_exceeded"
            return {
                "ok": True,
                "state": FSMState.ABORT,
                "should_abort": True,
                "abort_reason": "hard_timeout_exceeded"
            }
        
        # Check scene hash loop
        if data and data.get('scene_hash'):
            scene_hash = data['scene_hash']
            session["scene_hash_count"].setdefault(scene_hash, 0)
            session["scene_hash_count"][scene_hash] += 1
            
            if scene_hash == session.get("last_scene_hash"):
                count = session["scene_hash_count"][scene_hash]
                if count >= self.max_same_scene_hash:
                    session["state"] = FSMState.REPAIR
                    return {
                        "ok": True,
                        "state": FSMState.REPAIR,
                        "should_abort": False,
                        "needs_recovery": True,
                        "reason": "same_scene_loop_detected"
                    }
            
            session["last_scene_hash"] = scene_hash
        
        # Check error loop
        if data and data.get('error'):
            error_key = str(data['error'])[:50]
            session["error_count"].setdefault(error_key, 0)
            session["error_count"][error_key] += 1
            
            if session["error_count"][error_key] >= self.max_same_error:
                session["state"] = FSMState.ABORT
                session["abort_reason"] = "same_error_repeated"
                return {
                    "ok": True,
                    "state": FSMState.ABORT,
                    "should_abort": True,
                    "abort_reason": "same_error_repeated"
                }
        
        # Valid transitions
        valid_transitions = {
            FSMState.IDLE: [FSMState.SNAPSHOT],
            FSMState.SNAPSHOT: [FSMState.PLAN],
            FSMState.PLAN: [FSMState.EXECUTE, FSMState.ABORT],
            FSMState.EXECUTE: [FSMState.VERIFY, FSMState.ABORT],
            FSMState.VERIFY: [FSMState.DONE, FSMState.REPAIR, FSMState.EXECUTE],
            FSMState.REPAIR: [FSMState.EXECUTE, FSMState.ABORT],
            FSMState.DONE: [FSMState.IDLE],
            FSMState.ABORT: []
        }
        
        if next_state not in valid_transitions.get(current_state, []):
            logger.warning(f"Invalid transition: {current_state} -> {next_state}")
            return {
                "ok": False,
                "error": f"Invalid transition: {current_state} -> {next_state}"
            }
        
        # Perform transition
        session["state"] = next_state
        session["steps"].append({
            "from": current_state,
            "to": next_state,
            "ts": int(time.time() * 1000)
        })
        
        logger.info(f"🐕 Watchdog {session_id}: {current_state} -> {next_state}")
        
        return {
            "ok": True,
            "state": next_state,
            "should_abort": next_state == FSMState.ABORT,
            "abort_reason": session.get("abort_reason")
        }
    
    def get_status(self, session_id: str) -> Dict[str, Any]:
        """Get current watchdog status"""
        if session_id not in self.sessions:
            return {
                "error": f"Session {session_id} not found",
                "state": FSMState.IDLE
            }
        
        session = self.sessions[session_id]
        elapsed = int(time.time() * 1000) - session["start_time"]
        
        return {
            "session_id": session_id,
            "state": session["state"],
            "elapsed_ms": elapsed,
            "steps_count": len(session["steps"]),
            "scene_hash_counts": session["scene_hash_count"],
            "error_counts": session["error_count"],
            "abort_reason": session.get("abort_reason")
        }
    
    def cleanup(self, session_id: str):
        """Cleanup watchdog session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"🐕 Watchdog session {session_id} cleaned up")


# Global instance
watchdog_fsm = WatchdogFSM()
