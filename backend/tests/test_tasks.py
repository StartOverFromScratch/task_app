from datetime import datetime, timedelta

import pytest

from tests.conftest import create_task


class TestTaskCRUD:
    def test_create_task(self, client):
        res = client.post(
            "/tasks",
            json={
                "title": "タスクA",
                "task_type": "execution",
                "priority": "must",
                "done_criteria": "完了基準",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == "タスクA"
        assert data["status"] == "todo"
        assert data["task_type"] == "execution"

    def test_create_task_missing_required(self, client):
        res = client.post("/tasks", json={"title": "不完全"})
        assert res.status_code == 422

    def test_get_tasks(self, client):
        create_task(client, title="T1")
        create_task(client, title="T2")
        res = client.get("/tasks")
        assert res.status_code == 200
        assert len(res.json()) == 2

    def test_get_tasks_filter_status(self, client):
        t = create_task(client)
        client.patch(f"/tasks/{t['id']}", json={"status": "doing"})
        res = client.get("/tasks?status=doing")
        assert res.status_code == 200
        assert len(res.json()) == 1

    def test_get_tasks_filter_priority(self, client):
        create_task(client, priority="must")
        create_task(client, priority="should")
        res = client.get("/tasks?priority=must")
        assert len(res.json()) == 1

    def test_get_task_detail(self, client):
        t = create_task(client)
        res = client.get(f"/tasks/{t['id']}")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == t["id"]
        assert "children" in data
        assert "checklist" in data

    def test_get_task_not_found(self, client):
        res = client.get("/tasks/9999")
        assert res.status_code == 404

    def test_update_task(self, client):
        t = create_task(client)
        res = client.patch(f"/tasks/{t['id']}", json={"title": "更新後", "status": "doing"})
        assert res.status_code == 200
        assert res.json()["title"] == "更新後"
        assert res.json()["status"] == "doing"

    def test_update_task_status_done_forbidden(self, client):
        t = create_task(client)
        res = client.patch(f"/tasks/{t['id']}", json={"status": "done"})
        assert res.status_code == 400

    def test_delete_task(self, client):
        t = create_task(client)
        res = client.delete(f"/tasks/{t['id']}")
        assert res.status_code == 204
        assert client.get(f"/tasks/{t['id']}").status_code == 404

    def test_delete_task_not_found(self, client):
        res = client.delete("/tasks/9999")
        assert res.status_code == 404


class TestChildren:
    def test_get_children_empty(self, client):
        t = create_task(client)
        res = client.get(f"/tasks/{t['id']}/children")
        assert res.status_code == 200
        assert res.json() == []

    def test_create_child(self, client):
        parent = create_task(client, title="親タスク")
        res = client.post(
            f"/tasks/{parent['id']}/children",
            json={
                "title": "子タスク",
                "task_type": "execution",
                "priority": "must",
                "done_criteria": "子の完了基準",
            },
        )
        assert res.status_code == 201
        child = res.json()
        assert child["parent_id"] == parent["id"]

    def test_children_appear_in_detail(self, client):
        parent = create_task(client)
        client.post(
            f"/tasks/{parent['id']}/children",
            json={"title": "子", "task_type": "execution", "priority": "must", "done_criteria": "基準"},
        )
        res = client.get(f"/tasks/{parent['id']}")
        assert len(res.json()["children"]) == 1


class TestComplete:
    def test_complete_task(self, client):
        t = create_task(client)
        res = client.post(f"/tasks/{t['id']}/complete", json={})
        assert res.status_code == 201
        log = res.json()
        assert log["task_id"] == t["id"]
        assert client.get(f"/tasks/{t['id']}").json()["status"] == "done"

    def test_complete_with_note(self, client):
        t = create_task(client)
        res = client.post(f"/tasks/{t['id']}/complete", json={"note": "完了メモ"})
        assert res.status_code == 201
        assert res.json()["note"] == "完了メモ"

    def test_complete_blocked_by_uncompleted_checklist(self, client):
        t = create_task(client)
        client.post(f"/tasks/{t['id']}/checklist", json={"text": "未完了アイテム"})
        res = client.post(f"/tasks/{t['id']}/complete", json={})
        assert res.status_code == 400

    def test_complete_allowed_when_checklist_done(self, client):
        t = create_task(client)
        item_res = client.post(f"/tasks/{t['id']}/checklist", json={"text": "アイテム"})
        item_id = item_res.json()["id"]
        client.patch(f"/tasks/{t['id']}/checklist/{item_id}", json={"is_done": True})
        res = client.post(f"/tasks/{t['id']}/complete", json={})
        assert res.status_code == 201

    def test_get_completion_log(self, client):
        t = create_task(client)
        client.post(f"/tasks/{t['id']}/complete", json={"note": "ログテスト"})
        res = client.get(f"/tasks/{t['id']}/completion-log")
        assert res.status_code == 200
        logs = res.json()
        assert len(logs) == 1
        assert logs[0]["note"] == "ログテスト"


class TestConvergence:
    def test_convergence_no_limit(self, client):
        t = create_task(client, task_type="research")
        res = client.get(f"/tasks/{t['id']}/convergence")
        assert res.status_code == 200
        data = res.json()
        assert data["exploration_used"] == 0
        assert data["exploration_remaining"] is None
        assert data["convergence_checklist"]["options_within_limit"] is True

    def test_convergence_with_limit_not_exceeded(self, client):
        t = create_task(client, task_type="research", exploration_limit=3, reversible=True)
        res = client.get(f"/tasks/{t['id']}/convergence")
        data = res.json()
        assert data["exploration_limit"] == 3
        assert data["exploration_remaining"] == 3
        assert data["is_convergeable"] is True

    def test_convergence_limit_exceeded(self, client):
        t = create_task(client, task_type="research", exploration_limit=2)
        for i in range(3):
            client.post(
                f"/tasks/{t['id']}/children",
                json={"title": f"子{i}", "task_type": "research", "priority": "must", "done_criteria": "基準"},
            )
        res = client.get(f"/tasks/{t['id']}/convergence")
        data = res.json()
        assert data["exploration_used"] == 3
        assert data["convergence_checklist"]["options_within_limit"] is False
        assert data["is_convergeable"] is False


class TestStale:
    def test_stale_tasks(self, client, db):
        t = create_task(client, priority="must")
        # last_updated_at を過去に書き換え
        from app.models.task import Task
        task = db.get(Task, t["id"])
        task.last_updated_at = datetime.utcnow() - timedelta(days=8)
        db.commit()

        res = client.get("/tasks/stale")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["stale_days"] >= 8
        assert data[0]["threshold_days"] == 7

    def test_not_stale_within_threshold(self, client):
        create_task(client, priority="must")
        res = client.get("/tasks/stale")
        assert res.status_code == 200
        assert len(res.json()) == 0

    def test_stale_filter_by_priority(self, client, db):
        from app.models.task import Task

        t_must = create_task(client, priority="must")
        t_should = create_task(client, priority="should")

        for task_id in [t_must["id"], t_should["id"]]:
            task = db.get(Task, task_id)
            task.last_updated_at = datetime.utcnow() - timedelta(days=30)
            db.commit()

        res = client.get("/tasks/stale?priority=must")
        assert all(t["priority"] == "must" for t in res.json())


class TestCaptures:
    def test_create_capture(self, client):
        res = client.post("/captures", json={"text": "分岐メモ"})
        assert res.status_code == 201
        assert res.json()["text"] == "分岐メモ"
        assert res.json()["is_resolved"] is False

    def test_list_captures(self, client):
        client.post("/captures", json={"text": "A"})
        client.post("/captures", json={"text": "B"})
        res = client.get("/captures")
        assert len(res.json()) == 2

    def test_list_captures_filter_resolved(self, client):
        r = client.post("/captures", json={"text": "未解決"}).json()
        client.patch(f"/captures/{r['id']}", json={"is_resolved": True})
        client.post("/captures", json={"text": "新しい未解決"})
        res = client.get("/captures?is_resolved=false")
        assert all(not c["is_resolved"] for c in res.json())

    def test_update_capture(self, client):
        r = client.post("/captures", json={"text": "元テキスト"}).json()
        res = client.patch(f"/captures/{r['id']}", json={"text": "更新", "is_resolved": True})
        assert res.json()["text"] == "更新"
        assert res.json()["is_resolved"] is True

    def test_delete_capture(self, client):
        r = client.post("/captures", json={"text": "消すやつ"}).json()
        assert client.delete(f"/captures/{r['id']}").status_code == 204
        assert client.get("/captures").json() == []

    def test_capture_with_related_task(self, client):
        t = create_task(client)
        res = client.post("/captures", json={"text": "関連メモ", "related_task_id": t["id"]})
        assert res.json()["related_task_id"] == t["id"]
