"""
Agent message and event system.

Records all inter-agent communication for analysis and reproducibility.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


@dataclass
class AgentMessage:
    """
    A single message exchanged between agents (via the orchestrator).

    Attributes:
        message_id: Unique identifier for this message.
        run_id: ID of the experiment run this message belongs to.
        timestamp: ISO 8601 timestamp of when the message was created.
        sender: Name of the sending agent.
        receiver: Name of the receiving agent.
        message_type: Type of message (e.g., 'artifact', 'review', 'failure_report').
        content: Message content (text or serialized data).
        artifact_id: Optional reference to an artifact.
    """
    message_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    run_id: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    sender: str = ""
    receiver: str = ""
    message_type: str = "artifact"
    content: str = ""
    artifact_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "message_id": self.message_id,
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "sender": self.sender,
            "receiver": self.receiver,
            "message_type": self.message_type,
            "content": self.content,
            "artifact_id": self.artifact_id,
        }

    def to_json(self) -> str:
        """Serialize to JSON string (for JSONL logging)."""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class MessageBus:
    """
    Records and queries inter-agent messages.

    All messages flow through the orchestrator; this bus records them
    for later analysis of agent interactions.
    """

    def __init__(self) -> None:
        self._messages: list[AgentMessage] = []

    def record(self, message: AgentMessage) -> None:
        """Record a new message."""
        self._messages.append(message)

    def create_and_record(
        self,
        sender: str,
        receiver: str,
        message_type: str,
        content: str,
        run_id: str = "",
        artifact_id: Optional[str] = None,
    ) -> AgentMessage:
        """Create a message and record it in one step."""
        msg = AgentMessage(
            run_id=run_id,
            sender=sender,
            receiver=receiver,
            message_type=message_type,
            content=content,
            artifact_id=artifact_id,
        )
        self.record(msg)
        return msg

    def get_messages(
        self,
        sender: Optional[str] = None,
        receiver: Optional[str] = None,
        message_type: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> list[AgentMessage]:
        """Query messages with optional filters."""
        results = self._messages
        if sender:
            results = [m for m in results if m.sender == sender]
        if receiver:
            results = [m for m in results if m.receiver == receiver]
        if message_type:
            results = [m for m in results if m.message_type == message_type]
        if run_id:
            results = [m for m in results if m.run_id == run_id]
        return results

    @property
    def all_messages(self) -> list[AgentMessage]:
        """Get all recorded messages."""
        return list(self._messages)

    @property
    def count(self) -> int:
        """Number of recorded messages."""
        return len(self._messages)

    def clear(self) -> None:
        """Clear all messages."""
        self._messages.clear()

    def save(self, path: str | Path) -> None:
        """Save all messages to a JSONL file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            for msg in self._messages:
                f.write(msg.to_json() + "\n")

    @classmethod
    def load(cls, path: str | Path) -> MessageBus:
        """Load messages from a JSONL file."""
        bus = cls()
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    msg = AgentMessage(**data)
                    bus.record(msg)
        return bus
