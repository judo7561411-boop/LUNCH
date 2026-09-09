import streamlit as st
import pandas as pd
import requests
import json
import time
from datetime import date

st.set_page_config(page_title="中餐點餐系統", page_icon="🍱", layout="wide")

APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbw0UEIp80umbupbDQkMQAa5-3Z4HQp01r9VH_Zr-0nYnPzXv6jgY_gKYFyScn7e2Lrj/exec"
SHEET_ID = "1mHnXoG-Duq45EvwZTRVuq86rsK8T5DA9NkLnOi30wuM"

st.markdown("""
<style>
    html, body, [class*="css"] { font-size: 20px; }
    .user-btn button {
        width: 100% !important; min-height: 80px !important;
        font-size: 24px !important; font-weight: bold !important;
        border-radius: 14px !important; margin-bottom: 12px !important;
        border: 2px solid #CBD5E1 !important;
    }
    .user-btn button:hover { border-color: #2563EB !important; background-color: #EFF6FF !important; }
    .food-card {
        background-color: #FFFFFF; border: 2px solid #E2E8F0;
        border-radius: 16px; padding: 16px; margin-bottom: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .cart-item {
        background-color: #F8FAFC; border-left: 6px solid #2563EB;
        padding: 12px 18px; border-radius: 8px; margin-bottom: 10px; font-size: 20px;
    }
    .budget-banner {
        background-color: #EFF6FF; border: 2px solid #3B82F6;
        border-radius: 14px; padding: 16px 20px; font-size: 24px;
        font-weight: bold; color: #1E3A8A; margin-bottom: 20px;
    }
    .big-pay-box {
        background-color: #DEF7EC;
        border: 3px solid #31C48D;
        border-radius: 18px;
        padding: 26px;
        font-size: 32px;
        font-weight: bold;
        color: #03543F;
        text-align: center;
        margin-top: 15px;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .big-next-btn button {
        width: 100% !important;
        min-height: 90px !important;
        font-size: 32px !important;
        font-weight: bold !important;
        border-radius: 18px !important;
        background-color: #EF4444 !important;
        color: white !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }
    .big-next-btn button:hover {
        background-color: #DC2626 !important;
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

SVG_100 = """<svg width="180" height="90" viewBox="0 0 180 90" xmlns="http://www.w3.org/2000/svg" style="border-radius:6px; box-shadow:2px 3px 6px rgba(0,0,0,0.3); margin:4px;"><rect width="180" height="90" rx="6" fill="#C53030"/><rect x="4" y="4" width="172" height="82" rx="4" fill="none" stroke="#FED7D7" stroke-width="1.5" stroke-dasharray="4,2"/><circle cx="45" cy="45" r="22" fill="#9B2C2C"/><circle cx="45" cy="45" r="18" fill="none" stroke="#FEB2B2" stroke-width="1"/><text x="45" y="52" font-family="sans-serif" font-size="20" font-weight="bold" fill="#FED7D7" text-anchor="middle">100</text><text x="135" y="55" font-family="sans-serif" font-size="44" font-weight="900" fill="#FFFFFF" text-anchor="middle">100</text><text x="90" y="22" font-family="sans-serif" font-size="12" font-weight="bold" fill="#FED7D7" text-anchor="middle">中華民國中央銀行</text><text x="135" y="75" font-family="sans-serif" font-size="14" font-weight="bold" fill="#FEEBC8" text-anchor="middle">壹佰圓</text></svg>"""
SVG_50 = """<svg width="84" height="84" viewBox="0 0 84 84" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(2px 3px 4px rgba(0,0,0,0.35)); margin:4px;"><circle cx="42" cy="42" r="40" fill="#D69E2E" stroke="#744210" stroke-width="2"/><circle cx="42" cy="42" r="34" fill="#ECC94B" stroke="#B7791F" stroke-width="1.5"/><circle cx="42" cy="42" r="26" fill="#D69E2E"/><text x="42" y="49" font-family="sans-serif" font-size="28" font-weight="900" fill="#5A3207" text-anchor="middle">50</text><text x="42" y="61" font-family="sans-serif" font-size="11" font-weight="bold" fill="#744210" text-anchor="middle">圓</text></svg>"""
SVG_10 = """<svg width="76" height="76" viewBox="0 0 76 76" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(2px 3px 4px rgba(0,0,0,0.3)); margin:4px;"><circle cx="38" cy="38" r="36" fill="#A0AEC0" stroke="#4A5568" stroke-width="2"/><circle cx="38" cy="38" r="30" fill="#E2E8F0" stroke="#718096" stroke-width="1.5"/><text x="38" y="44" font-family="sans-serif" font-size="26" font-weight="900" fill="#2D3748" text-anchor="middle">10</text><text x="38" y="56" font-family="sans-serif" font-size="11" font-weight="bold" fill="#4A5568" text-anchor="middle">圓</text></svg>"""
SVG_5 = """<svg width="66" height="66" viewBox="0 0 66 66" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(2px 3px 4px rgba(0,0,0,0.3)); margin:4px;"><circle cx="33" cy="33" r="31" fill="#CBD5E0" stroke="#718096" stroke-width="2"/><circle cx="33" cy="33" r="25" fill="#EDF2F7" stroke="#A0AEC0" stroke-width="1"/><text x="33" y="39" font-family="sans-serif" font-size="22" font-weight="900" fill="#2D3748" text-anchor="middle">5</text><text x="33" y="49" font-family="sans-serif" font-size="10" font-weight="bold" fill="#4A5568" text-anchor="middle">圓</text></svg>"""
SVG_1 = """<svg width="58" height="58" viewBox="0 0 58 58" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(2px 3px 4px rgba(0,0,0,0.3)); margin:4px;"><circle cx="29" cy="29" r="27" fill="#DD6B20" stroke="#7B341E" stroke-width="2"/><circle cx="29" cy="29" r="21" fill="#ED8936" stroke="#9C4221" stroke-width="1"/><text x="29" y="35" font-family="sans-serif" font-size="20" font-weight="900" fill="#431407" text-anchor="middle">1</text><text x="29" y="45" font-family="sans-serif" font-size="10" font-weight="bold" fill="#652B19" text-anchor="middle">圓</text></svg>"""

REQUIRED_ORDER_COLS = [
    "訂單編號", "訂購日期", "員工編號", "員工姓名", "所屬部門", 
    "餐點品項", "麵類選擇", "是否加麵", "單價", "數量", "小計金額", "付款狀態"
]

def load_menu():
    try:
        t = int(time.time())
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=menu&_t={t}"
        df = pd.read_csv(url)
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
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=orders&_t={t}"
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

        for req in REQUIRED_ORDER_COLS:
            if req not in df.columns:
                df[req] = ""

        if "員工姓名" in df.columns:
            df = df.dropna(subset=["員工姓名"])
            df = df[~df["員工姓名"].astype(str).str.contains("總計|合計", na=False)]
            df = df[df["員工姓名"].astype(str).str.strip() != ""]
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

if "orders_data" not in st.session_state:
    st.session_state.orders_data = load_orders_from_sheet()
if "selected_user" not in st.session_state:
    st.session_state.selected_user = None
if "user_limit" not in st.session_state:
    st.session_state.user_limit = 0
if "cart" not in st.session_state:
    st.session_state.cart = []
if "order_finished" not in st.session_state:
    st.session_state.order_finished = False
if "last_paid_amount" not in st.session_state:
    st.session_state.last_paid_amount = 0

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
# 分頁 1：友善大圖點餐
# -------------------------------------------------------------
with tab1:
    today_str = str(date.today())
    
    # 點餐完成畫面：明確提示應付款金額，僅保留「換下一位點餐」
    if st.session_state.order_finished:
        pay_amount = st.session_state.last_paid_amount
        st.markdown(f"""
        <div class="big-pay-box">
            🎉 已完成訂單！<br>
            請準備 <span style="color: #DC2626; font-size: 42px; font-weight: 900;">${pay_amount}</span> 元付款
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="big-next-btn">', unsafe_allow_html=True)
        if st.button("👉 換下一位點餐", key="btn_next_user"):
            st.session_state.selected_user = None
            st.session_state.user_limit = 0
            st.session_state.cart = []
            st.session_state.last_paid_amount = 0
            st.session_state.order_finished = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.selected_user is None:
        st.subheader("👉 第一步：請問你是誰？（點你的名字）")
        if df_users.empty or "姓名" not in df_users.columns:
            st.warning("⚠️ 尚無人員名單，請至【👥 人員名單管理】確認。")
        else:
            cols = st.columns(2)
            for idx, (_, u_row) in enumerate(df_users.iterrows()):
                u_name = str(u_row["姓名"]).strip()
                raw_lim = u_row.get("金額限制", 0)
                try:
                    lim_val = int(float(str(raw_lim).replace("$", "").replace(",", "").strip())) if pd.notnull(raw_lim) else 0
                except:
                    lim_val = 0

                lim_badge = f"（限額 ${lim_val} 元）" if lim_val > 0 else "（不限額）"

                with cols[idx % 2]:
                    st.markdown('<div class="user-btn">', unsafe_allow_html=True)
                    if st.button(f"👤 {u_name} {lim_badge}", key=f"sel_u_{u_name}_{idx}"):
                        st.session_state.selected_user = u_name
                        st.session_state.user_limit = lim_val
                        st.session_state.cart = []
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    else:
        u_name = st.session_state.selected_user
        u_limit = st.session_state.user_limit
        cart_sum = sum(x["subtotal"] for x in st.session_state.cart)
        remain = (u_limit - cart_sum) if u_limit > 0 else 999999

        limit_txt = f"個人上限額度：<b>${u_limit} 元</b> ｜ 剩餘可用：<b style='color:#DC2626;'>${remain} 元</b>" if u_limit > 0 else "個人上限額度：<b>無限制</b>"
        st.markdown(f'<div class="budget-banner">👤 目前同仁：{u_name} ｜ {limit_txt}</div>', unsafe_allow_html=True)

        with st.container():
            col_t1, col_t2 = st.columns([3, 1])
            with col_t1:
                st.markdown(f"### 🛒 已選餐點清單（共 {len(st.session_state.cart)} 樣，合計 **${cart_sum}** 元）")
            with col_t2:
                if st.button("⬅️ 重選同仁 (清空)"):
                    st.session_state.selected_user = None
                    st.session_state.cart = []
                    st.rerun()

            if st.session_state.cart:
                for c_idx, c_item in enumerate(st.session_state.cart):
                    cc1, cc2 = st.columns([4, 1])
                    with cc1:
                        st.markdown(f"""
                        <div class="cart-item">
                            🍲 <b>{c_item['item']}</b> ｜ 麵體：<b>{c_item['noodle']}</b> ｜ 份量：<b>{c_item['extra']}</b> ｜ 金額：<b style="color:#DC2626;">${c_item['subtotal']} 元</b>
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
                            "單價": f"${it['price']}",
                            "數量": 1,
                            "小計金額": f"${it['subtotal']}",
                            "付款狀態": "未付款"
                        })

                    # 紀錄應付總額供完成畫面呈現
                    st.session_state.last_paid_amount = cart_sum

                    # 本地同步一份
                    new_df = pd.DataFrame(new_rows)
                    st.session_state.orders_data = pd.concat([st.session_state.orders_data, new_df], ignore_index=True)

                    # 寫入試算表
                    with st.spinner("同步儲存至 Google 試算表..."):
                        sync_to_google_sheet({
                            "action": "append",
                            "rows": new_rows
                        })

                    st.session_state.order_finished = True
                    st.rerun()

        st.write("---")
        st.subheader("👇 請挑選餐點：")

        available_menu = df_menu[df_menu["供應狀態"] == "供應中"] if "供應狀態" in df_menu.columns else df_menu
        displayed_items = []
        for _, row in available_menu.iterrows():
            raw_p = row.get("單價", 0)
            try:
                base_p = int(str(raw_p).replace("$", "").replace(",", "").strip())
            except:
                base_p = 0
            if u_limit > 0 and base_p > u_limit:
                continue
            displayed_items.append((row, base_p))

        if not displayed_items:
            st.warning("⚠️ 沒有符合你金額限制內的餐點項目。")
        else:
            cols = st.columns(2)
            for idx, (m_row, base_p) in enumerate(displayed_items):
                item_name = m_row["餐點名稱"]
                with cols[idx % 2]:
                    with st.container():
                        st.markdown(f"""
                        <div class="food-card">
                            <h3 style="margin-top:0; color:#1E293B;">🍲 {item_name}</h3>
                            <div style="font-size:20px; color:#475569; margin-bottom:8px;">基本價格：<b style="color:#059669;">${base_p} 元</b></div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        c_nd, c_ex = st.columns(2)
                        with c_nd:
                            nd_choice = st.selectbox("麵體", ["意麵", "冬粉", "泡飯", "雞絲麵", "王子麵", "烏龍麵 (+10元)"], key=f"nd_{idx}")
                        with c_ex:
                            ex_choice = st.radio("份量", ["不加麵", "要加麵 (+15元)"], horizontal=True, key=f"ex_{idx}")

                        extra_nd = 10 if "烏龍麵" in nd_choice else 0
                        extra_ex = 15 if ex_choice == "要加麵 (+15元)" else 0
                        final_price = base_p + extra_nd + extra_ex

                        can_add = (u_limit == 0) or (final_price <= remain)
                        btn_txt = f"➕ 加入點餐清單 (${final_price} 元)" if can_add else f"❌ 超出剩餘額度 (${final_price} 元)"

                        if st.button(btn_txt, key=f"add_btn_{idx}", disabled=not can_add):
                            st.session_state.cart.append({
                                "item": item_name,
                                "price": base_p,
                                "noodle": nd_choice,
                                "extra": ex_choice,
                                "subtotal": final_price
                            })
                            st.rerun()

# -------------------------------------------------------------
# 分頁 2：明細與對帳
# -------------------------------------------------------------
with tab2:
    st.subheader("📊 每日點餐明細與收款找零對帳")

    c_q1, c_q2, c_q3 = st.columns([2, 1, 1])
    with c_q1:
        query_date = st.date_input("選擇欲對帳或查詢的日期", value=date.today())
    with c_q2:
        filter_mode = st.radio("檢視模式", ["📅 依所選日期", "📋 顯示全部訂單"], horizontal=True)
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
            st.warning(f"⚠️ 在【{query_date}】查無點單紀錄。（可切換為「📋 顯示全部訂單」查看）")
        else:
            def parse_money(v):
                try:
                    return int(str(v).replace("$", "").replace(",", "").strip())
                except:
                    return 0

            current_orders["金額數值"] = current_orders["小計金額"].apply(parse_money)
            total_money = current_orders["金額數值"].sum()
            total_items = len(current_orders)

            paid_orders = current_orders[current_orders["付款狀態"] == "已付款"]
            paid_money = paid_orders["金額數值"].sum()
            unpaid_money = total_money - paid_money
            unpaid_count = total_items - len(paid_orders)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("當前檢視總額", f"${total_money:,} 元")
            m2.metric("總訂單數", f"{total_items} 筆")
            m3.metric("已收款總額", f"${paid_money:,} 元", f"{len(paid_orders)} 筆已收")
            m4.metric("待收餘額 (未收)", f"${unpaid_money:,} 元", f"{unpaid_count} 筆待收", delta_color="inverse")

            st.write("---")

            # 現場找零輔助器
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
                        target_due = user_unpaid_items["金額數值"].sum()
                        
                        st.markdown(f"""
                        <div style="background-color: #FEF2F2; border: 2px solid #F87171; border-radius: 12px; padding: 14px; margin-top: 10px;">
                            👤 收款對象：<b>{target_user}</b><br>
                            💰 應收金額：<b style="color: #DC2626; font-size: 32px;">${target_due}</b> 元
                        </div>
                        """, unsafe_allow_html=True)

                    with calc_col2:
                        st.write("點選同仁拿出的鈔票：")
                        q_col1, q_col2, q_col3 = st.columns(3)
                        with q_col1:
                            if st.button("剛好", key="pay_exact"):
                                st.session_state.received_cash = target_due
                        with q_col2:
                            if st.button("💵 拿 100", key="pay_100"):
                                st.session_state.received_cash = 100
                        with q_col3:
                            if st.button("💵 拿 500", key="pay_500"):
                                st.session_state.received_cash = 500

                        default_val = st.session_state.get("received_cash", target_due)
                        paid_input = st.number_input("或自訂實收金額 (元)", min_value=0, value=int(default_val), step=10)

                        change = paid_input - target_due
                        if change >= 0:
                            st.markdown(f"""
                            <div style="background-color: #ECFDF5; border: 2px solid #34D399; border-radius: 12px; padding: 14px; margin-top: 10px;">
                                🪙 應找零錢：<b style="color: #059669; font-size: 34px;">${change}</b> 元
                            </div>
                            """, unsafe_allow_html=True)

                            rem_c = change
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
                                    board_html += f"<div class='money-group-row'>{''.join([SVG_100 if False else SVG_10 for _ in range(c10)])}</div>"
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
                            st.error(f"⚠️ 還不夠喔！同仁還差 ${abs(change)} 元")

            st.write("---")
            st.markdown("#### 📋 點單明細清單與收款切換：")
            for row_idx, row_data in current_orders.iterrows():
                row_c1, row_c2, row_c3, row_c4 = st.columns([2, 3, 2, 2])
                with row_c1:
                    st.write(f"**{row_data.get('員工姓名', '')}** ({row_data.get('所屬部門', '-')})")
                with row_c2:
                    st.write(f"{row_data.get('餐點品項', '')} ｜ {row_data.get('麵類選擇', '')} ｜ {row_data.get('是否加麵', '')}")
                with row_c3:
                    st.write(f"金額：<b style='color:#DC2626;'>{row_data.get('小計金額', '')}</b>", unsafe_allow_html=True)
                with row_c4:
                    cur_status = row_data.get("付款狀態", "未付款")
                    if cur_status == "已付款":
                        if st.button("🟢 已付款 (改未付)", key=f"status_btn_{row_idx}"):
                            st.session_state.orders_data.loc[row_idx, "付款狀態"] = "未付款"
                            sync_to_google_sheet({
                                "action": "update_status",
                                "date": str(row_data.get("訂購日期", "")),
                                "user": row_data.get("員工姓名", ""),
                                "status": "未付款"
                            })
                            st.rerun()
                    else:
                        if st.button("🔴 未付款 (改已付)", key=f"status_btn_{row_idx}"):
                            st.session_state.orders_data.loc[row_idx, "付款狀態"] = "已付款"
                            sync_to_google_sheet({
                                "action": "update_status",
                                "date": str(row_data.get("訂購日期", "")),
                                "user": row_data.get("員工姓名", ""),
                                "status": "已付款"
                            })
                            st.rerun()

# -------------------------------------------------------------
# 分頁 3：菜單管理
# -------------------------------------------------------------
with tab3:
    st.subheader("⚙️ 菜單品項維護")
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
