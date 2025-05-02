# scraper.py
import os
import requests
from datetime import datetime

LOGIN_URL = 'https://www.xn--eh3ba264jh3i.com/bbs/login_check.php'
TARGET_URL = 'https://www.xn--eh3ba264jh3i.com/theme/banhal/html/mypage_order.php'

headers = {
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded'
}

def login_and_get_html(user_id, password):
    with requests.Session() as session:
        resp = session.post(LOGIN_URL, headers=headers, data={
            'mb_id': user_id,
            'mb_password': password,
            'url': 'https://www.xn--eh3ba264jh3i.com:443'
        })

        if resp.status_code not in (200, 302):
            raise Exception('로그인 실패')

        target_resp = session.get(TARGET_URL, headers=headers)
        return target_resp.text

def save_html(content):
    now = datetime.now()
    filename = f'public/banchan-{now.year}-{now.month:02}.html'
    os.makedirs('public', exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Saved to {filename}')

if __name__ == '__main__':
    user = os.environ.get('BANCHAN_ID')
    pw = os.environ.get('BANCHAN_PW')
    if not user or not pw:
        raise Exception("환경변수 BANCHAN_ID / BANCHAN_PW 설정 필요")

    html = login_and_get_html(user, pw)
    save_html(html)
