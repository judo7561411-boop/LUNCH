import streamlit as st
import pandas as pd
import requests
import json
import time
import re
import hashlib
from datetime import date, timedelta

st.set_page_config(page_title="中餐點餐系統", page_icon="🍱", layout="wide")

APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbw0UEIp80umbupbDQkMQAa5-3Z4HQp01r9VH_Zr-0nYnPzXv6jgY_gKYFyScn7e2Lrj/exec"
SHEET_ID = "1mHnXoG-Duq45EvwZTRVuq86rsK8T5DA9NkLnOi30wuM"
ORDERS_GID = "1002"

SVG_100 = """<svg width="180" height="90" viewBox="0 0 180 90" xmlns="http://www.w3.org/2000/svg" style="border-radius:6px; box-shadow:2px 3px 6px rgba(0,0,0,0.3); margin:4px;"><rect width="180" height="90" rx="6" fill="#C53030"/><rect x="4" y="4" width="172" height="82" rx="4" fill="none" stroke="#FED7D7" stroke-width="1.5" stroke-dasharray="4,2"/><circle cx="45" cy="45" r="22" fill="#9B2C2C"/><circle cx="45" cy="45" r="18" fill="none" stroke="#FEB2B2" stroke-width="1"/><text x="45" y="52" font-family="sans-serif" font-size="20" font-weight="bold" fill="#FED7D7" text-anchor="middle">100</text><text x="135" y="55" font-family="sans-serif" font-size="44" font-weight="900" fill="#FFFFFF" text-anchor="middle">100</text><text x="90" y="22" font-family="sans-serif" font-size="12" font-weight="bold" fill="#FED7D7" text-anchor="middle">中華民國中央銀行</text><text x="135" y="75" font-family="sans-serif" font-size="14" font-weight="bold" fill="#FEEBC8" text-anchor="middle">壹佰圓</text></svg>"""
SVG_50 = """<svg width="84" height="84" viewBox="0 0 84 84" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(2px 3px 4px rgba(0,0,0,0.35)); margin:4px;"><circle cx="42" cy="42" r="40" fill="#D69E2E" stroke="#744210" stroke-width="2"/><circle cx="42" cy="42" r="34" fill="#ECC94B" stroke="#B7791F" stroke-width="1.5"/><circle cx="42" cy="42" r="26" fill="#D69E2E"/><text x="42" y="49" font-family="sans-serif" font-size="28" font-weight="900" fill="#5A3207" text-anchor="middle">50</text><text x="42" y="61" font-family="sans-serif" font-size="11" font-weight="bold" fill="#744210" text-anchor="middle">圓</text></svg>"""
SVG_10 = """<svg width="76" height="76" viewBox="0 0 76 76" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(2px 3px 4px rgba(0,0,0,0.3)); margin:4px;"><circle cx="38" cy="38" r="36" fill="#A0AEC0" stroke="#4A5568" stroke-width="2"/><circle cx="38" cy="38" r="30" fill="#E2E8F0" stroke="#718096" stroke-width="1.5"/><text x="38" y="44" font-family="sans-serif" font-size="26" font-weight="900" fill="#2D3748" text-anchor="middle">10</text><text x="38" y="56" font-family="sans-serif" font-size="11" font-weight="bold" fill="#4A5568" text-anchor="middle">圓</text></svg>"""
SVG_5 = """<svg width="66" height="66" viewBox="0 0 66 66" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(2px 3px 4px rgba(0,0,0,0.3)); margin:4px;"><circle cx="33" cy="33" r="31" fill="#CBD5E0" stroke="#718096" stroke-width="2"/><circle cx="33" cy="33" r="25" fill="#EDF2F7" stroke="#A0AEC0" stroke-width="1"/><text x="33" y="39" font-family="sans-serif" font-size="22" font-weight="900" fill="#2D3748" text-anchor="middle">5</text><text x="33" y="49" font-family="sans-serif" font-size="10" font-weight="bold" fill="#4A5568" text-anchor="middle">圓</text></svg>"""
SVG_1 = """<svg width="58" height="58" viewBox="0 0 58 58" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(2px 3px 4px rgba(0,0,0,0.3)); margin:4px;"><circle cx="29" cy="29" r="27" fill="#DD6B20" stroke="#7B341E" stroke-width="2"/><circle cx="29" cy="29" r="21" fill="#ED8936" stroke="#9C4221" stroke-width="1"/><text x="29" y="35" font-family="sans-serif" font-size="20" font-weight="900" fill="#431407" text-anchor="middle">1</text><text x="29" y="45" font-family="sans-serif" font-size="10" font-weight="bold" fill="#652B19" text-anchor="middle">圓</text></svg>"""

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
        workweek.append({"date": d, "label": label, "is_today": is_today})
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

st.markdown("""
<style>
    html { scroll-behavior: smooth; }
    html, body, [class*="css"] { font-size: 22px; }
    
    .simple-title {
        font-size: 32px !important;
        font-weight: 900 !important;
        color: #1E3A8A !important;
        margin-top: 10px !important;
        margin-bottom: 16px !important;
        padding-left: 10px;
        border-left: 8px solid #3B82F6;
    }

    /* 日期大按鈕 */
    .date-btn button {
        width: 100% !important; min-height: 95px !important;
        font-size: 26px !important; font-weight: 900 !important;
        border-radius: 18px !important; border: 3px solid #CBD5E1 !important;
        background-color: #F8FAFC !important; color: #1E293B !important;
        white-space: pre-line !important;
    }
    .date-btn-active button {
        width: 100% !important; min-height: 95px !important;
        font-size: 26px !important; font-weight: 900 !important;
        border-radius: 18px !important; border: 3.5px solid #1E40AF !important;
        background-color: #2563EB !important; color: #FFFFFF !important;
        white-space: pre-line !important;
    }

    /* 未點餐同仁按鍵 */
    .user-btn button {
        width: 100% !important; min-height: 100px !important;
        font-size: 28px !important; font-weight: 900 !important;
        border-radius: 18px !important; border: 3px solid #22C55E !important;
        background-color: #F0FDF4 !important; color: #166534 !important;
        margin-bottom: 14px !important; white-space: pre-line !important;
    }
    
    /* 已完成點餐同仁按鍵（灰底標記已點餐） */
    .user-btn-done button {
        width: 100% !important; min-height: 100px !important;
        font-size: 28px !important; font-weight: 900 !important;
        border-radius: 18px !important; border: 3px solid #94A3B8 !important;
        background-color: #F1F5F9 !important; color: #64748B !important;
        margin-bottom: 14px !important; white-space: pre-line !important;
    }

    /* 店家大按鍵 */
    .store-btn button {
        width: 100% !important; min-height: 95px !important;
        font-size: 28px !important; font-weight: 900 !important;
        border-radius: 18px !important; border: 3px solid #F59E0B !important;
        background-color: #FFFBEB !important; color: #92400E !important;
        margin-bottom: 14px !important;
    }

    /* 餐點大卡片 */
    .food-card {
        background-color: #FFFFFF; border: 2.5px solid #CBD5E1;
        border-radius: 20px; padding: 22px; margin-bottom: 22px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }

    /* 橫式選項大按鈕：未選中 */
    .h-option-btn button {
        width: 100% !important; min-height: 72px !important;
        font-size: 22px !important; font-weight: 900 !important;
        border-radius: 16px !important; border: 2.5px solid #94A3B8 !important;
        background-color: #F8FAFC !important; color: #334155 !important;
        white-space: pre-line !important;
    }
    .h-option-btn button:hover {
        border-color: #3B82F6 !important; background-color: #EFF6FF !important;
    }

    /* 橫式選項大按鈕：已選中 (深藍底白字) */
    .h-option-btn-active button {
        width: 100% !important; min-height: 72px !important;
        font-size: 22px !important; font-weight: 900 !important;
        border-radius: 16px !important; border: 3.5px solid #1D4ED8 !important;
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(37,99,235,0.35) !important;
        white-space: pre-line !important;
    }

    .qty-btn button {
        font-size: 32px !important; font-weight: 900 !important;
        min-height: 56px !important; width: 100% !important;
        border-radius: 14px !important; border: 2px solid #3B82F6 !important;
        background-color: #EFF6FF !important; color: #1D4ED8 !important;
    }
    .qty-display {
        font-size: 28px; font-weight: 900; color: #1E293B;
        text-align: center; line-height: 56px;
        background-color: #F8FAFC; border-radius: 12px;
        border: 2px solid #CBD5E1;
    }

    /* 鮮豔亮橘色確認加入按鈕 */
    div[data-testid="stButton"] button[kind="primary"],
    div.food-order-btn button,
    div.food-order-btn button[kind="primary"],
    div.food-order-btn button[data-testid="stBaseButton-primary"] {
        width: 100% !important;
        min-height: 86px !important;
        font-size: 26px !important;
        font-weight: 900 !important;
        border-radius: 18px !important;
        border: 3px solid #C2410C !important;
        background: linear-gradient(135deg, #FF6B00 0%, #EA580C 100%) !important;
        background-color: #FF6B00 !important;
        color: #FFFFFF !important;
        box-shadow: 0 6px 14px rgba(234,88,12,0.4) !important;
        margin-top: 14px !important;
        white-space: pre-line !important;
        line-height: 1.3 !important;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover,
    div.food-order-btn button:hover {
        background: linear-gradient(135deg, #EA580C 0%, #C2410C 100%) !important;
        background-color: #EA580C !important;
        color: #FFFFFF !important;
        border-color: #9A3412 !important;
        transform: translateY(-2px);
    }

    .big-pay-card {
        background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
        border: 4px solid #22C55E;
        border-radius: 24px;
        padding: 30px 24px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 8px 24px rgba(34,197,94,0.25);
    }

    .already-ordered-card {
        background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%);
        border: 3.5px solid #64748B;
        border-radius: 22px;
        padding: 26px;
        text-align: center;
        margin-bottom: 24px;
    }

    .added-feedback-card {
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        border: 4px solid #2563EB;
        border-radius: 22px;
        padding: 24px;
        text-align: center;
        margin-bottom: 24px;
        box-shadow: 0 8px 22px rgba(37,99,235,0.25);
    }

    .budget-banner {
        background-color: #F8FAFC;
        border-radius: 14px;
        padding: 12px 18px;
        border-left: 8px solid #3B82F6;
        font-size: 24px;
        font-weight: 800;
        margin-bottom: 16px;
    }

    .category-filter-btn button {
        width: 100% !important; min-height: 64px !important;
        font-size: 22px !important; font-weight: 900 !important;
        border-radius: 14px !important; border: 2.5px solid #94A3B8 !important;
        background-color: #F8FAFC !important; color: #334155 !important;
        margin-bottom: 8px !important;
    }
    .category-filter-btn button:hover {
        border-color: #3B82F6 !important; background-color: #EFF6FF !important;
    }
    .category-filter-active button {
        width: 100% !important; min-height: 64px !important;
        font-size: 22px !important; font-weight: 900 !important;
        border-radius: 14px !important; border: 3px solid #1D4ED8 !important;
        background-color: #2563EB !important; color: #FFFFFF !important;
        margin-bottom: 8px !important; box-shadow: 0 4px 10px rgba(37,99,235,0.3) !important;
    }

    .cart-summary {
        background-color: #FEF3C7; border: 3px solid #F59E0B;
        border-radius: 18px; padding: 18px; font-size: 24px;
        font-weight: 900; color: #92400E; margin-bottom: 20px;
    }

    .cart-edit-card {
        background-color: #F0FDF4; border: 2.5px solid #22C55E;
        border-radius: 16px; padding: 16px; margin-bottom: 16px;
    }

    .money-visual-board {
        background-color: #FFFFFF; border: 3px dashed #60A5FA;
        border-radius: 16px; padding: 20px; margin-top: 14px; margin-bottom: 14px;
    }
    .money-group-row {
        display: flex; flex-wrap: wrap; align-items: center; gap: 14px;
        margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px solid #F1F5F9;
    }

    .order-row-card {
        background-color: #FFFFFF; border: 1.5px solid #E2E8F0;
        border-radius: 14px; padding: 16px 20px; margin-bottom: 14px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }

    .receipt-box {
        background-color: #FFFFFF;
        border: 2px dashed #475569;
        border-radius: 16px;
        padding: 24px;
        margin-top: 16px;
        margin-bottom: 24px;
    }
    .receipt-header {
        text-align: center;
        border-bottom: 2px dashed #94A3B8;
        padding-bottom: 16px;
        margin-bottom: 18px;
    }

    .float-top-btn {
        position: fixed; bottom: 25px; left: 25px; z-index: 99999;
        background-color: #0284C7; color: white !important;
        width: 70px; height: 70px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 32px; font-weight: bold; text-decoration: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3); border: 2px solid white;
    }

    @media print {
        body * { visibility: hidden; }
        #print-area, #print-area * { visibility: visible; }
        #print-area { position: absolute; left: 0; top: 0; width: 100%; }
        .no-print { display: none !important; }
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

def reset_ordering():
    st.session_state.date_selected = False
    st.session_state.selected_user = None
    st.session_state.selected_store = None
    st.session_state.selected_category = "全部"
    st.session_state.user_daily_limit = 0.0
    st.session_state.cart = []
    st.session_state.order_finished = False
    st.session_state.jump_to_items = False
    st.session_state.cart_edit_idx = None
    st.session_state.just_added_item = None
    st.session_state.last_order_total = 0.0
    
    keys_to_clear = [k for k in st.session_state.keys() if k.startswith("qty_") or k.startswith("sel_opt_") or k.startswith("sel_ex_")]
    for k in keys_to_clear:
        del st.session_state[k]

if "orders_data" not in st.session_state:
    st.session_state.orders_data = load_orders_from_sheet()
if "target_order_date" not in st.session_state:
    st.session_state.target_order_date = date.today()
if "date_selected" not in st.session_state:
    st.session_state.date_selected = False
if "selected_user" not in st.session_state:
    st.session_state.selected_user = None
if "user_daily_limit" not in st.session_state:
    st.session_state.user_daily_limit = 0.0
if "selected_store" not in st.session_state:
    st.session_state.selected_store = None
if "selected_category" not in st.session_state:
    st.session_state.selected_category = "全部"
if "jump_to_items" not in st.session_state:
    st.session_state.jump_to_items = False
if "cart" not in st.session_state:
    st.session_state.cart = []
if "cart_edit_idx" not in st.session_state:
    st.session_state.cart_edit_idx = None
if "just_added_item" not in st.session_state:
    st.session_state.just_added_item = None
if "order_finished" not in st.session_state:
    st.session_state.order_finished = False
if "last_order_total" not in st.session_state:
    st.session_state.last_order_total = 0.0
if "edit_row_idx" not in st.session_state:
    st.session_state.edit_row_idx = None

df_menu = load_menu()
df_users = load_users()

st.title("🍱 中餐點餐與管理系統")

tab1, tab2, tab3 = st.tabs(["🛒 友善大圖點餐", "💵 現場收款對帳", "🖨️ 訂單彙整出單"])

# -------------------------------------------------------------
# 分頁 1：友善大圖點餐
# -------------------------------------------------------------
with tab1:
    chosen_date_str = str(st.session_state.target_order_date)

    # 1. 送單完成畫面
    if st.session_state.order_finished:
        order_total_pay = st.session_state.last_order_total
        st.markdown(f"""
        <div class="big-pay-card">
            <div style="font-size: 34px; font-weight: 900; color: #166534; margin-bottom: 10px;">
                🎉 【{st.session_state.selected_user}】訂單已成功送出！
            </div>
            <div style="font-size: 26px; color: #374151; margin-bottom: 14px;">
                📅 預訂用餐日期：<b>{chosen_date_str}</b>
            </div>
            <div style="font-size: 30px; font-weight: 900; color: #1F2937;">
                👉 請準備好現金：<span style="color: #DC2626; font-size: 56px; font-weight: 900;">${fmt_price(order_total_pay)}</span> 元
            </div>
        </div>
        """, unsafe_allow_html=True)

        rem_p = int(order_total_pay)
        p100, rem_p = rem_p // 100, rem_p % 100
        p50, rem_p = rem_p // 50, rem_p % 50
        p10, rem_p = rem_p // 10, rem_p % 10
        p5, p1 = rem_p // 5, rem_p % 5

        if order_total_pay > 0:
            st.markdown("#### 🪙 您可以準備這些錢交給幹部：")
            board_html = "<div class='money-visual-board'>"
            if p100 > 0: board_html += f"<div class='money-group-row'>{''.join([SVG_100 for _ in range(p100)])}</div>"
            if p50 > 0: board_html += f"<div class='money-group-row'>{''.join([SVG_50 for _ in range(p50)])}</div>"
            if p10 > 0: board_html += f"<div class='money-group-row'>{''.join([SVG_10 for _ in range(p10)])}</div>"
            if p5 > 0: board_html += f"<div class='money-group-row'>{''.join([SVG_5 for _ in range(p5)])}</div>"
            if p1 > 0: board_html += f"<div class='money-group-row'>{''.join([SVG_1 for _ in range(p1)])}</div>"
            board_html += "</div>"
            st.markdown(board_html, unsafe_allow_html=True)

        st.write("")
        if st.button("👉 換下一位點餐", type="primary", use_container_width=True):
            reset_ordering()
            st.rerun()

    # 2. 步驟 1：選用餐日期
    elif not st.session_state.date_selected:
        st.markdown('<div class="simple-title">第 1 步：請點選預訂用餐日期</div>', unsafe_allow_html=True)
        workweek_list = get_current_workweek_dates()
        
        d_cols = st.columns(5)
        for idx, w in enumerate(workweek_list):
            is_active = (st.session_state.target_order_date == w["date"])
            with d_cols[idx]:
                st.markdown(f'<div class="{"date-btn-active" if is_active else "date-btn"}">', unsafe_allow_html=True)
                if st.button(w["label"], key=f"date_btn_{idx}"):
                    st.session_state.target_order_date = w["date"]
                    st.session_state.date_selected = True
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        st.write("")
        st.markdown("#### 📅 或自行選擇其他日期：")
        col_cd1, col_cd2 = st.columns([2, 2])
        with col_cd1:
            custom_date = st.date_input("點選月曆挑選日期", value=st.session_state.target_order_date, key="custom_date_selector")
        with col_cd2:
            st.write("")
            st.write("")
            if st.button("👉 確認此日期並前往點餐", type="primary", use_container_width=True):
                st.session_state.target_order_date = custom_date
                st.session_state.date_selected = True
                st.rerun()

    # 3. 步驟 2：選姓名（自動辨識已點餐過的人）
    elif st.session_state.selected_user is None:
        c_head1, c_head2 = st.columns([3, 1])
        with c_head1:
            st.markdown(f'<div class="simple-title">第 2 步：請問你是誰？（預訂：<b>{chosen_date_str}</b>）</div>', unsafe_allow_html=True)
        with c_head2:
            if st.button("⬅️ 更換日期", use_container_width=True):
                st.session_state.date_selected = False
                st.rerun()

        # 檢查當天有哪些同仁已經有點過餐
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
                lim_text = f"限額 ${fmt_price(u_lim)} 元" if u_lim > 0 else "無限制額度"
                
                # 自動辨識已點過餐的人
                is_already_ordered = (u_name in ordered_users_today)
                if is_already_ordered:
                    btn_u_label = f"👤 {u_name}（✅ 今日已點過餐）"
                    btn_class = "user-btn-done"
                else:
                    btn_u_label = f"👤 {u_name}\n（{lim_text}）"
                    btn_class = "user-btn"

                with u_cols[idx % 2]:
                    st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
                    if st.button(btn_u_label, key=f"user_{idx}"):
                        st.session_state.selected_user = u_name
                        st.session_state.user_daily_limit = u_lim
                        st.session_state.selected_category = "全部"
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    # 4. 步驟 3：已點餐者提示 或 選擇店家
    elif st.session_state.selected_store is None:
        u_name = st.session_state.selected_user
        u_lim = st.session_state.user_daily_limit

        # 再次檢查該同仁在該日是否已點過餐
        all_orders = st.session_state.orders_data
        user_already_orders = pd.DataFrame()
        if not all_orders.empty and "訂購日期" in all_orders.columns and "員工姓名" in all_orders.columns:
            date_mask = all_orders["訂購日期"].astype(str).str.replace("-", "/").str.contains(chosen_date_str.replace("-", "/"))
            user_already_orders = all_orders[date_mask & (all_orders["員工姓名"] == u_name)]

        # 如果已經點過餐，跳出已完成提示，不用再點餐
        if not user_already_orders.empty:
            spent_amount = user_already_orders["小計金額"].apply(parse_price).sum()
            ordered_items_text = "、".join(user_already_orders["餐點品項"].tolist())
            
            st.markdown(f"""
            <div class="already-ordered-card">
                <div style="font-size:36px; font-weight:900; color:#1E293B; margin-bottom:10px;">
                    ✅ 【{u_name}】您在【{chosen_date_str}】已經點過餐囉！
                </div>
                <div style="font-size:26px; color:#334155; margin-bottom:12px;">
                    🍲 已點餐點：<b>{ordered_items_text}</b>
                </div>
                <div style="font-size:28px; font-weight:900; color:#DC2626; margin-bottom:16px;">
                    應付總金額：${fmt_price(spent_amount)} 元 ｜ 狀態：{user_already_orders['付款狀態'].values[0]}
                </div>
                <div style="font-size:22px; color:#64748B;">
                    （系統已自動記錄，您不需重複點餐）
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_bk1, col_bk2 = st.columns(2)
            with col_bk1:
                if st.button("👉 換下一位點餐", type="primary", use_container_width=True):
                    reset_ordering()
                    st.rerun()
            with col_bk2:
                if st.button("➕ 我還要加點其他餐點", use_container_width=True):
                    # 允許額外加點
                    st.session_state.selected_store = "主要合作店家" if "店家名稱" not in df_menu.columns else df_menu["店家名稱"].dropna().unique()[0]
                    st.rerun()

        else:
            lim_str = f"今日限額：<b>${fmt_price(u_lim)} 元</b>" if u_lim > 0 else "今日限額：<b>無限制</b>"
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f'<div class="budget-banner">👤 同仁：<b>{u_name}</b> ｜ 📅 預訂：<b>{chosen_date_str}</b> ｜ {lim_str}</div>', unsafe_allow_html=True)
            with c2:
                if st.button("⬅️ 重選名字/日期"):
                    st.session_state.selected_user = None
                    st.rerun()

            st.markdown('<div class="simple-title">第 3 步：想吃哪一家？（點店家）</div>', unsafe_allow_html=True)
            store_list = df_menu["店家名稱"].dropna().unique().tolist() if "店家名稱" in df_menu.columns else ["主要合作店家"]
            s_cols = st.columns(2)
            for idx, s_name in enumerate(store_list):
                with s_cols[idx % 2]:
                    st.markdown('<div class="store-btn">', unsafe_allow_html=True)
                    if st.button(f"🏪 {s_name}", key=f"store_{idx}"):
                        st.session_state.selected_store = s_name
                        st.session_state.selected_category = "全部"
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    # 5. 步驟 4：挑選餐點（自動依限額過濾可選餐點 + 橫式選項）
    else:
        u_name = st.session_state.selected_user
        store_name = st.session_state.selected_store
        u_lim = st.session_state.user_daily_limit

        # 計算今日已點金額
        all_orders = st.session_state.orders_data
        already_spent_today = 0.0
        if not all_orders.empty and "訂購日期" in all_orders.columns and "員工姓名" in all_orders.columns:
            d_mask = all_orders["訂購日期"].astype(str).str.replace("-", "/").str.contains(chosen_date_str.replace("-", "/"))
            user_done = all_orders[d_mask & (all_orders["員工姓名"] == u_name)]
            if not user_done.empty:
                already_spent_today = user_done["小計金額"].apply(parse_price).sum()

        cart_sum = sum(x["subtotal"] for x in st.session_state.cart)
        remain_budget = round(u_lim - already_spent_today - cart_sum, 2) if u_lim > 0 else 999999

        if u_lim > 0:
            budget_banner_text = f"👤 <b>{u_name}</b> ｜ 每日限額：<b>${fmt_price(u_lim)}</b> 元 ｜ 已點/購物車：<b>${fmt_price(already_spent_today + cart_sum)}</b> 元 ｜ 剩餘可用：<b style='color:#DC2626;'>${fmt_price(remain_budget)}</b> 元"
        else:
            budget_banner_text = f"👤 <b>{u_name}</b> ｜ 每日限額：<b>無限制</b> ｜ 目前合計：<b>${fmt_price(cart_sum)}</b> 元"

        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f'<div class="budget-banner">{budget_banner_text}</div>', unsafe_allow_html=True)
        with c2:
            if st.button("⬅️ 重選店家"):
                st.session_state.selected_store = None
                st.session_state.selected_category = "全部"
                st.session_state.cart = []
                st.session_state.cart_edit_idx = None
                st.session_state.just_added_item = None
                st.rerun()

        # -------------------------------------------------------------
        # 點選餐點後跳出的大回饋卡片
        # -------------------------------------------------------------
        if st.session_state.just_added_item is not None:
            added_info = st.session_state.just_added_item
            st.markdown(f"""
            <div class="added-feedback-card">
                <div style="font-size:36px; font-weight:900; color:#1E40AF; margin-bottom:8px;">
                    🎉 已加入購物車！
                </div>
                <div style="font-size:26px; font-weight:900; color:#1F2937; margin-bottom:6px;">
                    🍲 【{added_info['item']}】（{added_info['spec']} ｜ {added_info['extra']}）
                </div>
                <div style="font-size:24px; color:#DC2626; font-weight:900; margin-bottom:14px;">
                    數量：{added_info['qty']} 份 ｜ 小計：${fmt_price(added_info['subtotal'])} 元 ｜ 購物車累計：${fmt_price(cart_sum)} 元
                </div>
            </div>
            """, unsafe_allow_html=True)

            fb_col1, fb_col2 = st.columns(2)
            with fb_col1:
                if st.button("➕ 還想再點其他餐點", key="btn_continue_add", use_container_width=True):
                    st.session_state.just_added_item = None
                    st.rerun()
            with fb_col2:
                if st.button("🛒 我點好了，直接送出訂單！", type="primary", key="btn_go_checkout", use_container_width=True):
                    st.session_state.just_added_item = None
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
                    with st.spinner("同步雲端資料中..."):
                        sync_to_google_sheet({"action": "append", "rows": new_rows})
                    st.session_state.order_finished = True
                    st.rerun()
            st.write("---")

        # -------------------------------------------------------------
        # 本次點餐清單
        # -------------------------------------------------------------
        if st.session_state.cart and st.session_state.just_added_item is None:
            st.markdown("### 🛒 本次點餐清單：")

            if st.session_state.cart_edit_idx is not None and st.session_state.cart_edit_idx < len(st.session_state.cart):
                e_c_idx = st.session_state.cart_edit_idx
                cart_item_to_edit = st.session_state.cart[e_c_idx]

                st.markdown(f"""
                <div class="cart-edit-card">
                    <div style="font-size:24px; font-weight:900; color:#166534; margin-bottom:10px;">
                        ✏️ 正在修改：{cart_item_to_edit['item']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_ce1, col_ce2, col_ce3 = st.columns([2, 1, 1])
                with col_ce1:
                    new_c_spec = st.text_input("種類 / 規格", value=cart_item_to_edit['spec'], key=f"ce_spec_{e_c_idx}")
                with col_ce2:
                    new_c_qty = st.number_input("數量", min_value=1, value=int(cart_item_to_edit['qty']), step=1, key=f"ce_qty_{e_c_idx}")
                with col_ce3:
                    is_liumei_store = "劉妹" in str(store_name)
                    if is_liumei_store:
                        new_c_extra = st.selectbox("加麵", ["不加麵", "要加麵 (+15元)"],
                                                    index=0 if "不加" in cart_item_to_edit.get("extra", "") else 1, key=f"ce_ex_{e_c_idx}")
                    else:
                        new_c_extra = "不加麵"

                b_sub1, b_sub2 = st.columns(2)
                with b_sub1:
                    if st.button("💾 確認修改並更新此道餐點", type="primary", key="btn_save_cart_edit"):
                        unit_p = cart_item_to_edit['unit_price']
                        if "要加麵" in new_c_extra and "不加" in cart_item_to_edit.get("extra", ""):
                            unit_p += 15
                        elif "不加" in new_c_extra and "要加麵" in cart_item_to_edit.get("extra", ""):
                            unit_p = max(0, unit_p - 15)

                        st.session_state.cart[e_c_idx]['spec'] = new_c_spec
                        st.session_state.cart[e_c_idx]['qty'] = new_c_qty
                        st.session_state.cart[e_c_idx]['extra'] = new_c_extra
                        st.session_state.cart[e_c_idx]['unit_price'] = unit_p
                        st.session_state.cart[e_c_idx]['subtotal'] = round(unit_p * new_c_qty, 2)
                        st.session_state.cart_edit_idx = None
                        st.success("已更新餐點！")
                        time.sleep(0.3)
                        st.rerun()
                with b_sub2:
                    if st.button("❌ 放棄修改", key="btn_cancel_cart_edit"):
                        st.session_state.cart_edit_idx = None
                        st.rerun()

            for c_idx, c_item in enumerate(st.session_state.cart):
                cc1, cc2, cc3 = st.columns([3, 1, 1])
                with cc1:
                    st.markdown(f"""
                    <div style="font-size:22px; padding:10px 0; border-bottom:1px solid #E2E8F0;">
                        🍲 <b>{c_item['item']}</b> ｜ 種類：<b>{c_item['spec']}</b> ｜ {c_item.get('extra', '不加麵')} ｜ <b>{c_item['qty']} 份</b> ｜ <b style="color:#EA580C;">${fmt_price(c_item['subtotal'])} 元</b>
                    </div>
                    """, unsafe_allow_html=True)
                with cc2:
                    if st.button("✏️ 改這道", key=f"btn_edit_cart_{c_idx}"):
                        st.session_state.cart_edit_idx = c_idx
                        st.rerun()
                with cc3:
                    if st.button("🗑️ 取消", key=f"btn_del_cart_{c_idx}"):
                        st.session_state.cart.pop(c_idx)
                        if st.session_state.cart_edit_idx == c_idx:
                            st.session_state.cart_edit_idx = None
                        st.rerun()

            st.markdown(f"""
            <div class="cart-summary" style="margin-top:14px;">
                💰 目前合計共 <b>{len(st.session_state.cart)}</b> 項 ｜ 總應付金額：<span style="color:#DC2626; font-size:32px;">${fmt_price(cart_sum)}</span> 元
            </div>
            """, unsafe_allow_html=True)
            
            sc1, sc2 = st.columns([2, 1])
            with sc1:
                if st.button(f"✅ 我選好了，確認送出訂單（應付 ${fmt_price(cart_sum)} 元）！", type="primary", use_container_width=True):
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
                    with st.spinner("同步雲端資料中..."):
                        sync_to_google_sheet({"action": "append", "rows": new_rows})
                    st.session_state.order_finished = True
                    st.rerun()
            with sc2:
                if st.button("🗑️ 清空重選", use_container_width=True):
                    st.session_state.cart = []
                    st.session_state.cart_edit_idx = None
                    st.rerun()

        st.write("---")

        current_store_menu = df_menu[df_menu["店家名稱"] == store_name] if "店家名稱" in df_menu.columns else df_menu

        # 餐點種類篩選按鍵
        st.markdown('<div class="simple-title">📌 餐點種類（點選後自動跳轉餐點）：</div>', unsafe_allow_html=True)
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
                if st.button(get_category_icon(cat_name), key=f"cat_btn_{c_idx}"):
                    st.session_state.selected_category = cat_name
                    st.session_state.jump_to_items = True
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        st.write("---")

        st.markdown('<div id="menu_items_anchor"></div>', unsafe_allow_html=True)
        if st.session_state.jump_to_items:
            st.markdown("""
            <script>
                setTimeout(function() {
                    var el = window.parent.document.getElementById('menu_items_anchor');
                    if (el) { el.scrollIntoView({behavior: 'smooth'}); }
                }, 100);
            </script>
            """, unsafe_allow_html=True)
            st.session_state.jump_to_items = False
        
        active_cat = st.session_state.selected_category
        if active_cat != "全部" and "分類" in current_store_menu.columns:
            filtered_menu = current_store_menu[current_store_menu["分類"] == active_cat]
        else:
            filtered_menu = current_store_menu

        # -------------------------------------------------------------
        # 系統依限額自動篩選：只顯示符合預算（未超額）的餐點
        # -------------------------------------------------------------
        affordable_items = []
        for _, item_row in filtered_menu.iterrows():
            item_base_price = parse_price(item_row.get("單價", 0))
            if u_lim > 0 and item_base_price > remain_budget:
                continue  # 自動隱藏超出剩餘預算的餐點
            affordable_items.append(item_row)

        st.markdown(f'<div class="simple-title">今天我要吃？（【{active_cat}】預算內可選購餐點）</div>', unsafe_allow_html=True)

        if not affordable_items:
            if u_lim > 0 and remain_budget <= 0:
                st.warning(f"⚠️ 【{u_name}】您今天的額度已用完（剩餘 ${fmt_price(remain_budget)} 元），無法再加點其他餐點！")
            else:
                st.info(f"此種類【{active_cat}】目前沒有符合您剩餘預算的餐點。")
        else:
            m_cols = st.columns(2)
            for idx, item in enumerate(affordable_items):
                i_name = str(item.get("餐點名稱", "")).strip()
                base_p = parse_price(item.get("單價", 0))
                category = str(item.get("分類", ""))
                
                raw_options = ""
                if "種類選擇" in item: raw_options = str(item["種類選擇"]).strip()
                elif "麵類選擇" in item: raw_options = str(item["麵類選擇"]).strip()

                is_soup = "湯" in i_name or "湯" in category or any(x in raw_options for x in ["小", "中", "大"])

                if raw_options and raw_options not in ["-", "nan", "無", "固定"]:
                    type_options = [opt.strip() for opt in re.split(r"[/,、|]+", raw_options) if opt.strip()]
                elif is_soup:
                    type_options = ["小", "中 (+10元)", "大 (+20元)"]
                else:
                    type_options = ["標準配置"]

                is_liumei = "劉妹" in str(store_name)
                qty_key = safe_key("qty", i_name, idx)
                opt_sel_key = safe_key("sel_opt", i_name, idx)
                ex_sel_key = safe_key("sel_ex", i_name, idx)

                if qty_key not in st.session_state:
                    st.session_state[qty_key] = 1
                if opt_sel_key not in st.session_state:
                    st.session_state[opt_sel_key] = type_options[0]
                if ex_sel_key not in st.session_state:
                    st.session_state[ex_sel_key] = "不加麵"

                chosen_type = st.session_state[opt_sel_key]
                chosen_ex = st.session_state[ex_sel_key]

                with m_cols[idx % 2]:
                    with st.container():
                        st.markdown(f"""
                        <div class="food-card">
                            <div style="font-size: 30px; font-weight: 900; color: #1E293B; margin-bottom: 6px;">🍲 {i_name}</div>
                            <div style="font-size: 24px; color: #475569; margin-bottom: 12px;">單價：<b style="color:#059669; font-size:28px;">${fmt_price(base_p)} 元</b></div>
                        """, unsafe_allow_html=True)
                        
                        # -------------------------------------------------------------
                        # 橫式點選：種類與尺寸大按鍵（橫向排列，方便單手與不識字操作）
                        # -------------------------------------------------------------
                        if len(type_options) > 1:
                            st.markdown("<div style='font-size:22px; font-weight:bold; color:#1E3A8A; margin-bottom:8px;'>👉 請點選種類 / 規格：</div>", unsafe_allow_html=True)
                            opt_cols = st.columns(len(type_options))
                            for o_idx, opt_txt in enumerate(type_options):
                                is_opt_active = (chosen_type == opt_txt)
                                opt_btn_class = "h-option-btn-active" if is_opt_active else "h-option-btn"
                                opt_label = f"✅ {opt_txt}" if is_opt_active else opt_txt
                                with opt_cols[o_idx]:
                                    st.markdown(f'<div class="{opt_btn_class}">', unsafe_allow_html=True)
                                    if st.button(opt_label, key=safe_key("btn_h_opt", f"{i_name}_{opt_txt}", idx)):
                                        st.session_state[opt_sel_key] = opt_txt
                                        st.rerun()
                                    st.markdown('</div>', unsafe_allow_html=True)

                        # 橫式點選：加麵選項大按鈕
                        if is_liumei:
                            st.markdown("<div style='font-size:22px; font-weight:bold; color:#1E3A8A; margin-top:10px; margin-bottom:8px;'>👉 是否要加麵：</div>", unsafe_allow_html=True)
                            ex_cols = st.columns(2)
                            for e_idx, ex_opt in enumerate(["不加麵", "要加麵 (+15元)"]):
                                is_ex_active = (chosen_ex == ex_opt)
                                ex_btn_class = "h-option-btn-active" if is_ex_active else "h-option-btn"
                                ex_label = f"✅ {ex_opt}" if is_ex_active else ex_opt
                                with ex_cols[e_idx]:
                                    st.markdown(f'<div class="{ex_btn_class}">', unsafe_allow_html=True)
                                    if st.button(ex_label, key=safe_key("btn_h_ex", f"{i_name}_{ex_opt}", idx)):
                                        st.session_state[ex_sel_key] = ex_opt
                                        st.rerun()
                                    st.markdown('</div>', unsafe_allow_html=True)

                        # 挑選數量
                        st.markdown("<div style='font-size:22px; font-weight:bold; color:#1E3A8A; margin-top:10px; margin-bottom:6px;'>👉 挑選數量：</div>", unsafe_allow_html=True)
                        cq1, cq2, cq3 = st.columns([1, 2, 1])
                        with cq1:
                            st.markdown('<div class="qty-btn">', unsafe_allow_html=True)
                            if st.button("➖", key=safe_key("minus", i_name, idx)):
                                if st.session_state[qty_key] > 1:
                                    st.session_state[qty_key] -= 1
                                    st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)
                        with cq2:
                            st.markdown(f'<div class="qty-display">{st.session_state[qty_key]} 份</div>', unsafe_allow_html=True)
                        with cq3:
                            st.markdown('<div class="qty-btn">', unsafe_allow_html=True)
                            if st.button("➕", key=safe_key("plus", i_name, idx)):
                                if st.session_state[qty_key] < 30:
                                    st.session_state[qty_key] += 1
                                    st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)

                        extra_type_price = parse_extra_price(chosen_type)
                        extra_ex_price = 15 if chosen_ex == "要加麵 (+15元)" else 0
                        current_unit_price = round(base_p + extra_type_price + extra_ex_price, 2)
                        current_qty = st.session_state[qty_key]
                        current_subtotal = round(current_unit_price * current_qty, 2)

                        can_add = (u_lim == 0) or (current_subtotal <= remain_budget)

                        if can_add:
                            order_btn_label = f"🛒 確認加入：{i_name} ({chosen_type})\n{current_qty} 份 ｜ 共 ${fmt_price(current_subtotal)} 元"
                        else:
                            order_btn_label = f"❌ 超出今日限額（剩餘額度 ${fmt_price(remain_budget)} 元）"

                        st.markdown('<div class="food-order-btn">', unsafe_allow_html=True)
                        if st.button(order_btn_label, key=safe_key("add_order", i_name, idx), type="primary", disabled=not can_add):
                            item_data = {
                                "item": i_name,
                                "spec": chosen_type,
                                "extra": chosen_ex,
                                "unit_price": current_unit_price,
                                "qty": current_qty,
                                "subtotal": current_subtotal
                            }
                            st.session_state.cart.append(item_data)
                            st.session_state.just_added_item = item_data
                            st.session_state[qty_key] = 1
                            st.toast(f"✅ 已成功加入購物車：{i_name} x {current_qty} 份！", icon="🛒")
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

                        st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------
# 分頁 2：現場收款對帳
# -------------------------------------------------------------
with tab2:
    st.subheader("💵 現場收款、找零與訂單修改維護")
    q_date = st.date_input("選擇收款日期", value=st.session_state.target_order_date, key="q_date_recon")
    if st.button("🔄 重新載入最新資料", key="btn_reload_recon"):
        st.session_state.orders_data = load_orders_from_sheet()
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
                target_user = st.selectbox("選擇要繳費收款的同仁", options=user_options)
                user_unpaid_items = unpaid[unpaid["員工姓名"] == target_user]
                target_due = round(user_unpaid_items["金額數值"].sum(), 2)

                st.markdown(f"""
                <div style="background-color: #FEF2F2; border: 2px solid #F87171; border-radius: 14px; padding: 16px; margin-top: 10px;">
                    👤 收款對象：<b>{target_user}</b><br>
                    💰 應收金額：<b style="color: #DC2626; font-size: 34px;">${fmt_price(target_due)}</b> 元
                </div>
                """, unsafe_allow_html=True)

            with calc_col2:
                st.write("點選同仁拿出的面額：")
                q_col1, q_col2, q_col3 = st.columns(3)
                with q_col1:
                    if st.button("剛好", key="pay_exact"):
                        st.session_state.received_cash = float(target_due)
                with q_col2:
                    if st.button("💵 拿 100", key="pay_100"):
                        st.session_state.received_cash = 100.0
                with q_col3:
                    if st.button("💵 拿 500", key="pay_500"):
                        st.session_state.received_cash = 500.0

                default_val = st.session_state.get("received_cash", float(target_due))
                paid_input = st.number_input("或自訂實收金額 (元)", min_value=0.0, value=float(default_val), step=1.0)

                change = round(paid_input - target_due, 2)
                if change >= 0:
                    st.markdown(f"""
                    <div style="background-color: #ECFDF5; border: 2px solid #34D399; border-radius: 14px; padding: 16px; margin-top: 10px;">
                        🪙 應找零錢：<b style="color: #059669; font-size: 34px;">${fmt_price(change)}</b> 元
                    </div>
                    """, unsafe_allow_html=True)

                    rem_c = int(change)
                    c100, rem_c = rem_c // 100, rem_c % 100
                    c50, rem_c = rem_c // 50, rem_c % 50
                    c10, rem_c = rem_c // 10, rem_c % 10
                    c5, c1 = rem_c // 5, rem_c % 5

                    if change > 0:
                        st.markdown("### 👉 請照著畫面「看到幾個就拿幾個」找給同仁：")
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
                        st.success(f"已完成 {target_user} 收款並同步至雲端！")
                        time.sleep(0.5)
                        st.rerun()
                else:
                    st.error(f"⚠️ 還不夠喔！同仁還差 ${fmt_price(abs(change))} 元")

        st.write("---")

        # 單筆訂單編輯面板
        if st.session_state.edit_row_idx is not None:
            e_idx = st.session_state.edit_row_idx
            if e_idx in st.session_state.orders_data.index:
                orig = st.session_state.orders_data.loc[e_idx]
                with st.form("edit_order_form_recon"):
                    st.subheader(f"✏️ 編輯訂單：【第 {e_idx + 1} 筆 - {orig.get('訂單編號', '')}】")
                    ed1, ed2 = st.columns(2)
                    with ed1:
                        new_name = st.text_input("同仁姓名", value=str(orig.get("員工姓名", "")))
                        new_date = st.text_input("用餐/訂單日期", value=str(orig.get("訂購日期", "")))
                        new_item = st.text_input("餐點品項", value=str(orig.get("餐點品項", "")))
                        new_qty = st.number_input("數量", min_value=1, value=int(parse_price(orig.get("數量", 1)) or 1), step=1)
                    with ed2:
                        new_price = st.number_input("小計金額 (元)", min_value=0.0, value=float(parse_price(orig.get("小計金額", 0))), step=0.5)
                        new_spec = st.text_input("種類 / 規格選擇", value=str(orig.get("麵類選擇", "標準配置")))
                        new_extra = st.selectbox("是否加麵", ["不加麵", "要加麵 (+15元)"],
                                                index=0 if "不加" in str(orig.get("是否加麵", "")) else 1)
                        new_status = st.selectbox("付款狀態", ["未付款", "已付款"],
                                                 index=0 if orig.get("付款狀態", "") != "已付款" else 1)

                    btn_c1, btn_c2 = st.columns(2)
                    with btn_c1:
                        if st.form_submit_button("💾 儲存修改並同步雲端", type="primary", use_container_width=True):
                            updated_dict = {
                                "訂單編號": str(orig.get("訂單編號", "")),
                                "訂購日期": new_date,
                                "員工編號": str(orig.get("員工編號", "")),
                                "員工姓名": new_name,
                                "所屬部門": str(orig.get("所屬部門", "")),
                                "餐點品項": new_item,
                                "麵類選擇": new_spec,
                                "是否加麵": new_extra,
                                "單價": f"${fmt_price(new_price / new_qty)}",
                                "數量": new_qty,
                                "小計金額": f"${fmt_price(new_price)}",
                                "付款狀態": new_status
                            }
                            for k, v in updated_dict.items():
                                st.session_state.orders_data.loc[e_idx, k] = v

                            with st.spinner("正在將修改完整同步至 Google 試算表..."):
                                sync_to_google_sheet({
                                    "action": "edit_order",
                                    "order_id": str(orig.get("訂單編號", "")),
                                    "orig_user": str(orig.get("員工姓名", "")),
                                    "row": updated_dict
                                })
                            st.session_state.edit_row_idx = None
                            st.success("訂單修改完成！")
                            time.sleep(0.5)
                            st.rerun()
                    with btn_c2:
                        if st.form_submit_button("❌ 取消編輯", use_container_width=True):
                            st.session_state.edit_row_idx = None
                            st.rerun()

        st.markdown("#### 📋 訂單清單（可直接點擊 ✏️ 編輯 或 🗑️ 刪除）：")
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
                            st.rerun()
                with r6:
                    ed_c1, ed_c2 = st.columns(2)
                    with ed_c1:
                        if st.button("✏️", key=f"recon_edit_{row_idx}_{ord_id}", help="編輯此筆訂單"):
                            st.session_state.edit_row_idx = row_idx
                            st.rerun()
                    with ed_c2:
                        if st.button("🗑️", key=f"recon_del_{row_idx}_{ord_id}", help="刪除這筆訂單"):
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
                            st.success("訂單已成功刪除！")
                            time.sleep(0.4)
                            st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------
# 分頁 3：訂單彙整出單
# -------------------------------------------------------------
with tab3:
    st.subheader("🖨️ 中餐訂單出單與分發彙整表")
    
    col_od1, col_od2 = st.columns([2, 1])
    with col_od1:
        order_out_date = st.date_input("選擇欲出單的日期", value=st.session_state.target_order_date, key="out_order_date_input")
    with col_od2:
        st.write("")
        if st.button("🔄 重新整理訂單數據", type="primary", key="btn_refresh_out"):
            st.session_state.orders_data = load_orders_from_sheet()
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
            st.warning(f"⚠️ 在【{order_out_date}】查無點單紀錄，請先確認同仁是否已送出餐點。")
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
                st.success(f"🎉【{order_out_date}】全體同仁皆已完成付款！可直接放心出單給店家。")
            else:
                st.warning(f"⚠️ 提醒：尚有 {unpaid_cnt} 筆訂單尚未付款（待收 ${fmt_price(unpaid_sum)} 元），請先至【💵 現場收款對帳】完成收款！")

            def make_spec_name(r):
                item = str(r.get("餐點品項", "")).strip()
                nd = str(r.get("麵類選擇", "")).strip()
                ex = str(r.get("是否加麵", "")).strip()
                spec_parts = []
                if nd and nd not in ["-", "nan", "無", "標準配置", "標準"]:
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
            person_grouped.columns = ["同仁姓名", "點購餐點品項明細", "應付小計", "付款狀態"]

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
                st.markdown("#### 📞 1. 店家總單（打電話報單照這個唸）：")
                st.dataframe(summary_grouped, use_container_width=True, hide_index=True)

            with c_out_col2:
                st.markdown("#### 👥 2. 個人發放核對名單（便當送達時對照發放）：")
                st.dataframe(person_grouped, use_container_width=True, hide_index=True)

            st.write("")
            with st.expander("📲 點此展開「LINE 一鍵複製店家格式」文字", expanded=False):
                st.text_area("直接複製以下文字傳給店家即可：", value=line_order_text, height=220)

            c_p1, c_p2 = st.columns([1, 3])
            with c_p1:
                st.button("🖨️ 列印此出單表 (PDF)", on_click=lambda: st.components.v1.html("<script>window.print();</script>", height=0))
            with c_p2:
                st.caption("💡 提示：點擊「列印出單表」後，可在彈出視窗中選擇另存為 PDF 或直接列印紙本發餐勾選單！")
