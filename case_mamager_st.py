import streamlit as st
import requests, json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials
import datetime, calendar

# ========== 你只需要改這個 ==========
# 把你上傳到 Google Drive 的 service_account.json 檔案 ID 貼進來
JSON_FILE_ID = "1Soz_zcUJlqJWsg2fTojj1vaTrIS00o3Q"
# ===================================

DATA_FILE_NAME = "cases.json"  # 存案件資料的檔案名（會放在 service account 的雲端硬碟）

st.set_page_config(page_title="案件管理系統", layout="wide")
st.title("📂 案件管理系統（Streamlit + Google Drive）")

# ----------- 初始化 Google Drive（Service Account）-----------
@st.cache_resource
def init_drive(json_file_id: str):
    # 1) 從 Google Drive 直接下載 service_account.json 文字
    url = f"https://drive.google.com/uc?id={json_file_id}"
    resp = requests.get(url)
    resp.raise_for_status()
    service_account_info = json.loads(resp.text)

    # 2) 建立 service account 憑證
    scope = ["https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)

    # 3) 套用到 PyDrive2
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive_client = GoogleDrive(gauth)

    # 額外：把 service account 的 email 顯示給你（方便你去分享檔案/資料夾權限）
    sa_email = service_account_info.get("client_email", "(未知)")
    return drive_client, sa_email

try:
    drive, service_account_email = init_drive(JSON_FILE_ID)
except Exception as e:
    st.error("初始化 Google Drive 失敗。請確認 JSON_FILE_ID 是否正確、檔案是否設定為可存取。")
    st.exception(e)
    st.stop()

st.info(f"目前使用的 Service Account：`{service_account_email}`\n\n"
        f"請確保你要讀寫的 Google Drive 檔案/資料夾**已分享**給這個 email（至少「編輯」權限）。")

# ----------- 讀寫 cases.json -----------
def load_cases():
    # 以檔名搜尋（在該 service account 擁有的雲端硬碟中）
    file_list = drive.ListFile({'q': f"title='{DATA_FILE_NAME}' and trashed=false"}).GetList()
    if not file_list:
        return []
    file_obj = file_list[0]
    content = file_obj.GetContentString()
    try:
        return json.loads(content)
    except:
        return []

def save_cases(cases):
    file_list = drive.ListFile({'q': f"title='{DATA_FILE_NAME}' and trashed=false"}).GetList()
    if file_list:
        file_obj = file_list[0]
    else:
        file_obj = drive.CreateFile({'title': DATA_FILE_NAME})
    file_obj.SetContentString(json.dumps(cases, ensure_ascii=False, indent=2))
    file_obj.Upload()

cases = load_cases()

# ----------- 側邊欄：新增/更新案件 -----------
with st.sidebar:
    st.header("➕ 新增 / 更新案件")
    case_number = st.text_input("案號")
    case_date = st.date_input("案件日期", value=datetime.date.today())
    case_name = st.text_input("案件名稱")

    # 額外欄位（多行：欄位=值，每行一個）
    extra_fields_text = st.text_area("額外欄位（格式：欄位=值，每行一個）", value="")
    # 測試日期（逗號分隔）
    test_dates_text = st.text_area("測試日期（多筆用逗號分隔，格式 YYYY-MM-DD）", value="")

    if st.button("💾 儲存/更新"):
        new_case = {
            "案號": case_number.strip(),
            "日期 (YYYY-MM-DD)": case_date.strftime("%Y-%m-%d"),
            "案件名稱": case_name.strip(),
        }

        # 解析額外欄位
        if extra_fields_text.strip():
            for line in extra_fields_text.splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip()
                    if k:
                        new_case[k] = v

        # 解析測試日期
        test_dates = []
        if test_dates_text.strip():
            for d in test_dates_text.split(","):
                d = d.strip()
                if d:
                    test_dates.append(d)
        new_case["測試日期"] = test_dates

        # 以案號為唯一鍵：存在就更新，否則新增
        updated = False
        for i, c in enumerate(cases):
            if c.get("案號") == new_case["案號"] and new_case["案號"]:
                cases[i] = new_case
                updated = True
                break
        if not updated:
            cases.append(new_case)

        save_cases(cases)
        st.success("✅ 已儲存！")
        st.rerun()

# ----------- 畫萬年曆（測試日期標綠）-----------
today = datetime.date.today()
year, month = today.year, today.month

# 收集本月要標記的測試日期
test_date_set = set()
for c in cases:
    for d_str in c.get("測試日期", []):
        try:
            d = datetime.datetime.strptime(d_str, "%Y-%m-%d").date()
            if d.year == year and d.month == month:
                test_date_set.add(d)
        except:
            pass

st.subheader(f"📅 {year} 年 {month} 月（綠色為測試日期）")

cal = calendar.Calendar(firstweekday=6)  # 週日=第一欄
weeks = cal.monthdatescalendar(year, month)

html = []
html.append("<table style='border-collapse:collapse; font-size:20px;'>")
html.append("<tr>" + "".join(
    f"<th style='padding:8px 12px; border:1px solid #ddd;'>{w}</th>"
    for w in ["日","一","二","三","四","五","六"]
) + "</tr>")

for week in weeks:
    html.append("<tr>")
    for day in week:
        style = "padding:10px 14px; text-align:center; border:1px solid #ddd;"
        if day.month != month:
            style += " color:#aaa;"
        if day in test_date_set:
            style += " background: #b9f6ca; font-weight:600;"  # 淺綠
        html.append(f"<td style='{style}'>{day.day}</td>")
    html.append("</tr>")
html.append("</table>")

st.markdown("".join(html), unsafe_allow_html=True)

# ----------- 本月案件清單（顯示所有欄位）-----------
st.subheader("📑 本月案件清單（顯示所有欄位）")

def is_in_this_month(d: datetime.date) -> bool:
    return d.year == year and d.month == month

month_cases = []
for c in cases:
    show = False
    # 1) 主案件日期
    try:
        d = datetime.datetime.strptime(c.get("日期 (YYYY-MM-DD",""), "%Y-%m-%d").date()
        if is_in_this_month(d):
            show = True
    except:
        # 欄位名可能剛好沒打對，退而求其次：
        try:
            d2 = datetime.datetime.strptime(c.get("日期", ""), "%Y-%m-%d").date()
            if is_in_this_month(d2):
                show = True
        except:
            pass
    # 2) 測試日期
    for d_str in c.get("測試日期", []):
        try:
            td = datetime.datetime.strptime(d_str, "%Y-%m-%d").date()
            if is_in_this_month(td):
                show = True
        except:
            pass
    if show:
        month_cases.append(c)

if not month_cases:
    st.info("📭 本月尚無案件")
else:
    for idx, c in enumerate(month_cases, start=1):
        st.write(f"### 案件 {idx}")
        # 顯示所有欄位
        for k, v in c.items():
            st.write(f"**{k}**：{v}")
        st.divider()
