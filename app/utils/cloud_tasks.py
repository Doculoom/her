import datetime
import json
from typing import Dict, Optional

from google.cloud import tasks_v2
from google.protobuf import duration_pb2, timestamp_pb2

from app.core.config import settings


def add_to_cloud_tasks(
    payload: Dict,
    in_seconds: Optional[int] = None,
    deadline: Optional[int] = None,
    task_name: Optional[str] = None,
):
    client = tasks_v2.CloudTasksClient()
    project, location, queue = settings.GCP_PROJECT_ID, settings.GCP_LOCATION, settings.CLOUD_TASKS_QUEUE
    parent = client.queue_path(project, location, queue)

    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": settings.HER_API_URL + "api/v1/queue",
        }
    }
    if payload is not None:
        if isinstance(payload, dict):
            payload = json.dumps(payload)
            task["http_request"]["headers"] = {"Content-type": "application/json"}

        converted_payload = payload.encode()
        task["http_request"]["body"] = converted_payload

    if in_seconds is not None:
        d = datetime.datetime.utcnow() + datetime.timedelta(seconds=in_seconds)
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(d)
        task["schedule_time"] = timestamp

    if task_name is not None:
        task["name"] = client.task_path(project, location, queue, task_name)

    if deadline is not None:
        duration = duration_pb2.Duration()
        task["dispatch_deadline"] = duration.FromSeconds(deadline)

    response = client.create_task(request={"parent": parent, "task": task})
    return response
