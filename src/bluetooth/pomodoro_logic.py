import json
import threading
import time
from datetime import datetime, date
from typing import Dict

class PomodoroTask:
    def __init__(self, task_id: str, name: str, work_minutes: int = 25, break_minutes: int = 5):
        self.task_id = task_id
        self.name = name
        self.work_minutes = work_minutes
        self.break_minutes = break_minutes
        self.stats = {
            "total_sessions": 0,
            "today_sessions": 0,
            "last_session_at": None,
            "is_running": False,
        }
        self._timer = None
        self._stop_event = threading.Event()

    def start_session(self, phase: str = "work") -> dict:
        if self.stats["is_running"]:
            return {"error": "Already running"}

        self.stats["is_running"] = True
        duration = self.work_minutes if phase == "work" else self.break_minutes

        def run_timer():
            print(f"⏱️  [Task {self.task_id}] Starting {phase} for {duration} minutes...")
            time.sleep(duration * 60)  # Simulasi — nanti ganti dengan timer real
            if not self._stop_event.is_set():
                self._on_session_end(phase)

        self._timer = threading.Thread(target=run_timer, daemon=True)
        self._timer.start()
        return {"status": "started", "phase": phase, "duration_min": duration}

    def _on_session_end(self, phase: str):
        self.stats["is_running"] = False
        self.stats["total_sessions"] += 1
        self.stats["last_session_at"] = datetime.now().isoformat()

        # Reset today_sessions tiap hari
        today = date.today().isoformat()
        if not self.stats.get("last_reset_day") or self.stats["last_reset_day"] != today:
            self.stats["today_sessions"] = 0
            self.stats["last_reset_day"] = today
        self.stats["today_sessions"] += 1

        print(f"✅ [Task {self.task_id}] {phase.capitalize()} session ended. Total: {self.stats['total_sessions']}")

        if hasattr(self, "_on_update_callback"):
            self._on_update_callback(self.to_dict())

    def stop_session(self):
        if self._timer and self._timer.is_alive():
            self._stop_event.set()
            self._timer.join(timeout=0.1)
        self.stats["is_running"] = False
        print(f"⏹️  [Task {self.task_id}] Session stopped.")

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "work_minutes": self.work_minutes,
            "break_minutes": self.break_minutes,
            "stats": self.stats,
        }

class PomodoroManager:
    def __init__(self):
        self.tasks: Dict[str, PomodoroTask] = {}
        self._on_task_update = None

    def set_update_callback(self, callback):
        self._on_task_update = callback

    def create_or_get_task(self, task_id: str, name: str, work: int = 25, break_min: int = 5) -> PomodoroTask:
        if task_id not in self.tasks:
            self.tasks[task_id] = PomodoroTask(task_id, name, work, break_min)
            # Bind callback
            self.tasks[task_id]._on_update_callback = self._on_task_update
        return self.tasks[task_id]

    def handle_command(self, cmd: dict) -> dict:
        try:
            action = cmd.get("cmd")
            task_id = cmd.get("task_id", "default")
            name = cmd.get("name", "Unnamed Task")

            task = self.create_or_get_task(
                task_id,
                name,
                cmd.get("work_minutes", 25),
                cmd.get("break_minutes", 5)
            )

            if action == "start_pomodoro":
                return task.start_session("work")
            elif action == "start_break":
                return task.start_session("break")
            elif action == "stop":
                task.stop_session()
                return {"status": "stopped"}
            elif action == "get_stats":
                return task.to_dict()
            else:
                return {"error": f"Unknown command: {action}"}
        except Exception as e:
            return {"error": str(e)}