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
                msg.rate = 0.90;
                msg.pitch = 1.05;
                window.speechSynthesis.speak(msg);
            }}
        </script>
        """, height=0)

def get_first_name(full_name):
    name_str = str(full_name).strip()
    if not name_str:
        return ""
    double_surnames = ["歐陽", "司徒", "諸葛", "公孫", "上官", "夏侯", "皇甫"]
    for ds in double_surnames:
        if name_str.startswith(ds) and len(name_str) > 2:
            return name_str[2:]
    if len(name_str) >= 2:
        return name_str[1:]
    return name_str

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
    elif "蒸餃" in cat_str: return f"🥟♨️ {cat_str}"
    elif "湯" in cat_str: return f"🥣 {cat_str}"
    elif "飯" in cat_str: return f"🍚 {cat_str}"
    elif "麵" in cat_str or "意麵" in cat_str or "冬粉" in cat_str: return f"🍜 {cat_str}"
    elif "飲" in cat_str or "茶" in cat_str: return f"🥤 {cat_str}"
    elif "小菜" in cat_str or "切" in cat_str or "炸" in cat_str: return f"🥗 {cat_str}"
    else: return f"🥢 {cat_str}"

def get_food_aac_icon(item_name, category=""):
    s = f"{item_name} {category}"
    if "蒸餃" in s: return "🥟♨️"
    elif "鍋貼" in s: return "🥟🔥"
    elif "水餃" in s: return "🥟"
    elif "便當" in s or "飯包" in s or "招牌飯" in s: return "🍱"
    elif "滷肉飯" in s or "肉燥飯" in s or "排骨" in s or "雞腿" in s: return "🍖🍚"
    elif "炒飯" in s or "燴飯" in s: return "🍛"
    elif "意麵" in s or "油麵" in s or "鍋燒" in s: return "🍜"
    elif "冬粉" in s or "米粉" in s or "板條" in s: return "🍲"
    elif "湯" in s: return "🥣"
    elif "飲" in s or "茶" in s or "豆漿" in s or "紅茶" in s: return "🥤"
    elif "蛋" in s or "小菜" in s or "豆干" in s: return "🥗"
    else: return "🍱"

# 判斷是否為按「顆」計算的水餃與鍋貼（排除蒸餃，蒸餃為份）
def is_dumpling_item(item_name):
    s = str(item_name).strip()
    if "蒸餃" in s:
        return False
    return ("水餃" in s or "鍋貼" in s)

st.markdown("""
<style>
    html { scroll-behavior: smooth; }
    html, body, [class*="css"] { font-size: 24px; font-weight: 700; }

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

    .date-status-bar {
        background-color: #EFF6FF;
        border: 2.5px solid #3B82F6;
        border-radius: 16px;
        padding: 14px 20px;
        font-size: 24px;
        font-weight: 900;
        color: #1E40AF;
        margin-bottom: 16px;
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

    .qty-select-tile button {
        width: 100% !important;
        min-height: 110px !important;
        font-size: 32px !important;
        font-weight: 900 !important;
        border-radius: 20px !important;
        border: 3.5px solid #0284C7 !important;
        background: #F0F9FF !important;
        color: #0369A1 !important;
        margin-bottom: 14px !important;
    }

    .qty-btn button {
        font-size: 40px !important; font-weight: 900 !important;
        min-height: 75px !important; width: 100% !important;
        border-radius: 18px !important; border: 3px solid #3B82F6 !important;
        background-color: #EFF6FF !important; color: #1D4ED8 !important;
    }
    .qty-display {
        font-size: 38px; font-weight: 900; color: #1E293B;
        text-align: center; line-height: 75px;
        background-color: #F8FAFC; border-radius: 16px;
        border: 3px solid #CBD5E1;
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
        # 店家名稱自動校正為「元春餃子館」
        if "店家名稱" in df.columns:
            df["店家名稱"] = df["店家名稱"].astype(str).str.replace("元餃子館", "元春餃子館")
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
if "dumpling_qty" not in st.session_state:
    st.session_state.dumpling_qty = 10

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
    st.session_state.dumpling_qty = 10
    st.session_state.cart = []
    st.session_state.last_order_total = 0.0

df_menu = load_menu()
df_users = load_users()

render_speech_player()

st.title("🍱 中餐友善點餐系統")

nav_col1, nav_col2, nav_col3 = st.columns(3)
with nav_col1:
    is_active = (st.session_state.active_main_tab == "tab_order")
    btn_class = "nav-tab-btn-active" if is_active else "nav-tab-btn"
    st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
    if st.button("🛒 友善大圖點餐", key="nav_btn_order"):
        st.session_state.active_main_tab = "tab_order"
        queue_speech("來到點餐頁面囉！")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with nav_col2:
    is_active = (st.session_state.active_main_tab == "tab_recon")
    btn_class = "nav-tab-btn-active" if is_active else "nav-tab-btn"
    st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
    if st.button("💵 現場收款對帳", key="nav_btn_recon"):
        st.session_state.active_main_tab = "tab_recon"
        queue_speech("收錢人員對帳頁面")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with nav_col3:
    is_active = (st.session_state.active_main_tab == "tab_report")
    btn_class = "nav-tab-btn-active" if is_active else "nav-tab-btn"
    st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
    if st.button("🖨️ 訂單彙整出單", key="nav_btn_report"):
        st.session_state.active_main_tab = "tab_report"
        queue_speech("訂單出單彙整表")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.write("---")

# -------------------------------------------------------------
# 分頁 1：畫面式逐項轉跳點餐（元春餃子館 / 蒸餃以份計算）
# -------------------------------------------------------------
if st.session_state.active_main_tab == "tab_order":
    chosen_date_str = str(st.session_state.target_order_date)

    if st.session_state.order_step not in ["DATE", "FINISH"]:
        d_bar_c1, d_bar_c2 = st.columns([4, 1])
        with d_bar_c1:
            st.markdown(f'<div class="date-status-bar">📅 目前預訂用餐日期：<b>{chosen_date_str}</b></div>', unsafe_allow_html=True)
        with d_bar_c2:
            if st.button("🔄 更換日期", use_container_width=True):
                st.session_state.order_step = "DATE"
                queue_speech("好的，重新挑選用餐日期！")
                st.rerun()

    # 畫面 A：送單完成
    if st.session_state.order_step == "FINISH":
        order_total_pay = st.session_state.last_order_total
        display_first_name = get_first_name(st.session_state.selected_user)

        st.markdown(f"""
        <div class="big-pay-card">
            <div style="font-size: 38px; font-weight: 900; color: #166534; margin-bottom: 12px;">
                🎉 【{display_first_name}】點好餐囉！
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
        if st.button("👉 換下一位好朋友點餐", type="primary", use_container_width=True):
            queue_speech("換下一位好朋友囉，請點選用餐日期！")
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
                    queue_speech(f"好的，選了{w['weekday_zh']}的午餐！請問是哪一位好朋友呢？")
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
                queue_speech(f"好的，選了{custom_date.strftime('%m月%d日')}！請問是哪一位好朋友呢？")
                st.rerun()

    # 畫面 2：選擇姓名
    elif st.session_state.order_step == "USER":
        c_head1, c_head2 = st.columns([4, 1])
        with c_head1:
            st.markdown(f'<div class="aac-step-banner">👤 第 2 步：請問你是哪一位好朋友？</div>', unsafe_allow_html=True)
        with c_head2:
            if st.button("⬅️ 重選日期", use_container_width=True):
                st.session_state.order_step = "DATE"
                queue_speech("好的，我們重選日期！")
                st.rerun()

        all_orders = st.session_state.orders_data
        ordered_users_today = set()
        if not all_orders.empty and "訂購日期" in all_orders.columns and "員工姓名" in all_orders.columns:
            date_filter = all_orders["訂購日期"].astype(str).str.replace("-", "/").str.contains(chosen_date_str.replace("-", "/"))
            ordered_users_today = set(all_orders[date_filter]["員工姓名"].dropna().astype(str).str.strip().tolist())

        if not df_users.empty and "姓名" in df_users.columns:
            u_cols = st.columns(2)
            for idx, (_, u) in enumerate(df_users.iterrows()):
                u_full_name = str(u["姓名"]).strip()
                u_first_name = get_first_name(u_full_name)
                u_lim = parse_price(u.get("金額限制", 0))
                lim_text = f"限額 ${fmt_price(u_lim)} 元" if u_lim > 0 else "無金額上限"
                
                is_already_ordered = (u_full_name in ordered_users_today)
                btn_u_label = f"👤 {u_first_name}\n（✅ 今天已經點過囉）" if is_already_ordered else f"👤 {u_first_name}\n（{lim_text}）"
                btn_class = "user-btn-done" if is_already_ordered else "user-btn"

                with u_cols[idx % 2]:
                    st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
                    if st.button(btn_u_label, key=f"scr_user_{idx}"):
                        st.session_state.selected_user = u_full_name
                        st.session_state.user_daily_limit = u_lim
                        
                        if is_already_ordered:
                            st.session_state.order_step = "ALREADY_DONE"
                            queue_speech(f"{u_first_name}，你今天已經點過餐囉！不用再重複點了喔！")
                        else:
                            st.session_state.order_step = "STORE"
                            lim_speech = f"今天有{int(u_lim)}元的零用額度" if u_lim > 0 else "沒有預算限制"
                            queue_speech(f"{u_first_name}，你好！{lim_speech}，來選想吃哪一家好吃的吧！")
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    # 畫面 2-B：今日已點餐提示
    elif st.session_state.order_step == "ALREADY_DONE":
        u_name = st.session_state.selected_user
        u_first_name = get_first_name(u_name)
        all_orders = st.session_state.orders_data
        date_mask = all_orders["訂購日期"].astype(str).str.replace("-", "/").str.contains(chosen_date_str.replace("-", "/"))
        user_done_df = all_orders[date_mask & (all_orders["員工姓名"] == u_name)]
        spent_amount = user_done_df["小計金額"].apply(parse_price).sum()
        ordered_items_text = "、".join(user_done_df["餐點品項"].tolist())

        st.markdown(f"""
        <div class="big-pay-card" style="border-color:#64748B;">
            <div style="font-size:38px; font-weight:900; color:#1E293B; margin-bottom:12px;">
                ✅ 【{u_first_name}】您今天已經點過餐囉！
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
            if st.button("👉 換下一位好朋友點餐", type="primary", use_container_width=True):
                queue_speech("換下一位好朋友！")
                reset_ordering()
                st.rerun()
        with col_bk2:
            if st.button("➕ 我還要再加點其他食物", use_container_width=True):
                st.session_state.order_step = "STORE"
                queue_speech("想要再多吃一點嗎？請挑選店家！")
                st.rerun()

    # 畫面 3：選擇店家（支援「元春餃子館」）
    elif st.session_state.order_step == "STORE":
        u_name = st.session_state.selected_user
        u_first_name = get_first_name(u_name)
        u_lim = st.session_state.user_daily_limit

        c1, c2 = st.columns([4, 1])
        with c1:
            lim_msg = f"每日限額：${fmt_price(u_lim)} 元" if u_lim > 0 else "無預算上限"
            st.markdown(f'<div class="aac-step-banner">🏪 第 3 步：想吃哪一家？（{u_first_name}，{lim_msg}）</div>', unsafe_allow_html=True)
        with c2:
            if st.button("⬅️ 重選名字", use_container_width=True):
                st.session_state.order_step = "USER"
                queue_speech("沒問題，重選名字！")
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
                    queue_speech(f"選了{s_name}，裡面有很多好吃的，直接按大方塊點餐吧！")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # 畫面 4：挑選餐點大框框
    elif st.session_state.order_step == "FOOD":
        u_name = st.session_state.selected_user
        u_first_name = get_first_name(u_name)
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
                queue_speech("想換別家吃看看嗎？好的！")
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
                    queue_speech(f"看{cat_name}的餐點")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        st.write("---")

        active_cat = st.session_state.selected_category
        if active_cat != "全部" and "分類" in current_store_menu.columns:
            filtered_menu = current_store_menu[current_store_menu["分類"] == active_cat].copy()
        else:
            filtered_menu = current_store_menu.copy()

        filtered_menu["parsed_price"] = filtered_menu["單價"].apply(parse_price)
        filtered_menu = filtered_menu.sort_values(by="parsed_price", ascending=True)

        affordable_items = []
        for _, item_row in filtered_menu.iterrows():
            item_base_price = item_row["parsed_price"]
            if u_lim > 0 and item_base_price > remain_budget:
                continue
            affordable_items.append(item_row)

        if not affordable_items:
            st.warning("⚠️ 這個分類目前沒有符合您剩餘預算的食物喔！")
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
                
                # 水餃/鍋貼算「顆」，蒸餃算「份」
                is_dumpling = is_dumpling_item(i_name)
                unit_str = "顆" if is_dumpling else "份"
                btn_tile_label = f"{food_icon} {i_name}\n${fmt_price(base_p)} 元 / {unit_str}"

                with pos_cols[idx % 2]:
                    st.markdown('<div class="screen-choice-tile">', unsafe_allow_html=True)
                    if st.button(btn_tile_label, key=safe_key("scr_food_tile", i_name, idx)):
                        st.session_state.current_picking_item = {
                            "name": i_name,
                            "price": base_p,
                            "options": type_options,
                            "icon": food_icon,
                            "allow_extra": allow_extra,
                            "is_dumpling": is_dumpling
                        }
                        
                        # 水餃/鍋貼跳轉挑選顆數；蒸餃與其他直接走一般流程
                        if is_dumpling:
                            st.session_state.dumpling_qty = 10
                            st.session_state.order_step = "DUMPLING_QTY"
                            queue_speech(f"{i_name}，請問要吃幾顆呢？")
                        elif has_spec:
                            st.session_state.order_step = "SPEC"
                            queue_speech(f"想吃{i_name}呀！請問想要哪一種麵或份量呢？")
                        elif allow_extra:
                            st.session_state.picked_spec = type_options[0]
                            st.session_state.order_step = "EXTRA"
                            queue_speech(f"{i_name}，請問份量要不要加麵吃得更飽呢？")
                        else:
                            # 蒸餃或單一規格餐點直接加入購物籃（以份為單位）
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
                            queue_speech(f"哇！{i_name}聽起來好好吃，已經放進點餐籃囉！")
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    # 畫面 4-B：水餃/鍋貼顆數獨立選擇
    elif st.session_state.order_step ==
