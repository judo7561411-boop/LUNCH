import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="中餐點餐與對帳管理系統", page_icon="🍱", layout="wide")

# CSS 注入：友善大字體、大按鈕與超額警示
st.markdown("""
<style>
    .big-btn button {
        width: 100% !important;
        min-height: 80px !important;
        font-size: 22px !important;
        font-weight: bold !important;
        border-radius: 14px !important;
        margin-bottom: 10px !important;
        border: 2px solid #CBD5E1 !important;
    }
    .big-btn button:hover {
        border-color: #3B82F6 !important;
        background-color: #EFF6FF !important;
    }
    .big-success-box {
        background-color: #DEF7EC;
        border: 3px solid #31C48D;
        border-radius: 16px;
        padding: 20px;
        font-size: 28px;
        font-weight: bold;
        color: #03543F;
        text-align: center;
        margin-top: 15px;
    }
    .over-budget-box {
        background-color: #FDE8E8;
        border: 3px solid #F98080;
        border-radius: 16px;
        padding: 18px;
        font-size: 24px;
        font-weight: bold;
        color: #9B1C1C;
        text-align: center;
        margin-top: 15px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

SHEET_ID = "1mHnXoG-Duq45EvwZTRVuq86rsK8T5DA9NkLnOi30wuM"

@st.cache_data(ttl=0)
def load_menu_sheet():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=menu"
        df = pd.read_csv(url)
        return df.dropna(subset=["餐點名稱"]) if "餐點名稱" in df.columns else df
    except:
        return pd.DataFrame(columns=["店家名稱", "分類", "餐點名稱", "麵類選擇", "單價", "供應狀態", "備註"])

@st.cache_data(ttl=0)
def load_users_sheet():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=users"
        df = pd.read_csv(url)
        return df.dropna(subset=["姓名"]) if "姓名" in df.columns else df
    except:
        return pd.DataFrame(columns=["姓名", "組別"])

@st.cache_data(ttl=0)
def load_orders_sheet():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=orders"
        raw_df = pd.read_csv(url, header=None)
        header_row_idx = None
        for i in range(min(10, len(raw_df))):
            row_vals = raw_df.iloc[i].astype(str).tolist()
            if any("訂單編號" in str(v) for v in row_vals):
                header_row_idx = i
                break
        
        df = pd.read_csv(url, header=header_row_idx if header_row_idx is not None else 3)
        if not df.empty and "訂單編號" in df.columns:
            df = df.dropna(subset=["訂單編號"])
            df = df[df["訂單編號"].astype(str).str.strip() != "總計"]
            df = df[df["訂單編號"].astype(str).str.startswith("ORD")]
        return df
    except:
        return pd.DataFrame(columns=[
            "訂單編號", "訂購日期", "員工編號", "員工姓名", "所屬部門", 
            "餐點品項", "麵類選擇", "是否加麵", "單價", "數量", "小計金額", "付款狀態"
        ])

# 預設每人補助/金額上限（預設 120 元）
if "max_budget_per_person" not in st.session_state:
    st.session_state.max_budget_per_person = 120

if "df_menu" not in st.session_state:
    st.session_state.df_menu = load_menu_sheet()

if "df_users" not in st.session_state:
    st.session_state.df_users = load_users_sheet()

if "df_orders" not in st.session_state:
    st.session_state.df_orders = load_orders_sheet()

if "step" not in st.session_state:
    st.session_state.step = 1
if "order_name" not in st.session_state:
    st.session_state.order_name = None
if "order_item" not in st.session_state:
    st.session_state.order_item = None
if "order_item_price" not in st.session_state:
    st.session_state.order_item_price = 0
if "order_noodle" not in st.session_state:
    st.session_state.order_noodle = "意麵"
if "order_extra" not in st.session_state:
    st.session_state.order_extra = "不加麵"

st.title("🍱 中餐點餐與對帳管理系統")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🛒 友善大圖點餐", 
    "📊 明細與對帳", 
    "⚙️ 菜單管理與編輯", 
    "👥 人員名單管理",
    "🛡️ 規則與金額限制"
])

# -------------------------------------------------------------
# 分頁 1：友善大圖點餐（含金額上限檢驗）
# -------------------------------------------------------------
with tab1:
    st.markdown(f"## 👉 目前步驟：第 {st.session_state.step} 步 / 共 4 步")

    if st.session_state.step == 1:
        st.subheader("請問你是誰？（點選你的名字）")
        user_list = st.session_state.df_users["姓名"].dropna().tolist()
        if not user_list:
            st.warning("目前尚無人員資料，請至【👥 人員名單管理】新增。")
        else:
            cols = st.columns(2)
            for idx, name in enumerate(user_list):
                with cols[idx % 2]:
                    st.markdown('<div class="big-btn">', unsafe_allow_html=True)
                    if st.button(f"👤 {name}", key=f"user_{name}"):
                        st.session_state.order_name = name
                        st.session_state.step = 2
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.step == 2:
        st.subheader(f"你好，{st.session_state.order_name}！今天想吃什麼？")
        menu_df = st.session_state.df_menu
        available_menu = menu_df[menu_df["供應狀態"] == "供應中"] if "供應狀態" in menu_df.columns else menu_df
        
        if available_menu.empty:
            st.warning("目前沒有供應中的餐點。")
        else:
            cols = st.columns(2)
            for idx, (_, row) in enumerate(available_menu.iterrows()):
                item_name = row["餐點名稱"]
                raw_p = row.get("單價", 0)
                price = int(str(raw_p).replace("$", "").replace(",", "").strip()) if pd.notnull(raw_p) else 0
                with cols[idx % 2]:
                    st.markdown('<div class="big-btn">', unsafe_allow_html=True)
                    if st.button(f"🍲 {item_name}\n${price} 元", key=f"item_{item_name}"):
                        st.session_state.order_item = item_name
                        st.session_state.order_item_price = price
                        st.session_state.step = 3
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
        st.write("")
        if st.button("⬅️ 重選名字"):
            st.session_state.step = 1
            st.rerun()

    elif st.session_state.step == 3:
        st.subheader(f"已選餐點：{st.session_state.order_item}")
        st.write("#### 1. 想要哪種麵？")
        noodles = ["意麵", "冬粉", "泡飯", "雞絲麵", "王子麵", "烏龍麵 (+10元)"]
        n_cols = st.columns(3)
        for idx, nd in enumerate(noodles):
            with n_cols[idx % 3]:
                st.markdown('<div class="big-btn">', unsafe_allow_html=True)
                if st.button(f"🍜 {nd}", key=f"nd_{nd}"):
                    st.session_state.order_noodle = nd
                st.markdown('</div>', unsafe_allow_html=True)
        st.info(f"👉 目前選的麵：**{st.session_state.order_noodle}**")
        st.write("---")
        
        st.write("#### 2. 吃得飽嗎？需要加麵嗎？")
        e_col1, e_col2 = st.columns(2)
        with e_col1:
            st.markdown('<div class="big-btn">', unsafe_allow_html=True)
            if st.button("🥣 正常份量 (不加麵)", key="no_extra"):
                st.session_state.order_extra = "不加麵"
            st.markdown('</div>', unsafe_allow_html=True)
        with e_col2:
            st.markdown('<div class="big-btn">', unsafe_allow_html=True)
            if st.button("➕ 加大份量 (+15元)", key="yes_extra"):
                st.session_state.order_extra = "加麵 (+15元)"
            st.markdown('</div>', unsafe_allow_html=True)
        st.info(f"👉 目前選的份量：**{st.session_state.order_extra}**")
        st.write("---")
        
        b1, b2 = st.columns(2)
        with b1:
            if st.button("⬅️ 重選餐點"):
                st.session_state.step = 2
                st.rerun()
        with b2:
            if st.button("👉 點好了，看確認畫面！", type="primary"):
                st.session_state.step = 4
                st.rerun()

    elif st.session_state.step == 4:
        st.subheader("請看清楚，這是你的餐點嗎？")
        extra_nd_fee = 10 if "烏龍麵" in st.session_state.order_noodle else 0
        extra_fee = 15 if "加麵" in st.session_state.order_extra else 0
        total_p = st.session_state.order_item_price + extra_nd_fee + extra_fee

        # 金額限制檢核
        max_limit = st.session_state.max_budget_per_person
        is_over_budget = total_p > max_limit

        st.markdown(f"""
        <div style="background-color: #F8FAFC; border: 2px solid #CBD5E1; border-radius: 16px; padding: 24px; font-size: 26px; line-height: 2.2;">
            👤 姓名：<b>{st.session_state.order_name}</b><br>
            🍲 餐點：<b>{st.session_state.order_item}</b><br>
            🍜 麵類：<b>{st.session_state.order_noodle}</b><br>
            🥣 份量：<b>{st.session_state.order_extra}</b><br>
            💵 金額：<b style="color: {'#E02424' if is_over_budget else '#1E40AF'}; font-size: 36px;">${total_p} 元</b>
            <span style="font-size: 20px; color: #64748B;">（每人上限：${max_limit} 元）</span>
        </div>
        """, unsafe_allow_html=True)

        if is_over_budget:
            st.markdown(f"""
            <div class="over-budget-box">
                ⚠️ 超過金額上限囉！目前上限為 ${max_limit} 元，請重選餐點或不加麵。
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("❌ 不對，重新選餐"):
                st.session_state.step = 2
                st.rerun()
        with c2:
            # 超額時停用送出按鈕
            if st.button("✅ 正確，按這裡送出！", type="primary", disabled=is_over_budget):
                user_dept = ""
                if not st.session_state.df_users.empty and "姓名" in st.session_state.df_users.columns:
                    match_u = st.session_state.df_users[st.session_state.df_users["姓名"] == st.session_state.order_name]
                    if not match_u.empty and "組別" in match_u.columns:
                        user_dept = match_u["組別"].values[0]

                new_order_row = pd.DataFrame([{
                    "訂單編號": f"ORD-{len(st.session_state.df_orders) + 1:03d}",
                    "訂購日期": str(date.today()),
                    "員工編號": "",
                    "員工姓名": st.session_state.order_name,
                    "所屬部門": user_dept,
                    "餐點品項": st.session_state.order_item,
                    "麵類選擇": st.session_state.order_noodle,
                    "是否加麵": st.session_state.order_extra,
                    "單價": f"${st.session_state.order_item_price}",
                    "數量": 1,
                    "小計金額": f"${total_p}",
                    "付款狀態": "未付款"
                }])
                st.session_state.df_orders = pd.concat([st.session_state.df_orders, new_order_row], ignore_index=True)

                st.markdown("""
                <div class="big-success-box">
                    🎉 點餐成功！資料已送出！
                </div>
                """, unsafe_allow_html=True)
                st.write("")
                if st.button("幫下一位同仁點餐"):
                    st.session_state.step = 1
                    st.session_state.order_name = None
                    st.session_state.order_item = None
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
            st.session_state.df_orders = load_orders_sheet()
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
# 分頁 4：人員名單管理
# -------------------------------------------------------------
with tab4:
    st.subheader("👥 人員名單維護")
    with st.expander("➕ 新增同仁名單", expanded=False):
        with st.form("add_user_form"):
            new_user_name = st.text_input("姓名")
            new_user_dept = st.text_input("組別 / 部門")
            if st.form_submit_button("新增同仁"):
                if new_user_name:
                    new_person = pd.DataFrame([{"姓名": new_user_name, "組別": new_user_dept}])
                    st.session_state.df_users = pd.concat([st.session_state.df_users, new_person], ignore_index=True)
                    st.success(f"同仁【{new_user_name}】新增成功！")
                    st.rerun()

    st.write("#### 目前同仁名單（可直接修改）：")
    edited_users = st.data_editor(st.session_state.df_users, use_container_width=True, num_rows="dynamic", key="users_editor")
    if st.button("💾 儲存人員名單修改"):
        st.session_state.df_users = edited_users
        st.success("人員名單已更新至系統！")

# -------------------------------------------------------------
# 分頁 5：規則與金額限制（管理員自訂上限）
# -------------------------------------------------------------
with tab5:
    st.subheader("🛡️ 點餐規則與每人金額上限設定")
    st.info("💡 此處設定的金額將作為同仁點餐的最高限制。若點餐總額（含換麵、加麵）超過該數值，系統將不允許送出點單。")
    
    current_limit = st.session_state.max_budget_per_person
    new_limit = st.number_input("設定每人單餐最高上限金額 (元)", min_value=50, max_value=500, value=current_limit, step=5)
    
    if st.button("💾 儲存金額上限設定", type="primary"):
        st.session_state.max_budget_per_person = int(new_limit)
        st.success(f"✅ 金額上限已成功修改為：每人 ${new_limit} 元！")
