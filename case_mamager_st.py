import streamlit as st
import json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

# ====== Google Drive 設定 ======
FOLDER_ID = "1Z4v2n2n7jDK5DM-f4qDW8gHy0wiM4Lr5"   # ← 換成你的 Google Drive 資料夾 ID
DATA_FILE_NAME = "cases.json"

# ====== 初始化 Google Drive ======
@st.cache_resource
def init_drive():
    service_account_info = dict(st.secrets["gcp_service_account"])
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        service_account_info,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)

    # 顯示目前使用的 Service Account
    sa_email = service_account_info.get("client_email", "(未知)")
    st.sidebar.info(f"📧 目前使用的 Service Account：{sa_email}")
    return drive

drive = init_drive()

# ====== 資料存取 ======
def load_cases():
    file_list = drive.ListFile({
        "q": f"'{FOLDER_ID}' in parents and title='{DATA_FILE_NAME}' and trashed=false"
    }).GetList()

    if file_list:
        file = file_list[0]
        file.GetContentFile(DATA_FILE_NAME)
        with open(DATA_FILE_NAME, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return []

def save_cases(cases):
    file_list = drive.ListFile({
        "q": f"'{FOLDER_ID}' in parents and title='{DATA_FILE_NAME}' and trashed=false"
    }).GetList()

    if file_list:
        file = file_list[0]
    else:
        file = drive.CreateFile({
            "title": DATA_FILE_NAME,
            "parents": [{"id": FOLDER_ID}]
        })

    with open(DATA_FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)

    file.SetContentFile(DATA_FILE_NAME)
    file.Upload()

# ====== Streamlit 主介面 ======
st.title("📂 案件管理系統")

cases = load_cases()

# ➕ 新增案件表單
with st.form("add_case_form"):
    case_name = st.text_input("案件名稱")
    case_desc = st.text_area("案件描述")
    submitted = st.form_submit_button("✅ 儲存案件")

    if submitted:
        if case_name:
            cases.append({"name": case_name, "desc": case_desc})
            save_cases(cases)
            st.success("案件已新增！")
            st.rerun()
        else:
            st.warning("請輸入案件名稱！")

# 📋 案件列表
st.subheader("📋 已有案件")

for idx, case in enumerate(cases):
    with st.expander(f"📁 {case['name']}"):
        st.write(f"**描述：** {case['desc']}")

        col1, col2, col3 = st.columns([1, 1, 6])

        # ✏ 編輯
        with col1:
            if st.button("✏ 編輯", key=f"edit_{idx}"):
                st.session_state[f"editing_{idx}"] = True

        # 🗑 刪除
        with col2:
            if st.button("🗑 刪除", key=f"delete_{idx}"):
                cases.pop(idx)
                save_cases(cases)
                st.success(f"案件「{case['name']}」已刪除")
                st.rerun()

        # 編輯模式
        if st.session_state.get(f"editing_{idx}", False):
            with st.form(f"edit_form_{idx}"):
                new_name = st.text_input("案件名稱", value=case["name"])
                new_desc = st.text_area("案件描述", value=case["desc"])
                save_edit = st.form_submit_button("💾 儲存修改")

                if save_edit:
                    case["name"] = new_name
                    case["desc"] = new_desc
                    save_cases(cases)
                    st.success(f"案件「{new_name}」已更新！")
                    st.session_state[f"editing_{idx}"] = False
                    st.rerun()
