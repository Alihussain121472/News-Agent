"""Validate user input before any planner database write."""
import re
from datetime import date
from urllib.parse import urlsplit

STATUSES = ('saved', 'preparing', 'submitted', 'interview', 'offer', 'closed')
CHECKLIST = ('eligibility', 'cv', 'statement', 'documents')


def text(value, name, limit, required=False):
    if not isinstance(value, str):
        raise ValueError(f'{name} must be text.')
    value = value.strip()
    if (required and not value) or len(value) > limit:
        raise ValueError(f'{name} must be {"1 to " if required else "at most "}{limit} characters.')
    if any((ord(char) < 32 and char not in '\n\t') or 127 <= ord(char) <= 159 for char in value):
        raise ValueError(f'{name} contains unsupported characters.')
    return value


def date_value(value):
    if value is None or value == '':
        return None
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('Use a date in YYYY-MM-DD format.')
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise ValueError('Please enter a valid calendar date.') from None
    if not 2000 <= parsed.year <= 2100:
        raise ValueError('Choose a date between 2000 and 2100.')
    return parsed.isoformat()


def safe_url(value):
    value = text(value, 'Website link', 2000)
    if not value:
        return ''
    try:
        parts = urlsplit(value)
        if (parts.scheme not in {'http', 'https'} or not parts.hostname
                or parts.username is not None or parts.password is not None
                or any(char.isspace() or ord(char) < 32 for char in value)
                or '\\' in value):
            raise ValueError()
        parts.port
    except ValueError:
        raise ValueError('Use a complete http:// or https:// website link without login details.') from None
    return value


def payload(data, kind, partial=False):
    if not isinstance(data, dict) or not data:
        raise ValueError('Please provide the fields to save.')
    fields = ({'title', 'due_date', 'completed'} if kind == 'task' else
              {'title', 'company', 'registration_url', 'deadline', 'status', 'notes', 'checklist'})
    if kind == 'application' and not partial and 'program_id' in data:
        if set(data) != {'program_id'} or type(data['program_id']) is not int or not 0 < data['program_id'] <= 2147483647:
            raise ValueError('Please select a valid student program.')
        return {'program_id': data['program_id']}
    if set(data) - fields:
        raise ValueError('Some fields are not supported.')
    result = {}
    if not partial or 'title' in data:
        result['title'] = text(data.get('title'), 'Title', 200, required=True)
    if kind == 'task':
        if not partial or 'due_date' in data:
            result['due_date'] = date_value(data.get('due_date'))
        if not partial or 'completed' in data:
            if type(data.get('completed', False)) is not bool:
                raise ValueError('Task completion must be true or false.')
            result['completed'] = data.get('completed', False)
        return result
    for field, label, limit in [('company', 'Organization', 120), ('notes', 'Notes', 4000)]:
        if not partial or field in data:
            result[field] = text(data.get(field, ''), label, limit)
    if not partial or 'registration_url' in data:
        result['registration_url'] = safe_url(data.get('registration_url', ''))
    if not partial or 'deadline' in data:
        result['deadline'] = date_value(data.get('deadline'))
    if not partial or 'status' in data:
        status = data.get('status', 'saved')
        if not isinstance(status, str) or status not in STATUSES:
            raise ValueError('Choose a valid application status.')
        result['status'] = status
    if not partial or 'checklist' in data:
        checked = data.get('checklist', [])
        if not isinstance(checked, list) or len(checked) > len(CHECKLIST) or any(
                not isinstance(key, str) or key not in CHECKLIST for key in checked):
            raise ValueError('Choose items from the preparation checklist.')
        result['checklist'] = list(dict.fromkeys(checked))
    return result
