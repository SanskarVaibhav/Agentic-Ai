import re, datetime

_captured_leads = []

def mock_lead_capture(name, email, platform):
    lead = {
        'lead_id': 'LEAD-' + str(len(_captured_leads) + 1001),
        'name': name,
        'email': email,
        'platform': platform,
        'captured_at': datetime.datetime.utcnow().isoformat() + 'Z',
        'status': 'new',
        'source': 'inflx-autostream-agent',
    }
    _captured_leads.append(lead)
    print('=' * 60)
    print('LEAD CAPTURED SUCCESSFULLY')
    print('=' * 60)
    print('  Lead captured successfully: ' + name + ', ' + email + ', ' + platform)
    print('  Lead ID  : ' + lead['lead_id'])
    print('  Timestamp: ' + lead['captured_at'])
    print('=' * 60)
    return {'success': True, 'lead_id': lead['lead_id']}

def get_all_leads():
    return _captured_leads

def validate_email(email):
    return bool(re.match(r'^[\w._%+-]+@[\w.-]+\.[a-zA-Z]{2,}$', email.strip()))

def extract_lead_fields_from_text(text, existing):
    result = dict(existing)
    if not result.get('email'):
        import re as _re
        m = _re.search(r'[\w._%+-]+@[\w.-]+\.[a-zA-Z]{2,}', text)
        if m:
            result['email'] = m.group(0)
    platforms = ['youtube','instagram','tiktok','facebook','twitter','linkedin','twitch','snapchat']
    if not result.get('platform'):
        for p in platforms:
            if p in text.lower():
                result['platform'] = p.capitalize()
                break
    return result
