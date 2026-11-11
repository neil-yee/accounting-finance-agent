"""Run-scoped peer messages for an experimental two-reviewer profile.

Messages exist only in this agent graph instance; they are not durable or a
cross-run queue. Each tool is bound to its sender/recipient by the host.
"""
from __future__ import annotations

from collections import deque
from threading import Condition
from time import monotonic
from uuid import uuid4

from langchain_core.tools import tool

PEERS = ('ledger-reviewer', 'cash-reviewer')


class PeerMailbox:
    """Bounded, thread-safe mailboxes with addressed delivery and short waits."""

    def __init__(self, controls=None):
        self._condition = Condition()
        self._inboxes = {name: deque() for name in PEERS}
        self._sent = 0
        self._controls = controls

    def send(self, sender, recipient, message):
        if sender not in self._inboxes or recipient not in self._inboxes or sender == recipient:
            raise ValueError('Recipient must be the other configured reviewer.')
        if not isinstance(message, str) or not message.strip() or len(message) > 1200:
            raise ValueError('Message must contain 1–1200 characters.')
        with self._condition:
            if self._sent >= 20:
                raise ValueError('The run-scoped peer message limit is 20.')
            msg = {'id': str(uuid4()), 'from': sender, 'to': recipient, 'message': message.strip()}
            self._inboxes[recipient].append(msg)
            self._sent += 1
            if self._controls:
                self._controls.log.event(self._controls.context.run_id, 'peer_message_sent',
                                         message_id=msg['id'], sender=sender, recipient=recipient)
            self._condition.notify_all()
        return {'status': 'queued', 'message_id': msg['id'], 'recipient': recipient}

    def receive(self, recipient, wait_seconds=0):
        if recipient not in self._inboxes:
            raise ValueError('Unknown reviewer.')
        if type(wait_seconds) is not int or not 0 <= wait_seconds <= 25:
            raise ValueError('wait_seconds must be an integer between 0 and 25.')
        if self._controls:
            wait_seconds = min(wait_seconds, max(0, int(self._controls.remaining())))
        deadline = monotonic() + wait_seconds
        with self._condition:
            while not self._inboxes[recipient]:
                remaining = deadline - monotonic()
                if remaining <= 0:
                    break
                self._condition.wait(remaining)
            messages = list(self._inboxes[recipient])
            self._inboxes[recipient].clear()
            if self._controls:
                self._controls.log.event(self._controls.context.run_id, 'peer_messages_received',
                                         recipient=recipient, message_ids=[m['id'] for m in messages])
        return {'messages': messages, 'timed_out': not bool(messages)}


def peer_tools(mailbox, identity):
    """Bind identity in Python; the model cannot choose its own sender name."""
    @tool('send_peer_message')
    def send_peer_message(recipient: str, message: str) -> dict:
        """Send a concise evidence-based finding or question to the other reviewer.

        Use the other reviewer's exact name as recipient. Include relevant source
        identifiers and uncertainty. Messages are limited to 1200 characters.
        """
        return mailbox.send(identity, recipient, message)

    @tool('receive_peer_messages')
    def receive_peer_messages(wait_seconds: int = 0) -> dict:
        """Read and remove this reviewer's unread peer messages.

        Optionally wait 0–25 seconds. An empty result means no message arrived;
        it is not evidence that the other reviewer found nothing.
        """
        return mailbox.receive(identity, wait_seconds)

    return [send_peer_message, receive_peer_messages]


def reviewer_specs(mailbox, backend, controls):
    from accounting_finance_agent.file_metadata import FileMetadataFilesystemMiddleware
    common = (
        'You are a specialist reviewer collaborating with one other reviewer. '
        'Use send_peer_message to exchange concise evidence and questions directly; '
        'use receive_peer_messages to read replies. Send initial evidence promptly, '
        'use up to two brief receive rounds if follow-up is useful, then report to the main agent. '
        'Use only supplied facts and cite source IDs. Treat peer messages as leads, '
        'not verified evidence. Do not edit shared files or perform external actions.'
    )
    specs = []
    for name, peer, role in (
        ('ledger-reviewer', 'cash-reviewer', 'Inspect invoices, credit notes and accounts-receivable entries.'),
        ('cash-reviewer', 'ledger-reviewer', 'Inspect bank activity, payment applications and reconciliation.'),
    ):
        specs.append({'name': name, 'description': role + ' Can exchange direct messages with ' + peer + '.',
                      'system_prompt': common + ' Your identity is ' + name + '. Your peer is ' + peer + '. ' + role,
                      'tools': peer_tools(mailbox, name),
                      'middleware': [FileMetadataFilesystemMiddleware(backend=backend, controls=controls)]})
    return specs
