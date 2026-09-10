"""Presentation-only profile labels; never changes account names or permissions."""


def display_identity(name, email):
    name = ' '.join(name.split()) if isinstance(name, str) else ''
    email = email.strip() if isinstance(email, str) else ''
    generic = {'user', 'admin', 'administrator', 'nova admin', 'novabrief admin', 'nova brief admin'}
    personal_name = name if name.casefold() not in generic else ''
    source = personal_name or email.partition('@')[0]
    initial = next((char.upper()[0] for char in source if char.isalnum()), '?')
    return {'name': personal_name or 'My account', 'initial': initial}
