"""Tests for the message channel."""

from company.engine.channel import MessageChannel, MessageType


def test_send_and_receive():
    channel = MessageChannel()
    channel.send("pm", "backend", "Please check the API spec", MessageType.DIRECT)
    inbox = channel.get_inbox("backend")
    assert len(inbox) == 1
    assert inbox[0].content == "Please check the API spec"


def test_unread():
    channel = MessageChannel()
    channel.send("pm", "backend", "msg 1")
    unread = channel.get_inbox("backend", unread_only=True)
    assert len(unread) == 1
    channel.mark_read("backend")
    unread = channel.get_inbox("backend", unread_only=True)
    assert len(unread) == 0


def test_broadcast():
    channel = MessageChannel()
    channel.send("backend", "all", "API is ready", MessageType.NOTIFICATION)
    # backend should not have its own message
    backend_inbox = channel.get_inbox("backend")
    # "all" creates a message in "all" inbox
    all_inbox = channel.get_inbox("all")
    assert len(all_inbox) == 1


def test_history():
    channel = MessageChannel()
    channel.send("pm", "backend", "msg 1")
    channel.send("backend", "qa", "msg 2")
    history = channel.get_history(agent_id="backend")
    assert len(history) == 2
