import streamlit as st
import pandas as pd
import requests
import json
import time
import re
import hashlib
from datetime import date, timedelta

st.set_page_config(page_title="中餐友善點餐系統", page_icon="🍱", layout="wide")

APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbw0UEIp80umbupbDQkMQAa5-3Z4HQp01r9VH_Zr-0nYnPzXv6jgY_gKYFyScn7e2Lrj/exec"
SHEET_ID = "1mHnXoG-Duq45EvwZTRVuq86rsK8T5DA9NkLnOi30wuM"
ORDERS_GID = "1002"

SVG_100 = """<svg width="180" height="90" viewBox="0 0 180 90" xmlns="http://www.w3.org/2000/svg" style="border-radius:6px; box-shadow:2px 3px 6px rgba(0,0,0,0.3); margin:4px;"><rect width="180" height="90" rx="6" fill="#C53030"/><rect x="4" y="4" width="172" height="82" rx="4" fill="none" stroke="#FED7D7" stroke-width="1.5" stroke-dasharray="4,2"/><circle cx="45" cy="45" r="22" fill="#9B2C2C"/><circle cx="45" cy="45" r="18" fill="none" stroke="#FEB2B2" stroke-width="1"/><text x="45" y="52" font-family="sans-serif" font-size="20" font-weight="bold" fill="#FED7D7" text-anchor="middle">100</text><text x="135" y="55" font-family="sans-serif" font-size="44" font-weight="900" fill="#FFFFFF" text-anchor="middle">100</text><text x="90" y="22" font-family="sans-serif" font-size="12" font-weight="bold" fill="#FED7D7" text-anchor="middle">中華民國中央銀行</text><text x="135" y="75" font-family="sans-serif" font-size="14" font-weight="bold" fill="#FEEBC8" text-anchor="middle">壹佰圓</text></svg>"""
SVG_50 = """<svg width="84" height="84" viewBox="0 0 84 84" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(2px 3px 4px rgba(0,0,0,0.35)); margin:4px;"><circle cx="42" cy="42" r="40" fill="#D69E2E" stroke="#744210" stroke-width="2"/><circle cx="42" cy="42" r="34" fill="#ECC94B" stroke="#B7791F" stroke-width="1.5"/><circle cx="42" cy="42" r="26" fill="#D69E2E"/><text x="42" y="49" font-family="sans-serif" font-size="28" font-weight="900" fill="#5A3207" text-anchor="middle">50</text><text x="42" y="61" font-family="sans-serif" font-size="11" font-weight="bold" fill="#744210" text-anchor="middle">圓</text></svg>"""
SVG_10 = """<svg width="76" height="76" viewBox="0 0 76 76" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(2px 3px 4px rgba(0,0,0,0.3)); margin:4px;"><circle cx="38" cy="38" r="36" fill="#A0AEC0" stroke="#4A5568" stroke-width="2"/><circle cx="38" cy="38" r="30" fill="#E2E8F0" stroke="#718096" stroke-width="1.5"/><text x="38" y="44" font-family="sans-serif" font-size="26" font-weight="900" fill="#2D3748" text-anchor="middle">10</text><text x="38" y="56" font-family="sans-serif" font-size="11" font-weight="bold" fill="#4A5568" text-anchor="middle">圓</text></svg>"""
SVG_5 = """<svg width="66" height="66" viewBox="0 0 66 66" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(2px 3px 4px rgba(0,0,0,0.3)); margin:4px;"><circle cx="33" cy="33" r="31" fill="#CBD5E0" stroke="#718096" stroke-width="2"/><circle cx="33" cy="33" r="25" fill="#EDF2F7" stroke="#A0AEC0" stroke-width="1"/><text x="33" y="39" font-family="sans-serif" font-size="22" font-weight="900" fill="#2D3748" text-anchor="middle">5</text><text x="33" y="49" font-family="sans-serif" font-size="10" font-weight="bold" fill="#4A5568" text-anchor="middle">圓</text></svg>"""
SVG_1 = """<svg width="58" height="58" viewBox="0 0 58 58" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(2px 3px 4px rgba(0,0,0,0.3)); margin:4px;"><circle cx="29" cy="29" r="27" fill="#DD6B20" stroke="#7B341E" stroke-width="2"/><circle cx="29" cy="29" r="21" fill="#ED8936" stroke="#9C4221" stroke-width="1"/><text x="29" y="35" font-family="sans-serif" font-size="20" font-weight="900" fill="#431407" text-anchor="middle">1</text><text x="29" y="45" font-family="sans-serif" font-size="10" font-weight="bold" fill="#652B19" text-anchor="middle">圓</text></svg>"""

if "tts_speak_text" not in st.session_state:
    st.session_state.tts_speak_text = None

def queue_speech(text):
    st.session_state.tts_speak_text = str(text).replace("'", "").replace('"', "")

def render_speech_player():
    if st.session_state.tts_speak_text:
        txt = st.session_state.tts_speak_text
        st.session_state.tts_speak_text = None
        st.components.v1.html(f"""
        <script>
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel();
                var msg = new SpeechSynthesisUtterance('{txt}');
                msg.lang = 'zh-TW';
                msg.rate = 0.95;
                window.speechSynthesis.speak(msg);
            }}
        </script>
        """, height=0)

def get_current_workweek_dates():
    today = date.today()
    if today.weekday() >= 5:
        monday = today + timedelta(days=(7 - today.weekday()))
    else:
        monday = today - timedelta(days=today.weekday())
    
    workweek = []
    weekdays_zh = ["週一", "週二", "週三", "週四", "週五"]
    for i in range(5):
        d = monday + timedelta(days=i)
        is_today = (d == today)
        label = f"{'🌟 ' if is_today else ''}{weekdays_zh[i]}\n{d.strftime('%m/%d')}"
        workweek.append({"date": d, "label": label, "is_today": is_today, "weekday_zh": weekdays_zh[i]})
    return workweek

def get_category_icon(cat_name):
    cat_str = str(cat_name).strip()
    if "全部" in cat_str: return f"🍽️ {cat_str}"
    elif "便當" in cat_str: return f"🍱 {cat_str}"
    elif "水餃" in cat_str: return f"🥟 {cat_str}"
    elif "鍋貼" in cat_str: return f"🥟🔥 {cat_str}"
    elif "湯" in cat_str: return f"🥣 {cat_str}"
    elif "飯" in cat_str: return f"🍚 {cat_str}"
    elif "麵" in cat_str or "意麵" in cat_str or "冬粉" in cat_str: return f"🍜 {cat_str}"
    elif "飲" in cat_str or "茶" in cat_str: return f"🥤 {cat_str}"
    elif "小菜" in cat_str or "切" in cat_str or "炸" in cat_str: return f"🥗 {cat_str}"
    else: return f"🥢 {cat_str}"

def get_food_aac_icon(item_name, category=""):
    s = f"{item_name} {category}"
    if "鍋貼" in s: return "🥟🔥"
    elif "水餃" in s or "蒸餃" in s: return "🥟"
    elif "便當" in s or "飯包" in s or "招牌飯" in s: return "🍱"
    elif "滷肉飯" in s or "肉燥飯" in s or "排骨" in s or "雞腿" in s: return "🍖🍚"
    elif "炒飯" in s or "燴飯" in s: return "🍛"
    elif "意麵" in s or "油麵" in s or "鍋燒" in s: return "🍜"
    elif "冬粉" in s or "米粉" in s or "板條" in s: return "🍲"
    elif "湯" in s: return "🥣"
    elif "飲" in s or "茶" in s or "豆漿" in s or "紅茶" in s: return "🥤"
    elif "蛋" in s or "小菜" in s or "豆干" in s: return "🥗"
    else: return "🍱"

st.markdown("""
<style>
    html { scroll-behavior: smooth; }
    html, body, [class*="css"] { font-size: 24px; font-weight: 700; }

    /* 頂部主導航分頁大按鍵 */
    .nav-tab-btn button {
        width: 100% !important; min-height: 85px !important;
        font-size: 26px !important; font-weight: 900 !important;
        border-radius: 18px !important; border: 3px solid #CBD5E1 !important;
        background-color: #F8FAFC !important; color: #475569 !important;
        margin-bottom: 20px !important;
    }
    .nav-tab-btn-active button {
        width: 100% !important; min-height: 85px !important;
        font-size: 26px !important; font-weight: 900 !important;
        border-radius: 18px !important; border: 4px solid #1D4ED8 !important;
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 6px 16px rgba(37,99,235,0.35) !important;
        margin-bottom: 20px !important;
    }

    .aac-step-banner {
        background-color: #FEF3C7;
        border-left: 12px solid #F59E0B;
        border-radius: 18px;
        padding: 20px 24px;
        font-size: 34px !important;
        font-weight: 900 !important;
        color: #78350F !important;
        margin-bottom: 22px;
    }

    .screen-choice-tile button {
        width: 100% !important;
        min-height: 160px !important;
        font-size: 30px !important;
        font-weight: 900 !important;
        border-radius: 26px !important;
        border: 4.5px solid #2563EB !important;
        background: linear-gradient(135deg, #FFFFFF 0%, #F0F9FF 100%) !important;
        color: #0F172A !important;
        box-shadow: 0 8px 18px rgba(37,99,235,0.16) !important;
        margin-bottom: 18px !important;
        white-space: pre-line !important;
        line-height: 1.35 !important;
        transition: all 0.15s ease-in-out !important;
    }
    .screen-choice-tile button:hover {
        background: #DBEAFE !important;
        border-color: #1D4ED8 !important;
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(29,78,216,0.25) !important;
    }

    .spec-choice-tile button {
        width: 100% !important;
        min-height: 140px !important;
        font-size: 28px !important;
        font-weight: 900 !important;
        border-radius: 22px !important;
        border: 4px solid #059669 !important;
        background: linear-gradient(135deg, #FFFFFF 0%, #ECFDF5 100%) !important;
        color: #064E3B !important;
        box-shadow: 0 6px 14px rgba(5,150,105,0.18) !important;
        margin-bottom: 16px !important;
        white-space: pre-line !important;
    }
    .spec-choice-tile button:hover {
        background: #D1FAE5 !important;
        border-color: #047857 !important;
        transform: translateY(-3px);
    }

    div[data-testid="stButton"] button[kind="primary"] {
        width: 100% !important;
        min-height: 95px !important;
        font-size: 30px !important;
        font-weight: 900 !important;
        border-radius: 22px !important;
        border: 4px solid #C2410C !important;
        background: linear-gradient(135deg, #FF6B00 0%, #EA580C 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 6px 16px rgba(234,88,12,0.4) !important;
        white-space: pre-line !important;
        line-height: 1.3 !important;
    }

    .user-btn button {
        width: 100% !important; min-height: 120px !important;
        font-size: 32px !important; font-weight: 900 !important;
        border-radius: 22px !important; border: 4.5px solid #22C55E !important;
        background-color: #F0FDF4 !important; color: #166534 !important;
        margin-bottom: 18px !important; white-space: pre-line !important;
    }
    .user-btn-done button {
        width: 100% !important; min-height: 120px !important;
        font-size: 30px !important; font-weight: 900 !important;
        border-radius: 22px !important; border: 3.5px solid #94A3B8 !important;
        background-color: #F1F5F9 !important; color: #64748B !important;
        margin-bottom: 18px !important; white-space: pre-line !important;
    }

    .store-btn button {
        width: 100% !important; min-height: 130px !important;
        font-size: 32px !important; font-weight: 900 !important;
        border-radius: 24px !important; border: 4.5px solid #F59E0B !important;
        background-color: #FFFBEB !important; color: #92400E !important;
        margin-bottom: 18px !important;
    }

    .date-btn button {
        width: 100% !important; min-height: 110px !important;
        font-size: 28px !important; font-weight: 900 !important;
        border-radius: 22px !important; border: 3.5px solid #CBD5E1 !important;
        background-color: #F8FAFC !important; color: #1E293B !important;
        white-space: pre-line !important;
    }

    .big-pay-card {
        background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
        border: 5px solid #22C55E;
        border-radius: 26px;
        padding: 34px 26px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 10px 28px rgba(34,197,94,0.25);
    }

    .added-feedback-card {
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        border: 4.5px solid #2563EB;
        border-radius: 26px;
        padding: 28px;
        text-align: center;
        margin-bottom: 24px;
        box-shadow: 0 10px 24px rgba(37,99,235,0.25);
    }

    .money-visual-board {
        background-color: #FFFFFF; border: 3.5px dashed #60A5FA;
        border-radius: 20px; padding: 22px; margin-top: 16px; margin-bottom: 16px;
    }
    .money-group-row {
        display: flex; flex-wrap: wrap; align-items: center; gap: 14px;
        margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px solid #F1F5F9;
    }

    .float-top-btn {
        position: fixed; bottom: 25px; left: 25px; z-index: 99999;
        background-color: #0284C7; color: white !important;
        width: 75px; height: 75px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 34px; font-weight: bold; text-decoration: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3); border: 2px solid white;
    }

    .category-filter-btn button {
        width: 100% !important; min-height: 72px !important;
        font-size: 24px !important; font-weight: 900 !important;
        border-radius: 18px !important; border: 3px solid #94A3B8 !important;
        background-color: #F8FAFC !important; color: #334155 !important;
        margin-bottom: 10px !important;
    }
    .category-filter-active button {
        width: 100% !important; min-height: 72px !important;
        font-size: 24px !important; font-weight: 900 !important;
        border-radius: 18px !important; border: 4px solid #1D4ED8 !important;
        background-color: #2563EB !important; color: #FFFFFF !important;
        margin-bottom: 10px !important; box-shadow: 0 4px 12px rgba(37,99,235,0.35) !important;
    }

    .order-row-card {
        background-color: #FFFFFF; border: 1.5px solid #E2E8F0;
        border-radius: 14px; padding: 16px 20px; margin-bottom: 14px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }
    .receipt-box {
        background-color: #FFFFFF; border: 2px dashed #475569;
        border-radius: 16px; padding: 24px; margin-top: 16px; margin-bottom: 24px;
    }
    .receipt-header {
        text-align: center; border-bottom: 2px dashed #94A3B8;
        padding-bottom: 16px; margin-bottom: 18px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div id="top_anchor"></div>', unsafe_allow_html=True)
st.markdown('<a href="#top_anchor" class="float-top-btn" title="回頂端">⬆️</a>', unsafe_allow_html=True)

REQUIRED_ORDER_COLS = ["訂單編號", "訂購日期", "員工編號", "員工姓名", "所屬部門", "餐點品項", "麵類選擇", "是否加麵", "單價", "數量", "小計金額", "付款狀態"]

def safe_key(prefix, text, idx=0):
    clean_txt = hashlib.md5(str(text).encode('utf-8')).hexdigest()[:8]
    return f"{prefix}_{idx}_{clean_txt}"

def parse_price(val):
    try:
        clean = str(val).replace("$", "").replace(",", "").strip()
        v = float(clean)
        return int(v) if v.is_integer() else round(v, 2)
    except:
        return 0.0

def fmt_price(val):
    try:
        v = float(str(val).replace("$", "").replace(",", "").strip())
        return f"{int(v)}" if v.is_integer() else f"{v:.1f}".rstrip('0').rstrip('.')
    except:
        return "0"

def parse_extra_price(option_text):
    match = re.search(r"\+(\d+(?:\.\d+)?)", str(option_text))
    if match:
        v = float(match.group(1))
        return int(v) if v.is_integer() else v
    return 0

def load_menu():
    try:
        t = int(time.time() * 1000)
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=menu&_t={t}"
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        if "種類選擇" in df.columns and "麵類選擇" not in df.columns:
            df.rename(columns={"種類選擇": "麵類選擇"}, inplace=True)
        return df.dropna(subset=["餐點名稱"]) if "餐點名稱" in df.columns else df
    except:
        return pd.DataFrame()

def load_users():
    try:
        t = int(time.time() * 1000)
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=users&_t={t}"
        df = pd.read_csv(url)
        return df.dropna(subset=["姓名"]) if "姓名" in df.columns else df
    except:
        return pd.DataFrame()

def load_orders_from_sheet():
    t = int(time.time() * 1000)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={ORDERS_GID}&_t={t}"
    try:
        raw_df = pd.read_csv(url, header=None)
        h_idx = 3
        for i in range(min(10, len(raw_df))):
            if any("訂單編號" in str(v) or "員工姓名" in str(v) for v in raw_df.iloc[i].tolist()):
                h_idx = i
                break
        df = pd.read_csv(url, header=h_idx)
        df.columns = [str(c).strip() for c in df.columns]
        for req in REQUIRED_ORDER_COLS:
            if req not in df.columns:
                df[req] = ""
        df = df.dropna(subset=["員工姓名"])
        return df[df["員工姓名"].astype(str).str.strip() != ""].reset_index(drop=True)
    except:
        return pd.DataFrame(columns=REQUIRED_ORDER_COLS)

def sync_to_google_sheet(payload):
    try:
        resp = requests.post(APPS_SCRIPT_URL, data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                             headers={"Content-Type": "text/plain;charset=utf-8"}, timeout=20)
        return True, resp.text
    except Exception as e:
        return False, str(e)

# 鎖定主導航分頁（避免 rerun 後跳回點餐頁）
if "active_main_tab" not in st.session_state:
    st.session_state.active_main_tab = "tab_order"

if "order_step" not in st.session_state:
    st.session_state.order_step = "DATE"
if "target_order_date" not in st.session_state:
    st.session_state.target_order_date = date.today()
if "selected_user" not in st.session_state:
    st.session_state.selected_user = None
if "user_daily_limit" not in st.session_state:
    st.session_state.user_daily_limit = 0.0
if "selected_store" not in st.session_state:
    st.session_state.selected_store = None
if "selected_category" not in st.session_state:
    st.session_state.selected_category = "全部"

if "current_picking_item" not in st.session_state:
    st.session_state.current_picking_item = None
if "picked_spec" not in st.session_state:
    st.session_state.picked_spec = "標準份量"

if "cart" not in st.session_state:
    st.session_state.cart = []
if "orders_data" not in st.session_state:
    st.session_state.orders_data = load_orders_from_sheet()
if "last_order_total" not in st.session_state:
    st.session_state.last_order_total = 0.0

def reset_ordering():
    st.session_state.order_step = "DATE"
    st.session_state.selected_user = None
    st.session_state.selected_store = None
    st.session_state.selected_category = "全部"
    st.session_state.user_daily_limit = 0.0
    st.session_state.current_picking_item = None
    st.session_state.picked_spec = "標準份量"
    st.session_state.cart = []
    st.session_state.last_order_total = 0.0

df_menu = load_menu()
df_users = load_users()

render_speech_player()

st.title("🍱 中餐友善點餐系統")

# 頂部受控主分頁導航（保證切換與重整時不跳頁）
nav_col1, nav_col2, nav_col3 = st.columns(3)
with nav_col1:
    is_active = (st.session_state.active_main_tab == "tab_order")
    btn_class = "nav-tab-btn-active" if is_active else "nav-tab-btn"
    st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
    if st.button("🛒 友善大圖點餐", key="nav_btn_order"):
        st.session_state.active_main_tab = "tab_order"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with nav_col2:
    is_active = (st.session_state.active_main_tab == "tab_recon")
    btn_class = "nav-tab-btn-active" if is_active else "nav-tab-btn"
    st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
    if st.button("💵 現場收款對帳", key="nav_btn_recon"):
        st.session_state.active_main_tab = "tab_recon"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with nav_col3:
    is_active = (st.session_state.active_main_tab == "tab_report")
    btn_class = "nav-tab-btn-active" if is_active else "nav-tab-btn"
    st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
    if st.button("🖨️ 訂單彙整出單", key="nav_btn_report"):
        st.session_state.active_main_tab = "tab_report"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.write("---")

# -------------------------------------------------------------
# 分頁 1：畫面式逐項轉跳點餐
# -------------------------------------------------------------
if st.session_state.active_main_tab == "tab_order":
    chosen_date_str = str(st.session_state.target_order_date)

    # 畫面 A：送單完成（大字顯示金額，付給收錢人員）
    if st.session_state.order_step == "FINISH":
        order_total_pay = st.session_state.last_order_total
        st.markdown(f"""
        <div class="big-pay-card">
            <div style="font-size: 38px; font-weight: 900; color: #166534; margin-bottom: 12px;">
                🎉 【{st.session_state.selected_user}】點好餐囉！
            </div>
            <div style="font-size: 28px; color: #374151; margin-bottom: 16px;">
                📅 預訂日期：<b>{chosen_date_str}</b>
            </div>
            <div style="font-size: 34px; font-weight: 900; color: #1F2937;">
                👉 請把錢錢拿給收錢人員：<br>
                <span style="color: #DC2626; font-size: 64px; font-weight: 900;">${fmt_price(order_total_pay)}</span> 元
            </div>
        </div>
        """, unsafe_allow_html=True)

        rem_p = int(order_total_pay)
        p100, rem_p = rem_p // 100, rem_p % 100
        p50, rem_p = rem_p // 50, rem_p % 50
        p10, rem_p = rem_p // 10, rem_p % 10
        p5, p1 = rem_p // 5, rem_p % 5

        if order_total_pay > 0:
            st.markdown("#### 🪙 請拿這些錢給收錢人員：")
            board_html = "<div class='money-visual-board'>"
            if p100 > 0: board_html += f"<div class='money-group-row'>{''.join([SVG_100 for _ in range(p100)])}</div>"
            if p50 > 0: board_html += f"<div class='money-group-row'>{''.join([SVG_50 for _ in range(p50)])}</div>"
            if p10 > 0: board_html += f"<div class='money-group-row'>{''.join([SVG_10 for _ in range(p10)])}</div>"
            if p5 > 0: board_html += f"<div class='money-group-row'>{''.join([SVG_5 for _ in range(p5)])}</div>"
            if p1 > 0: board_html += f"<div class='money-group-row'>{''.join([SVG_1 for _ in range(p1)])}</div>"
            board_html += "</div>"
            st.markdown(board_html, unsafe_allow_html=True)

        st.write("")
        if st.button("👉 換下一位同學點餐", type="primary", use_container_width=True):
            queue_speech("換下一位同學，請選日期")
            reset_ordering()
            st.rerun()

    # 畫面 1：選擇日期
    elif st.session_state.order_step == "DATE":
        st.markdown('<div class="aac-step-banner">📅 第 1 步：請點選想吃哪一天的午餐？</div>', unsafe_allow_html=True)
        workweek_list = get_current_workweek_dates()
        
        d_cols = st.columns(5)
        for idx, w in enumerate(workweek_list):
            with d_cols[idx]:
                st.markdown('<div class="date-btn">', unsafe_allow_html=True)
                if st.button(w["label"], key=f"scr_date_{idx}"):
                    st.session_state.target_order_date = w["date"]
                    st.session_state.order_step = "USER"
                    queue_speech(f"選擇{w['weekday_zh']}，請問你是誰？")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        st.write("")
        st.markdown("#### 📅 或是挑選其他指定日期：")
        col_cd1, col_cd2 = st.columns([2, 2])
        with col_cd1:
            custom_date = st.date_input("點開日曆選日期", value=st.session_state.target_order_date, key="scr_custom_date")
        with col_cd2:
            st.write("")
            st.write("")
            if st.button("👉 確認這個日期", type="primary", use_container_width=True):
                st.session_state.target_order_date = custom_date
                st.session_state.order_step = "USER"
                queue_speech(f"選擇日期{custom_date.strftime('%m月%d日')}，請問你是誰？")
                st.rerun()

    # 畫面 2：選擇同學姓名
    elif st.session_state.order_step == "USER":
        c_head1, c_head2 = st.columns([4, 1])
        with c_head1:
            st.markdown(f'<div class="aac-step-banner">👤 第 2 步：請問你是哪一位同學？（預訂：{chosen_date_str}）</div>', unsafe_allow_html=True)
        with c_head2:
            if st.button("⬅️ 重選日期", use_container_width=True):
                st.session_state.order_step = "DATE"
                queue_speech("重選日期")
                st.rerun()

        all_orders = st.session_state.orders_data
        ordered_users_today = set()
        if not all_orders.empty and "訂購日期" in all_orders.columns and "員工姓名" in all_orders.columns:
            date_filter = all_orders["訂購日期"].astype(str).str.replace("-", "/").str.contains(chosen_date_str.replace("-", "/"))
            ordered_users_today = set(all_orders[date_filter]["員工姓名"].dropna().astype(str).str.strip().tolist())

        if not df_users.empty and "姓名" in df_users.columns:
            u_cols = st.columns(2)
            for idx, (_, u) in enumerate(df_users.iterrows()):
                u_name = str(u["姓名"]).strip()
                u_lim = parse_price(u.get("金額限制", 0))
                lim_text = f"限額 ${fmt_price(u_lim)} 元" if u_lim > 0 else "無金額上限"
                
                is_already_ordered = (u_name in ordered_users_today)
                btn_u_label = f"👤 {u_name}\n（✅ 今天已經點過囉）" if is_already_ordered else f"👤 {u_name}\n（{lim_text}）"
                btn_class = "user-btn-done" if is_already_ordered else "user-btn"

                with u_cols[idx % 2]:
                    st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
                    if st.button(btn_u_label, key=f"scr_user_{idx}"):
                        st.session_state.selected_user = u_name
                        st.session_state.user_daily_limit = u_lim
                        
                        if is_already_ordered:
                            st.session_state.order_step = "ALREADY_DONE"
                            queue_speech(f"{u_name}同學，你今天已經點過餐囉")
                        else:
                            st.session_state.order_step = "STORE"
                            lim_speech = f"今日限額{int(u_lim)}元" if u_lim > 0 else "無金額限制"
                            queue_speech(f"{u_name}好，{lim_speech}，請選想吃哪一家")
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    # 畫面 2-B：今日已點餐提示
    elif st.session_state.order_step == "ALREADY_DONE":
        u_name = st.session_state.selected_user
        all_orders = st.session_state.orders_data
        date_mask = all_orders["訂購日期"].astype(str).str.replace("-", "/").str.contains(chosen_date_str.replace("-", "/"))
        user_done_df = all_orders[date_mask & (all_orders["員工姓名"] == u_name)]
        spent_amount = user_done_df["小計金額"].apply(parse_price).sum()
        ordered_items_text = "、".join(user_done_df["餐點品項"].tolist())

        st.markdown(f"""
        <div class="big-pay-card" style="border-color:#64748B;">
            <div style="font-size:38px; font-weight:900; color:#1E293B; margin-bottom:12px;">
                ✅ 【{u_name}】您今天已經點過餐囉！
            </div>
            <div style="font-size:28px; color:#334155; margin-bottom:14px;">
                🍲 已點餐點：<b>{ordered_items_text}</b>
            </div>
            <div style="font-size:32px; font-weight:900; color:#DC2626; margin-bottom:18px;">
                應付金額：${fmt_price(spent_amount)} 元 ｜ 狀態：{user_done_df['付款狀態'].values[0]}
            </div>
            <div style="font-size:24px; color:#64748B;">
                （系統已經登記好了，請不要重複點餐喔！）
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_bk1, col_bk2 = st.columns(2)
        with col_bk1:
            if st.button("👉 換下一位同學點餐", type="primary", use_container_width=True):
                queue_speech("換下一位同學")
                reset_ordering()
                st.rerun()
        with col_bk2:
            if st.button("➕ 我還要再加點其他食物", use_container_width=True):
                st.session_state.order_step = "STORE"
                queue_speech("加點其他餐點，請選店家")
                st.rerun()

    # 畫面 3：選擇店家
    elif st.session_state.order_step == "STORE":
        u_name = st.session_state.selected_user
        u_lim = st.session_state.user_daily_limit

        c1, c2 = st.columns([4, 1])
        with c1:
            lim_msg = f"每日限額：${fmt_price(u_lim)} 元" if u_lim > 0 else "無預算上限"
            st.markdown(f'<div class="aac-step-banner">🏪 第 3 步：想吃哪一家？（{u_name}，{lim_msg}）</div>', unsafe_allow_html=True)
        with c2:
            if st.button("⬅️ 重選名字", use_container_width=True):
                st.session_state.order_step = "USER"
                queue_speech("重選姓名")
                st.rerun()

        store_list = df_menu["店家名稱"].dropna().unique().tolist() if "店家名稱" in df_menu.columns else ["主要合作店家"]
        s_cols = st.columns(2)
        for idx, s_name in enumerate(store_list):
            with s_cols[idx % 2]:
                st.markdown('<div class="store-btn">', unsafe_allow_html=True)
                if st.button(f"🏪 {s_name}", key=f"scr_store_{idx}"):
                    st.session_state.selected_store = s_name
                    st.session_state.selected_category = "全部"
                    st.session_state.order_step = "FOOD"
                    queue_speech(f"選擇{s_name}，請按大框框選餐點")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # 畫面 4：挑選餐點大框框
    elif st.session_state.order_step == "FOOD":
        u_name = st.session_state.selected_user
        store_name = st.session_state.selected_store
        u_lim = st.session_state.user_daily_limit

        all_orders = st.session_state.orders_data
        already_spent_today = 0.0
        if not all_orders.empty and "訂購日期" in all_orders.columns and "員工姓名" in all_orders.columns:
            d_mask = all_orders["訂購日期"].astype(str).str.replace("-", "/").str.contains(chosen_date_str.replace("-", "/"))
            user_done = all_orders[d_mask & (all_orders["員工姓名"] == u_name)]
            if not user_done.empty:
                already_spent_today = user_done["小計金額"].apply(parse_price).sum()

        cart_sum = sum(x["subtotal"] for x in st.session_state.cart)
        remain_budget = round(u_lim - already_spent_today - cart_sum, 2) if u_lim > 0 else 999999

        c1, c2 = st.columns([4, 1])
        with c1:
            if u_lim > 0:
                st.markdown(f'<div class="aac-step-banner">👇 第 4 步：想吃什麼？(直接點) ｜ 剩餘可用：<b style="color:#DC2626;">${fmt_price(remain_budget)}</b> 元</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="aac-step-banner">👇 第 4 步：想吃什麼？(直接點)</div>', unsafe_allow_html=True)
        with c2:
            if st.button("⬅️ 更換店家", use_container_width=True):
                st.session_state.order_step = "STORE"
                queue_speech("更換店家")
                st.rerun()

        current_store_menu = df_menu[df_menu["店家名稱"] == store_name] if "店家名稱" in df_menu.columns else df_menu

        category_list = ["全部"]
        if "分類" in current_store_menu.columns:
            extracted_cats = [str(c).strip() for c in current_store_menu["分類"].dropna().unique().tolist() if str(c).strip() not in ["", "nan"]]
            category_list.extend(extracted_cats)

        cat_cols = st.columns(min(len(category_list), 5))
        for c_idx, cat_name in enumerate(category_list):
            is_cat_active = (st.session_state.selected_category == cat_name)
            btn_style = "category-filter-active" if is_cat_active else "category-filter-btn"
            with cat_cols[c_idx % min(len(category_list), 5)]:
                st.markdown(f'<div class="{btn_style}">', unsafe_allow_html=True)
                if st.button(get_category_icon(cat_name), key=f"scr_cat_{c_idx}"):
                    st.session_state.selected_category = cat_name
                    queue_speech(f"切換到{cat_name}")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        st.write("---")

        active_cat = st.session_state.selected_category
        if active_cat != "全部" and "分類" in current_store_menu.columns:
            filtered_menu = current_store_menu[current_store_menu["分類"] == active_cat].copy()
        else:
            filtered_menu = current_store_menu.copy()

        # 價格由低到高排序
        filtered_menu["parsed_price"] = filtered_menu["單價"].apply(parse_price)
        filtered_menu = filtered_menu.sort_values(by="parsed_price", ascending=True)

        affordable_items = []
        for _, item_row in filtered_menu.iterrows():
            item_base_price = item_row["parsed_price"]
            if u_lim > 0 and item_base_price > remain_budget:
                continue
            affordable_items.append(item_row)

        if not affordable_items:
            st.warning("⚠️ 此分類目前沒有符合您剩餘預算的食物喔！")
        else:
            pos_cols = st.columns(2)
            for idx, item in enumerate(affordable_items):
                i_name = str(item.get("餐點名稱", "")).strip()
                base_p = item["parsed_price"]
                category = str(item.get("分類", ""))
                food_icon = get_food_aac_icon(i_name, category)

                raw_options = ""
                if "種類選擇" in item: raw_options = str(item["種類選擇"]).strip()
                elif "麵類選擇" in item: raw_options = str(item["麵類選擇"]).strip()

                is_soup = "湯" in i_name or "湯" in category or any(x in raw_options for x in ["小", "中", "大"])

                if raw_options and raw_options not in ["-", "nan", "無", "固定"]:
                    type_options = [opt.strip() for opt in re.split(r"[/,、|]+", raw_options) if opt.strip()]
                elif is_soup:
                    type_options = ["小", "中 (+10元)", "大 (+20元)"]
                else:
                    type_options = ["標準份量"]

                allow_extra = ("劉妹" in str(store_name)) or ("意麵" in i_name) or ("麵" in category)
                has_spec = len(type_options) > 1

                btn_tile_label = f"{food_icon} {i_name}\n${fmt_price(base_p)} 元"
                with pos_cols[idx % 2]:
                    st.markdown('<div class="screen-choice-tile">', unsafe_allow_html=True)
                    if st.button(btn_tile_label, key=safe_key("scr_food_tile", i_name, idx)):
                        st.session_state.current_picking_item = {
                            "name": i_name,
                            "price": base_p,
                            "options": type_options,
                            "icon": food_icon,
                            "allow_extra": allow_extra
                        }
                        
                        if has_spec:
                            st.session_state.order_step = "SPEC"
                            queue_speech(f"請選擇{i_name}的規格")
                        elif allow_extra:
                            st.session_state.picked_spec = type_options[0]
                            st.session_state.order_step = "EXTRA"
                            queue_speech(f"請問要不要加麵？")
                        else:
                            item_data = {
                                "item": i_name,
                                "spec": type_options[0],
                                "extra": "不加麵",
                                "unit_price": base_p,
                                "qty": 1,
                                "subtotal": base_p
                            }
                            st.session_state.cart.append(item_data)
                            st.session_state.order_step = "CART_CONFIRM"
                            queue_speech(f"成功放入{i_name}")
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    # 畫面 5：挑選規格
    elif st.session_state.order_step == "SPEC":
        cur_item = st.session_state.current_picking_item
        p_name = cur_item["name"]
        p_base_p = cur_item["price"]
        p_options = cur_item["options"]
        p_icon = cur_item["icon"]
        allow_extra = cur_item["allow_extra"]

        c1, c2 = st.columns([4, 1])
        with c1:
            st.markdown(f'<div class="aac-step-banner">{p_icon} 請點選【{p_name}】的種類規格：</div>', unsafe_allow_html=True)
        with c2:
            if st.button("⬅️ 重選餐點", use_container_width=True):
                st.session_state.order_step = "FOOD"
                queue_speech("重選餐點")
                st.rerun()

        cols_spec = st.columns(min(len(p_options), 3))
        for o_idx, opt_txt in enumerate(p_options):
            opt_extra_p = parse_extra_price(opt_txt)
            final_p = p_base_p + opt_extra_p
            with cols_spec[o_idx % min(len(p_options), 3)]:
                st.markdown('<div class="spec-choice-tile">', unsafe_allow_html=True)
                if st.button(f"👉 {opt_txt}\n(${fmt_price(final_p)}元)", key=f"scr_spec_btn_{o_idx}"):
                    st.session_state.picked_spec = opt_txt
                    
                    if allow_extra:
                        st.session_state.order_step = "EXTRA"
                        queue_speech(f"選擇{opt_txt}，請問要不要加麵？")
                    else:
                        item_data = {
                            "item": p_name,
                            "spec": opt_txt,
                            "extra": "不加麵",
                            "unit_price": final_p,
                            "qty": 1,
                            "subtotal": final_p
                        }
                        st.session_state.cart.append(item_data)
                        st.session_state.order_step = "CART_CONFIRM"
                        queue_speech(f"成功放入{p_name}{opt_txt}")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # 畫面 6：挑選加麵
    elif st.session_state.order_step == "EXTRA":
        cur_item = st.session_state.current_picking_item
        p_name = cur_item["name"]
        p_base_p = cur_item["price"]
        chosen_spec = st.session_state.picked_spec
        spec_extra_p = parse_extra_price(chosen_spec)

        c1, c2 = st.columns([4, 1])
        with c1:
            st.markdown(f'<div class="aac-step-banner">🍜 【{p_name}（{chosen_spec}）】要不要加麵？</div>', unsafe_allow_html=True)
        with c2:
            if st.button("⬅️ 重選規格", use_container_width=True):
                st.session_state.order_step = "SPEC" if len(cur_item["options"]) > 1 else "FOOD"
                queue_speech("重選規格")
                st.rerun()

        cols_ex = st.columns(2)
        with cols_ex[0]:
            st.markdown('<div class="spec-choice-tile">', unsafe_allow_html=True)
            p_normal = p_base_p + spec_extra_p
            if st.button(f"🍜 不加麵\n(${fmt_price(p_normal)}元)", key="scr_ex_no"):
                item_data = {
                    "item": p_name,
                    "spec": chosen_spec,
                    "extra": "不加麵",
                    "unit_price": p_normal,
                    "qty": 1,
                    "subtotal": p_normal
                }
                st.session_state.cart.append(item_data)
                st.session_state.order_step = "CART_CONFIRM"
                queue_speech(f"不加麵，已放入點餐籃")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with cols_ex[1]:
            st.markdown('<div class="spec-choice-tile">', unsafe_allow_html=True)
            p_plus = p_base_p + spec_extra_p + 15
            if st.button(f"➕ 要加麵 (+15元)\n(${fmt_price(p_plus)}元)", key="scr_ex_yes"):
                item_data = {
                    "item": p_name,
                    "spec": chosen_spec,
                    "extra": "要加麵 (+15元)",
                    "unit_price": p_plus,
                    "qty": 1,
                    "subtotal": p_plus
                }
                st.session_state.cart.append(item_data)
                st.session_state.order_step = "CART_CONFIRM"
                queue_speech(f"加麵，已放入點餐籃")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # 畫面 7：點餐確認
    elif st.session_state.order_step == "CART_CONFIRM":
        u_name = st.session_state.selected_user
        cart_sum = sum(x["subtotal"] for x in st.session_state.cart)
        last_item = st.session_state.cart[-1]

        st.markdown(f"""
        <div class="added-feedback-card">
            <div style="font-size:40px; font-weight:900; color:#1E40AF; margin-bottom:12px;">
                🎉 已經放進點餐籃囉！
            </div>
            <div style="font-size:32px; font-weight:900; color:#1F2937; margin-bottom:10px;">
                🍲 【{last_item['item']}】（{last_item['spec']} ｜ {last_item['extra']}）
            </div>
            <div style="font-size:30px; color:#DC2626; font-weight:900; margin-bottom:16px;">
                目前點餐籃總共有 {len(st.session_state.cart)} 樣食物 ｜ 總共：${fmt_price(cart_sum)} 元
            </div>
        </div>
        """, unsafe_allow_html=True)

        c_opt1, c_opt2 = st.columns(2)
        with c_opt1:
            if st.button("➕ 我還要再點別的", use_container_width=True):
                st.session_state.order_step = "FOOD"
                queue_speech("繼續選其他餐點")
                st.rerun()

        with c_opt2:
            if st.button(f"✅ 我點好了，送出訂單（共 ${fmt_price(cart_sum)} 元）", type="primary", use_container_width=True):
                new_rows = []
                current_len = len(st.session_state.orders_data)
                for i, it in enumerate(st.session_state.cart):
                    new_rows.append({
                        "訂單編號": f"ORD-{current_len + i + 1:03d}",
                        "訂購日期": chosen_date_str,
                        "員工編號": "",
                        "員工姓名": u_name,
                        "所屬部門": "",
                        "餐點品項": it["item"],
                        "麵類選擇": it["spec"],
                        "是否加麵": it.get("extra", "不加麵"),
                        "單價": f"${fmt_price(it['unit_price'])}",
                        "數量": it["qty"],
                        "小計金額": f"${fmt_price(it['subtotal'])}",
                        "付款狀態": "未付款"
                    })
                st.session_state.orders_data = pd.concat([st.session_state.orders_data, pd.DataFrame(new_rows)], ignore_index=True)
                st.session_state.last_order_total = cart_sum
                with st.spinner("正在送出訂單..."):
                    sync_to_google_sheet({"action": "append", "rows": new_rows})
                queue_speech(f"點單成功，請把{int(cart_sum)}元現金交給收錢人員")
                st.session_state.order_step = "FINISH"
                st.rerun()

        st.write("---")
        st.markdown("#### 🛒 目前點餐籃明細：")
        for c_idx, c_item in enumerate(st.session_state.cart):
            cc1, cc2 = st.columns([4, 1])
            with cc1:
                st.write(f"▪ {c_item['item']}（{c_item['spec']} ｜ {c_item['extra']}）- ${fmt_price(c_item['subtotal'])} 元")
            with cc2:
                if st.button("🗑️ 取消這道", key=f"scr_del_{c_idx}"):
                    st.session_state.cart.pop(c_idx)
                    if not st.session_state.cart:
                        st.session_state.order_step = "FOOD"
                    queue_speech("已取消這道菜")
                    st.rerun()

# -------------------------------------------------------------
# 分頁 2：現場收款對帳（鎖定當前頁面，點擊不再跳轉）
# -------------------------------------------------------------
elif st.session_state.active_main_tab == "tab_recon":
    st.subheader("💵 現場收款、找零與訂單維護")
    q_date = st.date_input("選擇收款日期", value=st.session_state.target_order_date, key="q_date_recon")
    if st.button("🔄 重新載入最新資料", key="btn_reload_recon"):
        st.session_state.orders_data = load_orders_from_sheet()
        queue_speech("已重新載入收款資料")
        st.rerun()

    all_orders = st.session_state.orders_data.copy()
    q_str = str(q_date).strip()
    q_str_slash = q_str.replace("-", "/")
    
    d_series = all_orders["訂購日期"].astype(str).str.strip()
    date_mask = (d_series == q_str) | (d_series == q_str_slash) | (d_series.str.replace("-", "/") == q_str_slash)
    day_orders = all_orders[date_mask].copy()

    if day_orders.empty:
        st.info(f"【{q_date}】尚無任何點餐紀錄。")
    else:
        day_orders["金額數值"] = day_orders["小計金額"].apply(parse_price)
        total_money = round(day_orders["金額數值"].sum(), 2)
        paid_orders = day_orders[day_orders["付款狀態"] == "已付款"]
        paid_money = round(paid_orders["金額數值"].sum(), 2)
        unpaid_money = round(total_money - paid_money, 2)
        unpaid_count = len(day_orders) - len(paid_orders)

        m1, m2, m3 = st.columns(3)
        m1.metric("本日訂單總額", f"${fmt_price(total_money)} 元")
        m2.metric("已收總額", f"${fmt_price(paid_money)} 元", f"{len(paid_orders)} 筆")
        m3.metric("待收餘額 (未收)", f"${fmt_price(unpaid_money)} 元", f"{unpaid_count} 筆", delta_color="inverse")

        st.write("---")

        unpaid = day_orders[day_orders["付款狀態"] != "已付款"]
        if unpaid.empty:
            st.success("🎉 本日全部訂單已收款完畢！可前往【🖨️ 訂單彙整出單】分頁出單。")
        else:
            user_options = unpaid["員工姓名"].dropna().unique().tolist()
            calc_col1, calc_col2 = st.columns([1, 1])

            with calc_col1:
                target_user = st.selectbox("選擇要繳費給收錢人員的同學", options=user_options)
                user_unpaid_items = unpaid[unpaid["員工姓名"] == target_user]
                target_due = round(user_unpaid_items["金額數值"].sum(), 2)

                st.markdown(f"""
                <div style="background-color: #FEF2F2; border: 2px solid #F87171; border-radius: 14px; padding: 16px; margin-top: 10px;">
                    👤 收款對象：<b>{target_user}</b><br>
                    💰 應收金額：<b style="color: #DC2626; font-size: 34px;">${fmt_price(target_due)}</b> 元
                </div>
                """, unsafe_allow_html=True)

            with calc_col2:
                st.write("點選同學交給收錢人員的面額：")
                q_col1, q_col2, q_col3 = st.columns(3)
                with q_col1:
                    if st.button("剛好", key="pay_exact"):
                        st.session_state.received_cash = float(target_due)
                        queue_speech(f"收剛好{int(target_due)}元")
                with q_col2:
                    if st.button("💵 拿 100", key="pay_100"):
                        st.session_state.received_cash = 100.0
                        queue_speech("收一百元")
                with q_col3:
                    if st.button("💵 拿 500", key="pay_500"):
                        st.session_state.received_cash = 500.0
                        queue_speech("收五百元")

                default_val = st.session_state.get("received_cash", float(target_due))
                paid_input = st.number_input("或自訂實收金額 (元)", min_value=0.0, value=float(default_val), step=1.0)

                change = round(paid_input - target_due, 2)
                if change >= 0:
                    st.markdown(f"""
                    <div style="background-color: #ECFDF5; border: 2px solid #34D399; border-radius: 14px; padding: 16px; margin-top: 10px;">
                        🪙 收錢人員應找零錢：<b style="color: #059669; font-size: 34px;">${fmt_price(change)}</b> 元
                    </div>
                    """, unsafe_allow_html=True)

                    rem_c = int(change)
                    c100, rem_c = rem_c // 100, rem_c % 100
                    c50, rem_c = rem_c // 50, rem_c % 50
                    c10, rem_c = rem_c // 10, rem_c % 10
                    c5, c1 = rem_c // 5, rem_c % 5

                    if change > 0:
                        st.markdown("### 👉 請收錢人員照著畫面「看到幾個就拿幾個」找給同學：")
                        board_html = "<div class='money-visual-board'>"
                        if c100 > 0: board_html += f"<div class='money-group-row'>{''.join([SVG_100 for _ in range(c100)])}</div>"
                        if c50 > 0: board_html += f"<div class='money-group-row'>{''.join([SVG_50 for _ in range(c50)])}</div>"
                        if c10 > 0: board_html += f"<div class='money-group-row'>{''.join([SVG_10 for _ in range(c10)])}</div>"
                        if c5 > 0: board_html += f"<div class='money-group-row'>{''.join([SVG_5 for _ in range(c5)])}</div>"
                        if c1 > 0: board_html += f"<div class='money-group-row'>{''.join([SVG_1 for _ in range(c1)])}</div>"
                        board_html += "</div>"
                        st.markdown(board_html, unsafe_allow_html=True)
                    else:
                        st.info("👌 剛好收齊，不需要找錢！")

                    st.write("")
                    if st.button(f"✅ 確認收款完畢（將 {target_user} 設為已付款）", type="primary", use_container_width=True):
                        target_indices = st.session_state.orders_data[st.session_state.orders_data["員工姓名"] == target_user].index
                        st.session_state.orders_data.loc[target_indices, "付款狀態"] = "已付款"
                        with st.spinner("同步雲端狀態中..."):
                            sync_to_google_sheet({
                                "action": "update_status",
                                "user": target_user,
                                "status": "已付款"
                            })
                        queue_speech(f"{target_user}收款完成")
                        st.success(f"已完成 {target_user} 收款並同步至雲端！")
                        time.sleep(0.5)
                        st.rerun()
                else:
                    st.error(f"⚠️ 還不夠喔！同學還差 ${fmt_price(abs(change))} 元")

        st.write("---")
        st.markdown("#### 📋 訂單流水清單：")
        for row_idx, row_data in day_orders.iterrows():
            ord_id = row_data.get("訂單編號", "")
            with st.container():
                st.markdown('<div class="order-row-card">', unsafe_allow_html=True)
                r1, r2, r3, r4, r5, r6 = st.columns([1.5, 2, 3.5, 1.5, 2, 1.5])
                with r1:
                    st.write(f"**{ord_id}**")
                    st.caption(f"📅 {row_data.get('訂購日期', '')}")
                with r2:
                    st.write(f"👤 **{row_data.get('員工姓名', '')}**")
                with r3:
                    q_info = f" x {row_data.get('數量', 1)}" if str(row_data.get('數量', 1)) not in ["", "1"] else ""
                    st.write(f"{row_data.get('餐點品項', '')}{q_info} ｜ {row_data.get('麵類選擇', '')} ｜ {row_data.get('是否加麵', '')}")
                with r4:
                    st.write(f"<b style='color:#DC2626;'>{row_data.get('小計金額', '')}</b>", unsafe_allow_html=True)
                with r5:
                    cur_status = row_data.get("付款狀態", "未付款")
                    if cur_status == "已付款":
                        if st.button("🟢 已付 (改未付)", key=f"recon_status_{row_idx}_{ord_id}"):
                            st.session_state.orders_data.loc[row_idx, "付款狀態"] = "未付款"
                            with st.spinner("更新狀態中..."):
                                sync_to_google_sheet({
                                    "action": "update_status",
                                    "order_id": str(ord_id),
                                    "user": row_data.get("員工姓名", ""),
                                    "status": "未付款"
                                })
                            queue_speech(f"{row_data.get('員工姓名', '')}改為未付款")
                            st.rerun()
                    else:
                        if st.button("🔴 未付 (改已付)", key=f"recon_status_{row_idx}_{ord_id}"):
                            st.session_state.orders_data.loc[row_idx, "付款狀態"] = "已付款"
                            with st.spinner("更新狀態中..."):
                                sync_to_google_sheet({
                                    "action": "update_status",
                                    "order_id": str(ord_id),
                                    "user": row_data.get("員工姓名", ""),
                                    "status": "已付款"
                                })
                            queue_speech(f"{row_data.get('員工姓名', '')}改為已付款")
                            st.rerun()
                with r6:
                    if st.button("🗑️ 刪除", key=f"recon_del_{row_idx}_{ord_id}", help="刪除這筆訂單"):
                        target_ord = str(ord_id)
                        target_u = str(row_data.get("員工姓名", ""))
                        target_d = str(row_data.get("訂購日期", ""))
                        target_it = str(row_data.get("餐點品項", ""))
                        
                        st.session_state.orders_data.drop(row_idx, inplace=True)
                        st.session_state.orders_data.reset_index(drop=True, inplace=True)
                        
                        with st.spinner(f"正在從雲端刪除..."):
                            sync_to_google_sheet({
                                "action": "delete_order",
                                "order_id": target_ord,
                                "user": target_u,
                                "date": target_d,
                                "item": target_it
                            })
                        queue_speech("訂單已刪除")
                        st.success("訂單已成功刪除！")
                        time.sleep(0.4)
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------
# 分頁 3：訂單彙整出單（鎖定當前頁面）
# -------------------------------------------------------------
elif st.session_state.active_main_tab == "tab_report":
    st.subheader("🖨️ 中餐訂單出單與分發彙整表")
    
    col_od1, col_od2 = st.columns([2, 1])
    with col_od1:
        order_out_date = st.date_input("選擇欲出單的日期", value=st.session_state.target_order_date, key="out_order_date_input")
    with col_od2:
        st.write("")
        if st.button("🔄 重新整理訂單數據", type="primary", key="btn_refresh_out"):
            st.session_state.orders_data = load_orders_from_sheet()
            queue_speech("出單數據已刷新")
            st.rerun()

    all_orders = st.session_state.orders_data.copy()
    q_str_dash = str(order_out_date).strip()
    q_str_slash = q_str_dash.replace("-", "/")

    if all_orders.empty:
        st.info("目前尚無任何訂單資料。")
    else:
        d_series = all_orders["訂購日期"].astype(str).str.strip()
        date_mask = (d_series == q_str_dash) | (d_series == q_str_slash) | (d_series.str.replace("-", "/") == q_str_slash)
        out_day_orders = all_orders[date_mask].copy()

        if out_day_orders.empty:
            st.warning(f"⚠️ 在【{order_out_date}】查無點單紀錄，請先確認是否已送出餐點。")
        else:
            out_day_orders["金額數值"] = out_day_orders["小計金額"].apply(parse_price)
            out_day_orders["數量數值"] = out_day_orders["數量"].apply(lambda x: int(parse_price(x)) if parse_price(x) > 0 else 1)

            total_money = round(out_day_orders["金額數值"].sum(), 2)
            total_portions = int(out_day_orders["數量數值"].sum())
            total_items = len(out_day_orders)

            unpaid_subset = out_day_orders[out_day_orders["付款狀態"] != "已付款"]
            unpaid_cnt = len(unpaid_subset)
            unpaid_sum = round(unpaid_subset["金額數值"].sum(), 2)

            if unpaid_cnt == 0:
                st.success(f"🎉【{order_out_date}】全體同學皆已完成付款！可直接放心出單給店家。")
            else:
                st.warning(f"⚠️ 提醒：尚有 {unpaid_cnt} 筆訂單尚未付款（待收 ${fmt_price(unpaid_sum)} 元），請先至【💵 現場收款對帳】交給收錢人員完成收款！")

            def make_spec_name(r):
                item = str(r.get("餐點品項", "")).strip()
                nd = str(r.get("麵類選擇", "")).strip()
                ex = str(r.get("是否加麵", "")).strip()
                spec_parts = []
                if nd and nd not in ["-", "nan", "無", "標準配置", "標準", "標準份量"]:
                    spec_parts.append(nd)
                if "要加麵" in ex:
                    spec_parts.append("加麵")
                spec_str = f" ({' / '.join(spec_parts)})" if spec_parts else ""
                return f"{item}{spec_str}"

            out_day_orders["餐點規格彙整"] = out_day_orders.apply(make_spec_name, axis=1)

            summary_grouped = out_day_orders.groupby("餐點規格彙整")["數量數值"].sum().reset_index()
            summary_grouped.columns = ["餐點項目與規格", "總數量 (份)"]
            summary_grouped = summary_grouped.sort_values(by="總數量 (份)", ascending=False)

            person_grouped = out_day_orders.groupby("員工姓名").agg({
                "餐點規格彙整": lambda x: "、".join(f"{item} x{qty}" if qty > 1 else item for item, qty in zip(x, out_day_orders.loc[x.index, "數量數值"])),
                "金額數值": "sum",
                "付款狀態": lambda s: "已付款" if all(x == "已付款" for x in s) else "未付款"
            }).reset_index()
            person_grouped.columns = ["同學姓名", "點購餐點品項明細", "應付小計", "付款狀態"]

            line_order_text = f"【午餐訂單 - {order_out_date}】\n--------------------\n"
            line_order_text += "【餐點彙整清單】\n"
            for _, s_row in summary_grouped.iterrows():
                line_order_text += f"▪ {s_row['餐點項目與規格']}：{s_row['總數量 (份)']} 份\n"
            line_order_text += "--------------------\n"
            line_order_text += f"總計：{total_portions} 份\n總金額：${fmt_price(total_money)} 元\n"

            st.markdown(f"""
            <div class="receipt-box" id="print-area">
                <div class="receipt-header">
                    <h2 style="margin:0; font-size:32px; color:#1E293B;">🍱 中餐訂單彙整出單表</h2>
                    <div style="font-size:22px; color:#475569; margin-top:8px;">
                        📅 訂購日期：<b>{order_out_date}</b> ｜ 總份數：<b>{total_portions} 份</b> ｜ 總金額：<b style="color:#DC2626; font-size:26px;">${fmt_price(total_money)} 元</b>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            c_out_col1, c_out_col2 = st.columns([1, 1])
            with c_out_col1:
                st.markdown("#### 📞 1. 店家總單（報單照這個唸即可）：")
                st.dataframe(summary_grouped, use_container_width=True, hide_index=True)

            with c_out_col2:
                st.markdown("#### 👥 2. 個人發放核對名單（餐點送達時對照發放）：")
                st.dataframe(person_grouped, use_container_width=True, hide_index=True)

            st.write("")
            with st.expander("📲 點此展開「LINE 一鍵複製店家格式」文字", expanded=False):
                st.text_area("直接複製以下文字傳給店家即可：", value=line_order_text, height=220)

            c_p1, c_p2 = st.columns([1, 3])
            with c_p1:
                st.button("🖨️ 列印此出單表 (PDF)", on_click=lambda: st.components.v1.html("<script>window.print();</script>", height=0))
            with c_p2:
                st.caption("💡 提示：點擊「列印出單表」後，可在彈出視窗中選擇另存為 PDF 或直接列印紙本發餐勾選單！")
