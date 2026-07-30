from app.services.graph_client import graph_request


async def list_events(access_token: str, limit: int = 50) -> dict:
    return await graph_request(
        "GET",
        "/me/events",
        access_token,
        params={
            "$top": limit,
            "$select": "id,subject,bodyPreview,start,end,location,organizer",
            "$orderby": "start/dateTime",
        },
    )


async def create_event(access_token: str, event: dict) -> dict:
    return await graph_request("POST", "/me/events", access_token, json=event)


async def update_event(access_token: str, event_id: str, changes: dict) -> dict:
    return await graph_request(
        "PATCH",
        f"/me/events/{event_id}",
        access_token,
        json=changes,
    )


async def delete_event(access_token: str, event_id: str) -> None:
    await graph_request("DELETE", f"/me/events/{event_id}", access_token)
