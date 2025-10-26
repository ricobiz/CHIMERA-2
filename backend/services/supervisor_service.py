"""
Mission Supervisor Service
Управляет выполнением миссии автоматизации на высоком уровне
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class MissionSupervisor:
    """
    Супервизор миссии - следит за выполнением глобальной задачи
    
    Статусы миссии:
    - "in_progress": миссия выполняется
    - "completed": миссия успешно завершена
    - "needs_human": требуется вмешательство человека
    - "failed": миссия провалена (критическая ошибка)
    """
    
    def __init__(self):
        self.current_mission: Optional[Dict[str, Any]] = None
        self.mission_history: List[Dict[str, Any]] = []
        
    def start_mission(self, goal: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Начать новую миссию"""
        if not job_id:
            job_id = str(uuid.uuid4())
            
        self.current_mission = {
            "job_id": job_id,
            "goal": goal,
            "mission_status": "in_progress",
            "steps": [],
            "retry_count": {},  # Счетчик попыток для каждого шага
            "human_help_reason": None,
            "result_bundle": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"🎯 Mission started: {goal} (job_id: {job_id})")
        return self.current_mission
    
    def add_step(self, step_result: Dict[str, Any]) -> None:
        """Добавить результат выполнения шага"""
        if not self.current_mission:
            logger.warning("No active mission to add step to")
            return
            
        # Unified step format validation
        required_fields = ['success', 'confidence', 'step_name']
        if not all(field in step_result for field in required_fields):
            logger.error(f"Step result missing required fields: {step_result}")
            return
        
        # Добавляем timestamp если его нет
        if 'timestamp' not in step_result:
            step_result['timestamp'] = datetime.utcnow().isoformat()
        
        self.current_mission['steps'].append(step_result)
        self.current_mission['updated_at'] = datetime.utcnow().isoformat()
        
        # Проверяем на зацикливание
        step_name = step_result.get('step_name', 'unknown')
        if not step_result.get('success', False):
            # Увеличиваем счетчик неудач для этого шага
            if step_name not in self.current_mission['retry_count']:
                self.current_mission['retry_count'][step_name] = 0
            self.current_mission['retry_count'][step_name] += 1
            
            # Если шаг не удался много раз - помечаем как needs_human
            if self.current_mission['retry_count'][step_name] >= 3:
                self._mark_needs_human(
                    f"Не удалось выполнить шаг '{step_name}' после 3 попыток. "
                    f"Последняя ошибка: {step_result.get('details', {}).get('error', 'Unknown')}"
                )
        
        logger.info(f"📝 Step added: {step_name} - {'✅' if step_result['success'] else '❌'}")
    
    def _mark_needs_human(self, reason: str) -> None:
        """Пометить миссию как требующую вмешательства человека"""
        if not self.current_mission:
            return
            
        self.current_mission['mission_status'] = 'needs_human'
        self.current_mission['human_help_reason'] = reason
        self.current_mission['updated_at'] = datetime.utcnow().isoformat()
        
        logger.warning(f"🤔 Mission needs human: {reason}")
    
    def mark_captcha_challenge(self, details: str) -> None:
        """Отметить встречу с капчей (не ошибка!)"""
        self._mark_needs_human(f"Требуется пройти капчу: {details}")
    
    def mark_sms_required(self, details: str) -> None:
        """Отметить необходимость SMS кода"""
        self._mark_needs_human(f"Требуется SMS код: {details}")
    
    def mark_completed(self, result_bundle: Optional[Dict[str, Any]] = None) -> None:
        """Отметить успешное завершение миссии"""
        if not self.current_mission:
            return
            
        self.current_mission['mission_status'] = 'completed'
        self.current_mission['result_bundle'] = result_bundle
        self.current_mission['updated_at'] = datetime.utcnow().isoformat()
        
        # Добавляем в историю
        self.mission_history.append(self.current_mission.copy())
        
        logger.info(f"✅ Mission completed: {self.current_mission['goal']}")
    
    def mark_failed(self, reason: str) -> None:
        """Отметить критическую ошибку миссии"""
        if not self.current_mission:
            return
            
        self.current_mission['mission_status'] = 'failed'
        self.current_mission['human_help_reason'] = f"Критическая ошибка: {reason}"
        self.current_mission['updated_at'] = datetime.utcnow().isoformat()
        
        # Добавляем в историю
        self.mission_history.append(self.current_mission.copy())
        
        logger.error(f"❌ Mission failed: {reason}")
    
    def get_current_mission(self) -> Optional[Dict[str, Any]]:
        """Получить текущую миссию"""
        return self.current_mission
    
    def create_result_bundle(
        self,
        credentials: Optional[Dict[str, str]] = None,
        proof: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Создать бандл результатов миссии
        
        Args:
            credentials: {"login": "...", "password": "..."}
            proof: {"final_url": "...", "screenshot": "..."}
            notes: Дополнительные заметки
        """
        bundle = {
            "credentials": credentials or {},
            "proof": proof or {},
            "notes": notes or "",
            "created_at": datetime.utcnow().isoformat()
        }
        
        if self.current_mission:
            self.current_mission['result_bundle'] = bundle
            
        return bundle
    
    def get_mission_report(self) -> Dict[str, Any]:
        """Получить детальный отчет о миссии"""
        if not self.current_mission:
            return {
                "active": False,
                "message": "No active mission"
            }
        
        total_steps = len(self.current_mission['steps'])
        successful_steps = sum(1 for s in self.current_mission['steps'] if s.get('success', False))
        
        return {
            "active": True,
            "job_id": self.current_mission['job_id'],
            "goal": self.current_mission['goal'],
            "mission_status": self.current_mission['mission_status'],
            "human_help_reason": self.current_mission['human_help_reason'],
            "progress": {
                "total_steps": total_steps,
                "successful_steps": successful_steps,
                "failed_steps": total_steps - successful_steps,
                "progress_percent": int((successful_steps / max(total_steps, 1)) * 100)
            },
            "result_ready": self.current_mission['result_bundle'] is not None,
            "created_at": self.current_mission['created_at'],
            "updated_at": self.current_mission['updated_at']
        }
    
    def should_continue(self) -> bool:
        """Проверить, можно ли продолжать выполнение"""
        if not self.current_mission:
            return False
            
        status = self.current_mission['mission_status']
        return status == 'in_progress'
    
    def get_step_count(self) -> int:
        """Получить количество выполненных шагов"""
        if not self.current_mission:
            return 0
        return len(self.current_mission['steps'])

# Global instance
mission_supervisor = MissionSupervisor()
