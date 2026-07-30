from app.services.graph_client import graph_request


async def get_default_task_list_id(access_token: str) -> str:
    # Keep this request simple because To-Do list discovery supports fewer
    # query options than some other Graph collections.
    lists = await graph_request(
        "GET",
        "/me/todo/lists",
        access_token,
    )
    values = lists.get("value", [])
    if not values:
        raise ValueError("No Microsoft To-Do list is available")
    return values[0]["id"]


async def list_todos(access_token: str, limit: int = 50) -> dict:
    list_id = await get_default_task_list_id(access_token)
    # Keep the task-list request simple for Microsoft To-Do compatibility.
    result = await graph_request(
        "GET",
        f"/me/todo/lists/{list_id}/tasks",
        access_token,
    )
    if isinstance(result, dict) and isinstance(result.get("value"), list):
        result["value"] = result["value"][:limit]
    return result


async def create_todo(access_token: str, task: dict) -> dict:
    list_id = await get_default_task_list_id(access_token)
    return await graph_request(
        "POST",
        f"/me/todo/lists/{list_id}/tasks",
        access_token,
        json=task,
    )


async def update_todo(access_token: str, task_id: str, changes: dict) -> dict:
    list_id = await get_default_task_list_id(access_token)
    return await graph_request(
        "PATCH",
        f"/me/todo/lists/{list_id}/tasks/{task_id}",
        access_token,
        json=changes,
    )


async def delete_todo(access_token: str, task_id: str) -> None:
    list_id = await get_default_task_list_id(access_token)
    await graph_request(
        "DELETE",
        f"/me/todo/lists/{list_id}/tasks/{task_id}",
        access_token,
    )
