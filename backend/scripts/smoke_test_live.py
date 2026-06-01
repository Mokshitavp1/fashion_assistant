import httpx
import time
import os

# Allow overriding target base URL via environment variable `SMOKE_BASE`.
base = os.environ.get("SMOKE_BASE", "http://127.0.0.1:8002")
email = f"smoketest_{int(time.time())}@gmail.com"
password = 'TestPass123A'
print('Using base', base)
try:
    with httpx.Client(timeout=10) as c:
        r=c.post(base+'/auth/register', json={'name':'Smoke Tester','email':email,'password':password})
        print('\nREGISTER', r.status_code, r.text)
        if r.status_code!=200:
            raise SystemExit('register failed')
        jt=r.json()
        token=jt.get('verification_token')
        if token:
            v=c.post(base+'/auth/verify-email', json={'verification_token':token})
            print('\nVERIFY', v.status_code, v.text)
            if v.status_code!=200:
                raise SystemExit('verify failed')
        lo=c.post(base+'/auth/login', data={'email':email,'password':password})
        print('\nLOGIN', lo.status_code, lo.text)
        if lo.status_code!=200:
            raise SystemExit('login failed')
        data=lo.json()
        access=data.get('access_token')
        user_id=data.get('user_id')
        headers={'Authorization':f'Bearer {access}'}
        p=c.get(f'{base}/users/{user_id}', headers=headers)
        print('\nPROFILE', p.status_code, p.text)
except Exception as e:
    print('ERROR', e)
