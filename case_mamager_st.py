import streamlit as st
import calendar
import datetime
import requests, json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# ============= Google Drive 設定 =============
JSON_FILE_ID = "1lI7IwoMVv49RyDuSVKNoS81jnHQ2bYYY"   # 這裡換成你上傳到 Google Drive 的 service_account.json ID
DATA_FILE_NAME = "cases.json"        # 存放案件資料的檔案名稱

@st.cache_resource
def init_drive():
    url = f"https://drive.google.com/uc?id={JSON_FILE_ID}"
    response = requests.get(url)
    service_account_info = json.loads(response.text)

    gauth = GoogleAuth()
    gauth.ServiceAccountAuth(service_account_info)
    return GoogleDrive(gauth)

drive = init_drive()

# 讀取案件資料
def load_cases():
    file_list = drive.ListFile({'q': f"title='{DATA_FILE_NAME}' and trashed=false"}).GetList()
    if not file_list:
        return []
    file_obj = file_list[0]
    content = file_obj.GetContentString()
    return json.loads(content)

# 儲存案件資料
def save_cases(cases):
    file_list = drive.ListFile({'q': f"title='{DATA_FILE_NAME}' and trashed=false"}).GetList()
    if file_list:
        file_obj = file_list[0]
    else:
        file_obj = drive.CreateFile({'title': DATA_FILE_NAME})
    file_obj.SetContentString(json.dumps(cases, ensure_ascii=False, indent=2))
    file_obj.Upload()

cases = load_cases()

# ============= Streamlit UI =============
st.set_page_config(layout="wide")
st.title("📂 案件管理系統")

# 輸入區
with st.sidebar:
    st.header("➕ 新增 / 編輯案件")
    case_id = st.text_input("案件編號")
    case_date = st.date_input("案件日期")
    case_name = st.text_input("案件名稱")
    test_dates = st.text_area("測試日期（多個日期用逗號分隔，格式 YYYY-MM-DD）")

    if st.button("💾 儲存案件"):
        new_case = {
            "案件編號": case_id,
            "案件名稱": case_name,
            "日期": str(case_date),
            "測試日期": [d.strip() for d in test_dates.split(",") if d.strip()]
        }

        # 如果案件編號已存在 → 覆蓋
        found = False
        for i, c in enumerate(cases):
            if c.get("案件編號") == case_id:
                cases[i] = new_case
                found = True
                break
        if not found:
            cases.append(new_case)

        save_cases(cases)
        st.success("✅ 案件已儲存！")
        st.experimental_rerun()

# 萬年曆顯示
today = datetime.date.today()
year, month = today.year, today.month
cal = calendar.Calendar(firstweekday=6)  # 週日開始
month_days = cal.monthdatescalendar(year, month)

st.subheader(f"📅 {year}年 {month}月")

# 標記所有測試日期
test_date_set = set()
for c in cases:
    for td in c.get("測試日期", []):
        try:
            d = datetime.datetime.strptime(td, "%Y-%m-%d").date()
            test_date_set.add(d)
        except:
            pass

# 畫萬年曆
calendar_html = "<table style='font-size:20px; border-collapse: collapse;'>"
calendar_html += "<tr>" + "".join([f"<th style='padding:5px;'>{w}</th>" for w in ["日","一","二","三","四","五","六"]]) + "</tr>"

for week in month_days:
    calendar_html += "<tr>"
    for day in week:
        style = "padding:10px; text-align:center; border:1px solid #ccc;"
        if day.month != month:
            style += "color:#aaa;"
        if day in test_date_set:
            style += " background-color:lightgreen; font-weight:bold;"
        calendar_html += f"<td style='{style}'>{day.day}</td>"
    calendar_html += "</tr>"

calendar_html += "</table>"
st.markdown(calendar_html, unsafe_allow_html=True)

# 顯示本月案件清單
st.subheader("📑 本月案件清單")
month_cases = []
for c in cases:
    show = False
    if "日期" in c:
        try:
            d = datetime.datetime.strptime(c["日期"], "%Y-%m-%d").date()
            if d.year == year and d.month == month:
                show = True
        except:
            pass
    for td in c.get("測試日期", []):
        try:
            d = datetime.datetime.strptime(td, "%Y-%m-%d").date()
            if d.year == year and d.month == month:
                show = True
        except:
            pass
    if show:
        month_cases.append(c)

if not month_cases:
    st.info("📭 本月尚無案件")
else:
    for c in month_cases:
        st.write("———")
        for k, v in c.items():
            st.write(f"**{k}**: {v}")
