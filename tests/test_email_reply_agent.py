import unittest
from unittest.mock import patch

import email_reply_agent


class AutomatedReplyTests(unittest.TestCase):
    @patch('email_reply_agent.send_email', return_value=True)
    @patch('email_reply_agent.generate_reply_text', return_value='')
    @patch('database.NewsDatabase')
    def test_fallback_reply_is_sent_and_message_is_marked_replied(
        self, database, generate_reply_text, send_email
    ):
        email_reply_agent.process_and_reply_to_contact_message(
            'Reader Name',
            'reader@real-domain.com',
            'Login problem',
            'I cannot log in.',
            msg_id=42,
        )

        generate_reply_text.assert_called_once()
        send_email.assert_called_once()
        self.assertEqual(send_email.call_args.args[0], 'reader@real-domain.com')
        self.assertEqual(send_email.call_args.args[1], 'Re: Login problem')
        self.assertIn('Hi Reader', send_email.call_args.args[2])
        database.return_value.mark_message_replied.assert_called_once()

    @patch('email_reply_agent.send_email', return_value=False)
    @patch('email_reply_agent.generate_reply_text', return_value='A reply')
    @patch('database.NewsDatabase')
    def test_failed_delivery_does_not_mark_message_replied(
        self, database, generate_reply_text, send_email
    ):
        email_reply_agent.process_and_reply_to_contact_message(
            'Reader',
            'reader@real-domain.com',
            'Question',
            'Please help.',
            msg_id=43,
        )

        send_email.assert_called_once()
        database.return_value.mark_message_replied.assert_not_called()


if __name__ == '__main__':
    unittest.main()
