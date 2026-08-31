import os
import smtplib
import unittest
from unittest.mock import MagicMock, patch

import ai_news_agent


class EmailCredentialTests(unittest.TestCase):
    def test_credentials_preserve_pairs_and_remove_duplicates(self):
        env = {
            'SMTP_USERNAME': 'sender@example.test',
            'SMTP_PASSWORD': 'abcd efgh-ijkl',
            'GMAIL_USER': 'sender@example.test',
            'GMAIL_APP_PASSWORD': 'abcdefghijkl',
            'EMAIL_USER': 'backup@example.test',
            'EMAIL_APP_PASSWORD': 'other-password',
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(ai_news_agent._smtp_credentials(), [
                ('SMTP', 'sender@example.test', 'abcdefghijkl'),
                ('EMAIL', 'backup@example.test', 'otherpassword'),
            ])

    def test_send_email_uses_next_pair_after_authentication_failure(self):
        rejected = MagicMock()
        rejected.__enter__.return_value = rejected
        rejected.__exit__.return_value = False
        rejected.login.side_effect = smtplib.SMTPAuthenticationError(535, b'bad credentials')
        accepted = MagicMock()
        accepted.__enter__.return_value = accepted
        accepted.__exit__.return_value = False
        env = {
            'GMAIL_USER': 'first@gmail.com',
            'GMAIL_APP_PASSWORD': 'bad-password',
            'EMAIL_USER': 'second@gmail.com',
            'EMAIL_APP_PASSWORD': 'good-password',
            'SMTP_HOST': 'smtp.gmail.com',
            'SMTP_PORT': '465',
        }
        with patch.dict(os.environ, env, clear=True), \
                patch.object(ai_news_agent.smtplib, 'SMTP_SSL', side_effect=[rejected, accepted]):
            self.assertTrue(ai_news_agent.send_email('user@real-domain.com', 'Welcome', '<p>Hello</p>'))
        rejected.login.assert_called_once_with('first@gmail.com', 'badpassword')
        accepted.login.assert_called_once_with('second@gmail.com', 'goodpassword')
        accepted.send_message.assert_called_once()

    def test_send_email_fails_cleanly_without_credentials(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(ai_news_agent.send_email('user@real-domain.com', 'Welcome', '<p>Hello</p>'))

    def test_send_email_prefers_resend_and_does_not_open_smtp(self):
        response = MagicMock(status_code=200)
        response.json.return_value = {'id': 'email_123'}
        env = {
            'RESEND_API_KEY': 're_test_key',
            'RESEND_FROM_EMAIL': 'Nova Brief <updates@novabrief.tech>',
            'RESEND_REPLY_TO': 'support@novabrief.tech',
        }
        with patch.dict(os.environ, env, clear=True), \
                patch.object(ai_news_agent.requests, 'post', return_value=response) as post, \
                patch.object(ai_news_agent.smtplib, 'SMTP_SSL') as smtp:
            self.assertTrue(ai_news_agent.send_email(
                'user@real-domain.com', 'Welcome', '<p>Hello</p>'))

        smtp.assert_not_called()
        request_headers = post.call_args.kwargs['headers']
        self.assertTrue(request_headers['Authorization'].startswith('Bearer '))
        self.assertTrue(request_headers['Idempotency-Key'].startswith('novabrief-'))
        self.assertNotIn('re_test_key', str(post.call_args.kwargs['json']))

    def test_resend_retries_temporary_failure_with_same_idempotency_key(self):
        temporary = MagicMock(status_code=500)
        accepted = MagicMock(status_code=200)
        accepted.json.return_value = {'id': 'email_456'}
        env = {
            'RESEND_API_KEY': 're_test_key',
            'RESEND_FROM_EMAIL': 'Nova Brief <updates@novabrief.tech>',
        }
        with patch.dict(os.environ, env, clear=True), \
                patch.object(ai_news_agent.requests, 'post', side_effect=[temporary, accepted]) as post, \
                patch.object(ai_news_agent.time, 'sleep') as sleep:
            self.assertTrue(ai_news_agent._send_via_resend(
                'user@real-domain.com', 'Welcome', '<p>Hello</p>'))

        self.assertEqual(post.call_count, 2)
        first_headers = post.call_args_list[0].kwargs['headers']
        second_headers = post.call_args_list[1].kwargs['headers']
        self.assertEqual(first_headers['Idempotency-Key'], second_headers['Idempotency-Key'])
        sleep.assert_called_once()


class WelcomeBatchTests(unittest.TestCase):
    def test_batch_sends_only_to_pending_real_users(self):
        fake_db = MagicMock()
        fake_db.get_users_pending_welcome_email.return_value = [
            {'email': 'person@real-domain.com', 'name': 'Person'},
            {'email': 'test@example.com', 'name': 'Test'},
        ]
        with patch.object(ai_news_agent, 'NewsDatabase', return_value=fake_db), \
                patch.object(ai_news_agent, 'send_welcome_email', return_value=True) as send_welcome:
            result = ai_news_agent.send_welcome_to_registered_users()

        self.assertEqual(result, {'total': 2, 'eligible': 1, 'sent': 1, 'failed': 0, 'skipped': 1})
        send_welcome.assert_called_once_with('person@real-domain.com', 'Person')
        fake_db.mark_welcome_email_sent.assert_called_once_with('person@real-domain.com')
        fake_db.log_email_sent.assert_called_once_with(
            'person@real-domain.com', 'Welcome to Nova Brief', 0, 'success')


class ProgramNotificationTests(unittest.TestCase):
    def test_failed_program_delivery_remains_retryable(self):
        fake_db = MagicMock()
        fake_db.get_programs_to_notify.return_value = [{
            'id': 7, 'title': 'Cloud Internship', 'company': 'Nova',
            'description': 'Build cloud products', 'url': 'https://example.test/apply',
            'deadline': None,
        }]
        fake_db.get_pending_program_subscribers.return_value = ['person@real-domain.com']
        fake_db.program_notification_is_complete.return_value = False

        with patch.object(ai_news_agent, 'NewsDatabase', return_value=fake_db), \
                patch.object(ai_news_agent, 'send_email', return_value=False):
            sent = ai_news_agent.send_program_notifications()

        self.assertEqual(sent, 0)
        fake_db.record_program_notification_delivery.assert_called_once_with(
            7, 'person@real-domain.com', 'failed', 'SMTP delivery failed')
        fake_db.mark_program_notified.assert_not_called()


if __name__ == '__main__':
    unittest.main()
