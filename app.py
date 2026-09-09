import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="中餐點餐系統", page_icon="🍱", layout="wide")

# CSS 注入：高擬真台灣貨幣圖卡與大數字
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-size: 20px;
    }
    .user-btn button {
        width: 100% !important;
        min-height: 80px !important;
        font-size: 24px !important;
        font-weight: bold !important;
        border-radius: 14px !important;
        margin-bottom: 12px !important;
        border: 2px solid #CBD5E1 !important;
    }
    .user-btn button:hover {
        border-color: #2563EB !important;
        background-color: #EFF6FF !important;
    }
    .food-card {
        background-color: #FFFFFF;
        border: 2px solid #E2E8F0;
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .cart-item {
        background-color: #F8FAFC;
        border-left: 6px solid #2563EB;
        padding: 12px 18px;
        border-radius: 8px;
        margin-bottom: 10px;
        font-size: 20px;
    }
    .budget-banner {
        background-color: #EFF6FF;
        border: 2px solid #3B82F6;
        border-radius: 14px;
        padding: 16px 20px;
        font-size: 24px;
        font-weight: bold;
        color: #1E3A8A;
        margin-bottom: 20px;
    }
    .big-success {
        background-color: #DEF7EC;
        border: 3px solid #31C48D;
        border-radius: 16px;
        padding: 24px;
        font-size: 30px;
        font-weight: bold;
        color: #03543F;
        text-align: center;
        margin-top: 20px;
    }

    /* 貨幣容器 */
    .money-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin: 10px 14px;
    }
    .money-count {
        font-size: 24px;
        font-weight: 900;
        color: #1E293B;
        margin-top: 6px;
    }

    /* 100元 紙鈔 */
    .tw-bill-100 {
        background: linear-gradient(135deg, #DC2626 0%, #991B1B 100%);
        color: #FEF08A;
        border: 3px solid #7F1D1D;
        border-radius: 10px;
        width: 170px;
        height: 85px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        padding: 6px 10px;
        box-shadow: 3px 3px 8px rgba(0,0,0,0.3);
        font-family: sans-serif;
    }
    .tw-bill-100 .top-row {
        display: flex;
        justify-content: space-between;
        font-size: 14px;
        font-weight: bold;
    }
    .tw-bill-100 .center-val {
        font-size: 34px;
        font-weight: 900;
        text-align: center;
        color: #FFFFFF;
        text-shadow: 1px 1px 2px #000;
        letter-spacing: 2px;
    }
    .tw-bill-100 .bot-row {
        font-size: 12px;
        text-align: right;
        color: #FCA5A5;
    }

    /* 50元 硬幣 (金色) */
    .tw-coin-50 {
        background: radial-gradient(circle at 35% 35%, #FDE047 0%, #CA8A04 70%, #854D0E 100%);
        color: #451A03;
        border: 4px solid #A16207;
        border-radius: 50%;
        width: 82px;
        height: 82px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        box-shadow: inset 0 0 0 3px #FACC15, 3px 3px 6px rgba(0,0,0,0.35);
        text-shadow: 0 1px 1px rgba(255,255,255,0.7);
    }
    .tw-coin-50 .coin-num {
        font-size: 32px;
        font-weight: 900;
        line-height: 1;
    }
    .tw-coin-50 .coin-unit {
        font-size: 13px;
        font-weight: bold;
    }

    /* 10元 硬幣 (銀色中圓) */
    .tw-coin-10 {
        background: radial-gradient(circle at 35% 35%, #F8FAFC 0%, #94A3B8 70%, #475569 100%);
        color: #0F172A;
        border: 3px solid #64748B;
        border-radius: 50%;
        width: 72px;
        height: 72px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        box-shadow: inset 0 0 0 2px #E2E8F0, 3px 3px 5px rgba(0,0,0,0.3);
    }
    .tw-coin-10 .coin-num {
        font-size: 28px;
        font-weight: 900;
        line-height: 1;
    }
    .tw-coin-10 .coin-unit {
        font-size: 12px;
        font-weight: bold;
    }

    /* 5元 硬幣 (銀色小圓) */
    .tw-coin-5 {
        background: radial-gradient(circle at 35% 35%, #F8FAFC 0%, #94A3B8 70%, #475569 100%);
        color: #0F172A;
        border: 3px solid #64748B;
        border-radius: 50%;
        width: 62px;
        height: 62px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        box-shadow: inset 0 0 0 2px #E2E8F0, 2px 2px 4px rgba(0,0,0,0.3);
    }
    .tw-coin-5 .coin-num {
        font-size: 24px;
        font-weight: 900;
        line-height: 1;
    }
    .tw-coin-5 .coin-unit {
        font-size: 11px;
        font-weight: bold;
    }

    /* 1元 硬幣 (銅色小圓) */
    .tw-coin-1 {
        background: radial-gradient(circle at 35% 35%, #FDBA74 0%, #C2410C 70%, #7C2D12 100%);
        color: #431407;
        border: 3px solid #9A3412;
        border-radius: 50%;
        width: 54px;
        height: 54px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        box-shadow: inset 0 0 0 2px #FED7AA, 2px 2px 4px rgba(0,0,0,0.3);
        text-shadow: 0 1px 0 rgba(255,255,255,0.4);
    }
    .tw-coin-1 .coin-num {
        font-size: 22px;
        font-weight: 900;
        line-height: 1;
    }
    .tw-coin-1 .coin-unit {
        font-size: 10px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

SHEET_ID = "1mHnXoG-Duq45EvwZTRVuq86rsK8T5DA9NkLnOi30wuM"

def load_menu():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=menu"
        df = pd.read_csv(url)
        return df.dropna(subset=["餐點名稱"]) if "餐點名稱" in df.columns else df
    except:
        return pd.DataFrame()

def load_users():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=users"
        df = pd.read_csv(url)
        return df.dropna(subset=["姓名"]) if "姓名" in df.columns else df
    except:
        return pd.DataFrame()

def load_orders():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=orders"
        raw_df = pd.read_csv(url, header=None)
        h_idx = 3
        for i in range(min(10, len(raw_df))):
            if any("訂單編號" in str(v) for v in raw_df.iloc[i].astype(str)):
                h_idx = i
                break
        df = pd.read_csv(url, header=h_idx)
        if "訂單編號" in df.columns:
            df = df.dropna(subset=["訂單編號"])
            df = df[df["訂單編號"].astype(str).str.startswith("ORD")]
        return df
    except:
        return pd.DataFrame()

if "df_menu" not in st.session_state:
    st.session_state.df_menu = load_menu()
if "df_users" not in st.session_state:
    st.session_state.df_users = load_users()
if "df_orders" not in st.session_state:
    st.session_state.df_orders = load_orders()

if "selected_user" not in st.session_state:
    st.session_state.selected_user = None
if "user_limit" not in st.session_state:
    st.session_state.user_limit = 0
if "cart" not in st.session_state:
    st.session_state.cart = []
if "order_finished" not in st.session_state:
    st.session_state.order_finished = False

st.title("🍱 中餐點餐與管理系統")

tab1, tab2, tab3, tab4 = st.tabs([
    "🛒 友善大圖點餐", 
    "📊 明細與對帳", 
    "⚙️ 菜單管理與編輯", 
    "👥 人員名單管理"
])

# -------------------------------------------------------------
# 分頁 1：友善點餐
# -------------------------------------------------------------
with tab1:
    if st.session_state.order_finished:
        st.markdown('<div class="big-success">🎉 點餐完成！資料已成功送出！</div>', unsafe_allow_html=True)
        st.write("")
        if st.button("👉 幫下一位同仁點餐", type="primary"):
            st.session_state.selected_user = None
            st.session_state.user_limit = 0
            st.session_state.cart = []
            st.session_state.order_finished = False
            st.rerun()

    elif st.session_state.selected_user is None:
        st.subheader("👉 第一步：請問你是誰？（點你的名字）")
        df_u = st.session_state.df_users
        
        if df_u.empty or "姓名" not in df_u.columns:
            st.warning("⚠️ 尚無人員名單，請至【👥 人員名單管理】確認。")
        else:
            cols = st.columns(2)
            for idx, (_, u_row) in enumerate(df_u.iterrows()):
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
                    df_u = st.session_state.df_users
                    if not df_u.empty and "姓名" in df_u.columns:
                        match_u = df_u[df_u["姓名"] == u_name]
                        if not match_u.empty and "組別" in match_u.columns:
                            user_dept = match_u["組別"].values[0]

                    new_rows = []
                    for it in st.session_state.cart:
                        new_rows.append({
                            "訂單編號": f"ORD-{len(st.session_state.df_orders) + len(new_rows) + 1:03d}",
                            "訂購日期": str(date.today()),
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

                    st.session_state.df_orders = pd.concat([st.session_state.df_orders, pd.DataFrame(new_rows)], ignore_index=True)
                    st.session_state.order_finished = True
                    st.rerun()

        st.write("---")
        st.subheader("👇 請挑選餐點：")

        menu_df = st.session_state.df_menu
        available_menu = menu_df[menu_df["供應狀態"] == "供應中"] if "供應狀態" in menu_df.columns else menu_df

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
# 分頁 2：明細與對帳（擬真台灣貨幣圖卡找零）
# -------------------------------------------------------------
with tab2:
    st.subheader("📊 每日點餐明細與收款找零對帳")

    col_q1, col_q2 = st.columns([2, 1])
    with col_q1:
        query_date = st.date_input("選擇欲對帳或查詢的日期", value=date.today())
    with col_q2:
        st.write("")
        st.write("")
        if st.button("🔄 重新載入最新資料"):
            st.session_state.df_orders = load_orders()
            st.session_state.df_menu = load_menu()
            st.session_state.df_users = load_users()
            st.rerun()

    df_orders = st.session_state.df_orders

    if df_orders.empty or "訂購日期" not in df_orders.columns:
        st.info("尚無任何訂單紀錄。")
    else:
        date_mask = df_orders["訂購日期"].astype(str) == str(query_date)
        current_orders = df_orders[date_mask].copy()

        if current_orders.empty:
            st.info(f"【{query_date}】當日尚無任何點單紀錄。")
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
            m1.metric("當日訂單總額", f"${total_money:,} 元")
            m2.metric("總訂單數", f"{total_items} 筆")
            m3.metric("已收款總額", f"${paid_money:,} 元", f"{len(paid_orders)} 筆已收")
            m4.metric("待收餘額 (未收)", f"${unpaid_money:,} 元", f"{unpaid_count} 筆待收", delta_color="inverse")

            st.write("---")

            # ---------------------------------------------------------
            # 台灣實體貨幣找零輔助器
            # ---------------------------------------------------------
            with st.expander("💵 現場收款與【台灣鈔票/硬幣】找零輔助器（點擊展開）", expanded=True):
                unpaid_list = current_orders[current_orders["付款狀態"] != "已付款"]
                
                if unpaid_list.empty:
                    st.success("🎉 今日所有訂單皆已全數收款完畢！")
                else:
                    user_options = unpaid_list["員工姓名"].unique().tolist()
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
                                🪙 應找零錢總計：<b style="color: #059669; font-size: 34px;">${change}</b> 元
                            </div>
                            """, unsafe_allow_html=True)

                            # 拆解貨幣面額 (100, 50, 10, 5, 1)
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
                                st.write("#### 👉 請拿給同仁這些鈔票與硬幣：")
                                visual_html = "<div style='display: flex; flex-wrap: wrap; align-items: flex-start; margin-top: 10px;'>"
                                
                                if c100 > 0:
                                    visual_html += f"""
                                    <div class='money-container'>
                                        <div class='tw-bill-100'>
                                            <div class='top-row'><span>100</span><span>中央印製廠</span></div>
                                            <div class='center-val'>100</div>
                                            <div class='bot-row'>壹佰圓</div>
                                        </div>
                                        <div class='money-count'>× {c100} 張</div>
                                    </div>
                                    """
                                if c50 > 0:
                                    visual_html += f"""
                                    <div class='money-container'>
                                        <div class='tw-coin-50'>
                                            <div class='coin-num'>50</div>
                                            <div class='coin-unit'>圓</div>
                                        </div>
                                        <div class='money-count'>× {c50} 枚</div>
                                    </div>
                                    """
                                if c10 > 0:
                                    visual_html += f"""
                                    <div class='money-container'>
                                        <div class='tw-coin-10'>
                                            <div class='coin-num'>10</div>
                                            <div class='coin-unit'>圓</div>
                                        </div>
                                        <div class='money-count'>× {c10} 枚</div>
                                    </div>
                                    """
                                if c5 > 0:
                                    visual_html += f"""
                                    <div class='money-container'>
                                        <div class='tw-coin-5'>
                                            <div class='coin-num'>5</div>
                                            <div class='coin-unit'>圓</div>
                                        </div>
                                        <div class='money-count'>× {c5} 枚</div>
                                    </div>
                                    """
                                if c1 > 0:
                                    visual_html += f"""
                                    <div class='money-container'>
                                        <div class='tw-coin-1'>
                                            <div class='coin-num'>1</div>
                                            <div class='coin-unit'>圓</div>
                                        </div>
                                        <div class='money-count'>× {c1} 枚</div>
                                    </div>
                                    """
                                visual_html += "</div>"
                                st.markdown(visual_html, unsafe_allow_html=True)
                            else:
                                st.info("👌 剛好收齊，不需要找零！")

                            st.write("")
                            if st.button(f"✅ 確認收款完畢（將 {target_user} 設為已付款）", type="primary", use_container_width=True):
                                target_indices = user_unpaid_items.index
                                st.session_state.df_orders.loc[target_indices, "付款狀態"] = "已付款"
                                st.success(f"已完成 {target_user} 收款！")
                                st.rerun()
                        else:
                            st.error(f"⚠️ 還不夠喔！同仁還差 ${abs(change)} 元")

            st.write("---")

            # ---------------------------------------------------------
            # 點單明細清單與一鍵切換狀態
            # ---------------------------------------------------------
            st.markdown("#### 📋 點單明細清單與收款切換：")
            st.caption("💡 提示：點擊右側按鈕可快速切換【已付款】或【未付款】狀態。")

            for row_idx, row_data in current_orders.iterrows():
                row_c1, row_c2, row_c3, row_c4 = st.columns([2, 3, 2, 2])
                with row_c1:
                    st.write(f"**{row_data['員工姓名']}** ({row_data.get('所屬部門', '-')})")
                with row_c2:
                    st.write(f"{row_data['餐點品項']} ｜ {row_data['麵類選擇']} ｜ {row_data['是否加麵']}")
                with row_c3:
                    st.write(f"金額：<b style='color:#DC2626;'>{row_data['小計金額']}</b>", unsafe_allow_html=True)
                with row_c4:
                    cur_status = row_data.get("付款狀態", "未付款")
                    if cur_status == "已付款":
                        if st.button("🟢 已付款 (改未付)", key=f"status_btn_{row_idx}"):
                            st.session_state.df_orders.loc[row_idx, "付款狀態"] = "未付款"
                            st.rerun()
                    else:
                        if st.button("🔴 未付款 (改已付)", key=f"status_btn_{row_idx}"):
                            st.session_state.df_orders.loc[row_idx, "付款狀態"] = "已付款"
                            st.rerun()

            st.write("---")
            st.markdown("#### ✏️ 完整表格檢視與批次編輯：")
            column_config = {
                "付款狀態": st.column_config.SelectboxColumn("付款狀態", options=["已付款", "未付款"], required=True)
            }
            display_cols = [c for c in current_orders.columns if c != "金額數值"]
            edited_today = st.data_editor(
                current_orders[display_cols],
                column_config=column_config,
                use_container_width=True,
                num_rows="dynamic",
                key="orders_editor"
            )

            if st.button("💾 儲存明細修改", type="primary"):
                other_orders = df_orders[~date_mask]
                st.session_state.df_orders = pd.concat([other_orders, edited_today], ignore_index=True)
                st.success("✅ 訂單與收款狀態已成功更新！")
                st.rerun()

# -------------------------------------------------------------
# 分頁 3：菜單管理
# -------------------------------------------------------------
with tab3:
    st.subheader("⚙️ 菜單品項維護")
    with st.expander("➕ 新增菜單餐點品項", expanded=False):
        with st.form("add_menu_form"):
            new_store = st.text_input("店家名稱", value="劉妹鍋燒意麵 (鹿港萬壽店)")
            new_category = st.text_input("分類", value="鍋燒系列")
            new_item_name = st.text_input("餐點名稱")
            new_noodles = st.text_input("麵類選擇", value="意麵 / 冬粉 / 泡飯 / 雞絲麵 / 王子麵 / 烏龍麵 (+10元)")
            new_price = st.number_input("單價", min_value=0, value=80, step=5)
            new_status = st.selectbox("供應狀態", options=["供應中", "已售完"])
            new_note = st.text_input("備註")
            if st.form_submit_button("確認新增品項"):
                if new_item_name:
                    new_entry = pd.DataFrame([{"店家名稱": new_store, "分類": new_category, "餐點名稱": new_item_name, "麵類選擇": new_noodles, "單價": f"${new_price}", "供應狀態": new_status, "備註": new_note}])
                    st.session_state.df_menu = pd.concat([st.session_state.df_menu, new_entry], ignore_index=True)
                    st.success(f"已新增品項：{new_item_name}！")
                    st.rerun()

    st.write("#### 菜單清單（可直接修改）：")
    edited_menu = st.data_editor(st.session_state.df_menu, use_container_width=True, num_rows="dynamic", key="menu_editor")
    if st.button("💾 儲存菜單修改內容"):
        st.session_state.df_menu = edited_menu
        st.success("菜單修改已更新至系統！")

# -------------------------------------------------------------
# 分頁 4：人員名單與金額限制管理
# -------------------------------------------------------------
with tab4:
    st.subheader("👥 人員名單與個人金額限制維護")
    with st.expander("➕ 新增同仁與限制", expanded=False):
        with st.form("add_user_form"):
            new_user_name = st.text_input("姓名")
            new_user_dept = st.text_input("組別 / 部門", value="向日葵")
            new_user_limit = st.number_input("個人金額限制 (0 代表不限額)", min_value=0, value=80, step=10)
            if st.form_submit_button("新增同仁"):
                if new_user_name:
                    new_person = pd.DataFrame([{
                        "姓名": new_user_name, 
                        "組別": new_user_dept,
                        "金額限制": new_user_limit
                    }])
                    st.session_state.df_users = pd.concat([st.session_state.df_users, new_person], ignore_index=True)
                    st.success(f"同仁【{new_user_name}】新增成功！")
                    st.rerun()

    st.write("#### 目前同仁清單（可在此直接調整每個人的金額限制）：")
    col_cfg = {
        "金額限制": st.column_config.NumberColumn("金額限制 (0=不限)", min_value=0, step=10)
    }
    edited_users = st.data_editor(
        st.session_state.df_users, 
        column_config=col_cfg,
        use_container_width=True, 
        num_rows="dynamic", 
        key="users_editor"
    )
    if st.button("💾 儲存人員名單與金額修改"):
        st.session_state.df_users = edited_users
        st.success("人員名單與金額限制已更新！")
