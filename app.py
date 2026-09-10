import streamlit as st
import pandas as pd
import requests
import json
import time
import re
import hashlib
from datetime import date

st.set_page_config(page_title="中餐點餐系統", page_icon="🍱", layout="wide")

APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbw0UEIp80umbupbDQkMQAa5-3Z4HQp01r9VH_Zr-0nYnPzXv6jgY_gKYFyScn7e2Lrj/exec"
SHEET_ID = "1mHnXoG-Duq45EvwZTRVuq86rsK8T5DA9NkLnOi30wuM"
ORDERS_GID = "1002"

st.markdown("""
<style>
    html { scroll-behavior: smooth; }
    html, body, [class*="css"] { font-size: 20px; }
    
    /* 姓名大按鈕 */
    .user-btn button {
        width: 100% !important; min-height: 85px !important;
        font-size: 26px !important; font-weight: bold !important;
        border-radius: 16px !important; margin-bottom: 12px !important;
        border: 2px solid #CBD5E1 !important; background-color: #FFFFFF !important;
        box-shadow: 0 3px 6px rgba(0,0,0,0.05) !important;
    }
    .user-btn button:hover { border-color: #2563EB !important; background-color: #EFF6FF !important; }
    
    /* 店家大按鈕 */
    .store-btn button {
        width: 100% !important; min-height: 95px !important;
        font-size: 28px !important; font-weight: 900 !important;
        border-radius: 18px !important; margin-bottom: 14px !important;
        background-color: #FEF3C7 !important; color: #92400E !important;
        border: 2px solid #F59E0B !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.08) !important;
    }
    .store-btn button:hover {
        background-color: #FDE68A !important; border-color: #D97706 !important;
    }

    /* 置頂吸附分類導航列 (Sticky Header) */
    .sticky-category-bar {
        position: -webkit-sticky;
        position: sticky;
        top: 0;
        z-index: 999;
        background-color: #F8FAFC;
        padding: 14px 10px;
        margin-bottom: 18px;
        border-bottom: 3px solid #3B82F6;
        border-radius: 0 0 16px 16px;
        box-shadow: 0 6px 12px rgba(0,0,0,0.08);
    }

    /* 分類大按鈕：加大字體、間距與點擊範圍 */
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label {
        background-color: #FFFFFF;
        border: 2px solid #94A3B8;
        border-radius: 14px;
        padding: 12px 24px !important;
        min-height: 64px !important;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px !important;
        font-weight: 900 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        cursor: pointer;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
        border-color: #2563EB;
        background-color: #EFF6FF;
    }

    /* 餐點大圖卡 */
    .food-card {
        background-color: #FFFFFF; border: 2px solid #CBD5E1;
        border-radius: 18px; padding: 18px; margin-bottom: 18px;
        box-shadow: 0 3px 8px rgba(0,0,0,0.06);
    }
    
    /* 數量加大計數按鈕 (+/-) */
    .qty-control button {
        font-size: 26px !important; font-weight: 900 !important;
        min-height: 52px !important; width: 100% !important;
        border-radius: 12px !important; border: 2px solid #94A3B8 !important;
    }
    .qty-display {
        font-size: 26px; font-weight: 900; color: #1E293B;
        text-align: center; line-height: 52px;
        background-color: #F8FAFC; border-radius: 10px;
        border: 1px solid #E2E8F0;
    }
    
    /* 購物車與預算欄 */
    .cart-item {
        background-color: #F8FAFC; border-left: 8px solid #2563EB;
        padding: 14px 18px; border-radius: 10px; margin-bottom: 10px; font-size: 22px;
    }
    .budget-banner {
        background-color: #EFF6FF; border: 2.5px solid #3B82F6;
        border-radius: 16px; padding: 16px 22px; font-size: 24px;
        font-weight: bold; color: #1E3A8A; margin-bottom: 20px;
    }
    .over-limit-box {
        background-color: #FDE8E8; border: 3px solid #F98080;
        border-radius: 18px; padding: 26px; font-size: 30px;
        font-weight: bold; color: #9B1C1C; text-align: center;
        margin-top: 20px; margin-bottom: 25px;
    }
    .big-pay-box {
        background-color: #DEF7EC; border: 3px solid #31C48D;
        border-radius: 18px; padding: 26px; font-size: 32px;
        font-weight: bold; color: #03543F; text-align: center;
        margin-top: 15px; margin-bottom: 25px;
    }
    .big-next-btn button {
        width: 100% !important; min-height: 90px !important;
        font-size: 32px !important; font-weight: bold !important;
        border-radius: 18px !important; background-color: #EF4444 !important;
        color: white !important; box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }
    .big-next-btn button:hover { background-color: #DC2626 !important; }
    
    .add-cart-btn button {
        width: 100% !important; min-height: 62px !important;
        font-size: 22px !important; font-weight: bold !important;
        border-radius: 14px !important;
    }
    
    .scroll-top-btn {
        display: block; width: 100%; text-align: center;
        background-color: #0284C7; color: #FFFFFF !important;
        font-size: 24px; font-weight: bold; padding: 18px;
        border-radius: 16px; text-decoration: none; margin-top: 25px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.12);
    }
    .scroll-top-btn:hover { background-color: #0369A1; }

    .float-top-btn {
        position: fixed; bottom: 25px; right: 25px; z-index: 9999;
        background-color: #0284C7; color: white !important;
        width: 65px; height: 65px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 28px; font-weight: bold; text-decoration: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .float-top-btn:hover { background-color: #0369A1; }

    .order-row-card {
        background-color: #FFFFFF; border: 1.5px solid #E2E8F0;
        border-radius: 12px; padding: 14px 18px; margin-bottom: 12px;
    }
    .money-visual-board {
        background-color: #FFFFFF; border: 3px dashed #60A5FA;
        border-radius: 16px; padding: 20px; margin-top: 14px; margin-bottom: 14px;
    }
    .money-group-row {
        display: flex; flex-wrap: wrap; align-items: center; gap: 14px;
        margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px solid #F1F5F9;
    }
</style>
""", unsafe_allow_html=True)

# 頂部錨點與全螢幕懸浮置頂按鈕
st.markdown('<div id="top_anchor"></div>', unsafe_allow_html=True)
st.markdown('<a href="#top_anchor" class="float-top-btn" title="回頂部">⬆️</a>', unsafe_allow_html=True)

SVG_100 = """<svg width="180" height="90" viewBox="0 0 180 90" xmlns="http://www.w3.org/2000/svg" style="border-radius:6px; box-shadow:2px 3px 6px rgba(0,0,0,0.3); margin:4px;"><rect width="180" height="90" rx="6" fill="#C53030"/><rect x="4" y="4" width="172" height="82" rx="4" fill="none" stroke="#FED7D7" stroke-width="1.5" stroke-dasharray="4,2"/><circle cx="45" cy="45" r="22" fill="#9B2C2C"/><circle cx="45" cy="45" r="18" fill="none" stroke="#FEB2B2" stroke-width="1"/><text x="45" y="52" font-family="sans-serif" font-size="20" font-weight="bold" fill="#FED7D7" text-anchor="middle">100</text><text x="135" y="55" font-family="sans-serif" font-size="44" font-weight="900" fill="#FFFFFF" text-anchor="middle">100</text><text x="90" y="22" font-family="sans-serif" font-size="12" font-weight="bold" fill="#FED7D7" text-anchor="middle">中華民國中央銀行</text><text x="135" y="75" font-family="sans-serif" font-size="14" font-weight="bold" fill="#FEEBC8" text-anchor="middle">壹佰圓</text></svg>"""
SVG_50 = """<svg width="84" height="84" viewBox="0 0 84 84" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(2px 3px 4px rgba(0,0,0,0.35)); margin:4px;"><circle cx="42" cy="42" r="40" fill="#D69E2E" stroke="#744210" stroke-width="2"/><circle cx="42" cy="42" r="34" fill="#ECC94B" stroke="#B7791F" stroke-width="1.5"/><circle cx="42" cy="42" r="26" fill="#D69E2E"/><text x="42" y="49" font-family="sans-serif" font-size="28" font-weight="900" fill="#5A3207" text-anchor="middle">50</text><text x="42" y="61" font-family="sans-serif" font-size="11" font-weight="bold" fill="#744210" text-anchor="middle">圓</text></svg>"""
SVG_10 = """<svg width="76" height="76" viewBox="0 0 76 76" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(2px 3px 4px rgba(0,0,0,0.3)); margin:4px;"><circle cx="38" cy="38" r="36" fill="#A0AEC0" stroke="#4A5568" stroke-width="2"/><circle cx="38" cy="38" r="30" fill="#E2E8F0" stroke="#718096" stroke-width="1.5"/><text x="38" y="44" font-family="sans-serif" font-size="26" font-weight="900" fill="#2D3748" text-anchor="middle">10</text><text x="38" y="56" font-family="sans-serif" font-size="11" font-weight="bold" fill="#4A5568" text-anchor="middle">圓</text></svg>"""
SVG_5 = """<svg width="66" height="66" viewBox="0 0 66 66" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(2px 3px 4px rgba(0,0,0,0.3)); margin:4px;"><circle cx="33" cy="33" r="31" fill="#CBD5E0" stroke="#718096" stroke-width="2"/><circle cx="33" cy="33" r="25" fill="#EDF2F7" stroke="#A0AEC0" stroke-width="1"/><text x="33" y="39" font-family="sans-serif" font-size="22" font-weight="900" fill="#2D3748" text-anchor="middle">5</text><text x="33" y="49" font-family="sans-serif" font-size="10" font-weight="bold" fill="#4A5568" text-anchor="middle">圓</text></svg>"""
SVG_1 = """<svg width="58" height="58" viewBox="0 0 58 58" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(2px 3px 4px rgba(0,0,0,0.3)); margin:4px;"><circle cx="29" cy="29" r="27" fill="#DD6B20" stroke="#7B341E" stroke-width="2"/><circle cx="29" cy="29" r="21" fill="#ED8936" stroke="#9C4221" stroke-width="1"/><text x="29" y="35" font-family="sans-serif" font-size="20" font-weight="900" fill="#431407" text-anchor="middle">1</text><text x="29" y="45" font-family="sans-serif" font-size="10" font-weight="bold" fill="#652B19" text-anchor="middle">圓</text></svg>"""

REQUIRED_ORDER_COLS = [
    "訂單編號", "訂購日期", "員工編號", "員工姓名", "所屬部門", 
    "餐點品項", "麵類選擇", "是否加麵", "單價", "數量", "小計金額", "付款狀態"
]

def safe_key(prefix, text, idx=0):
    clean_txt = hashlib.md5(str(text).encode('utf-8')).hexdigest()[:8]
    return f"{prefix}_{idx}_{clean_txt}"

def parse_price(val):
    try:
        clean = str(val).replace("$", "").replace(",", "").strip()
        v = float(clean)
        return int(v) if v.is_integer() else round(v, 2)
    except:
        return 0

def fmt_price(val):
    try:
        clean = str(val).replace("$", "").replace(",", "").strip()
        v = float(clean)
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
        t = int(time.time())
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
        t = int(time.time())
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=users&_t={t}"
        df = pd.read_csv(url)
        return df.dropna(subset=["姓名"]) if "姓名" in df.columns else df
    except:
        return pd.DataFrame()

def load_orders_from_sheet():
    t = int(time.time())
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={ORDERS_GID}&_t={t}"
    try:
        raw_df = pd.read_csv(url, header=None)
        h_idx = 3
        for i in range(min(10, len(raw_df))):
            row_vals = [str(x).strip() for x in raw_df.iloc[i].tolist()]
            if any("訂單編號" in v or "員工姓名" in v for v in row_vals):
                h_idx = i
                break
        
        df = pd.read_csv(url, header=h_idx)
        df.columns = [str(c).strip() for c in df.columns]

        for col in df.columns:
            if "日期" in col and "訂購日期" not in df.columns:
                df.rename(columns={col: "訂購日期"}, inplace=True)
            elif "姓名" in col and "員工姓名" not in df.columns:
                df.rename(columns={col: "員工姓名"}, inplace=True)
            elif "小計" in col and "小計金額" not in df.columns:
                df.rename(columns={col: "小計金額"}, inplace=True)
            elif "狀態" in col and "付款狀態" not in df.columns:
                df.rename(columns={col: "付款狀態"}, inplace=True)
            elif "種類" in col and "麵類選擇" not in df.columns:
                df.rename(columns={col: "麵類選擇"}, inplace=True)

        for req in REQUIRED_ORDER_COLS:
            if req not in df.columns:
                df[req] = ""

        if "員工姓名" in df.columns:
            df = df.dropna(subset=["員工姓名"])
            df = df[~df["員工姓名"].astype(str).str.contains("總計|合計", na=False)]
            df = df[df["員工姓名"].astype(str).str.strip() != ""]
            df = df[df["員工姓名"].astype(str).str.strip() != "nan"]
        return df
    except:
        return pd.DataFrame(columns=REQUIRED_ORDER_COLS)

def sync_to_google_sheet(payload):
    try:
        data_str = json.dumps(payload, ensure_ascii=False)
        headers = {"Content-Type": "text/plain;charset=utf-8"}
        resp = requests.post(APPS_SCRIPT_URL, data=data_str.encode('utf-8'), headers=headers, timeout=15, allow_redirects=True)
        return True, resp.text
    except Exception as e:
        return False, str(e)

def reset_to_next_user():
    st.session_state.selected_user = None
    st.session_state.selected_store = None
    st.session_state.selected_category = "全部品項"
    st.session_state.user_limit = 0
    st.session_state.cart = []
    st.session_state.last_paid_amount = 0
    st.session_state.order_finished = False
    
    keys_to_clear = [k for k in st.session_state.keys() if k.startswith("qty_val_") or k.startswith("nd_") or k.startswith("ex_")]
    for k in keys_to_clear:
        del st.session_state[k]

if "orders_data" not in st.session_state:
    st.session_state.orders_data = load_orders_from_sheet()
if "selected_user" not in st.session_state:
    st.session_state.selected_user = None
if "selected_store" not in st.session_state:
    st.session_state.selected_store = None
if "selected_category" not in st.session_state:
    st.session_state.selected_category = "全部品項"
if "user_limit" not in st.session_state:
    st.session_state.user_limit = 0
if "cart" not in st.session_state:
    st.session_state.cart = []
if "order_finished" not in st.session_state:
    st.session_state.order_finished = False
if "last_paid_amount" not in st.session_state:
    st.session_state.last_paid_amount = 0
if "edit_order_id" not in st.session_state:
    st.session_state.edit_order_id = None

df_menu = load_menu()
df_users = load_users()

st.title("🍱 中餐點餐與管理系統")

tab1, tab2, tab3, tab4 = st.tabs([
    "🛒 友善大圖點餐", 
    "📊 明細與對帳", 
    "⚙️ 菜單管理與編輯", 
    "👥 人員名單管理"
])

# -------------------------------------------------------------
# 分頁 1：友善大圖點餐（隨螢幕下滑置頂吸附的分類導航列）
# -------------------------------------------------------------
with tab1:
    today_str = str(date.today())
    
    # 點餐完成畫面
    if st.session_state.order_finished:
        pay_amount = st.session_state.last_paid_amount
        st.markdown(f"""
        <div class="big-pay-box">
            🎉 已完成訂單！<br>
            請準備 <span style="color: #DC2626; font-size: 48px; font-weight: 900;">${fmt_price(pay_amount)}</span> 元付款
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="big-next-btn">', unsafe_allow_html=True)
        if st.button("👉 換下一位點餐", key="btn_next_user"):
            reset_to_next_user()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 第一步：選擇姓名
    elif st.session_state.selected_user is None:
        st.subheader("👉 第一步：請問你是誰？（點你的名字）")
        if df_users.empty or "姓名" not in df_users.columns:
            st.warning("⚠️ 尚無人員名單，請至【👥 人員名單管理】確認。")
        else:
            cols = st.columns(2)
            for idx, (_, u_row) in enumerate(df_users.iterrows()):
                u_name = str(u_row["姓名"]).strip()
                raw_lim = u_row.get("金額限制", 0)
                lim_val = parse_price(raw_lim)
                lim_badge = f"（限額 ${fmt_price(lim_val)} 元）" if lim_val > 0 else "（不限額）"

                with cols[idx % 2]:
                    st.markdown('<div class="user-btn">', unsafe_allow_html=True)
                    if st.button(f"👤 {u_name} {lim_badge}", key=safe_key("sel_u", u_name, idx)):
                        st.session_state.selected_user = u_name
                        st.session_state.selected_store = None
                        st.session_state.selected_category = "全部品項"
                        st.session_state.user_limit = lim_val
                        st.session_state.cart = []
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    # 第二步：選擇店家
    elif st.session_state.selected_store is None:
        u_name = st.session_state.selected_user
        u_limit = st.session_state.user_limit

        df_all = st.session_state.orders_data
        already_spent_today = 0
        if not df_all.empty and "員工姓名" in df_all.columns and "訂購日期" in df_all.columns:
            d_s = df_all["訂購日期"].astype(str).str.replace("-", "/")
            today_slash = today_str.replace("-", "/")
            user_today_orders = df_all[(df_all["員工姓名"] == u_name) & (d_s == today_slash)]
            already_spent_today = round(user_today_orders["小計金額"].apply(parse_price).sum(), 2)

        if u_limit > 0 and already_spent_today >= u_limit:
            st.markdown(f"""
            <div class="over-limit-box">
                ⚠️ 【{u_name}】您今日已達到金額上限！<br>
                本日限定額度：${fmt_price(u_limit)} 元 ｜ 今日已點金額：<b>${fmt_price(already_spent_today)}</b> 元<br>
                <span style="font-size: 22px; color: #4B5563;">（今日不可再加點其他餐點）</span>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="big-next-btn">', unsafe_allow_html=True)
            if st.button("👉 換下一位點餐", key="btn_next_overlimit_store"):
                reset_to_next_user()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        else:
            rem_b = round(u_limit - already_spent_today, 2)
            limit_txt = f"今日限額：<b>${fmt_price(u_limit)}</b> 元 ｜ 今日已累計：<b>${fmt_price(already_spent_today)}</b> 元 ｜ 剩餘額度：<b style='color:#DC2626;'>${fmt_price(rem_b)}</b> 元" if u_limit > 0 else "今日限額：<b>無限制</b>"
            st.markdown(f'<div class="budget-banner">👤 目前同仁：{u_name} ｜ {limit_txt}</div>', unsafe_allow_html=True)

            c_head1, c_head2 = st.columns([3, 1])
            with c_head1:
                st.subheader("👉 第二步：今天想吃哪一家？（點選店家）")
            with c_head2:
                if st.button("⬅️ 重選同仁"):
                    reset_to_next_user()
                    st.rerun()

            if "店家名稱" in df_menu.columns:
                store_list = df_menu["店家名稱"].dropna().unique().tolist()
            else:
                store_list = ["主要合作店家"]

            if not store_list:
                store_list = ["主要合作店家"]

            cols_store = st.columns(2)
            for s_idx, store_name in enumerate(store_list):
                with cols_store[s_idx % 2]:
                    st.markdown('<div class="store-btn">', unsafe_allow_html=True)
                    if st.button(f"🏪 {store_name}", key=safe_key("sel_store", store_name, s_idx)):
                        st.session_state.selected_store = store_name
                        st.session_state.selected_category = "全部品項"
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    # 第三步：挑選餐點
    else:
        u_name = st.session_state.selected_user
        current_store = st.session_state.selected_store
        u_limit = st.session_state.user_limit

        df_all = st.session_state.orders_data
        already_spent_today = 0
        if not df_all.empty and "員工姓名" in df_all.columns and "訂購日期" in df_all.columns:
            d_s = df_all["訂購日期"].astype(str).str.replace("-", "/")
            today_slash = today_str.replace("-", "/")
            user_today_orders = df_all[(df_all["員工姓名"] == u_name) & (d_s == today_slash)]
            already_spent_today = round(user_today_orders["小計金額"].apply(parse_price).sum(), 2)

        cart_sum = round(sum(x["subtotal"] for x in st.session_state.cart), 2)
        remaining_daily_budget = round(u_limit - already_spent_today - cart_sum, 2) if u_limit > 0 else 999999

        if u_limit > 0:
            limit_info = f"今日限額：<b>${fmt_price(u_limit)}</b> 元 ｜ 今日已點：<b>${fmt_price(already_spent_today)}</b> 元 ｜ 本次還可點：<b style='color:#DC2626;'>${fmt_price(remaining_daily_budget)}</b> 元"
        else:
            limit_info = "今日限額：<b>無限制</b>"

        st.markdown(f'<div class="budget-banner">👤 同仁：{u_name} ｜ 🏪 店家：{current_store} ｜ {limit_info}</div>', unsafe_allow_html=True)

        with st.container():
            col_t1, col_t2 = st.columns([3, 1])
            with col_t1:
                st.markdown(f"### 🛒 本次點餐清單（共 {len(st.session_state.cart)} 樣，本次合計 **${fmt_price(cart_sum)}** 元）")
            with col_t2:
                if st.button("⬅️ 重選店家"):
                    st.session_state.selected_store = None
                    st.session_state.selected_category = "全部品項"
                    st.session_state.cart = []
                    st.rerun()

            if st.session_state.cart:
                for c_idx, c_item in enumerate(st.session_state.cart):
                    cc1, cc2 = st.columns([4, 1])
                    with cc1:
                        qty_str = f" x <b>{c_item['qty']}</b>" if c_item['qty'] > 1 else ""
                        st.markdown(f"""
                        <div class="cart-item">
                            🍲 <b>{c_item['item']}</b>{qty_str} ｜ 種類/份量：<b>{c_item['noodle']}</b> ｜ 加麵：<b>{c_item['extra']}</b> ｜ 金額：<b style="color:#DC2626;">${fmt_price(c_item['subtotal'])} 元</b>
                        </div>
                        """, unsafe_allow_html=True)
                    with cc2:
                        if st.button("🗑️ 取消", key=f"btn_del_{c_idx}"):
                            st.session_state.cart.pop(c_idx)
                            st.rerun()

                st.write("")
                if st.button("✅ 我選好了，送出全部餐點！", type="primary", use_container_width=True):
                    user_dept = ""
                    if not df_users.empty and "姓名" in df_users.columns:
                        match_u = df_users[df_users["姓名"] == u_name]
                        if not match_u.empty and "組別" in match_u.columns:
                            user_dept = match_u["組別"].values[0]

                    new_rows = []
                    current_len = len(st.session_state.orders_data)
                    for i, it in enumerate(st.session_state.cart):
                        new_rows.append({
                            "訂單編號": f"ORD-{current_len + i + 1:03d}",
                            "訂購日期": today_str,
                            "員工編號": "",
                            "員工姓名": u_name,
                            "所屬部門": user_dept,
                            "餐點品項": it["item"],
                            "麵類選擇": it["noodle"],
                            "是否加麵": it["extra"],
                            "單價": f"${fmt_price(it['unit_price'])}",
                            "數量": it["qty"],
                            "小計金額": f"${fmt_price(it['subtotal'])}",
                            "付款狀態": "未付款"
                        })

                    st.session_state.last_paid_amount = cart_sum
                    new_df = pd.DataFrame(new_rows)
                    st.session_state.orders_data = pd.concat([st.session_state.orders_data, new_df], ignore_index=True)

                    with st.spinner("同步儲存至 Google 試算表..."):
                        sync_to_google_sheet({
                            "action": "append",
                            "rows": new_rows
                        })

                    st.session_state.order_finished = True
                    st.rerun()

        st.write("---")

        # 篩選菜單
        store_menu = df_menu.copy()
        if "供應狀態" in store_menu.columns:
            store_menu = store_menu[store_menu["供應狀態"] == "供應中"]
        if "店家名稱" in store_menu.columns and current_store:
            store_menu = store_menu[store_menu["店家名稱"] == current_store]

        available_categories = ["全部品項"]
        if "分類" in store_menu.columns:
            raw_cats = [str(c).strip() for c in store_menu["分類"].dropna().unique().tolist() if str(c).strip() not in ["", "nan"]]
            available_categories.extend(raw_cats)

        # -------------------------------------------------------------
        # 隨著頁面下滑吸附置頂的分類選單 (Sticky Header + 大膠囊鍵)
        # -------------------------------------------------------------
        st.markdown('<div class="sticky-category-bar">', unsafe_allow_html=True)
        st.markdown(f"**📌 請選擇餐點分類（自動吸附置頂）：**")
        cat_choice = st.radio(
            label="餐點分類選單",
            options=available_categories,
            horizontal=True,
            index=available_categories.index(st.session_state.selected_category) if st.session_state.selected_category in available_categories else 0,
            key="category_selector",
            label_visibility="collapsed"
        )
        st.session_state.selected_category = cat_choice
        st.markdown('</div>', unsafe_allow_html=True)

        # 依所選類別進一步篩選菜單品項
        if cat_choice != "全部品項" and "分類" in store_menu.columns:
            filtered_menu = store_menu[store_menu["分類"] == cat_choice]
        else:
            filtered_menu = store_menu

        displayed_items = []
        for _, row in filtered_menu.iterrows():
            base_p = parse_price(row.get("單價", 0))
            if u_limit > 0 and base_p > remaining_daily_budget:
                continue
            displayed_items.append((row, base_p))

        st.write(f"#### 🍲 【{cat_choice}】餐點清單：")

        if not displayed_items:
            st.warning(f"⚠️ 【{cat_choice}】沒有符合您剩餘預算的餐點，或品項已達金額上限！")
        else:
            cols = st.columns(2)
            for idx, (m_row, base_p) in enumerate(displayed_items):
                item_name = m_row["餐點名稱"]
                category = str(m_row.get("分類", ""))
                
                raw_options = ""
                if "種類選擇" in m_row:
                    raw_options = str(m_row["種類選擇"]).strip()
                elif "麵類選擇" in m_row:
                    raw_options = str(m_row["麵類選擇"]).strip()

                is_soup = "湯" in item_name or "湯" in category or any(x in raw_options for x in ["小", "中", "大"])

                if raw_options and raw_options not in ["-", "nan", "無", "固定"]:
                    type_options = [opt.strip() for opt in re.split(r"[/,、|]+", raw_options) if opt.strip()]
                elif is_soup:
                    type_options = ["小", "中 (+10元)", "大 (+20元)"]
                else:
                    type_options = ["標準配置"]

                is_liumei = "劉妹" in str(current_store)
                select_label = "尺寸" if is_soup else "種類"
                
                qty_key = safe_key("qty_val", item_name, idx)
                if qty_key not in st.session_state:
                    st.session_state[qty_key] = 1

                with cols[idx % 2]:
                    with st.container():
                        st.markdown(f"""
                        <div class="food-card">
                            <h3 style="margin-top:0; margin-bottom:6px; color:#1E293B;">🍲 {item_name}</h3>
                            <div style="font-size:20px; color:#475569; margin-bottom:12px;">單價：<b style="color:#059669; font-size:24px;">${fmt_price(base_p)} 元</b></div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.write(f"**👉 選擇{select_label}：**")
                        nd_choice = st.radio(
                            label=f"選擇{select_label}",
                            options=type_options,
                            key=safe_key("nd", item_name, idx),
                            horizontal=True,
                            label_visibility="collapsed"
                        )

                        st.write("**👉 選擇數量：**")
                        c_minus, c_num, c_plus = st.columns([1, 2, 1])
                        with c_minus:
                            st.markdown('<div class="qty-control">', unsafe_allow_html=True)
                            if st.button("➖", key=safe_key("btn_minus", item_name, idx)):
                                if st.session_state[qty_key] > 1:
                                    st.session_state[qty_key] -= 1
                                    st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                        with c_num:
                            st.markdown(f'<div class="qty-display">{st.session_state[qty_key]} 份</div>', unsafe_allow_html=True)
                            
                        with c_plus:
                            st.markdown('<div class="qty-control">', unsafe_allow_html=True)
                            if st.button("➕", key=safe_key("btn_plus", item_name, idx)):
                                if st.session_state[qty_key] < 30:
                                    st.session_state[qty_key] += 1
                                    st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)

                        if is_liumei:
                            st.write("**👉 份量：**")
                            ex_choice = st.radio(
                                label="份量加麵",
                                options=["不加麵", "要加麵 (+15元)"],
                                horizontal=True,
                                key=safe_key("ex", item_name, idx),
                                label_visibility="collapsed"
                            )
                        else:
                            ex_choice = "不加麵"

                        cur_qty = st.session_state[qty_key]
                        extra_nd = parse_extra_price(nd_choice)
                        extra_ex = 15 if ex_choice == "要加麵 (+15元)" else 0
                        single_unit_price = round(base_p + extra_nd + extra_ex, 2)
                        total_item_price = round(single_unit_price * cur_qty, 2)

                        can_add = (u_limit == 0) or (total_item_price <= remaining_daily_budget)
                        btn_txt = f"➕ 加入點餐 ({cur_qty}份，共 ${fmt_price(total_item_price)} 元)" if can_add else f"❌ 超出今日限額 (${fmt_price(total_item_price)} 元)"

                        st.write("")
                        st.markdown('<div class="add-cart-btn">', unsafe_allow_html=True)
                        if st.button(btn_txt, key=safe_key("add_btn", item_name, idx), disabled=not can_add, type="primary" if can_add else "secondary"):
                            st.session_state.cart.append({
                                "item": item_name,
                                "unit_price": single_unit_price,
                                "qty": cur_qty,
                                "noodle": nd_choice,
                                "extra": ex_choice,
                                "subtotal": total_item_price
                            })
                            st.session_state[qty_key] = 1
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.write("---")

        # 底部大按鈕：返回最頂端
        st.markdown('<a href="#top_anchor" class="scroll-top-btn">⬆️ 返回最頂端（查看購物車／重選店家）</a>', unsafe_allow_html=True)

# -------------------------------------------------------------
# 分頁 2：明細與對帳
# -------------------------------------------------------------
with tab2:
    st.subheader("📊 每日點餐明細與收款找零對帳")

    c_q1, c_q2, c_q3 = st.columns([2, 1, 1])
    with c_q1:
        query_date = st.date_input("選擇欲對帳或查詢的日期", value=date.today())
    with c_q2:
        filter_mode = st.radio("檢視模式", ["📅 依所選日期", "📋 顯示全部訂單"], index=1, horizontal=True)
    with c_q3:
        st.write("")
        if st.button("🔄 重新從雲端抓取", type="primary"):
            st.session_state.orders_data = load_orders_from_sheet()
            st.rerun()

    all_orders = st.session_state.orders_data.copy()

    if all_orders.empty:
        st.info("尚無任何訂單紀錄。請先在【🛒 友善大圖點餐】送出餐點。")
    else:
        q_str_dash = str(query_date).strip()
        q_str_slash = q_str_dash.replace("-", "/")

        if filter_mode == "📋 顯示全部訂單":
            current_orders = all_orders.copy()
        else:
            d_series = all_orders["訂購日期"].astype(str).str.strip()
            date_mask = (d_series == q_str_dash) | (d_series == q_str_slash) | (d_series.str.replace("-", "/") == q_str_slash)
            current_orders = all_orders[date_mask].copy()

        if current_orders.empty:
            st.warning(f"⚠️ 在【{query_date}】查無點單紀錄。（請點選上方「📋 顯示全部訂單」確認）")
        else:
            current_orders["金額數值"] = current_orders["小計金額"].apply(parse_price)
            total_money = round(current_orders["金額數值"].sum(), 2)
            total_items = len(current_orders)

            paid_orders = current_orders[current_orders["付款狀態"] == "已付款"]
            paid_money = round(paid_orders["金額數值"].sum(), 2)
            unpaid_money = round(total_money - paid_money, 2)
            unpaid_count = total_items - len(paid_orders)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("當前檢視總額", f"${fmt_price(total_money)} 元")
            m2.metric("總訂單數", f"{total_items} 筆")
            m3.metric("已收款總額", f"${fmt_price(paid_money)} 元", f"{len(paid_orders)} 筆已收")
            m4.metric("待收餘額 (未收)", f"${fmt_price(unpaid_money)} 元", f"{unpaid_count} 筆待收", delta_color="inverse")

            st.write("---")

            with st.expander("💵 現場收款與【新臺幣實體貨幣】找零輔助器", expanded=True):
                unpaid_list = current_orders[current_orders["付款狀態"] != "已付款"]
                
                if unpaid_list.empty:
                    st.success("🎉 目前檢視範圍內的所有訂單皆已全數收款完畢！")
                else:
                    user_options = unpaid_list["員工姓名"].dropna().unique().tolist()
                    calc_col1, calc_col2 = st.columns([1, 1])
                    
                    with calc_col1:
                        target_user = st.selectbox("選擇要繳費收款的同仁", options=user_options)
                        user_unpaid_items = unpaid_list[unpaid_list["員工姓名"] == target_user]
                        target_due = round(user_unpaid_items["金額數值"].sum(), 2)
                        
                        st.markdown(f"""
                        <div style="background-color: #FEF2F2; border: 2px solid #F87171; border-radius: 12px; padding: 14px; margin-top: 10px;">
                            👤 收款對象：<b>{target_user}</b><br>
                            💰 應收金額：<b style="color: #DC2626; font-size: 32px;">${fmt_price(target_due)}</b> 元
                        </div>
                        """, unsafe_allow_html=True)

                    with calc_col2:
                        st.write("點選同仁拿出的鈔票：")
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
                            <div style="background-color: #ECFDF5; border: 2px solid #34D399; border-radius: 12px; padding: 14px; margin-top: 10px;">
                                🪙 應找零錢：<b style="color: #059669; font-size: 34px;">${fmt_price(change)}</b> 元
                            </div>
                            """, unsafe_allow_html=True)

                            rem_c = int(change)
                            c100 = rem_c // 100
                            rem_c %= 100
                            c50 = rem_c // 50
                            rem_c %= 50
                            c10 = rem_c // 10
                            rem_c %= 10
                            c5 = rem_c // 5
                            c1 = rem_c % 5

                            if change > 0:
                                st.markdown("### 👉 請照著畫面「看到幾個就拿幾個」找給同仁：")
                                board_html = "<div class='money-visual-board'>"
                                if c100 > 0:
                                    board_html += f"<div class='money-group-row'>{''.join([SVG_100 for _ in range(c100)])}</div>"
                                if c50 > 0:
                                    board_html += f"<div class='money-group-row'>{''.join([SVG_50 for _ in range(c50)])}</div>"
                                if c10 > 0:
                                    board_html += f"<div class='money-group-row'>{''.join([SVG_10 for _ in range(c10)])}</div>"
                                if c5 > 0:
                                    board_html += f"<div class='money-group-row'>{''.join([SVG_5 for _ in range(c5)])}</div>"
                                if c1 > 0:
                                    board_html += f"<div class='money-group-row'>{''.join([SVG_1 for _ in range(c1)])}</div>"
                                board_html += "</div>"
                                st.markdown(board_html, unsafe_allow_html=True)
                            else:
                                st.info("👌 剛好收齊，不需要找錢！")

                            st.write("")
                            if st.button(f"✅ 確認收款完畢（將 {target_user} 設為已付款）", type="primary", use_container_width=True):
                                target_indices = st.session_state.orders_data[st.session_state.orders_data["員工姓名"] == target_user].index
                                st.session_state.orders_data.loc[target_indices, "付款狀態"] = "已付款"
                                
                                sync_to_google_sheet({
                                    "action": "update_status",
                                    "date": str(query_date),
                                    "user": target_user,
                                    "status": "已付款"
                                })
                                st.success(f"已完成 {target_user} 收款！")
                                st.rerun()
                        else:
                            st.error(f"⚠️ 還不夠喔！同仁還差 ${fmt_price(abs(change))} 元")

            st.write("---")
            
            if st.session_state.edit_order_id is not None:
                e_id = st.session_state.edit_order_id
                matched_rows = st.session_state.orders_data[st.session_state.orders_data["訂單編號"] == e_id]
                if not matched_rows.empty:
                    orig = matched_rows.iloc[0]
                    with st.form("edit_single_order_form"):
                        st.subheader(f"✏️ 編輯訂單：【{e_id}】")
                        ed_c1, ed_c2 = st.columns(2)
                        with ed_c1:
                            new_name = st.text_input("同仁姓名", value=str(orig.get("員工姓名", "")))
                            new_item = st.text_input("餐點品項", value=str(orig.get("餐點品項", "")))
                            new_qty = st.number_input("數量", min_value=1, value=int(orig.get("數量", 1)), step=1)
                            new_price = st.number_input("小計金額 (元)", min_value=0.0, value=float(parse_price(orig.get("小計金額", 0))), step=0.5)
                        with ed_c2:
                            new_noodle = st.text_input("種類 / 麵類選擇", value=str(orig.get("麵類選擇", "標準配置")))
                            new_extra = st.selectbox("是否加麵", ["不加麵", "要加麵 (+15元)"],
                                                    index=0 if "不加" in str(orig.get("是否加麵", "")) else 1)
                            new_status = st.selectbox("付款狀態", ["未付款", "已付款"],
                                                     index=0 if orig.get("付款狀態", "") != "已付款" else 1)

                        btn_sub1, btn_sub2 = st.columns(2)
                        with btn_sub1:
                            if st.form_submit_button("💾 儲存修改", type="primary", use_container_width=True):
                                idx = matched_rows.index[0]
                                st.session_state.orders_data.loc[idx, "員工姓名"] = new_name
                                st.session_state.orders_data.loc[idx, "餐點品項"] = new_item
                                st.session_state.orders_data.loc[idx, "數量"] = new_qty
                                st.session_state.orders_data.loc[idx, "麵類選擇"] = new_noodle
                                st.session_state.orders_data.loc[idx, "是否加麵"] = new_extra
                                st.session_state.orders_data.loc[idx, "小計金額"] = f"${fmt_price(new_price)}"
                                st.session_state.orders_data.loc[idx, "付款狀態"] = new_status
                                
                                sync_to_google_sheet({
                                    "action": "update_status",
                                    "date": str(orig.get("訂購日期", "")),
                                    "user": new_name,
                                    "status": new_status
                                })
                                st.session_state.edit_order_id = None
                                st.success("訂單修改完成！")
                                st.rerun()
                        with btn_sub2:
                            if st.form_submit_button("❌ 取消編輯", use_container_width=True):
                                st.session_state.edit_order_id = None
                                st.rerun()

            st.markdown("#### 📋 點單明細清單（可直接修改與切換狀態）：")
            for row_idx, row_data in current_orders.iterrows():
                ord_id = row_data.get("訂單編號", "")
                with st.container():
                    st.markdown('<div class="order-row-card">', unsafe_allow_html=True)
                    r_c1, r_c2, r_c3, r_c4, r_c5, r_c6 = st.columns([1.5, 2, 3.5, 1.5, 2, 1.5])
                    with r_c1:
                        st.write(f"**{ord_id}**")
                    with r_c2:
                        st.write(f"👤 **{row_data.get('員工姓名', '')}**")
                    with r_c3:
                        q_info = f" x {row_data.get('數量', 1)}" if str(row_data.get('數量', 1)) not in ["", "1"] else ""
                        st.write(f"{row_data.get('餐點品項', '')}{q_info} ｜ {row_data.get('麵類選擇', '')} ｜ {row_data.get('是否加麵', '')}")
                    with r_c4:
                        st.write(f"<b style='color:#DC2626;'>{row_data.get('小計金額', '')}</b>", unsafe_allow_html=True)
                    with r_c5:
                        cur_status = row_data.get("付款狀態", "未付款")
                        if cur_status == "已付款":
                            if st.button("🟢 已付 (改未付)", key=f"status_btn_{row_idx}"):
                                st.session_state.orders_data.loc[row_idx, "付款狀態"] = "未付款"
                                sync_to_google_sheet({
                                    "action": "update_status",
                                    "date": str(row_data.get("訂購日期", "")),
                                    "user": row_data.get("員工姓名", ""),
                                    "status": "未付款"
                                })
                                st.rerun()
                        else:
                            if st.button("🔴 未付 (改已付)", key=f"status_btn_{row_idx}"):
                                st.session_state.orders_data.loc[row_idx, "付款狀態"] = "已付款"
                                sync_to_google_sheet({
                                    "action": "update_status",
                                    "date": str(row_data.get("訂購日期", "")),
                                    "user": row_data.get("員工姓名", ""),
                                    "status": "已付款"
                                })
                                st.rerun()
                    with r_c6:
                        c_ed1, c_ed2 = st.columns(2)
                        with c_ed1:
                            if st.button("✏️", key=f"btn_edit_{ord_id}", help="編輯此筆訂單"):
                                st.session_state.edit_order_id = ord_id
                                st.rerun()
                        with c_ed2:
                            if st.button("🗑️", key=f"btn_rm_{ord_id}", help="刪除這筆訂單"):
                                st.session_state.orders_data.drop(row_idx, inplace=True)
                                st.session_state.orders_data.reset_index(drop=True, inplace=True)
                                st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------
# 分頁 3：菜單管理
# -------------------------------------------------------------
with tab3:
    st.subheader("⚙️ 菜單品項維護")
    st.caption("💡 提示：在【種類選擇】欄位中填寫該餐點可選的種類（以斜線 / 隔開，如：大/中/小 或 燴飯/燴麵）。")
    if not df_menu.empty:
        st.dataframe(df_menu, use_container_width=True)
    else:
        st.warning("查無菜單資料。")

# -------------------------------------------------------------
# 分頁 4：人員名單與金額限制管理
# -------------------------------------------------------------
with tab4:
    st.subheader("👥 人員名單與個人金額限制維護")
    if not df_users.empty:
        st.dataframe(df_users, use_container_width=True)
    else:
        st.warning("查無人員名單資料。")
