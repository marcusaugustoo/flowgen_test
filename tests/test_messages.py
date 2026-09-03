"""Tests for the message system."""

import json
import tempfile
from pathlib import Path

import pytest

from src.orchestration.messages import AgentMessage, MessageBus


class TestAgentMessage:
    """Tests for AgentMessage."""

    def test_creation(self):
        msg = AgentMessage(
            sender="developer",
            receiver="tester",
            message_type="artifact",
            content="code artifact",
        )
        assert msg.sender == "developer"
        assert msg.receiver == "tester"
        assert msg.message_id  # Auto-generated
        assert msg.timestamp  # Auto-generated

    def test_to_dict(self):
        msg = AgentMessage(sender="a", receiver="b", content="test")
        d = msg.to_dict()
        assert d["sender"] == "a"
        assert d["receiver"] == "b"

    def test_to_json(self):
        msg = AgentMessage(sender="a", receiver="b", content="test")
        j = msg.to_json()
        parsed = json.loads(j)
        assert parsed["sender"] == "a"


class TestMessageBus:
    """Tests for MessageBus."""

    def test_record(self):
        bus = MessageBus()
        msg = AgentMessage(sender="a", receiver="b")
        bus.record(msg)
        assert bus.count == 1

    def test_create_and_record(self):
        bus = MessageBus()
        msg = bus.create_and_record(
            sender="dev", receiver="tester",
            message_type="artifact", content="code"
        )
        assert bus.count == 1
        assert msg.sender == "dev"

    def test_query_by_sender(self):
        bus = MessageBus()
        bus.create_and_record("a", "b", "artifact", "msg1")
        bus.create_and_record("c", "d", "artifact", "msg2")
        results = bus.get_messages(sender="a")
        assert len(results) == 1
        assert results[0].sender == "a"

    def test_query_by_type(self):
        bus = MessageBus()
        bus.create_and_record("a", "b", "artifact", "msg1")
        bus.create_and_record("a", "b", "review", "msg2")
        results = bus.get_messages(message_type="review")
        assert len(results) == 1

    def test_save_and_load(self):
        bus = MessageBus()
        bus.create_and_record("a", "b", "artifact", "content1")
        bus.create_and_record("c", "d", "review", "content2")

        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            bus.save(f.name)
            loaded = MessageBus.load(f.name)
            assert loaded.count == 2
            assert loaded.all_messages[0].sender == "a"

    def test_clear(self):
        bus = MessageBus()
        bus.create_and_record("a", "b", "artifact", "msg")
        bus.clear()
        assert bus.count == 0
