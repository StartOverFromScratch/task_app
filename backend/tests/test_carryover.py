from datetime import date, timedelta

import pytest

from tests.conftest import create_task


def create_overdue_task(client, db, days_overdue: int = 3) -> dict:
    past_date = (date.today() - timedelta(days=days_overdue)).isoformat()
    t = create_task(client, due_date=past_date)
    return t


class TestCarryoverCandidates:
    def test_no_candidates_when_no_overdue(self, client):
        future = (date.today() + timedelta(days=3)).isoformat()
        create_task(client, due_date=future)
        res = client.get("/tasks/carryover-candidates")
        assert res.status_code == 200
        assert res.json() == []

    def test_overdue_task_appears_as_candidate(self, client, db):
        t = create_overdue_task(client, db, days_overdue=3)
        res = client.get("/tasks/carryover-candidates")
        candidates = res.json()
        assert len(candidates) == 1
        assert candidates[0]["id"] == t["id"]
        assert candidates[0]["overdue_days"] == 3

    def test_done_task_not_in_candidates(self, client, db):
        t = create_overdue_task(client, db)
        client.post(f"/tasks/{t['id']}/complete", json={})
        res = client.get("/tasks/carryover-candidates")
        assert res.json() == []

    def test_no_due_date_not_in_candidates(self, client):
        create_task(client)  # due_date なし
        res = client.get("/tasks/carryover-candidates")
        assert res.json() == []


class TestCarryoverActions:
    def test_carryover_today(self, client, db):
        t = create_overdue_task(client, db)
        res = client.post(f"/tasks/{t['id']}/carryover", json={"action": "today"})
        assert res.status_code == 200
        updated = res.json()
        assert updated["due_date"] == date.today().isoformat()
        assert updated["status"] == "todo"

    def test_carryover_plus_2d(self, client, db):
        past = date.today() - timedelta(days=5)
        t = create_task(client, due_date=past.isoformat())
        res = client.post(f"/tasks/{t['id']}/carryover", json={"action": "plus_2d"})
        assert res.status_code == 200
        expected = (past + timedelta(days=2)).isoformat()
        assert res.json()["due_date"] == expected
        assert res.json()["status"] == "todo"

    def test_carryover_plus_7d(self, client, db):
        past = date.today() - timedelta(days=5)
        t = create_task(client, due_date=past.isoformat())
        res = client.post(f"/tasks/{t['id']}/carryover", json={"action": "plus_7d"})
        expected = (past + timedelta(days=7)).isoformat()
        assert res.json()["due_date"] == expected

    def test_carryover_needs_redefine(self, client, db):
        t = create_overdue_task(client, db)
        res = client.post(f"/tasks/{t['id']}/carryover", json={"action": "needs_redefine"})
        assert res.status_code == 200
        assert res.json()["status"] == "needs_redefine"

    def test_carryover_removes_from_candidates(self, client, db):
        t = create_overdue_task(client, db)
        client.post(f"/tasks/{t['id']}/carryover", json={"action": "today"})
        res = client.get("/tasks/carryover-candidates")
        assert res.json() == []

    def test_carryover_invalid_action(self, client, db):
        t = create_overdue_task(client, db)
        res = client.post(f"/tasks/{t['id']}/carryover", json={"action": "invalid"})
        assert res.status_code == 422

    def test_carryover_task_not_found(self, client):
        res = client.post("/tasks/9999/carryover", json={"action": "today"})
        assert res.status_code == 404
