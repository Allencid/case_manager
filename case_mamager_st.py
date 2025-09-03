import streamlit as st
import json
from datetime import datetime
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

# 這裡換成你 Google Drive 上案件 JSON 檔案的 file_id
FILE_ID = "1Z4v2n2n7jDK5DM-f4qDW8gHy0wiM4Lr5"

# ------------------------- Google Drive 初始化 -------------------------
@st.cache_resource
def init_drive():
    service_account_info = json.loads(st.secrets["DRIVE_SERVICE_ACCOUNT_JSON"])
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        service_account_info,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)
    sa_email = service_account_info.get("client_email", "(未知)")
    return drive, sa_email

def load_cases():
    drive, _ = init_drive()
    try:
        file = drive.CreateFile({'id': FILE_ID})
        content = file.GetContentString()
        cases = json.loads(content)
    except Exception as e:
        st.error(f"讀取案件失敗: {e}")
        cases = []
    return cases

def save_cases(cases):
    drive, _ = init_drive()
    try:
        file = drive.CreateFile({'id': FILE_ID})
        file.SetContentString(json.dumps(cases, ensure_ascii=False, indent=2))
        file.Upload()
    except Exception as e:
        st.error(f"儲存案件失敗: {e}")

# ------------------------- Streamlit 主程式 -------------------------
st.title("📂 案件管理系統 (Streamlit + Google Drive)")

drive, sa_email = init_drive()
st.info(f"目前使用的 Service Account：**{sa_email}**\n\n請確保你的 Google Drive 檔案已分享給這個帳號（至少編輯權限）")

cases = load_cases()

# 輸入表單
with st.form("case_form", clear_on_submit=True):
    st.subheader("新增 / 編輯案件")
    case = {}
    case["案號"] = st.text_input("案號")
    case["日期 (YYYY-MM-DD)"] = st.date_input("日期").strftime("%Y-%m-%d")
    case["委鑑單位"] = st.text_input("委鑑單位")
    case["案件名稱"] = st.text_input("案件名稱")
    case["受測人"] = st.text_input("受測人")
    case["承辦人"] = st.text_input("承辦人")

    # 多個測試日期
    test_dates = st.multiselect("測試日期 (可多選)", [])
    add_test_date = st.date_input("新增測試日期", datetime.today())
    if st.form_submit_button("➕ 加入測試日期"):
        test_dates.append(add_test_date.strftime("%Y-%m-%d"))

    case["測試日期"] = test_dates

    submitted = st.form_submit_button("✅ 儲存案件")
    if submitted:
        cases.append(case)
        save_cases(cases)
        st.success("案件已新增！")

# 顯示所有案件
st.subheader("📑 案件清單")
if not cases:
    st.write("目前沒有案件")
else:
    for i, c in enumerate(cases, 1):
        with st.expander(f"案件 {i}：{c.get('案件名稱', '未命名')}"):
            for k, v in c.items():
                st.write(f"**{k}**: {v}")
