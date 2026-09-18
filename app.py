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

st.markdown("""
<style>
    html { scroll-behavior: smooth; }
    html, body, [class*="css"] { font-size: 22px; }
    
    /* 極簡步驟大標題 */
    .simple-title {
        font-size: 32px !important;
        font-weight: 900 !important;
        color: #1E3A8A !important;
        margin-bottom: 16px !important;
        padding-left: 10px;
        border-left: 8px solid #3B82F6;
    }

    /* 日期大按鈕 */
    .date-btn button {
        width: 100% !important; min-height: 90px !important;
        font-size: 26px !important; font-weight: 900 !important;
        border-radius: 18px !important; border: 3px solid #CBD5E1 !important;
        background-color: #F8FAFC !important; color: #1E293B !important;
        white-space: pre-line !important;
    }
    .date-btn-active button {
        width: 100% !important; min-height: 90px !important;
        font-size: 26px !important; font-weight: 900 !important;
        border-radius: 18px !important; border: 3.5px solid #1E40AF !important;
        background-color: #2563EB !important; color: #FFFFFF !important;
        white-space: pre-line !important;
    }

    /* 人員大按鍵 */
    .user-btn button {
        width: 100% !important; min-height: 95px !important;
        font-size: 28px !important; font-weight: 900 !important;
        border-radius: 18px !important; border: 3px solid #22C55E !important;
        background-color: #F0FDF4 !important; color: #166534 !important;
        margin-bottom: 14px !important;
    }

    /* 店家大按鍵 */
    .store-btn button {
        width: 100% !important; min-height: 95px !important;
        font-size: 28px !important; font-weight: 900 !important;
        border-radius: 18px !important; border: 3px solid #F59E0B !important;
        background-color: #FFFBEB !important; color: #92400E !important;
        margin-bottom: 14px !important;
    }

    /* 餐點大按鍵（點選直接加入） */
    .food-order-btn button {
        width: 100% !important; min-height: 100px !important;
        font-size: 28px !important; font-weight: 900 !important;
        border-radius: 20px !important; border: 3px solid #3B82F6 !important;
        background-color: #EFF6FF !important; color: #1E40AF !important;
        margin-bottom: 16px !important; white-space: pre-line !important;
    }
    .food-order-btn button:hover {
        background-color: #DBEAFE !important; border-color: #1D4ED8 !important;
    }

    /* 購物車提示卡 */
    .cart-summary {
        background-color: #FEF3C7; border: 3px solid #F59E0B;
        border-radius: 18px; padding: 18px; font-size: 24px;
        font-weight: 900; color: #92400E; margin-bottom: 20px;
    }

    /* 左下角回頂部鍵 */
    .float-top-btn {
        position: fixed; bottom: 25px; left: 25px; z-index: 99999;
        background-color: #0284C7; color: white !important;
        width: 70px; height: 70px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 32px; font-weight: bold; text-decoration: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3); border: 2px solid white;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div id="top_anchor"></div>', unsafe_allow_html=True)
st.markdown('<a href="#top_anchor" class="float-top-btn" title="回頂端">⬆️</a>', unsafe_allow_html=True)

REQUIRED_ORDER_COLS = ["訂單編號", "訂購日期", "員工編號", "員工姓名", "所屬部門", "餐點品項", "麵類選擇", "是否加麵", "單價", "數量", "小計金額", "付款狀態"]

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

def load_menu():
    try:
        t = int(time.time() * 1000)
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=menu&_t={t}"
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
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
    st.session_state.selected_user = None
    st.session_state.selected_store = None
    st.session_state.cart = []
    st.session_state.order_finished = False

if "orders_data" not in st.session_state:
    st.session_state.orders_data = load_orders_from_sheet()
if "target_order_date" not in st.session_state:
    st.session_state.target_order_date = date.today()
if "selected_user" not in st.session_state:
    st.session_state.selected_user = None
if "selected_store" not in st.session_state:
    st.session_state.selected_store = None
if "cart" not in st.session_state:
    st.session_state.cart = []
if "order_finished" not in st.session_state:
    st.session_state.order_finished = False

df_menu = load_menu()
df_users = load_users()

st.title("🍱 中餐簡易點餐系統")

tab1, tab2, tab3 = st.tabs(["🛒 快速點餐", "💵 現場收款", "🖨️ 店家出單"])

# -------------------------------------------------------------
# 簡易點餐頁面
# -------------------------------------------------------------
with tab1:
    chosen_date_str = str(st.session_state.target_order_date)

    if st.session_state.order_finished:
        st.success(f"🎉 訂單已送出成功！用餐日期：【{chosen_date_str}】")
        if st.button("👉 換下一位點餐", type="primary", use_container_width=True):
            reset_ordering()
            st.rerun()

    # 步驟 1：選用餐日期
    elif st.session_state.selected_user is None:
        st.markdown('<div class="simple-title">第 1 步：選用餐日期</div>', unsafe_allow_html=True)
        workweek_list = get_current_workweek_dates()
        d_cols = st.columns(5)
        for idx, w in enumerate(workweek_list):
            is_active = (st.session_state.target_order_date == w["date"])
            with d_cols[idx]:
                st.markdown(f'<div class="{"date-btn-active" if is_active else "date-btn"}">', unsafe_allow_html=True)
                if st.button(w["label"], key=f"date_btn_{idx}"):
                    st.session_state.target_order_date = w["date"]
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        st.write("---")
        st.markdown(f'<div class="simple-title">第 2 步：請問你是誰？（點名字）</div>', unsafe_allow_html=True)
        if not df_users.empty and "姓名" in df_users.columns:
            u_cols = st.columns(2)
            for idx, (_, u) in enumerate(df_users.iterrows()):
                u_name = str(u["姓名"]).strip()
                with u_cols[idx % 2]:
                    st.markdown('<div class="user-btn">', unsafe_allow_html=True)
                    if st.button(f"👤 {u_name}", key=f"user_{idx}"):
                        st.session_state.selected_user = u_name
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    # 步驟 2：選店家
    elif st.session_state.selected_store is None:
        u_name = st.session_state.selected_user
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"### 👤 目前同仁：**{u_name}** ｜ 📅 日期：**{chosen_date_str}**")
        with c2:
            if st.button("⬅️ 重選名字/日期"):
                reset_ordering()
                st.rerun()

        st.markdown('<div class="simple-title">第 3 步：想吃哪一家？（點店家）</div>', unsafe_allow_html=True)
        store_list = df_menu["店家名稱"].dropna().unique().tolist() if "店家名稱" in df_menu.columns else ["主要合作店家"]
        s_cols = st.columns(2)
        for idx, s_name in enumerate(store_list):
            with s_cols[idx % 2]:
                st.markdown('<div class="store-btn">', unsafe_allow_html=True)
                if st.button(f"🏪 {s_name}", key=f"store_{idx}"):
                    st.session_state.selected_store = s_name
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # 步驟 3：極簡菜單列表（點按鈕直接加入）
    else:
        u_name = st.session_state.selected_user
        store_name = st.session_state.selected_store

        # 頂部控制列
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"### 👤 **{u_name}** ｜ 🏪 **{store_name}** ｜ 📅 **{chosen_date_str}**")
        with c2:
            if st.button("⬅️ 換店家/重選"):
                st.session_state.selected_store = None
                st.session_state.cart = []
                st.rerun()

        # 購物車彙整與送出
        if st.session_state.cart:
            cart_total = sum(x["subtotal"] for x in st.session_state.cart)
            item_desc = "、".join([f"{x['item']} x{x['qty']}" for x in st.session_state.cart])
            st.markdown(f"""
            <div class="cart-summary">
                🛒 已選餐點：{item_desc}<br>
                💰 目前合計：<b>${fmt_price(cart_total)} 元</b>
            </div>
            """, unsafe_allow_html=True)
            
            sc1, sc2 = st.columns([2, 1])
            with sc1:
                if st.button("✅ 我選好了，送出訂單！", type="primary", use_container_width=True):
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
                            "麵類選擇": it.get("spec", "標準"),
                            "是否加麵": "不加麵",
                            "單價": f"${fmt_price(it['price'])}",
                            "數量": it["qty"],
                            "小計金額": f"${fmt_price(it['subtotal'])}",
                            "付款狀態": "未付款"
                        })
                    st.session_state.orders_data = pd.concat([st.session_state.orders_data, pd.DataFrame(new_rows)], ignore_index=True)
                    sync_to_google_sheet({"action": "append", "rows": new_rows})
                    st.session_state.order_finished = True
                    st.rerun()
            with sc2:
                if st.button("🗑️ 清空重選", use_container_width=True):
                    st.session_state.cart = []
                    st.rerun()

        st.write("---")
        st.markdown('<div class="simple-title">👉 點擊按鈕直接點餐：</div>', unsafe_allow_html=True)

        # 菜單過濾
        current_menu = df_menu[df_menu["店家名稱"] == store_name] if "店家名稱" in df_menu.columns else df_menu
        m_cols = st.columns(2)
        for idx, (_, item) in enumerate(current_menu.iterrows()):
            i_name = item.get("餐點名稱", "")
            i_price = parse_price(item.get("單價", 0))
            btn_text = f"🍲 {i_name}\n${fmt_price(i_price)} 元（點此直接加入）"

            with m_cols[idx % 2]:
                st.markdown('<div class="food-order-btn">', unsafe_allow_html=True)
                if st.button(btn_text, key=f"food_{idx}"):
                    st.session_state.cart.append({
                        "item": i_name,
                        "price": i_price,
                        "qty": 1,
                        "subtotal": i_price,
                        "spec": "標準"
                    })
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------
# 現場收款對帳分頁
# -------------------------------------------------------------
with tab2:
    st.subheader("💵 現場收款與找零")
    q_date = st.date_input("選擇收款日期", value=st.session_state.target_order_date, key="q_date_recon")
    if st.button("🔄 重新載入最新資料"):
        st.session_state.orders_data = load_orders_from_sheet()
        st.rerun()

    df_orders = st.session_state.orders_data
    day_orders = df_orders[df_orders["訂購日期"].astype(str).str.contains(str(q_date))].copy()

    if day_orders.empty:
        st.info("該日期無點餐紀錄。")
    else:
        day_orders["金額"] = day_orders["小計金額"].apply(parse_price)
        unpaid = day_orders[day_orders["付款狀態"] != "已付款"]
        
        if unpaid.empty:
            st.success("🎉 本日全部訂單已收款完畢！")
        else:
            u_list = unpaid["員工姓名"].unique().tolist()
            u_sel = st.selectbox("選擇繳費同仁", u_list)
            due = unpaid[unpaid["員工姓名"] == u_sel]["金額"].sum()
            st.markdown(f"### 應收金額：**${fmt_price(due)} 元**")
            
            if st.button(f"✅ 確認收齊 {u_sel} 款項", type="primary"):
                sync_to_google_sheet({"action": "update_status", "user": u_sel, "status": "已付款"})
                st.session_state.orders_data.loc[st.session_state.orders_data["員工姓名"] == u_sel, "付款狀態"] = "已付款"
                st.success("收款完成！")
                st.rerun()

        st.write("---")
        st.dataframe(day_orders[["訂單編號", "員工姓名", "餐點品項", "數量", "小計金額", "付款狀態"]], use_container_width=True)

# -------------------------------------------------------------
# 店家出單彙整分頁
# -------------------------------------------------------------
with tab3:
    st.subheader("🖨️ 店家出單與發放明細")
    out_date = st.date_input("選擇出單日期", value=st.session_state.target_order_date, key="q_date_out")
    day_orders = st.session_state.orders_data[st.session_state.orders_data["訂購日期"].astype(str).str.contains(str(out_date))].copy()

    if day_orders.empty:
        st.info("該日期無訂單。")
    else:
        day_orders["數量數值"] = day_orders["數量"].apply(lambda x: int(parse_price(x)) if parse_price(x) > 0 else 1)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 📞 1. 店家總餐點清單（報單用）：")
            summary = day_orders.groupby("餐點品項")["數量數值"].sum().reset_index()
            summary.columns = ["餐點品項", "總數量 (份)"]
            st.dataframe(summary, use_container_width=True, hide_index=True)

        with c2:
            st.markdown("#### 👥 2. 個人發餐名單：")
            person = day_orders.groupby("員工姓名")["餐點品項"].apply(lambda x: "、".join(x)).reset_index()
            person.columns = ["姓名", "餐點明細"]
            st.dataframe(person, use_container_width=True, hide_index=True)
