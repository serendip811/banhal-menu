import os
import requests
from bs4 import BeautifulSoup
import re

BASE_URL = "https://www.xn--eh3ba264jh3i.com"
LIST_URL = f"{BASE_URL}/bbs/board.php?bo_table=today_menu"
DETAIL_URL = f"{BASE_URL}/bbs/board.php?bo_table=today_menu&wr_id="

HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded'
}

def login():
    session = requests.Session()
    user_id = os.environ.get("BANCHAN_ID")
    password = os.environ.get("BANCHAN_PW")

    if not user_id or not password:
        raise Exception("환경변수 BANCHAN_ID / BANCHAN_PW가 필요합니다")

    res = session.post(
        f"{BASE_URL}/bbs/login_check.php",
        headers=HEADERS,
        data={
            "mb_id": user_id,
            "mb_password": password,
            "url": f"{BASE_URL}:443"
        }
    )

    if res.status_code not in (200, 302):
        raise Exception("로그인 실패")

    return session

def get_saved_ids():
    os.makedirs("public", exist_ok=True)
    return {f.replace("wr_id_", "").replace(".html", "") for f in os.listdir("public") if f.startswith("wr_id_")}

def find_new_post(session, saved_ids):
    res = session.get(LIST_URL, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")
    items = soup.select("li.gw_gl_li .title a")

    for a_tag in items:
        href = a_tag.get("href")
        if not href:
            continue

        match = re.search(r"wr_id=(\d+)", href)
        if match:
            wr_id = match.group(1)
            if wr_id not in saved_ids:
                print(f"새 게시물 발견: wr_id={wr_id}")
                return wr_id
    return None

def save_post_detail(session, wr_id):
    url = f"{DETAIL_URL}{wr_id}"
    res = session.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")
    content_div = soup.select_one("div#bo_v_con")

    if not content_div:
        print(f"❌ 게시물 {wr_id}의 내용을 찾을 수 없습니다.")
        return

    # HTML 그대로 저장
    html = content_div.prettify()

    filename = f"public/wr_id_{wr_id}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ 게시물 내용 저장 완료: {filename}")

if __name__ == "__main__":
    session = login()
    saved_ids = get_saved_ids()
    wr_id = find_new_post(session, saved_ids)
    if wr_id:
        save_post_detail(session, wr_id)
    else:
        print("🟡 새로운 게시물이 없습니다.")