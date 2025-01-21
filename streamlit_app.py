import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

# กำหนดชื่อไฟล์ CSV สำหรับเก็บข้อมูล
CSV_FILE = "daily_votes.csv"

# ฟังก์ชันโหลดข้อมูลโหวต
def load_votes(current_date=""):
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        if current_date == "":
            return df
        return df[df["Date"] == current_date]
    else:
        return pd.DataFrame(columns=["Date", "Question", "Vote"])

# ฟังก์ชันบันทึกข้อมูลโหวต
def save_vote(date, question, vote):
    df = load_votes()
    new_vote = pd.DataFrame([{"Date": date, "Question": question, "Vote": vote}])
    df = pd.concat([df, new_vote], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)

# สร้าง session state สำหรับการตรวจสอบว่าผู้ใช้โหวตหรือยัง
if "has_voted" not in st.session_state:
    st.session_state["has_voted"] = False
if "vote_choice" not in st.session_state:
    st.session_state["vote_choice"] = None

# CSS สำหรับปุ่ม
button_style = """
    <style>
    /* ปุ่มกระทิง (สีเขียว) */
    div.stButton > button[data-testid="stButton-bull"] {
        background-color: #4CAF50; /* สีเขียว */
        color: white;
        font-size: 20px;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        cursor: pointer;
    }
    div.stButton > button[data-testid="stButton-bull"]:hover {
        background-color: #388E3C; /* สีเขียวเข้ม */
    }

    /* ปุ่มหมี (สีแดง) */
    div.stButton > button[data-testid="stButton-bear"] {
        background-color: #f44336; /* สีแดง */
        color: white;
        font-size: 20px;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        cursor: pointer;
    }
    div.stButton > button[data-testid="stButton-bear"]:hover {
        background-color: #d32f2f; /* สีแดงเข้ม */
    }
    </style>
"""

# ใส่ CSS ลงใน Streamlit
st.markdown(button_style, unsafe_allow_html=True)

# ส่วน UI
st.title("ระบบโหวตความคิดเห็นรายวัน")
st.write("โหวตของคุณจะช่วยให้เราประมวลผลความคิดเห็นของตลาดหุ้นได้!")

# คำถามสำหรับวันนี้
question = "คุณรู้สึกอย่างไรกับตลาดหุ้นตอนนี้? (กระทิง / หมี)"
current_date = datetime.now().strftime("%Y-%m-%d")

# โหลดข้อมูลโหวต
votes_data = load_votes(current_date)


#if not st.session_state["has_voted"]:
if not st.session_state.get("has_voted", False):
    # แสดงคำถาม
    st.subheader(f"คำถามสำหรับวันที่ {current_date}")
    st.write(question)

    # ปุ่มสำหรับตัวเลือกการโหวต
    col1, col2 = st.columns(2)
    with col1:
        if st.button("กระทิง 🐂", key="bull"):
            save_vote(current_date, question, "กระทิง")
            st.session_state["has_voted"] = True
            st.session_state["vote_choice"] = "กระทิง"
            # st.experimental_rerun() fix bug กรณี deploy ขึ้นไป 

    with col2:
        if st.button("หมี 🐻", key="bear"):
            save_vote(current_date, question, "หมี")
            st.session_state["has_voted"] = True
            st.session_state["vote_choice"] = "หมี"
            # st.experimental_rerun()

#if st.session_state["has_voted"]:
if st.session_state.get("has_voted", False):
    # แสดงผลโหวตของผู้ใช้
    st.subheader("ผลโหวตของคุณ")
    st.write(f"คุณโหวต: **{st.session_state['vote_choice']}**")

    # แสดงผลโหวตทั้งหมด
    st.subheader("ผลโหวตทั้งหมด")
    if not votes_data.empty:
        grouped_votes = votes_data.groupby(["Date", "Vote"]).size().reset_index(name="Count")
        st.write("**ผลรวมของการโหวตแต่ละวัน**")
        st.dataframe(grouped_votes)

        # สร้าง Bar Chart
        st.subheader("แผนภูมิแท่งแสดงผลโหวต")
        grouped_votes["Date"] = pd.to_datetime(grouped_votes["Date"]).dt.strftime("%Y-%m-%d")
        bar_chart = px.bar(
            grouped_votes,
            x="Date",
            y="Count",
            color="Vote",
            barmode="group",
            labels={"Date": "วันที่", "Count": "จำนวนโหวต", "Vote": "ตัวเลือก"},
            title="ผลรวมคะแนนโหวตในแต่ละวัน",
        )
        st.plotly_chart(bar_chart)


        # สร้างคอลัมน์ใหม่สำหรับคะแนน
        votes_data = load_votes()
        votes_data["Score"] = votes_data["Vote"].apply(lambda x: 1 if x == "กระทิง" else -1)
        # สรุปผลรายวัน
        daily_summary = votes_data.groupby("Date")["Score"].sum().reset_index()
        # คำนวณค่า cumsum
        daily_summary["Cumulative Score"] = daily_summary["Score"].cumsum()
        # แสดง DataFrame
        st.subheader("สรุปผลคะแนนสะสมรายวัน")
        st.dataframe(daily_summary)
        # สร้างกราฟเส้น
        st.subheader("กราฟแสดงผลคะแนนสะสมรายวัน (Cumulative Sum)")
        line_chart = px.line(
            daily_summary,
            x="Date",
            y="Cumulative Score",
            labels={"Date": "วันที่", "Cumulative Score": "คะแนนสะสม"},
            title="กราฟคะแนนสะสมรายวัน (Cumulative Sum)",
        )
        st.plotly_chart(line_chart)

    else:
        st.write("ยังไม่มีข้อมูลโหวตในระบบ")

    # ปุ่ม Reset
    if st.button("back"):
        # รีเซ็ตค่า session_state และกลับไปหน้าเริ่มต้น
        st.session_state["has_voted"] = False
        st.session_state["vote_choice"] = None

        # st.experimental_rerun()
        # st.session_state.clear()
