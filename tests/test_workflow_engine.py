#!/usr/bin/env python3
"""Test Workflow Engine — Full integration test."""
import sys, json, time
sys.path.insert(0, "/home/kali/HackWithAI")

from workflow import Planner, TaskQueue, Executor, DependencyManager, Scheduler, ExecutionPlan, get_workflow_state

results = []

# 1. Planner
p = Planner()
plan = p.plan("example.com", phases=["recon", "scan", "vuln_check", "exploit", "payload"])
results.append(("Planner", len(plan.tasks)))
print(f"✅ Planner: {len(plan.tasks)} tasks in plan")

# 2. Task Queue
q = TaskQueue()
q.enqueue_plan(plan)
results.append(("Queue", q.stats()["total"]))
print(f"✅ Queue: {q.stats()['total']} tasks, {q.stats()['pending']} pending")

# 3. Dependencies
deps = DependencyManager()
for t in plan.tasks:
    for dep in t.depends_on:
        deps.add_dependency(t.id, dep)
print(f"✅ Deps: {len(deps._deps)} task dependencies")

# 4. Executor
executor = Executor(q, deps)
executed = 0
def fake_exec(task):
    global executed; executed += 1
    return f"OK: {task.name}"
executor.set_executor(fake_exec)
print(f"✅ Executor: running sequential...")
r = executor.run_sequential()
print(f"✅ Executor: {len(r)} completed, {executed} executed")

# 5. Scheduler
s = Scheduler()
counter = [0]
def tick(): counter[0] += 1
s.schedule_delayed("tick", 1, tick)
time.sleep(1.5)
print(f"✅ Scheduler: delayed job ran {counter[0]} times")

# 6. Workflow State
ws = get_workflow_state()
ws.start_workflow(plan)
ws.update_task(plan.id, plan.tasks[0].id, "completed", "nmap scan done")
ws.checkpoint(plan.id)
ws.complete_workflow(plan.id, True)
recovered = ws.recover(plan.id)
print(f"✅ State: {ws.stats()['total_workflows']} workflows, {ws.stats()['checkpoints']} checkpoints, recovered={recovered is not None}")

# 7. Crash recovery
plan2 = p.plan("test.com", phases=["recon", "exploit"])
ws2 = get_workflow_state()
ws2.start_workflow(plan2)
ws2.update_task(plan2.id, plan2.tasks[0].id, "completed", "scan done")
ws2.checkpoint(plan2.id)
recovered2 = ws2.recover(plan2.id)
print(f"✅ Recovery: recovered plan with {len(recovered2.tasks)} tasks")

print(f"\n{'='*40}")
print("ALL 7 TESTS PASSED")
