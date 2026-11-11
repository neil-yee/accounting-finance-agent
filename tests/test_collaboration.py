"""Offline tests for bounded, run-scoped reviewer communication."""
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch
import os
import unittest

from accounting_finance_agent.collaboration import PeerMailbox, peer_tools
from accounting_finance_agent.config import COLLAB_PROFILE, load_settings


class PeerMailboxChecks(unittest.TestCase):
    def test_addressed_delivery_consumes_only_recipients_messages(self):
        box = PeerMailbox()
        msg = box.send('ledger-reviewer', 'cash-reviewer', 'Invoice A is $40k; see invoice A.')
        self.assertEqual(msg['status'], 'queued')
        self.assertEqual(box.receive('ledger-reviewer')['messages'], [])
        received = box.receive('cash-reviewer')['messages']
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['from'], 'ledger-reviewer')
        self.assertEqual(received[0]['id'], msg['message_id'])
        self.assertEqual(box.receive('cash-reviewer')['messages'], [])

    def test_waiter_receives_message_from_other_thread(self):
        box = PeerMailbox()
        started = Event()
        def wait():
            started.set()
            return box.receive('cash-reviewer', 3)
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(wait)
            self.assertTrue(started.wait(1))
            box.send('ledger-reviewer', 'cash-reviewer', 'Please check the bank deposit.')
            self.assertEqual(len(future.result(timeout=4)['messages']), 1)

    def test_bad_recipient_empty_oversize_and_message_limit(self):
        box = PeerMailbox()
        for recipient, message in [('unknown', 'x'), ('ledger-reviewer', 'x'), ('cash-reviewer', ''), ('cash-reviewer', 'x' * 1201)]:
            with self.assertRaises(ValueError):
                box.send('ledger-reviewer', recipient, message)
        for _ in range(20):
            box.send('ledger-reviewer', 'cash-reviewer', 'x')
        with self.assertRaises(ValueError):
            box.send('ledger-reviewer', 'cash-reviewer', 'x')
        with self.assertRaises(ValueError):
            box.receive('cash-reviewer', 26)

    def test_tool_sender_is_bound_to_reviewer(self):
        box = PeerMailbox()
        send = peer_tools(box, 'ledger-reviewer')[0]
        send.invoke({'recipient': 'cash-reviewer', 'message': 'Check deposit B1.'})
        self.assertEqual(box.receive('cash-reviewer')['messages'][0]['from'], 'ledger-reviewer')

    def test_mailboxes_do_not_share_messages(self):
        first, second = PeerMailbox(), PeerMailbox()
        first.send('ledger-reviewer', 'cash-reviewer', 'private to first run')
        self.assertEqual(second.receive('cash-reviewer')['messages'], [])

    def test_profile_disables_dynamic_interpreter(self):
        with patch('accounting_finance_agent.config.load_dotenv'), patch.dict(os.environ, {'AGENT_DYNAMIC_SUBAGENTS': 'true'}, clear=True):
            settings = load_settings(profile=COLLAB_PROFILE, validate_credentials=False)
        self.assertEqual(settings.profile, COLLAB_PROFILE)
        self.assertFalse(settings.dynamic_subagents_enabled)


if __name__ == '__main__':
    unittest.main()
