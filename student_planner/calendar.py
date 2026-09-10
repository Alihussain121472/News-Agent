"""Private iCalendar snapshot (RFC 5545), no email or automated reminders."""
from datetime import date, datetime, timedelta, timezone


def escape_text(value):
    return str(value or '').replace('\\', '\\\\').replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\\n').replace(';', '\\;').replace(',', '\\,')


def fold_line(line):
    # Fold at 75 octets without splitting a Unicode character.
    lines, current = [], ''
    for char in line:
        if len((current + char).encode('utf-8')) > 75:
            lines.append(current)
            current = ' '
        current += char
    return '\r\n'.join(lines + [current])


def build_calendar(data, today=None):
    today = today or date.today()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//NovaBrief Tech//Student Planner//EN',
             'CALSCALE:GREGORIAN', 'X-WR-CALNAME:NovaBrief Student Planner']
    for kind, items, field in [('application', data['applications'], 'deadline'), ('task', data['tasks'], 'due_date')]:
        for item in items:
            if not item.get(field) or (kind == 'task' and item['completed']):
                continue
            if kind == 'application' and item['status'] not in {'saved', 'preparing'}:
                continue
            due = date.fromisoformat(str(item[field])[:10])
            if due < today:
                continue
            prefix = 'Application deadline: ' if kind == 'application' else 'Study: '
            description = ('Verify the exact closing time and eligibility with the provider. '
                           if kind == 'application' else '') + 'Snapshot from NovaBrief. Changes in your planner do not update this calendar automatically.'
            lines.extend(['BEGIN:VEVENT', f'UID:{kind}-{item["id"]}@novabrief.tech',
                          f'DTSTAMP:{stamp}', f'DTSTART;VALUE=DATE:{due:%Y%m%d}',
                          f'DTEND;VALUE=DATE:{due + timedelta(days=1):%Y%m%d}',
                          'SUMMARY:' + escape_text(prefix + item['title']),
                          'DESCRIPTION:' + escape_text(description),
                          'CLASS:PRIVATE', 'TRANSP:TRANSPARENT', 'END:VEVENT'])
    lines.append('END:VCALENDAR')
    return '\r\n'.join(fold_line(line) for line in lines) + '\r\n'
