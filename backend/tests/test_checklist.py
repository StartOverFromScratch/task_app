import pytest

from tests.conftest import create_task


class TestChecklist:
    def test_create_checklist_item(self, client):
        t = create_task(client)
        res = client.post(f"/tasks/{t['id']}/checklist", json={"text": "手順1"})
        assert res.status_code == 201
        item = res.json()
        assert item["text"] == "手順1"
        assert item["is_done"] is False
        assert item["task_id"] == t["id"]

    def test_create_multiple_items_auto_order(self, client):
        t = create_task(client)
        client.post(f"/tasks/{t['id']}/checklist", json={"text": "手順1"})
        client.post(f"/tasks/{t['id']}/checklist", json={"text": "手順2"})
        res = client.get(f"/tasks/{t['id']}/checklist")
        items = res.json()
        assert len(items) == 2
        assert items[0]["order_no"] < items[1]["order_no"]

    def test_get_checklist(self, client):
        t = create_task(client)
        client.post(f"/tasks/{t['id']}/checklist", json={"text": "確認A"})
        client.post(f"/tasks/{t['id']}/checklist", json={"text": "確認B"})
        res = client.get(f"/tasks/{t['id']}/checklist")
        assert res.status_code == 200
        assert len(res.json()) == 2

    def test_update_checklist_item_done(self, client):
        t = create_task(client)
        item = client.post(f"/tasks/{t['id']}/checklist", json={"text": "作業X"}).json()
        res = client.patch(f"/tasks/{t['id']}/checklist/{item['id']}", json={"is_done": True})
        assert res.status_code == 200
        assert res.json()["is_done"] is True

    def test_update_checklist_item_text(self, client):
        t = create_task(client)
        item = client.post(f"/tasks/{t['id']}/checklist", json={"text": "旧テキスト"}).json()
        res = client.patch(f"/tasks/{t['id']}/checklist/{item['id']}", json={"text": "新テキスト"})
        assert res.json()["text"] == "新テキスト"

    def test_update_checklist_item_not_found(self, client):
        t = create_task(client)
        res = client.patch(f"/tasks/{t['id']}/checklist/9999", json={"is_done": True})
        assert res.status_code == 404

    def test_checklist_appears_in_task_detail(self, client):
        t = create_task(client)
        client.post(f"/tasks/{t['id']}/checklist", json={"text": "詳細確認"})
        res = client.get(f"/tasks/{t['id']}")
        assert len(res.json()["checklist"]) == 1


class TestExtract:
    def test_extract_creates_child_task(self, client):
        t = create_task(client)
        item = client.post(f"/tasks/{t['id']}/checklist", json={"text": "切り出しアイテム"}).json()

        res = client.post(f"/tasks/{t['id']}/checklist/{item['id']}/extract", json={})
        assert res.status_code == 201
        data = res.json()
        extracted = data["extracted_task"]
        checklist_item = data["checklist_item"]

        assert extracted["parent_id"] == t["id"]
        assert extracted["title"] == "切り出しアイテム"  # デフォルトはitemのtext
        assert extracted["origin_checklist_item_id"] == item["id"]
        assert checklist_item["is_done"] is True
        assert checklist_item["extracted_task_id"] == extracted["id"]

    def test_extract_with_custom_title(self, client):
        t = create_task(client)
        item = client.post(f"/tasks/{t['id']}/checklist", json={"text": "元テキスト"}).json()
        res = client.post(
            f"/tasks/{t['id']}/checklist/{item['id']}/extract",
            json={"title": "カスタムタイトル", "task_type": "research"},
        )
        assert res.json()["extracted_task"]["title"] == "カスタムタイトル"
        assert res.json()["extracted_task"]["task_type"] == "research"

    def test_extract_already_extracted_fails(self, client):
        t = create_task(client)
        item = client.post(f"/tasks/{t['id']}/checklist", json={"text": "再切り出し"}).json()
        client.post(f"/tasks/{t['id']}/checklist/{item['id']}/extract", json={})
        res = client.post(f"/tasks/{t['id']}/checklist/{item['id']}/extract", json={})
        assert res.status_code == 400

    def test_extracted_item_not_blocking_complete(self, client):
        t = create_task(client)
        item = client.post(f"/tasks/{t['id']}/checklist", json={"text": "切り出すやつ"}).json()
        client.post(f"/tasks/{t['id']}/checklist/{item['id']}/extract", json={})
        # 切り出し済みアイテムは完了のブロッカーにならない
        res = client.post(f"/tasks/{t['id']}/complete", json={})
        assert res.status_code == 201

    def test_extract_inherits_parent_priority(self, client):
        t = create_task(client, priority="should")
        item = client.post(f"/tasks/{t['id']}/checklist", json={"text": "優先度継承"}).json()
        res = client.post(f"/tasks/{t['id']}/checklist/{item['id']}/extract", json={})
        assert res.json()["extracted_task"]["priority"] == "should"

    def test_extracted_task_appears_in_origin(self, client):
        t = create_task(client)
        item = client.post(f"/tasks/{t['id']}/checklist", json={"text": "originテスト"}).json()
        extract_res = client.post(f"/tasks/{t['id']}/checklist/{item['id']}/extract", json={})
        extracted_id = extract_res.json()["extracted_task"]["id"]

        detail = client.get(f"/tasks/{extracted_id}").json()
        assert detail["origin"] is not None
        assert detail["origin"]["parent_task_id"] == t["id"]
        assert detail["origin"]["checklist_item_text"] == "originテスト"
