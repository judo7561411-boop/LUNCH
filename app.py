import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# 設定頁面資訊
st.set_page_config(page_title="中餐點餐與對帳系統", page_icon="🍱", layout="wide")

# 建立 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

# -------------------------------------------------------------
# 資料讀取函式（針對您的試算表格式客製化）
# -------------------------------------------------------------
@st.cache_data(ttl=0)
def load_menu_data():
    try:
        df = conn.read(worksheet="店家菜單", ttl=0)
        df = df.dropna(subset=["餐點名稱"])
        return df
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=0)
def load_users_data():
    try:
        df = conn.read(worksheet="人員名單", ttl=0)
        df = df.dropna(subset=["姓名"])
        return df
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=0)
def load_orders_data():
    try:
        # 因為每日訂單第 1~3 列是上方統計卡片，header 設定為第 3 列（索引 3 即第 4 列為標題）
        df = conn.read(worksheet="每日訂單", header=3, ttl=0)
        df = df.dropna(subset=["訂單編號"])
        # 排除最後一列的「總計」
        df = df[df["訂單編號"] != "總計"]
        return df
    except Exception as e:
        return pd.DataFrame()

# 載入資料
df_menu = load_menu_data()
df_users = load_users_data()
df_orders = load_orders_data()

st.title("🍱 中餐點餐與對帳系統")

# 功能分頁
tab1, tab2, tab3, tab4 = st.tabs([
    "🛒 我要點餐(含預訂)", 
    "📊 中餐明細與收款確認", 
    "⚙️ 店家與菜單維護", 
    "👥 人員名單管理"
])

# -------------------------------------------------------------
# 分頁 1：我要點餐
# -------------------------------------------------------------
with tab1:
    st.subheader("中餐登記")
    if df_menu.empty or df_users.empty:
        st.warning("⚠️ 尚未讀取到菜單或人員資料，請確認 Google Sheets 權限或工作表內容。")
    else:
        # 只篩選供應中的品項
        available_menu = df_menu[df_menu["供應狀態"] == "供應中"] if "供應狀態" in df_menu.columns else df_menu
        
        stores = available_menu["店家名稱"].dropna().unique()
        users = df_users["姓名"].dropna().unique()
        
        col1, col2 = st.columns(2)
        with col1:
            order_date = st.date_input("點餐日期", value=date.today())
            selected_user = st.selectbox("點餐人員", options=users)
            selected_store = st.selectbox("選擇店家", options=stores)
        
        store_items = available_menu[available_menu["店家名稱"] == selected_store]
        
        with col2:
            item_options = store_items["餐點名稱"].tolist()
            selected_item_name = st.selectbox("選擇餐點", options=item_options)
            
            # 取得該餐點的相關資訊
            item_info = store_items[store_items["餐點名稱"] == selected_item_name].iloc[0]
            raw_price = item_info.get("單價", 0)
            
            # 清理單價（去除 $ 與空格）
            base_price = int(str(raw_price).replace("$", "").replace(",", "").strip()) if pd.notnull(raw_price) else 0
            
            # 麵類選擇
            noodle_options_str = str(item_info.get("麵類選擇", "-"))
            if "/" in noodle_options_str:
                noodle_list = [n.strip() for n in noodle_options_str.split("/")]
            else:
                noodle_list = [noodle_options_str]
            selected_noodle = st.selectbox("麵類選擇", options=noodle_list)
            
            # 加麵選擇
            is_extra_noodle = st.radio("是否加麵", options=["不加麵", "加麵 (+15元)"], horizontal=True)
            quantity = st.number_input("數量", min_value=1, value=1, step=1)
            
        # 計算小計
        extra_fee = 10 if "烏龍麵" in selected_noodle else 0
        noodle_fee = 15 if "加麵" in is_extra_noodle else 0
        single_price = base_price + extra_fee
        total_item_price = (single_price + noodle_fee) * quantity
        
        st.info(f"💰 單價小計：${single_price} | 加麵與數量合計：**${total_item_price}**")
        
        if st.button("送出訂單", type="primary"):
            # 抓取該人員部門
            user_dept = df_users[df_users["姓名"] == selected_user]["組別"].values[0] if "組別" in df_users.columns else ""
            
            # 產生新訂單編號
            new_ord_id = f"ORD-{len(df_orders) + 1:03d}"
            
            new_record = pd.DataFrame([{
                "訂單編號": new_ord_id,
                "訂購日期": str(order_date),
                "員工編號": "",
                "員工姓名": selected_user,
                "所屬部門": user_dept,
                "餐點品項": selected_item_name,
                "麵類選擇": selected_noodle,
                "是否加麵": is_extra_noodle,
                "單價": f"${base_price}",
                "數量": quantity,
                "小計金額": f"${total_item_price}",
                "付款狀態": "未付款"
            }])
            
            updated_orders = pd.concat([df_orders, new_record], ignore_index=True)
            # 寫回每日訂單（保留前面結構，直接更新）
            conn.update(worksheet="每日訂單", data=updated_orders)
            st.cache_data.clear()
            st.success("✅ 點餐登記成功！")
            st.rerun()

# -------------------------------------------------------------
# 分頁 2：中餐明細與收款確認
# -------------------------------------------------------------
with tab2:
    st.subheader("明細與收款確認")
    col_d1, col_d2 = st.columns([3, 1])
    with col_d1:
        query_date = st.date_input("選擇欲對帳之日期", value=date.today(), key="admin_date")
    with col_d2:
        st.write("")
        st.write("")
        if st.button("🔄 即時同步最新狀態"):
            st.cache_data.clear()
            st.rerun()
            
    if not df_orders.empty and "訂購日期" in df_orders.columns:
        filtered_orders = df_orders[df_orders["訂購日期"].astype(str) == str(query_date)]
        if filtered_orders.empty:
            st.info(f"【{query_date}】查無任何中餐點單紀錄。")
        else:
            st.dataframe(filtered_orders, use_container_width=True)
            
            # 計算金額與份數
            try:
                amounts = filtered_orders["小計金額"].astype(str).str.replace("$", "").str.replace(",", "").astype(int)
                total_sum = amounts.sum()
            except:
                total_sum = 0
                
            total_count = len(filtered_orders)
            paid_count = len(filtered_orders[filtered_orders["付款狀態"] == "已付款"])
            
            c1, c2, c3 = st.columns(3)
            c1.metric("今日訂單總金額", f"${total_sum:,}")
            c2.metric("訂單總件數", f"{total_count} 筆")
            c3.metric("已收款 / 未收款", f"{paid_count} / {total_count - paid_count}")
    else:
        st.info("目前尚無訂單紀錄。")

# -------------------------------------------------------------
# 分頁 3：店家菜單檢視
# -------------------------------------------------------------
with tab3:
    st.subheader("店家與菜單列表")
    if not df_menu.empty:
        st.dataframe(df_menu, use_container_width=True)
    else:
        st.warning("查無店家菜單資料。")

# -------------------------------------------------------------
# 分頁 4：人員名單檢視
# -------------------------------------------------------------
with tab4:
    st.subheader("人員名單列表")
    if not df_users.empty:
        st.dataframe(df_users, use_container_width=True)
    else:
        st.warning("查無人員資料。")
