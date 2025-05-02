import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

BASE_URL = "https://www.xn--eh3ba264jh3i.com"
LIST_URL = f"{BASE_URL}/bbs/board.php?bo_table=today_menu"
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

def get_saved_dates():
    os.makedirs("docs", exist_ok=True)
    return {f.replace(".html", "") for f in os.listdir("docs") if re.match(r"\d{4}-\d{2}-\d{2}\.html", f)}

def find_new_post(session, saved_dates):
    res = session.get(LIST_URL, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")
    post_blocks = soup.select("li.gw_gl_li")

    for block in post_blocks:
        # wr_id 추출
        a_tag = block.select_one(".title a")
        if not a_tag or not a_tag.get("href"):
            continue

        href = a_tag["href"]
        wr_id_match = re.search(r"wr_id=(\d+)", href)
        if not wr_id_match:
            continue
        wr_id = wr_id_match.group(1)

        # 제목에서 날짜 추출
        title_span = a_tag.select_one("span.bo_tit_sub")
        if not title_span:
            continue

        post_date = get_actual_date_from_title(title_span.get_text())
        if not post_date:
            continue

        if post_date not in saved_dates:
            print(f"🆕 wr_id={wr_id}, post_date={post_date}")
            return wr_id, post_date

    return None, None

def save_post_content(session, wr_id, post_date):
    DETAIL_URL = f"{BASE_URL}/bbs/board.php?bo_table=today_menu&wr_id={wr_id}"
    res = session.get(DETAIL_URL, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")
    content_div = soup.select_one("div#bo_v_con")

    if not content_div:
        print(f"❌ 게시물 {wr_id}의 내용을 찾을 수 없습니다.")
        return

    html = content_div.prettify()
    filename = f"docs/{post_date}.html"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ 게시물 저장 완료: {filename}")


def get_actual_date_from_title(title_text: str) -> str:
    """
    제목 텍스트에서 '5월 1일'을 추출하고 연도 추정하여 'YYYY-MM-DD'로 반환
    """
    match = re.search(r'(\d{1,2})월\s*(\d{1,2})일', title_text)
    if not match:
        return None

    month = int(match.group(1))
    day = int(match.group(2))

    today = datetime.today()
    year = today.year

    # 연도 보정 (12월 31일에 1월 1일 게시물인 경우 → 다음 해)
    if month == 1 and today.month == 12:
        year += 1
    elif month == 12 and today.month == 1:
        year -= 1  # 혹시 반대로도 대비

    date_obj = datetime(year, month, day)
    return date_obj.strftime("%Y-%m-%d")

if __name__ == "__main__":
    session = login()
    saved_dates = get_saved_dates()
    wr_id, post_date = find_new_post(session, saved_dates)

    if wr_id and post_date:
        save_post_content(session, wr_id, post_date)
    else:
        print("🟡 저장되지 않은 새 게시물이 없습니다.")