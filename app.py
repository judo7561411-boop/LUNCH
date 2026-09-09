import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="中餐點餐系統", page_icon="🍱", layout="wide")

# CSS 注入：字體超大、按鈕醒目、認知友善高對比
st.markdown("""
<style>
    /* 全域放大 */
    html, body, [class*="css"] {
        font-size: 20px;
    }
    /* 人員大按鈕 */
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
    /* 餐點大卡片容器 */
    .food-card {
        background-color: #FFFFFF;
        border: 2px solid #E2E8F0;
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    /* 購物清單卡片 */
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
</style>
""", unsafe_allow_html=True)

SHEET_ID = "1mHnXoG-Duq45EvwZTRVuq86rsK8T5DA9NkLnOi30wuM"

@st.cache_data(ttl=0)
def load_menu():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=menu"
        df = pd.read_csv(url)
        return df.dropna(subset=["餐點名稱"]) if "餐點名稱" in df.columns else df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=0)
def load_users():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=users"
        df = pd.read_csv(url)
        return df.dropna(subset=["姓名"]) if "姓名" in df.columns else df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=0)
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

# 狀態管理
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

    # 第一階段：選擇人員
    elif st.session_state.selected_user is None:
        st.subheader("👉 第一步：請問你是誰？（點你的名字）")
        df_u = st.session_state.df_users
        
        if df_u.empty or "姓名" not in df_u.columns:
            st.warning("⚠️ 尚無人員名單，請至【👥 人員名單管理】確認。")
        else:
            cols = st.columns(2)
            for idx, (_, u_row) in enumerate(df_u.iterrows()):
                u_name = str(u_row["姓名"]).strip()
                # 抓取該同仁在 C 欄的金額限制
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

    # 第二階段：依限額篩選並支援複選加購
    else:
        u_name = st.session_state.selected_user
        u_limit = st.session_state.user_limit
        cart_sum = sum(x["subtotal"] for x in st.session_state.cart)
        remain = (u_limit - cart_sum) if u_limit > 0 else 999999

        # 上方個人資訊橫幅
        limit_txt = f"個人上限額度：<b>${u_limit} 元</b> ｜ 剩餘可用：<b style='color:#DC2626;'>${remain} 元</b>" if u_limit > 0 else "個人上限額度：<b>無限制</b>"
        st.markdown(f'<div class="budget-banner">👤 目前同仁：{u_name} ｜ {limit_txt}</div>', unsafe_allow_html=True)

        # 側邊/上方：目前已加入的餐點（購物清單）
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
                    # 寫入 orders 紀錄
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
            else:
                st.info("💡 請從下方點選想要吃的餐點加入清單（可選多樣）。")

        st.write("---")
        st.subheader("👇 請挑選餐點（系統已自動為你過濾買得起的品項）：")

        menu_df = st.session_state.df_menu
        available_menu = menu_df[menu_df["供應狀態"] == "供應中"] if "供應狀態" in menu_df.columns else menu_df

        # 【核心關鍵】事前篩選：只列出底價小於等於個人上限（且小於等於剩餘額度）的餐點
        displayed_items = []
        for _, row in available_menu.iterrows():
            raw_p = row.get("單價", 0)
            try:
                base_p = int(str(raw_p).replace("$", "").replace(",", "").strip())
            except:
                base_p = 0

            # 初始限制：餐點底價不得高於個人限額；加點時不得高於剩餘額度
            if u_limit > 0 and base_p > u_limit:
                continue  # 一開始就直接過濾淘汰！

            displayed_items.append((row, base_p))

        if not displayed_items:
            st.warning("⚠️ 沒有符合你金額限制內的餐點項目。")
        else:
            # 以 2 欄大卡片排列可選餐點
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
                        
                        # 麵體與加麵獨立選單
                        c_nd, c_ex = st.columns(2)
                        with c_nd:
                            nd_choice = st.selectbox("麵體", ["意麵", "冬粉", "泡飯", "雞絲麵", "王子麵", "烏龍麵 (+10元)"], key=f"nd_{idx}")
                        with c_ex:
                            ex_choice = st.radio("份量", ["不加麵", "加麵 (+15元)"], horizontal=True, key=f"ex_{idx}")

                        extra_nd = 10 if "烏龍麵" in nd_choice else 0
                        extra_ex = 15 if "加麵" in ex_choice else 0
                        final_price = base_p + extra_nd + extra_ex

                        # 檢核是否能加入（不超過剩餘額度）
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
    st.subheader("📊 每日點餐明細與收款對帳")
    col_q1, col_q2 = st.columns([2, 1])
    with col_q1:
        query_date = st.date_input("選擇欲對帳或查詢的日期", value=date.today())
    with col_q2:
        st.write("")
        st.write("")
        if st.button("🔄 重新載入最新資料"):
            st.cache_data.clear()
            st.session_state.df_orders = load_orders()
            st.rerun()

    df_orders = st.session_state.df_orders

    if df_orders.empty or "訂購日期" not in df_orders.columns:
        st.info("尚無任何訂單紀錄。")
    else:
        current_orders = df_orders[df_orders["訂購日期"].astype(str) == str(query_date)].copy()
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
            m3.metric("已收款總額", f"${paid_money:,} 元", f"{len(paid_orders)} 筆已付")
            m4.metric("待收餘額 (未付)", f"${unpaid_money:,} 元", f"{unpaid_count} 筆未付", delta_color="inverse")

            st.write("---")
            st.markdown("#### ✏️ 點單明細清單：")
            column_config = {
                "付款狀態": st.column_config.SelectboxColumn("付款狀態", options=["已付款", "未付款"], required=True)
            }
            display_cols = [c for c in current_orders.columns if c != "金額數值"]
            edited_today = st.data_editor(current_orders[display_cols], column_config=column_config, use_container_width=True, num_rows="dynamic", key="orders_editor")

            if st.button("💾 儲存明細修改", type="primary"):
                other_orders = df_orders[df_orders["訂購日期"].astype(str) != str(query_date)]
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
