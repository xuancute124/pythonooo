import traceback
from app import app

c = app.test_client()
try:
    r = c.get('/')
    print('status', r.status_code)
    print('data snippet:', r.data[:400])
except Exception as e:
    print('Exception:')
    traceback.print_exc()
