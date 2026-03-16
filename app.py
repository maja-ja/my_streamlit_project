import streamlit as st
from supabase import create_client, Client
from datetime import datetime

# ==========================================
# 1. 頁面設定與自定義 CSS (粗獷主義美學)
# ==========================================
st.set_page_config(page_title="RAW NOTES", page_icon="logo.png", layout="centered")

def apply_custom_css():
    st.markdown("""
        <style>
        html, body, [class*="css"] { font-family: "Courier New", Courier, "Noto Sans TC", monospace !important; }
        header {visibility: hidden;} footer {visibility: hidden;}
        
        /* 按鈕樣式 */
        .stButton > button {
            border: 2px solid #000000 !important; border-radius: 0px !important;
            color: #000000 !important; background-color: #ffffff !important;
            font-weight: 900 !important; text-transform: uppercase !important;
            transition: all 0.1s; width: 100%;
        }
        .stButton > button:hover { transform: translate(2px, 2px); box-shadow: none; }
        .stButton > button:active { background-color: #000000 !important; color: #ffffff !important; }
        button[kind="primary"] { background-color: #000000 !important; color: #ffffff !important; }
        button[kind="primary"]:active { background-color: #333333 !important; }
        
        /* 輸入框樣式 */
        .stTextInput > div > div > input, .stTextArea > div > div > textarea {
            border: 2px solid #000000 !important; border-radius: 0px !important;
            font-family: "Courier New", Courier, monospace !important; font-weight: bold;
        }
        h1, h2, h3 { font-weight: 900 !important; text-transform: uppercase; letter-spacing: -1px; }
        
        /* 卡片容器樣式 */[data-testid="stVerticalBlock"] > [style*="flex-direction: column"] {
            border: 2px solid black; padding: 10px; background-color: #ffffff;
        }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. Supabase 資料庫連線初始化
# ==========================================
@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
except Exception as e:
    st.error("⚠️ 無法連線至 Supabase，請確認 .streamlit/secrets.toml 設定是否正確。")
    st.stop()

# 初始化 Session 狀態
if "user" not in st.session_state:
    st.session_state.user = None
if "notes" not in st.session_state:
    st.session_state.notes =[]
if "page" not in st.session_state:
    st.session_state.page = "home"
if "current_id" not in st.session_state:
    st.session_state.current_id = None

# ==========================================
# 3. 資料庫操作函數 (CRUD)
# ==========================================
def fetch_notes():
    if st.session_state.user:
        try:
            res = supabase.table("notes").select("*").eq("user_id", st.session_state.user.id).order("id", desc=True).execute()
            st.session_state.notes = res.data
        except Exception as e:
            st.error(f"讀取筆記失敗: {e}")

def save_note_to_db(note):
    try:
        supabase.table("notes").upsert(note).execute()
    except Exception as e:
        st.error(f"儲存失敗: {e}")

def delete_note_from_db(note_id):
    try:
        supabase.table("notes").delete().eq("id", note_id).execute()
    except Exception as e:
        st.error(f"刪除失敗: {e}")

# ==========================================
# 4. 身份驗證畫面 (LOGIN / SIGN UP)
# ==========================================
def render_auth():
    st.markdown("<h1 style='text-align:center; font-size:40px;'>RAW NOTES</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-weight:900;'>ACCESS YOUR SECURE VAULT</p>", unsafe_allow_html=True)
    
    st.divider()
    
    email = st.text_input("EMAIL", placeholder="user@example.com")
    password = st.text_input("PASSWORD", type="password", placeholder="••••••••")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("LOGIN", type="primary"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                fetch_notes()
                st.rerun()
            except Exception:
                st.error("❌ 登入失敗：帳號或密碼錯誤！")
    with col2:
        if st.button("SIGN UP"):
            try:
                res = supabase.auth.sign_up({"email": email, "password": password})
                st.success("✅ 註冊成功！請直接點擊 LOGIN 登入。")
            except Exception:
                st.error("❌ 註冊失敗：密碼需至少 6 位數或帳號已存在。")

# ==========================================
# 5. 核心畫面邏輯
# ==========================================
def go_to_edit(note_id=None):
    if note_id is None:
        now = datetime.now()
        new_note = {
            "id": int(now.timestamp() * 1000), # 確保 ID 唯一性
            "user_id": st.session_state.user.id,
            "title": "",
            "content": "",
            "tags": "",
            "date": now.strftime("%b %d").upper(),
            "time": now.strftime("%H:%M")
        }
        st.session_state.notes.insert(0, new_note)
        st.session_state.current_id = new_note["id"]
    else:
        st.session_state.current_id = note_id
    st.session_state.page = "edit"

def go_to_home():
    fetch_notes() # 回到首頁時強制刷新資料以同步雲端
    st.session_state.page = "home"
    st.session_state.current_id = None

@st.dialog("SUPPORT RAW")
def show_support_modal():
    st.markdown("<h2 style='text-align:center;'>SUPPORT RAW</h2>", unsafe_allow_html=True)
    st.markdown("""
    <div style='border: 4px solid #000; padding: 15px; text-align: center; margin-bottom: 20px; background: #fff;'>
        <div style='font-size: 14px; font-weight: 900; color: #000; margin-bottom: 15px; letter-spacing: 1px;'>
            SCAN TO SUPPORT
        </div>
    """, unsafe_allow_html=True)
    try:
        st.image("qrcode.png", use_container_width=True)
    except FileNotFoundError:
        st.error("⚠️ 找不到 `qrcode.png`！")
    st.markdown("</div>", unsafe_allow_html=True)
    
    if st.button("CLOSE"):
        st.rerun()

def render_home():
    col1, col2, col3 = st.columns([1, 4, 1], vertical_alignment="center")
    with col1:
        try:
            st.image("logo.png", use_container_width=True)
        except:
            st.markdown("<h1>📝</h1>", unsafe_allow_html=True)
    with col2:
        st.markdown("<h1 style='margin-bottom:0px;'>RAW NOTES</h1>", unsafe_allow_html=True)
    with col3:
        if st.button("LOGOUT"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.session_state.notes =[]
            st.session_state.page = "home"
            st.rerun()

    # 搜尋過濾器
    search_query = st.text_input("🔍 FILTER...", placeholder="Type to search...").lower()
    
    filtered_notes =[n for n in st.session_state.notes if 
                      search_query in (n.get("title") or "").lower() or 
                      search_query in (n.get("content") or "").lower() or 
                      search_query in (n.get("tags") or "").lower()]
    
    if not filtered_notes:
        st.markdown("<br><br><h3 style='text-align:center; opacity:0.3;'>NO_DATA_FOUND</h3><br><br>", unsafe_allow_html=True)
    else:
        cols = st.columns(2)
        for i, note in enumerate(filtered_notes):
            with cols[i % 2]:
                with st.container(border=True):
                    st.caption(f"🕒 {note['date']} {note['time']}")
                    st.markdown(f"**{note['title'] or 'UNTITLED'}**")
                    
                    content_str = note['content'] if note['content'] else ""
                    content_preview = content_str[:50] + "..." if len(content_str) > 50 else content_str
                    st.write(content_preview)
                    
                    if note['tags']:
                        st.markdown(f"`{note['tags']}`")
                    if st.button("EDIT", key=f"edit_{note['id']}"):
                        go_to_edit(note["id"])
                        st.rerun()

    st.divider()
    c1, c2 = st.columns([2, 1])
    with c1:
        if st.button("＋ NEW NOTE", type="primary"):
            go_to_edit(None)
            st.rerun()
    with c2:
        if st.button("GIFT 💛"):
            show_support_modal()

def render_edit():
    try:
        note_idx = next(i for i, n in enumerate(st.session_state.notes) if n["id"] == st.session_state.current_id)
        note = st.session_state.notes[note_idx]
    except StopIteration:
        go_to_home()
        st.rerun()

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← BACK"):
            # 如果是空筆記，離開時自動刪除
            if not (note.get("title") or "").strip() and not (note.get("content") or "").strip():
                delete_note_from_db(note["id"])
            go_to_home()
            st.rerun()
    with col2:
        st.caption(f"CREATED: {note['date']} {note['time']}")

    new_title = st.text_input("TITLE", value=note.get("title", ""), placeholder="UNTITLED")
    new_tags = st.text_input("TAGS", value=note.get("tags", ""), placeholder="#TAGS")
    new_content = st.text_area("CONTENT", value=note.get("content", ""), placeholder="WRITE_HERE...", height=300)

    # 暫存於 Session
    st.session_state.notes[note_idx]["title"] = new_title
    st.session_state.notes[note_idx]["tags"] = new_tags
    st.session_state.notes[note_idx]["content"] = new_content

    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💾 SAVE", type="primary"):
            save_note_to_db(st.session_state.notes[note_idx])
            st.success("SAVED ✓")
    with c2:
        if st.button("📋 COPY"):
            st.info("請手動選取文字複製")
    with c3:
        if st.button("🗑️ DELETE"):
            delete_note_from_db(note["id"])
            go_to_home()
            st.rerun()

# ==========================================
# 6. 主程式路由
# ==========================================
apply_custom_css()

if st.session_state.user is None:
    render_auth()
elif st.session_state.page == "home":
    render_home()
else:
    render_edit()