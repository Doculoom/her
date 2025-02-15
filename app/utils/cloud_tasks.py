import datetime
import json
from typing import Optional

from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2

from app.core.config import settings


def add_to_cloud_tasks(
    payload: dict,
    task_type: str,
    timestamp: Optional[datetime] = None,
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

    if task_id:
        task_name = client.task_path(project, location, queue, task_id)
        task["name"] = task_name

    if payload is not None:
        if isinstance(payload, dict):
            payload = json.dumps(payload)
            task["http_request"]["headers"] = {"Content-type": "application/json"}

        converted_payload = payload.encode()
        task["http_request"]["body"] = converted_payload

    if timestamp is not None:
        schedule_time = timestamp_pb2.Timestamp()
        schedule_time.FromDatetime(timestamp)
        task["schedule_time"] = schedule_time

    response = client.create_task(request={"parent": parent, "task": task})
    return response


def reschedule_cloud_task(
    task_id: str,
    payload: dict,
    task_type: str,
    timestamp: Optional[datetime.datetime] = None,
):
    client = tasks_v2.CloudTasksClient()
    project, location, queue = (
        settings.GCP_PROJECT_ID,
        settings.GCP_LOCATION,
        settings.CLOUD_TASKS_QUEUE,
    )
    task_name = client.task_path(project, location, queue, task_id)
    try:
        client.delete_task(name=task_name)
    except Exception as e:
        print(f"Error deleting task {task_name}: {e}")

    return add_to_cloud_tasks(
        payload=payload, timestamp=timestamp, task_type=task_type, task_id=task_id
    )
