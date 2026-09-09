import streamlit as st
import pandas as pd
from datetime import date

# 頁面配置
st.set_page_config(page_title="中餐點餐與管理系統", page_icon="🍱", layout="wide")

# CSS 注入：點餐介面友善大字體與大按鈕
st.markdown("""
<style>
    /* 點餐介面字體放大 */
    .friendly-container {
        font-size: 22px !important;
    }
    /* 大圖卡按鈕樣式 */
    .big-btn button {
        width: 100% !important;
        min-height: 85px !important;
        font-size: 24px !important;
        font-weight: bold !important;
        border-radius: 16px !important;
        margin-bottom: 12px !important;
        border: 2px solid #D1D5DB !important;
    }
    .big-btn button:hover {
        border-color: #3B82F6 !important;
        background-color: #EFF6FF !important;
    }
    /* 成功確認大方框 */
    .big-success-box {
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
def load_sheet(sheet_name, header_row=0):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        return pd.read_csv(url, header=header_row)
    except Exception:
        return pd.DataFrame()

# 載入資料並在 Session State 中保持可編輯性
if "df_menu" not in st.session_state:
    loaded_menu = load_sheet("menu")
    if not loaded_menu.empty and "餐點名稱" in loaded_menu.columns:
        st.session_state.df_menu = loaded_menu.dropna(subset=["餐點名稱"])
    else:
        st.session_state.df_menu = pd.DataFrame(columns=["店家名稱", "分類", "餐點名稱", "麵類選擇", "單價", "供應狀態", "備註"])

if "df_users" not in st.session_state:
    loaded_users = load_sheet("users")
    if not loaded_users.empty and "姓名" in loaded_users.columns:
        st.session_state.df_users = loaded_users.dropna(subset=["姓名"])
    else:
        st.session_state.df_users = pd.DataFrame(columns=["姓名", "組別"])

# 初始化友善點餐狀態
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

st.title("🍱 中餐點餐與管理系統")

tab1, tab2, tab3, tab4 = st.tabs([
    "🛒 友善大圖點餐", 
    "📊 明細與對帳", 
    "⚙️ 菜單管理與編輯", 
    "👥 人員名單管理"
])

# -------------------------------------------------------------
# 分頁 1：符合智能障礙者操作之點餐流程（四步驟引導）
# -------------------------------------------------------------
with tab1:
    st.markdown(f"## 👉 目前步驟：第 {st.session_state.step} 步 / 共 4 步")

    # 步驟 1：選姓名
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

    # 步驟 2：選餐點
    elif st.session_state.step == 2:
        st.subheader(f"你好，{st.session_state.order_name}！今天想吃什麼？")
        
        # 只顯示供應中的菜單
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

    # 步驟 3：選麵類與份量
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

    # 步驟 4：大字核對與送出
    elif st.session_state.step == 4:
        st.subheader("請看清楚，這是你的餐點嗎？")
        extra_nd_fee = 10 if "烏龍麵" in st.session_state.order_noodle else 0
        extra_fee = 15 if "加麵" in st.session_state.order_extra else 0
        total_p = st.session_state.order_item_price + extra_nd_fee + extra_fee

        st.markdown(f"""
        <div style="background-color: #F8FAFC; border: 2px solid #CBD5E1; border-radius: 16px; padding: 24px; font-size: 26px; line-height: 2.2;">
            👤 姓名：<b>{st.session_state.order_name}</b><br>
            🍲 餐點：<b>{st.session_state.order_item}</b><br>
            🍜 麵類：<b>{st.session_state.order_noodle}</b><br>
            🥣 份量：<b>{st.session_state.order_extra}</b><br>
            💵 金額：<b style="color: #E02424; font-size: 36px;">${total_p} 元</b>
        </div>
        """, unsafe_allow_html=True)
        st.write("")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("❌ 不對，全部重新選"):
                st.session_state.step = 1
                st.session_state.order_name = None
                st.session_state.order_item = None
                st.rerun()
        with c2:
            if st.button("✅ 正確，按這裡送出！", type="primary"):
                st.markdown("""
                <div class="big-success-box">
                    🎉 點餐成功！廚房收到囉！
                </div>
                """, unsafe_allow_html=True)
                st.write("")
                if st.button("幫下一位同仁點餐"):
                    st.session_state.step = 1
                    st.session_state.order_name = None
                    st.session_state.order_item = None
                    st.rerun()

# -------------------------------------------------------------
# 分頁 2：明細與收款確認
# -------------------------------------------------------------
with tab2:
    st.subheader("每日點餐明細與對帳")
    df_orders = load_sheet("orders", header_row=3)
    if not df_orders.empty and "訂單編號" in df_orders.columns:
        df_orders = df_orders.dropna(subset=["訂單編號"])
        df_orders = df_orders[df_orders["訂單編號"] != "總計"]
        st.dataframe(df_orders, use_container_width=True)
    else:
        st.info("尚無今日點單資料。")

# -------------------------------------------------------------
# 分頁 3：菜單管理與編輯（管理者專用）
# -------------------------------------------------------------
with tab3:
    st.subheader("⚙️ 菜單管理與品項維護")
    
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
                    new_entry = pd.DataFrame([{
                        "店家名稱": new_store,
                        "分類": new_category,
                        "餐點名稱": new_item_name,
                        "麵類選擇": new_noodles,
                        "單價": f"${new_price}",
                        "供應狀態": new_status,
                        "備註": new_note
                    }])
                    st.session_state.df_menu = pd.concat([st.session_state.df_menu, new_entry], ignore_index=True)
                    st.success(f"已新增品項：{new_item_name}！")
                    st.rerun()

    st.write("#### 菜單清單（可直接修改價格與供應狀態）：")
    # 支援線上表格直接編輯
    edited_menu = st.data_editor(
        st.session_state.df_menu, 
        use_container_width=True, 
        num_rows="dynamic",
        key="menu_editor"
    )
    if st.button("💾 儲存菜單修改內容"):
        st.session_state.df_menu = edited_menu
        st.success("菜單修改已更新至系統！")

# -------------------------------------------------------------
# 分頁 4：人員名單管理（管理者專用）
# -------------------------------------------------------------
with tab4:
    st.subheader("👥 人員名單維護")
    
    with st.expander("➕ 新增同仁名單", expanded=False):
        with st.form("add_user_form"):
            new_user_name = st.text_input("姓名")
            new_user_dept = st.text_input("組別 / 部門")
            
            if st.form_submit_button("新增同仁"):
                if new_user_name:
                    new_person = pd.DataFrame([{
                        "姓名": new_user_name,
                        "組別": new_user_dept
                    }])
                    st.session_state.df_users = pd.concat([st.session_state.df_users, new_person], ignore_index=True)
                    st.success(f"同仁【{new_user_name}】新增成功！")
                    st.rerun()

    st.write("#### 目前同仁名單（可直接修改或刪除）：")
    edited_users = st.data_editor(
        st.session_state.df_users, 
        use_container_width=True, 
        num_rows="dynamic",
        key="users_editor"
    )
    if st.button("💾 儲存人員名單修改"):
        st.session_state.df_users = edited_users
        st.success("人員名單已更新至系統！")
