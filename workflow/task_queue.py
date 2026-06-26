#!/usr/bin/env python3
"""Task Queue + Executor + Dependency Manager — Queue, execute, track dependencies."""

import json, threading, time, queue
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Callable
from collections import defaultdict

from .planner import Task, ExecutionPlan

DATA_DIR = Path("/home/kali/HackWithAI/data/logs/workflow")
DATA_DIR.mkdir(parents=True, exist_ok=True)


class TaskQueue:
    """Priority queue with retry, timeout, and status tracking."""

    def __init__(self):
        self._queue: queue.PriorityQueue = queue.PriorityQueue()
        self._tasks: Dict[str, Task] = {}
        self._results: Dict[str, str] = {}
        self._history: List[Dict] = []
        self._lock = threading.Lock()

    def enqueue(self, task: Task):
        with self._lock:
            self._tasks[task.id] = task
            self._queue.put((-task.priority, task.id))

    def enqueue_plan(self, plan: ExecutionPlan):
        for task in plan.tasks:
            self.enqueue(task)

    def dequeue(self) -> Optional[Task]:
        try:
            _, tid = self._queue.get_nowait()
            with self._lock:
                task = self._tasks.get(tid)
                if task:
                    task.status = "running"
                    task.started = datetime.now().isoformat()
                return task
        except queue.Empty:
            return None

    def complete(self, task_id: str, result: str = "", success: bool = True):
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.status = "completed" if success else "failed"
                task.result = result[:1000]
                task.completed = datetime.now().isoformat()
                self._results[task_id] = result[:1000]
                self._history.append({"task_id": task_id, "status": task.status,
                                      "completed": task.completed})

    def retry(self, task_id: str) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            if task and task.max_retries > 0:
                task.max_retries -= 1
                task.status = "pending"
                self._queue.put((-task.priority, task_id))
                return True
        return False

    def status(self, task_id: str) -> str:
        task = self._tasks.get(task_id)
        return task.status if task else "unknown"

    def stats(self) -> Dict:
        with self._lock:
            statuses = defaultdict(int)
            for t in self._tasks.values():
                statuses[t.status] += 1
            return {
                "total": len(self._tasks),
                "by_status": dict(statuses),
                "completed": len([t for t in self._tasks.values() if t.status == "completed"]),
                "pending": self._queue.qsize(),
                "history": len(self._history),
            }


class DependencyManager:
    """Tracks task dependencies and determines execution order."""

    def __init__(self):
        self._deps: Dict[str, List[str]] = {}
        self._completed: set = set()

    def add_dependency(self, task_id: str, depends_on: str):
        if task_id not in self._deps:
            self._deps[task_id] = []
        self._deps[task_id].append(depends_on)

    def mark_complete(self, task_id: str):
        self._completed.add(task_id)

    def is_ready(self, task_id: str) -> bool:
        deps = self._deps.get(task_id, [])
        return all(d in self._completed for d in deps)

    def get_blocked(self) -> List[str]:
        return [tid for tid in self._deps if not self.is_ready(tid) and tid not in self._completed]

    def reset(self):
        self._deps.clear()
        self._completed.clear()


class Executor:
    """Executes tasks from queue with parallel/sequential support and retry logic."""

    def __init__(self, queue: TaskQueue, deps: DependencyManager):
        self.queue = queue
        self.deps = deps
        self.executor_fn: Optional[Callable] = None
        self.results: List[Dict] = []

    def set_executor(self, fn: Callable):
        """Set custom execution function: fn(task) -> str."""
        self.executor_fn = fn

    def run_sequential(self) -> List[Dict]:
        """Run all queued tasks sequentially respecting dependencies."""
        results = []
        max_iterations = len(self.queue._tasks) * 3

        for _ in range(max_iterations):
            task = self.queue.dequeue()
            if not task:
                break

            # Check dependencies
            if not self.deps.is_ready(task.id):
                self.queue.enqueue(task)
                time.sleep(0.1)
                continue

            # Execute
            start = time.time()
            try:
                if self.executor_fn:
                    output = self.executor_fn(task)
                else:
                    output = f"Task {task.name}: executed (no custom executor)"

                self.queue.complete(task.id, output, True)
                self.deps.mark_complete(task.id)
                results.append({"task_id": task.id, "status": "completed",
                               "output": output[:200], "duration_ms": int((time.time() - start) * 1000)})
            except Exception as e:
                if self.queue.retry(task.id):
                    results.append({"task_id": task.id, "status": "retrying", "error": str(e)})
                else:
                    self.queue.complete(task.id, str(e), False)
                    results.append({"task_id": task.id, "status": "failed", "error": str(e)})

        return results

    def run_parallel(self, max_workers: int = 4) -> List[Dict]:
        """Run tasks in parallel using threads, respecting dependencies."""
        results = []
        active: Dict[str, threading.Thread] = {}

        all_tasks = list(self.queue._tasks.values())
        all_tasks.sort(key=lambda t: t.priority, reverse=True)

        while all_tasks or active:
            # Clean up completed threads
            for tid, t in list(active.items()):
                if not t.is_alive():
                    t.join()
                    del active[tid]

            # Enqueue ready tasks
            for task in list(all_tasks):
                if len(active) < max_workers and self.deps.is_ready(task.id) and task.status == "pending":
                    task.status = "running"
                    task.started = datetime.now().isoformat()
                    t = threading.Thread(target=self._execute_one, args=(task, results))
                    t.start()
                    active[task.id] = t
                    all_tasks.remove(task)

            time.sleep(0.1)

        return results

    def _execute_one(self, task: Task, results: List):
        start = time.time()
        try:
            output = self.executor_fn(task) if self.executor_fn else f"Executed: {task.name}"
            self.queue.complete(task.id, output, True)
            self.deps.mark_complete(task.id)
            results.append({"task_id": task.id, "status": "completed",
                           "duration_ms": int((time.time() - start) * 1000)})
        except Exception as e:
            if not self.queue.retry(task.id):
                self.queue.complete(task.id, str(e), False)
                results.append({"task_id": task.id, "status": "failed", "error": str(e)})


class Scheduler:
    """Supports immediate, delayed, and recurring job scheduling."""

    def __init__(self):
        self.jobs: Dict[str, Dict] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def schedule_now(self, name: str, fn: Callable, *args):
        """Execute immediately in a thread."""
        t = threading.Thread(target=fn, args=args, daemon=True)
        t.start()
        self.jobs[name] = {"type": "immediate", "started": datetime.now().isoformat()}

    def schedule_delayed(self, name: str, delay_seconds: int, fn: Callable, *args):
        """Schedule after a delay."""
        def delayed():
            time.sleep(delay_seconds)
            fn(*args)
        t = threading.Thread(target=delayed, daemon=True)
        t.start()
        self.jobs[name] = {"type": "delayed", "delay_s": delay_seconds,
                           "scheduled": datetime.now().isoformat()}

    def schedule_recurring(self, name: str, interval_seconds: int, fn: Callable, *args):
        """Schedule recurring execution."""
        def recurring():
            while self._running:
                fn(*args)
                time.sleep(interval_seconds)
        t = threading.Thread(target=recurring, daemon=True)
        t.start()
        self.jobs[name] = {"type": "recurring", "interval_s": interval_seconds,
                           "scheduled": datetime.now().isoformat()}

    def start(self):
        self._running = True

    def stop(self):
        self._running = False

    def stats(self) -> Dict:
        return {"jobs": {k: v["type"] for k, v in self.jobs.items()}, "running": self._running}
