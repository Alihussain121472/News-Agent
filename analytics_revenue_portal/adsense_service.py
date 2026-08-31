import base64
import hashlib
import os
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

import requests
from cryptography.fernet import Fernet, InvalidToken

from . import adsense_repository as repository


AUTHORIZATION_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_URL = 'https://oauth2.googleapis.com/token'
REVOKE_URL = 'https://oauth2.googleapis.com/revoke'
API_ROOT = 'https://adsense.googleapis.com/v2'
READONLY_SCOPE = 'https://www.googleapis.com/auth/adsense.readonly'


class AdSenseError(RuntimeError):
    pass


def oauth_configured():
    return bool(os.getenv('GOOGLE_ADSENSE_CLIENT_ID') and os.getenv('GOOGLE_ADSENSE_CLIENT_SECRET'))


def _client_credentials():
    client_id = (os.getenv('GOOGLE_ADSENSE_CLIENT_ID') or '').strip()
    client_secret = (os.getenv('GOOGLE_ADSENSE_CLIENT_SECRET') or '').strip()
    if not client_id or not client_secret:
        raise AdSenseError('AdSense OAuth credentials have not been configured for Nova OS yet.')
    return client_id, client_secret


def _fernet():
    secret = (os.getenv('ADSENSE_TOKEN_ENCRYPTION_KEY') or os.getenv('SECRET_KEY') or '').encode('utf-8')
    if len(secret) < 32:
        raise AdSenseError('A stable application secret is required before AdSense can be connected.')
    key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
    return Fernet(key)


def encrypt_refresh_token(token):
    if not token:
        raise AdSenseError('Google did not return an offline refresh token. Reconnect and approve access again.')
    return _fernet().encrypt(token.encode('utf-8')).decode('ascii')


def decrypt_refresh_token(token):
    try:
        return _fernet().decrypt(token.encode('ascii')).decode('utf-8')
    except (InvalidToken, ValueError) as exc:
        raise AdSenseError('The saved AdSense connection can no longer be decrypted. Please reconnect it.') from exc


def build_authorization_url(redirect_uri, state, code_challenge):
    client_id, _ = _client_credentials()
    return f'{AUTHORIZATION_URL}?{urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": READONLY_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    })}'


def exchange_code(code, redirect_uri, code_verifier):
    client_id, client_secret = _client_credentials()
    response = requests.post(TOKEN_URL, data={
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
        'code_verifier': code_verifier,
    }, timeout=15)
    if not response.ok:
        raise AdSenseError('Google could not complete the AdSense authorization. Please try connecting again.')
    payload = response.json()
    if not payload.get('access_token'):
        raise AdSenseError('Google did not return an AdSense access token.')
    return payload


def refresh_access_token(encrypted_refresh_token):
    client_id, client_secret = _client_credentials()
    refresh_token = decrypt_refresh_token(encrypted_refresh_token)
    response = requests.post(TOKEN_URL, data={
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
    }, timeout=15)
    if not response.ok:
        raise AdSenseError('Google rejected the saved AdSense connection. Please reconnect the account.')
    access_token = response.json().get('access_token')
    if not access_token:
        raise AdSenseError('Google did not return a refreshed AdSense access token.')
    return access_token


def _authorized_get(url, access_token, params=None):
    response = requests.get(url, headers={'Authorization': f'Bearer {access_token}'}, params=params, timeout=20)
    if not response.ok:
        raise AdSenseError(f'AdSense returned an error while syncing data (HTTP {response.status_code}).')
    return response.json()


def list_accounts(access_token):
    payload = _authorized_get(f'{API_ROOT}/accounts', access_token)
    accounts = payload.get('accounts') or []
    return [account for account in accounts if account.get('name')]


def _number(value, integer=False):
    try:
        number = Decimal(str(value or '0'))
    except InvalidOperation:
        number = Decimal('0')
    return int(number) if integer else number


def fetch_daily_report(access_token, account_name, days=90):
    end = date.today()
    start = end - timedelta(days=max(7, min(int(days), 365)) - 1)
    params = [
        ('dateRange', 'CUSTOM'),
        ('startDate.year', start.year), ('startDate.month', start.month), ('startDate.day', start.day),
        ('endDate.year', end.year), ('endDate.month', end.month), ('endDate.day', end.day),
        ('dimensions', 'DATE'),
        ('metrics', 'ESTIMATED_EARNINGS'), ('metrics', 'IMPRESSIONS'),
        ('metrics', 'CLICKS'), ('metrics', 'PAGE_VIEWS'),
        ('reportingTimeZone', 'ACCOUNT_TIME_ZONE'), ('orderBy', '+DATE'),
    ]
    payload = _authorized_get(f'{API_ROOT}/{account_name}/reports:generate', access_token, params=params)
    headers = payload.get('headers') or []
    header_names = [header.get('name') for header in headers]
    currency = next((header.get('currencyCode') for header in headers if header.get('name') == 'ESTIMATED_EARNINGS' and header.get('currencyCode')), None)
    rows = []
    for row in payload.get('rows') or []:
        values = [cell.get('value', '0') for cell in row.get('cells') or []]
        record = dict(zip(header_names, values))
        if not record.get('DATE'):
            continue
        rows.append({
            'date': record['DATE'],
            'estimated_earnings': _number(record.get('ESTIMATED_EARNINGS')),
            'impressions': _number(record.get('IMPRESSIONS'), integer=True),
            'clicks': _number(record.get('CLICKS'), integer=True),
            'page_views': _number(record.get('PAGE_VIEWS'), integer=True),
        })
    return rows, currency


def connect_authorized_account(token_payload):
    accounts = list_accounts(token_payload['access_token'])
    if not accounts:
        raise AdSenseError('This Google account does not have an accessible AdSense account.')
    account = accounts[0]
    encrypted_token = encrypt_refresh_token(token_payload.get('refresh_token'))
    rows, report_currency = fetch_daily_report(token_payload['access_token'], account['name'])
    if report_currency:
        account['currencyCode'] = report_currency
    repository.save_connection(account, encrypted_token)
    repository.record_sync(account['name'], account.get('currencyCode') or 'USD', rows)
    return account


def sync_connection(force=False, access_token=None):
    connection = repository.get_connection(include_token=True)
    if not connection:
        return {'status': 'disconnected'}
    last_synced = connection.get('last_synced_at')
    if not force and last_synced:
        now = datetime.now(last_synced.tzinfo) if getattr(last_synced, 'tzinfo', None) else datetime.utcnow()
        if now - last_synced < timedelta(hours=1):
            return {'status': 'current', 'last_synced_at': last_synced}
    try:
        token = access_token or refresh_access_token(connection['encrypted_refresh_token'])
        rows, report_currency = fetch_daily_report(token, connection['account_name'])
        currency = report_currency or connection.get('currency_code') or 'USD'
        repository.record_sync(connection['account_name'], currency, rows)
        return {'status': 'synced', 'row_count': len(rows)}
    except Exception as exc:
        message = str(exc) if isinstance(exc, AdSenseError) else 'AdSense data could not be refreshed right now.'
        repository.record_sync_error(message)
        if force:
            raise AdSenseError(message) from exc
        return {'status': 'error', 'message': message}


def connection_status():
    connection = repository.get_connection()
    return {
        'configured': oauth_configured(),
        'connected': bool(connection),
        'account': connection,
    }


def revoke_and_disconnect():
    connection = repository.get_connection(include_token=True)
    if not connection:
        return False
    try:
        refresh_token = decrypt_refresh_token(connection['encrypted_refresh_token'])
        requests.post(REVOKE_URL, data={'token': refresh_token}, timeout=10)
    except Exception:
        pass
    return repository.disconnect()
