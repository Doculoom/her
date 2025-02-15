import datetime
import json
import threading
from typing import Optional

from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2

from app.core.config import settings
from app.services.firestore.tasks_service import FirestoreTasksService

tasks_service = FirestoreTasksService()


def background_delete_task_mapping(task_id: str):
    tasks_service.delete_task_mapping(task_id)


def add_to_cloud_tasks(
    payload: dict,
    task_type: str,
    timestamp: Optional[datetime.datetime] = None,
    task_id: str = None,
):
    client = tasks_v2.CloudTasksClient()
    project, location, queue = (
        settings.GCP_PROJECT_ID,
        settings.GCP_LOCATION,
        settings.CLOUD_TASKS_QUEUE,
    )
    parent = client.queue_path(project, location, queue)

    if task_type == "queue":
        endpoint_url = settings.HER_API_URL + "api/v1/queue"
    elif task_type == "summarize":
        endpoint_url = settings.HER_API_URL + "api/v1/summarize"
    elif task_type == "respond":
        endpoint_url = settings.HER_API_URL + "api/v1/respond"
    else:
        raise ValueError("Unsupported task type")

    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": endpoint_url,
        }
    }

    if payload is not None:
        if isinstance(payload, dict):
            payload_str = json.dumps(payload)
            task["http_request"]["headers"] = {"Content-type": "application/json"}
        else:
            payload_str = payload
        task["http_request"]["body"] = payload_str.encode()

    if timestamp is not None:
        schedule_time = timestamp_pb2.Timestamp()
        schedule_time.FromDatetime(timestamp)
        task["schedule_time"] = schedule_time

    response = client.create_task(request={"parent": parent, "task": task})

    if task_id:
        tasks_service.set_task_mapping(
            task_id, {"task_name": response.name, "expires_at": timestamp.isoformat()}
        )

    return response


def reschedule_cloud_task(
    task_id: str,
    payload: dict,
    task_type: str,
    timestamp: Optional[datetime.datetime] = None,
):
    client = tasks_v2.CloudTasksClient()
    mapping = tasks_service.get_task_mapping(task_id)
    if mapping and "task_name" in mapping:
        stored_task_name = mapping["task_name"]
        stored_expires_at_str = mapping.get("expires_at")
        should_delete = True

        if stored_expires_at_str:
            stored_expires_at = datetime.datetime.fromisoformat(stored_expires_at_str)
            if datetime.datetime.utcnow() >= stored_expires_at:
                should_delete = False

        if should_delete:
            try:
                client.delete_task(name=stored_task_name)
                print(f"Deleted previous task: {stored_task_name}")
            except Exception as e:
                print(f"Error deleting task {stored_task_name}: {e}")
            threading.Thread(
                target=background_delete_task_mapping, args=(task_id,), daemon=True
            ).start()
        else:
            print(
                f"Skipping deletion for task '{stored_task_name}' because current time "
                f"is >= stored expiration ({stored_expires_at.isoformat()})."
            )

    return add_to_cloud_tasks(
        payload=payload, task_type=task_type, timestamp=timestamp, task_id=task_id
    )
