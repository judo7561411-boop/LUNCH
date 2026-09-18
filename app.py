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

    /* 餐點大卡片 */
    .food-card {
        background-color: #FFFFFF; border: 2.5px solid #CBD5E1;
        border-radius: 20px; padding: 20px; margin-bottom: 22px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }

    /* 種類單選大按鈕 */
    div[data-testid="stRadio"] > div[role="radiogroup"] > label {
        background-color: #F0F9FF !important;
        border: 2px solid #38BDF8 !important;
        border-radius: 14px !important;
        padding: 8px 18px !important;
        min-height: 54px !important;
        font-size: 22px !important;
        font-weight: 800 !important;
        color: #0369A1 !important;
    }

    /* 數量加減大按鍵 */
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

    /* 確認點這道大按鈕 */
    .food-order-btn button {
        width: 100% !important; min-height: 80px !important;
        font-size: 26px !important; font-weight: 900 !important;
        border-radius: 18px !important; border: 2.5px solid #059669 !important;
        background-color: #10B981 !important; color: #FFFFFF !important;
        margin-top: 14px !important; white-space: pre-line !important;
        box-shadow: 0 4px 10px rgba(16,185,129,0.25) !important;
    }
    .food-order-btn button:hover {
        background-color: #059669 !important;
    }

    /* 購物車提示卡 */
    .cart-summary {
        background-color: #FEF3C7; border: 3px solid #F59E0B;
        border-radius: 18px; padding: 18px; font-size: 24px;
        font-weight: 900; color: #92400E; margin-bottom: 20px;
    }

    /* 彙整出單表列印專用樣式 */
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

    /* 左下角回頂端浮動圓鈕 */
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
    st.session_state.selected_user = None
    st.session_state.selected_store = None
    st.session_state.cart = []
    st.session_state.order_finished = False
    
    keys_to_clear = [k for k in st.session_state.keys() if k.startswith("qty_") or k.startswith("type_") or k.startswith("ex_")]
    for k in keys_to_clear:
        del st.session_state[k]

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

st.title("🍱 中餐點餐與管理系統")

tab1, tab2, tab3 = st.tabs(["🛒 友善大圖點餐", "💵 現場收款對帳", "🖨️ 訂單彙整出單"])

# -------------------------------------------------------------
# 分頁 1：友善大圖點餐
# -------------------------------------------------------------
with tab1:
    chosen_date_str = str(st.session_state.target_order_date)

    if st.session_state.order_finished:
        st.success(f"🎉 訂單已送出成功！預訂用餐日期：【{chosen_date_str}】")
        if st.button("👉 換下一位點餐", type="primary", use_container_width=True):
            reset_ordering()
            st.rerun()

    # 步驟 1：選用餐日期與姓名
    elif st.session_state.selected_user is None:
        st.markdown('<div class="simple-title">第 1 步：選擇用餐日期</div>', unsafe_allow_html=True)
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
        st.markdown(f'<div class="simple-title">第 2 步：請問你是誰？（點姓名）</div>', unsafe_allow_html=True)
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

    # 步驟 3：餐點卡片（含種類挑選、數量加減與一鍵點餐）
    else:
        u_name = st.session_state.selected_user
        store_name = st.session_state.selected_store

        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"### 👤 **{u_name}** ｜ 🏪 **{store_name}** ｜ 📅 **{chosen_date_str}**")
        with c2:
            if st.button("⬅️ 重選店家"):
                st.session_state.selected_store = None
                st.session_state.cart = []
                st.rerun()

        # 購物車摘要
        if st.session_state.cart:
            cart_total = sum(x["subtotal"] for x in st.session_state.cart)
            item_desc = "、".join([f"{x['item']}({x['spec']}) x{x['qty']}" for x in st.session_state.cart])
            st.markdown(f"""
            <div class="cart-summary">
                🛒 已選餐點：<b>{item_desc}</b><br>
                💰 目前合計：<b>${fmt_price(cart_total)} 元</b>
            </div>
            """, unsafe_allow_html=True)
            
            sc1, sc2 = st.columns([2, 1])
            with sc1:
                if st.button("✅ 我選好了，確認送出！", type="primary", use_container_width=True):
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
                    with st.spinner("同步雲端資料中..."):
                        sync_to_google_sheet({"action": "append", "rows": new_rows})
                    st.session_state.order_finished = True
                    st.rerun()
            with sc2:
                if st.button("🗑️ 清空重選", use_container_width=True):
                    st.session_state.cart = []
                    st.rerun()

        st.write("---")
        st.markdown('<div class="simple-title">👉 請選擇種類與數量，點擊綠色按鈕點餐：</div>', unsafe_allow_html=True)

        current_menu = df_menu[df_menu["店家名稱"] == store_name] if "店家名稱" in df_menu.columns else df_menu
        m_cols = st.columns(2)
        
        for idx, (_, item) in enumerate(current_menu.iterrows()):
            i_name = str(item.get("餐點名稱", "")).strip()
            base_p = parse_price(item.get("單價", 0))
            category = str(item.get("分類", ""))
            
            raw_options = ""
            if "種類選擇" in item:
                raw_options = str(item["種類選擇"]).strip()
            elif "麵類選擇" in item:
                raw_options = str(item["麵類選擇"]).strip()

            is_soup = "湯" in i_name or "湯" in category or any(x in raw_options for x in ["小", "中", "大"])

            if raw_options and raw_options not in ["-", "nan", "無", "固定"]:
                type_options = [opt.strip() for opt in re.split(r"[/,、|]+", raw_options) if opt.strip()]
            elif is_soup:
                type_options = ["小", "中 (+10元)", "大 (+20元)"]
            else:
                type_options = ["標準配置"]

            is_liumei = "劉妹" in str(store_name)
            qty_key = safe_key("qty", i_name, idx)
            type_key = safe_key("type", i_name, idx)
            ex_key = safe_key("ex", i_name, idx)

            if qty_key not in st.session_state:
                st.session_state[qty_key] = 1

            with m_cols[idx % 2]:
                with st.container():
                    st.markdown(f"""
                    <div class="food-card">
                        <div style="font-size: 28px; font-weight: 900; color: #1E293B; margin-bottom: 6px;">🍲 {i_name}</div>
                        <div style="font-size: 22px; color: #475569; margin-bottom: 12px;">基本單價：<b style="color:#059669; font-size:26px;">${fmt_price(base_p)} 元</b></div>
                    """, unsafe_allow_html=True)
                    
                    st.write("**👉 挑選種類 / 尺寸：**")
                    chosen_type = st.radio(
                        label=f"{i_name}_種類",
                        options=type_options,
                        key=type_key,
                        horizontal=True,
                        label_visibility="collapsed"
                    )

                    st.write("**👉 挑選數量：**")
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

                    if is_liumei:
                        st.write("**👉 加麵選項：**")
                        chosen_ex = st.radio(
                            label=f"{i_name}_加麵",
                            options=["不加麵", "要加麵 (+15元)"],
                            horizontal=True,
                            key=ex_key,
                            label_visibility="collapsed"
                        )
                    else:
                        chosen_ex = "不加麵"

                    extra_type_price = parse_extra_price(chosen_type)
                    extra_ex_price = 15 if chosen_ex == "要加麵 (+15元)" else 0
                    current_unit_price = round(base_p + extra_type_price + extra_ex_price, 2)
                    current_qty = st.session_state[qty_key]
                    current_subtotal = round(current_unit_price * current_qty, 2)

                    order_btn_label = f"🍲 確認加入：{i_name} ({chosen_type})\n共 {current_qty} 份 ｜ 合計 ${fmt_price(current_subtotal)} 元"
                    st.markdown('<div class="food-order-btn">', unsafe_allow_html=True)
                    if st.button(order_btn_label, key=safe_key("add_order", i_name, idx)):
                        st.session_state.cart.append({
                            "item": i_name,
                            "spec": chosen_type,
                            "extra": chosen_ex,
                            "unit_price": current_unit_price,
                            "qty": current_qty,
                            "subtotal": current_subtotal
                        })
                        st.session_state[qty_key] = 1
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------
# 分頁 2：現場收款對帳
# -------------------------------------------------------------
with tab2:
    st.subheader("💵 現場收款與找零")
    q_date = st.date_input("選擇收款日期", value=st.session_state.target_order_date, key="q_date_recon")
    if st.button("🔄 重新載入最新資料", key="btn_reload_recon"):
        st.session_state.orders_data = load_orders_from_sheet()
        st.rerun()

    df_orders = st.session_state.orders_data
    q_str = str(q_date).strip()
    day_orders = df_orders[df_orders["訂購日期"].astype(str).str.replace("-", "/").str.contains(q_str.replace("-", "/"))].copy()

    if day_orders.empty:
        st.info("該日期無點餐紀錄。")
    else:
        day_orders["金額"] = day_orders["小計金額"].apply(parse_price)
        unpaid = day_orders[day_orders["付款狀態"] != "已付款"]
        
        if unpaid.empty:
            st.success("🎉 本日全部訂單已收款完畢！可前往【🖨️ 訂單彙整出單】出單。")
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
        st.dataframe(day_orders[["訂單編號", "員工姓名", "餐點品項", "麵類選擇", "數量", "小計金額", "付款狀態"]], use_container_width=True)

# -------------------------------------------------------------
# 分頁 3：訂單彙整出單（完整保留店家出單、個人核對、LINE複製與列印）
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

            # 1. 店家品項加總總表
            summary_grouped = out_day_orders.groupby("餐點規格彙整")["數量數值"].sum().reset_index()
            summary_grouped.columns = ["餐點項目與規格", "總數量 (份)"]
            summary_grouped = summary_grouped.sort_values(by="總數量 (份)", ascending=False)

            # 2. 個人分發核對名單
            person_grouped = out_day_orders.groupby("員工姓名").agg({
                "餐點規格彙整": lambda x: "、".join(f"{item} x{qty}" if qty > 1 else item for item, qty in zip(x, out_day_orders.loc[x.index, "數量數值"])),
                "金額數值": "sum",
                "付款狀態": lambda s: "已付款" if all(x == "已付款" for x in s) else "未付款"
            }).reset_index()
            person_grouped.columns = ["同仁姓名", "點購餐點品項明細", "應付小計", "付款狀態"]

            # LINE 純文字格式
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
