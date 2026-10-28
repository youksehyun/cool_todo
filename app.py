import streamlit as st
import json
import os
import uuid
from datetime import datetime, timedelta

# 페이지 기본 설정
st.set_page_config(page_title="캘린더 기반 루틴 TODO", page_icon="📅", layout="wide")

DATA_FILE = "todos.json"

# ==========================================
# 1. 공통 데이터 I/O 로직
# ==========================================
def load_todos():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_todos(todos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

# 세션 상태(State) 초기화
if "todos" not in st.session_state:
    st.session_state.todos = load_todos()

if "selected_date" not in st.session_state:
    st.session_state.selected_date = datetime.now().date()

today_str = datetime.now().strftime("%Y-%m-%d")

# ==========================================
# 2. 상단 전체 요약 브리핑 (SummaryModal 역할)
# ==========================================
st.title("📅 캘린더 기반 루틴 TODO")

today_items = [t for t in st.session_state.todos if t.get("date") == today_str]
routines = {}
for t in st.session_state.todos:
    if t.get("is_routine"):
        r_id = t.get("routine_id", t.get("title"))
        if r_id not in routines:
            routines[r_id] = t

with st.expander("📋 나의 일정 & 루틴 한눈에 보기 (접속 요약)", expanded=True):
    col_sum1, col_sum2 = st.columns(2)
    with col_sum1:
        st.markdown(f"**📌 오늘의 할 일 ({len(today_items)}개)**")
        if today_items:
            for t in today_items:
                status = "✔ 완료" if t.get("is_completed") else "⏳ 미완료"
                prefix = "[루틴] " if t.get("is_routine") else ""
                st.write(f"- {prefix}**{t.get('title')}** ({status})")
        else:
            st.info("오늘 등록된 할 일이 없습니다.")

    with col_sum2:
        st.markdown(f"**🔄 진행 중인 루틴 ({len(routines)}개)**")
        if routines:
            for r in routines.values():
                mode = "매일" if r.get("repeat_mode") == "daily" else "평일만"
                st.write(f"- 🔄 **{r.get('title')}** (주기: {mode})")
        else:
            st.info("등록된 루틴이 없습니다.")

st.markdown("---")

# ==========================================
# 3. 메인 레이아웃 (좌측: 캘린더 / 우측: TODO)
# ==========================================
col_left, col_right = st.columns([1, 1.4], gap="large")

# [좌측 영역] 달력 선택 및 새 루틴 등록
with col_left:
    st.subheader("달력 선택")
    
    picked_date = st.date_input(
        "날짜를 선택하세요", 
        value=st.session_state.selected_date,
        label_visibility="collapsed"
    )
    if picked_date != st.session_state.selected_date:
        st.session_state.selected_date = picked_date
        st.rerun()
        
    sel_date_str = st.session_state.selected_date.strftime("%Y-%m-%d")
    st.info(f"선택된 날짜: **{sel_date_str}**")

    st.markdown("---")
    
    st.subheader("➕ 새 루틴 등록")
    with st.form("routine_create_form"):
        r_title = st.text_input("루틴 이름", placeholder="예: 매일 운동")
        r_mode = st.radio("반복 방식", options=["daily", "weekdays"], format_func=lambda x: "매일 (월~일)" if x == "daily" else "평일만 (월~금)")
        r_days = st.number_input("반복 기간 (일수)", min_value=1, max_value=60, value=14, step=1)
        r_submit = st.form_submit_button("루틴 일괄 생성", use_container_width=True)

        if r_submit and r_title.strip():
            start_d = datetime.now()
            new_routine_id = f"rt_{uuid.uuid4().hex[:6]}"
            new_items = []
            
            for i in range(int(r_days)):
                target = start_d + timedelta(days=i)
                if r_mode == "weekdays" and target.weekday() >= 5:
                    continue
                new_items.append({
                    "id": uuid.uuid4().hex[:8],
                    "title": r_title.strip(),
                    "date": target.strftime("%Y-%m-%d"),
                    "is_completed": False,
                    "is_routine": True,
                    "routine_id": new_routine_id,
                    "repeat_mode": r_mode
                })
            
            st.session_state.todos.extend(new_items)
            save_todos(st.session_state.todos)
            st.success(f"총 {len(new_items)}개의 루틴 일정이 등록되었습니다!")
            st.rerun()

# [우측 영역] 선택된 날짜의 할 일 CRUD 관리
with col_right:
    sel_date_str = st.session_state.selected_date.strftime("%Y-%m-%d")
    st.subheader(f"📝 {sel_date_str} 할 일 목록")

    # 할 일 추가 입력창
    col_in, col_btn = st.columns([4, 1])
    with col_in:
        new_todo_title = st.text_input("할 일 입력", placeholder="새로운 할 일을 입력하세요...", label_visibility="collapsed")
    with col_btn:
        if st.button("추가", use_container_width=True, type="primary"):
            if new_todo_title.strip():
                item = {
                    "id": uuid.uuid4().hex[:8],
                    "title": new_todo_title.strip(),
                    "date": sel_date_str,
                    "is_completed": False,
                    "is_routine": False
                }
                st.session_state.todos.append(item)
                save_todos(st.session_state.todos)
                st.rerun()

    st.markdown("---")

    day_todos = [t for t in st.session_state.todos if t.get("date") == sel_date_str]

    if not day_todos:
        st.write("등록된 할 일이 없습니다. 새 할 일을 등록해보세요!")
    else:
        for todo in day_todos:
            t_id = todo.get("id")
            c_check, c_text, c_del = st.columns([0.8, 4.2, 1])
            
            with c_check:
                checked = st.checkbox("", value=todo.get("is_completed", False), key=f"chk_{t_id}")
                if checked != todo.get("is_completed", False):
                    todo