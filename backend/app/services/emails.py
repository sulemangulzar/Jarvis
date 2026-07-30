from app.services.graph_client import graph_request


async def list_emails(access_token: str, limit: int = 20) -> dict:
    return await graph_request(
        "GET",
        "/me/messages",
        access_token,
        params={
            "$top": limit,
            "$select": "id,subject,from,receivedDateTime,bodyPreview,isRead",
            "$orderby": "receivedDateTime DESC",
        },
    )


async def get_email(access_token: str, email_id: str) -> dict:
    return await graph_request(
        "GET",
        f"/me/messages/{email_id}",
        access_token,
        params={
            "$select": "id,subject,from,toRecipients,receivedDateTime,body,bodyPreview,isRead",
        },
    )


async def create_email_draft(
    access_token: str,
    subject: str,
    body: str,
    recipients: list[str],
) -> dict:
    """Create a draft only. This function intentionally never sends email."""
    message = {
        "subject": subject,
        "body": {
            "contentType": "Text",
            "content": body,
        },
        "toRecipients": [
            {"emailAddress": {"address": recipient}}
            for recipient in recipients
        ],
    }
    return await graph_request(
        "POST",
        "/me/messages",
        access_token,
        json=message,
    )
