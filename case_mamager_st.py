# -*- coding: utf-8 -*-
"""
Created on Wed Sep  3 11:30:33 2025

@author: 歐陽泰儒
"""

import streamlit as st
import json
from datetime import datetime, date
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# ------------------------- Google Drive 設定 -------------------------
gauth = GoogleAuth()
gauth.LocalWebserverAuth()  # 初次授權，會跳出瀏覽器登入
drive = GoogleDrive(gauth)

# 檔案名稱
FILE_NAME = "cases.json"

# ------------------------- 取得或建立檔案 -------------------------
def get_or_create_file():
    file_list = drive.ListFile({'q': f"title='{FILE_NAME}'"}).GetList()
    if file_list:
        return file_list[0]  # 已存在
    else:
        # 建立空 JSON
        empty_cases = []
        with open(FILE_NAME, "w", encoding="utf-8") as f:
            json.dump(empty_cases, f, ensure_ascii=False, indent=2)
        file = drive.CreateFile({'title': FILE_NAME})
        file.SetContentFile(FILE_NAME)
        file.Upload()
        return file

file = get_or_create_file()

# ------------------------- 載入/儲存 -------------------------
def load_cases():
    file.GetContentFile(FILE_NAME)
    with open(FILE_NAME, "r", encoding="utf-8") as f:
        return json.load(f)

def save_cases(cases):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)
    file.SetContentFile(FILE_NAME)
    file.Upload()

# ------------------------- Streamlit 介面 -------------------------
st.title("案件管理系統 (Google Drive 版)")

cases = load_cases()

st.sidebar.header("新增/修改案件")
with st.sidebar.form("case_form"):
    case_number = st.text_input("案號")
    case_date = st.date_input("案件日期", date.today())
    case_name = st.text_input("案件名稱")
    
    extra_fields = st.text_area("額外欄位 (格式: 欄位名=值，每行一個)", "")
    test_dates_input = st.text_area("測試日期 (多筆用逗號隔開)", "")

    submitted = st.form_submit_button("新增/更新案件")
    if submitted:
        existing_case = next((c for c in cases if c.get("案號") == case_number), None)
        if existing_case:
            cases.remove(existing_case)

        new_case = {
            "案號": case_number,
            "日期 (YYYY-MM-DD)": case_date.strftime("%Y-%m-%d"),
            "案件名稱": case_name
        }

        # 額外欄位
        if extra_fields.strip():
            for line in extra_fields.splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    new_case[k.strip()] = v.strip()

        # 測試日期
        if test_dates_input.strip():
            new_case["測試日期"] = [d.strip() for d in test_dates_input.split(",")]
        else:
            new_case["測試日期"] = []

        cases.append(new_case)
        save_cases(cases)
        st.success("案件已新增/更新！")

# ------------------------- 本月案件清單 -------------------------
st.header("本月案件清單")
today = datetime.today()
for c in cases:
    try:
        case_dt = datetime.strptime(c["日期 (YYYY-MM-DD)"], "%Y-%m-%d")
        if case_dt.year == today.year and case_dt.month == today.month:
            st.write(c)
    except:
        pass
    for d_str in c.get("測試日期", []):
        try:
            test_dt = datetime.strptime(d_str, "%Y-%m-%d")
            if test_dt.year == today.year and test_dt.month == today.month:
                st.write(c)
        except:
            continue

# ------------------------- 月曆 (測試日期綠色) -------------------------
import streamlit.components.v1 as components
from calendar import HTMLCalendar

def generate_calendar(cases):
    cal = HTMLCalendar()
    month_html = cal.formatmonth(today.year, today.month)
    for c in cases:
        for d_str in c.get("測試日期", []):
            try:
                dt = datetime.strptime(d_str, "%Y-%m-%d")
                if dt.year == today.year and dt.month == today.month:
                    day = dt.day
                    month_html = month_html.replace(f">{day}<", f' style="background-color:lightgreen;">{day}<')
            except:
                continue
    return month_html

st.header("本月測試日期標記")
st.markdown(generate_calendar(cases), unsafe_allow_html=True)
