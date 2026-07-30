from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, ConversationMessage


def get_or_create_conversation(
    db: Session,
    user_id: int,
    conversation_id: int | None,
) -> Conversation:
    if conversation_id is not None:
        conversation = db.scalar(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        if conversation is None:
            raise ValueError("Conversation not found")
        return conversation

    conversation = Conversation(user_id=user_id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_messages(db: Session, conversation_id: int) -> list[ConversationMessage]:
    return list(
        db.scalars(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.id)
        )
    )


def save_message(
    db: Session,
    conversation_id: int,
    role: str,
    content: str,
) -> None:
    db.add(
        ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
    )
    db.commit()
