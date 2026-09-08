import csv
from datetime import date, datetime
import io
import json
import os
import socket
import sqlite3
import streamlit as st

# ==========================================
# 系統設定：網頁分頁標題與寬版佈局
# ==========================================
st.set_page_config(
    page_title="每日中餐點餐系統", page_icon="🍱", layout="wide"
)

DB_NAME = "orders.db"
IMAGE_DIR = "static/images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# ==========================================
# 注入視覺優化 CSS
# ==========================================
st.markdown(
    """
    <style>
    .stButton button {
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.2s ease-in-out;
    }
    .stButton button:active {
        transform: scale(0.98);
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        background-color: #ffffff;
    }
    .price-badge {
        background-color: #fee2e2;
        color: #dc2626;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 1.1rem;
        display: inline-block;
        margin-bottom: 6px;
    }
    .status-paid {
        background-color: #dcfce7;
        color: #15803d;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .status-unpaid {
        background-color: #fee2e2;
        color: #b91c1c;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 1. 資料庫連線工廠與自動升級初始化 (支援付款狀態)
# ==========================================


def get_db_connection():
    """取得資料庫連線：30秒逾時等待 + WAL 模式"""
    conn = sqlite3.connect(DB_NAME, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS stores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_name TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT '主食',
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            price_large INTEGER DEFAULT 0,
            options TEXT DEFAULT '',
            extra_type TEXT DEFAULT '',
            extra_price INTEGER DEFAULT 0,
            image_url TEXT DEFAULT ''
        )
    """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            daily_limit INTEGER NOT NULL DEFAULT 0
        )
    """
    )

    # 訂單紀錄表 (新增 is_paid 欄位：0 未付款，1 已付款)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            user_name TEXT NOT NULL,
            store_name TEXT NOT NULL,
            time TEXT NOT NULL,
            items TEXT NOT NULL,
            total INTEGER NOT NULL,
            note TEXT,
            is_paid INTEGER DEFAULT 0
        )
    """
    )

    # 自動升級 orders 資料表欄位 (防錯機制)
    c.execute("PRAGMA table_info(orders)")
    order_cols = [col[1] for col in c.fetchall()]
    if "is_paid" not in order_cols:
        c.execute("ALTER TABLE orders ADD COLUMN is_paid INTEGER DEFAULT 0")

    # 確保菜單欄位齊全
    c.execute("PRAGMA table_info(menu)")
    menu_cols = [col[1] for col in c.fetchall()]
    if "category" not in menu_cols:
        c.execute("ALTER TABLE menu ADD COLUMN category TEXT NOT NULL DEFAULT '主食'")
    if "store_name" not in menu_cols:
        c.execute("ALTER TABLE menu ADD COLUMN store_name TEXT NOT NULL DEFAULT '好味便當店'")
    if "options" not in menu_cols:
        c.execute("ALTER TABLE menu ADD COLUMN options TEXT DEFAULT ''")
    if "price_large" not in menu_cols:
        c.execute("ALTER TABLE menu ADD COLUMN price_large INTEGER DEFAULT 0")
    if "extra_type" not in menu_cols:
        c.execute("ALTER TABLE menu ADD COLUMN extra_type TEXT DEFAULT ''")
    if "extra_price" not in menu_cols:
        c.execute("ALTER TABLE menu ADD COLUMN extra_price INTEGER DEFAULT 0")
    if "image_url" not in menu_cols:
        c.execute("ALTER TABLE menu ADD COLUMN image_url TEXT DEFAULT ''")

    # 寫入預設店家
    c.execute("SELECT COUNT(*) FROM stores")
    if c.fetchone()[0] == 0:
        c.executemany(
            "INSERT INTO stores (name) VALUES (?)",
            [("老牌麵食館",), ("好味便當店",), ("清爽手搖茶",)],
        )

        default_dishes = [
            ("老牌麵食館", "麵食類", "紅燒牛肉麵", 140, 160, "拉麵,陽春麵,細麵,冬粉", "加麵", 15, "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=500&q=80"),
            ("老牌麵食館", "麵食類", "榨菜肉絲麵", 75, 90, "拉麵,陽春麵,細麵,米粉", "加麵", 10, ""),
            ("老牌麵食館", "麵食類", "古早味乾麵", 50, 65, "油麵,陽春麵,意麵", "加麵", 10, "https://images.unsplash.com/photo-1552611052-33e04de081de?auto=format&fit=crop&w=500&q=80"),
            ("老牌麵食館", "湯品小菜", "燙青菜", 40, 0, "", "", 0, ""),
            ("老牌麵食館", "湯品小菜", "貢丸湯", 35, 0, "", "", 0, "https://images.unsplash.com/photo-1547592166-23ac45744acd?auto=format&fit=crop&w=500&q=80"),
            ("好味便當店", "便當特餐", "招牌排骨便當", 110, 0, "", "加飯", 0, "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?auto=format&fit=crop&w=500&q=80"),
            ("好味便當店", "便當特餐", "酥炸雞腿便當", 120, 0, "", "加飯", 10, ""),
            ("好味便當店", "單點小菜", "滷蛋", 15, 0, "", "", 0, ""),
            ("清爽手搖茶", "純茶系列", "茉香綠茶", 35, 0, "", "", 0, "https://images.unsplash.com/photo-1556679343-c7306c1976bc?auto=format&fit=crop&w=500&q=80"),
            ("清爽手搖茶", "鮮奶系列", "熟成紅茶拿鐵", 55, 0, "", "", 0, ""),
        ]
        c.executemany(
            """
            INSERT INTO menu (store_name, category, name, price, price_large, options, extra_type, extra_price, image_url) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            default_dishes,
        )

    # 寫入預設人員
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.executemany(
            "INSERT INTO users (name, daily_limit) VALUES (?, ?)",
            [
                ("王小明", 100),
                ("李小華", 150),
                ("張專員", 80),
                ("陳經理", 0),
            ],
        )

    conn.commit()
    conn.close()


init_db()

# ==========================================
# 2. 輔助函式與收款狀態管理核心
# ==========================================


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_all_users():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT name, daily_limit FROM users ORDER BY id ASC")
    users = [dict(r) for r in c.fetchall()]
    conn.close()
    return users


def get_all_stores():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, name FROM stores ORDER BY id ASC")
    stores = [dict(r) for r in c.fetchall()]
    conn.close()
    return stores


def get_menu_by_store(store_name):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT id, store_name, category, name, price, price_large, options, extra_type, extra_price, image_url 
        FROM menu WHERE store_name = ? ORDER BY category ASC, id ASC
    """,
        (store_name,),
    )
    items = [dict(r) for r in c.fetchall()]
    conn.close()
    return items


def update_store_name(old_name, new_name):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("UPDATE stores SET name = ? WHERE name = ?", (new_name, old_name))
        c.execute("UPDATE menu SET store_name = ? WHERE store_name = ?", (new_name, old_name))
        c.execute("UPDATE orders SET store_name = ? WHERE store_name = ?", (new_name, old_name))
        conn.commit()
        return True, "店家名稱修改成功！"
    except sqlite3.IntegrityError:
        return False, "店家名稱已存在！"
    finally:
        conn.close()


def delete_store(store_name):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM stores WHERE name = ?", (store_name,))
    c.execute("DELETE FROM menu WHERE store_name = ?", (store_name,))
    conn.commit()
    conn.close()


def update_menu_item(dish_id, category, name, price, price_large, options, extra_type, extra_price, image_url):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        """
        UPDATE menu 
        SET category = ?, name = ?, price = ?, price_large = ?, options = ?, extra_type = ?, extra_price = ?, image_url = ?
        WHERE id = ?
    """,
        (category, name, price, price_large, options, extra_type, extra_price, image_url, dish_id),
    )
    conn.commit()
    conn.close()


def get_user_spent_by_date(user_name, target_date_str):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT SUM(total) FROM orders 
        WHERE (user_name = ? OR name = ?) AND time LIKE ?
    """,
        (user_name, user_name, f"{target_date_str}%"),
    )
    res = c.fetchone()[0]
    conn.close()
    return res if res else 0


def update_order_item(order_id, user_name, items, total, note, is_paid):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        """
        UPDATE orders 
        SET user_name = ?, name = ?, items = ?, total = ?, note = ?, is_paid = ?
        WHERE id = ?
    """,
        (user_name, user_name, items, total, note, is_paid, order_id),
    )
    conn.commit()
    conn.close()


def toggle_payment_status(order_id, current_status):
    """切換單筆訂單付款狀態 (0 -> 1 或 1 -> 0)"""
    new_status = 1 if current_status == 0 else 0
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE orders SET is_paid = ? WHERE id = ?", (new_status, order_id))
    conn.commit()
    conn.close()


def delete_order_item(order_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()


def export_menu_backup():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT name FROM stores ORDER BY id ASC")
    stores = [r["name"] for r in c.fetchall()]
    c.execute("SELECT store_name, category, name, price, price_large, options, extra_type, extra_price, image_url FROM menu")
    dishes = [dict(r) for r in c.fetchall()]
    conn.close()
    return json.dumps({"stores": stores, "menu": dishes}, ensure_ascii=False, indent=2)


def import_menu_backup(json_str):
    try:
        data = json.loads(json_str)
        stores = data.get("stores", [])
        dishes = data.get("menu", [])
        if not stores:
            return False, "備份檔案內容無有效店家資料！"
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM menu")
        c.execute("DELETE FROM stores")
        for s in stores:
            c.execute("INSERT OR IGNORE INTO stores (name) VALUES (?)", (s,))
        for d in dishes:
            c.execute(
                """
                INSERT INTO menu (store_name, category, name, price, price_large, options, extra_type, extra_price, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    d.get("store_name", ""),
                    d.get("category", "主食"),
                    d.get("name", ""),
                    d.get("price", 0),
                    d.get("price_large", 0),
                    d.get("options", ""),
                    d.get("extra_type", ""),
                    d.get("extra_price", 0),
                    d.get("image_url", ""),
                ),
            )
        conn.commit()
        conn.close()
        return True, f"成功還原 {len(stores)} 個店家與 {len(dishes)} 道餐點品項！"
    except Exception as e:
        return False, f"還原失敗：{str(e)}"


# ==========================================
# 3. Session State 狀態初始化
# ==========================================
if "cart" not in st.session_state:
    st.session_state.cart = {}
if "order_completed" not in st.session_state:
    st.session_state.order_completed = False
if "last_order_info" not in st.session_state:
    st.session_state.last_order_info = {}

st.title("🍱 每日中餐點餐系統")

local_ip = get_local_ip()
with st.sidebar:
    st.header("📶 連線狀態")
    st.success("✅ 多台平板資料即時互通中")
    st.caption("每台裝置皆為獨立點餐畫面，送出訂單後立即同步於後台收款系統。")

main_tab1, main_tab2, main_tab3, main_tab4 = st.tabs(
    ["🛒 我要點餐(含預訂)", "📊 中餐明細與收款確認", "👥 人員名單管理", "⚙️ 店家與菜單維護"]
)

# ------------------------------------------
# 分頁 1: 我要點餐
# ------------------------------------------
with main_tab1:
    if st.session_state.order_completed:
        info = st.session_state.last_order_info
        st.success("## 🎉 您已點餐完畢！")
        
        with st.container(border=True):
            st.markdown(f"### 📋 點餐明細確認")
            st.markdown(f"* **點餐人員**：`{info.get('user', '')}`")
            st.markdown(f"* **用餐/預訂日期**：`{info.get('date', '')}`")
            st.markdown(f"* **點餐內容**：{info.get('items', '')}")
            if info.get('note'):
                st.markdown(f"* **備註需求**：{info.get('note')}")
            st.markdown(f"### 應付總額：<span class='price-badge'>NT$ {info.get('total', 0)}</span>", unsafe_allow_html=True)
            st.caption(f"下單完成時間：{info.get('time', '')} ｜ 資料庫已安全同步存檔（預設狀態：待付款）")

        st.write("")
        col_btn1, col_btn2 = st.columns([1, 2])
        with col_btn1:
            if st.button("➕ 繼續點下一單 / 返回點餐", type="primary", use_container_width=True):
                st.session_state.order_completed = False
                st.session_state.last_order_info = {}
                st.session_state.cart = {}
                st.rerun()

    else:
        with st.container(border=True):
            st.markdown("#### 👤 **步驟一：設定用餐日期與點餐人姓名**")
            col_date_top, col_user_top = st.columns([1, 1], gap="large")

            with col_date_top:
                order_target_date = st.date_input(
                    "📅 1. 用餐/預訂日期：",
                    value=date.today(),
                    help="預設為今天。若要預訂明天或未來日期，請在此直接挑選！",
                )
                target_date_str = order_target_date.strftime("%Y-%m-%d")

            with col_user_top:
                user_list = get_all_users()
                user_names = [u["name"] for u in user_list]
                user_limit_map = {u["name"]: u["daily_limit"] for u in user_list}

                if not user_names:
                    st.error("⚠️ 系統內尚未建立人員名單，請先至「👥 人員名單管理」新增人員姓名。")
                    selected_user = None
                else:
                    selected_user = st.selectbox(
                        "👤 2. 請選擇您的姓名（下拉選單）：",
                        options=["-- 請選擇人員姓名 --"] + user_names,
                    )

            spent_on_target_date = 0
            user_limit = 0
            remain = 0
            has_selected_user = bool(
                selected_user and selected_user != "-- 請選擇人員姓名 --"
            )

            current_cart_total = sum(
                i["price"] * i["qty"] for i in st.session_state.cart.values()
            )

            if has_selected_user:
                user_limit = user_limit_map.get(selected_user, 0)
                spent_on_target_date = get_user_spent_by_date(selected_user, target_date_str)

                if user_limit > 0:
                    remain = max(0, user_limit - spent_on_target_date)
                    actual_available = max(0, remain - current_cart_total)
                    date_label = "今日" if target_date_str == date.today().strftime("%Y-%m-%d") else f"【{target_date_str}】"
                    st.warning(
                        f"💳 **【{selected_user}】額度通知**：每日上限 **NT$ {user_limit}** ｜ {date_label}已累計 **NT$ {spent_on_target_date}** ｜ 今日總剩餘 **NT$ {remain}** ｜ 本台還可點 **NT$ {actual_available}**"
                    )
                else:
                    actual_available = 999999
                    st.info(
                        f"ℹ️ **【{selected_user}】不限消費額度**（{target_date_str} 累積金額 NT$ {spent_on_target_date}）"
                    )
            else:
                actual_available = 0
                st.info("💡 請先於上方選取您的姓名，確認個人額度後即可開始點餐！")

        st.write("")

        st.markdown("#### 🍽️ **步驟二：挑選餐點與確認結帳**")
        col_menu_left, col_cart_right = st.columns([3, 2], gap="large")

        with col_menu_left:
            stores_data = get_all_stores()
            store_names = [s["name"] for s in stores_data]

            if not store_names:
                st.warning("⚠️ 目前尚未建立任何店家，請前往「⚙️ 店家與菜單維護」新增店家。")
            else:
                store_tabs = st.tabs([f"🏪 {s}" for s in store_names])
                for idx, s_name in enumerate(store_names):
                    with store_tabs[idx]:
                        dishes = get_menu_by_store(s_name)
                        if not dishes:
                            st.info(f"【{s_name}】目前尚無菜單品項，可至後台新增。")
                        else:
                            categories = sorted(list(set(d["category"] for d in dishes)))
                            for cat in categories:
                                st.markdown(f"##### 🏷️ {cat}")
                                cat_dishes = [d for d in dishes if d["category"] == cat]
                                dish_cols = st.columns(3)

                                for d_idx, dish in enumerate(cat_dishes):
                                    with dish_cols[d_idx % 3]:
                                        with st.container(border=True):
                                            img_source = (dish.get("image_url") or "").strip()
                                            if img_source:
                                                try:
                                                    st.image(img_source, use_container_width=True)
                                                except Exception:
                                                    pass

                                            st.markdown(f"### {dish['name']}")

                                            has_large = (
                                                dish.get("price_large")
                                                and dish["price_large"] > 0
                                            )
                                            chosen_size = ""
                                            base_price = dish["price"]

                                            if has_large:
                                                chosen_size = st.radio(
                                                    "規格分量：",
                                                    options=["小碗", "大碗"],
                                                    format_func=lambda x: f"{x} (NT$ {dish['price'] if x == '小碗' else dish['price_large']})",
                                                    key=f"size_{dish['id']}",
                                                    horizontal=True,
                                                )
                                                base_price = (
                                                    dish["price_large"]
                                                    if chosen_size == "大碗"
                                                    else dish["price"]
                                                )
                                            else:
                                                st.markdown(
                                                    f"<span class='price-badge'>NT$ {dish['price']}</span>",
                                                    unsafe_allow_html=True,
                                                )

                                            opt_str = (dish.get("options") or "").strip()
                                            chosen_option = ""
                                            if opt_str:
                                                option_list = [
                                                    o.strip()
                                                    for o in opt_str.split(",")
                                                    if o.strip()
                                                ]
                                                chosen_option = st.selectbox(
                                                    "🍜 選擇麵類：",
                                                    options=option_list,
                                                    key=f"opt_{dish['id']}",
                                                )

                                            extra_types = (
                                                dish.get("extra_type") or ""
                                            ).strip()
                                            extra_price = dish.get("extra_price") or 0
                                            chosen_extra = "正常"

                                            if extra_types:
                                                extra_choices = ["正常"] + [
                                                    e.strip()
                                                    for e in extra_types.split(",")
                                                    if e.strip()
                                                ]
                                                price_tag = (
                                                    f" (+NT$ {extra_price})"
                                                    if extra_price > 0
                                                    else " (免費)"
                                                )
                                                chosen_extra = st.selectbox(
                                                    "🍚 加量需求：",
                                                    options=extra_choices,
                                                    format_func=lambda x: f"{x}{price_tag if x != '正常' else ''}",
                                                    key=f"extra_{dish['id']}",
                                                )

                                            add_price = (
                                                extra_price
                                                if (chosen_extra and chosen_extra != "正常")
                                                else 0
                                            )
                                            final_item_price = base_price + add_price

                                            if add_price > 0:
                                                st.caption(
                                                    f"單份總額：NT$ {final_item_price}"
                                                )

                                            btn_disabled = False
                                            btn_label = "＋ 點選加入"

                                            if not has_selected_user:
                                                btn_disabled = True
                                                btn_label = "🔒 請先在上方選取姓名"
                                            elif user_limit > 0:
                                                if final_item_price > actual_available:
                                                    btn_disabled = True
                                                    diff = final_item_price - actual_available
                                                    btn_label = f"⛔ 超出預算 (差 ${diff})"

                                            if st.button(
                                                btn_label,
                                                key=f"btn_add_{dish['id']}",
                                                use_container_width=True,
                                                disabled=btn_disabled,
                                                type="secondary" if not btn_disabled else "primary",
                                            ):
                                                spec_parts = []
                                                if chosen_size:
                                                    spec_parts.append(chosen_size)
                                                if chosen_option:
                                                    spec_parts.append(chosen_option)
                                                if chosen_extra and chosen_extra != "正常":
                                                    spec_parts.append(chosen_extra)

                                                spec_label = (
                                                    f" ({' / '.join(spec_parts)})"
                                                    if spec_parts
                                                    else ""
                                                )
                                                display_name = f"{dish['name']}{spec_label}"
                                                cart_item_key = f"{dish['id']}_{chosen_size}_{chosen_option}_{chosen_extra}"

                                                if cart_item_key in st.session_state.cart:
                                                    st.session_state.cart[cart_item_key]["qty"] += 1
                                                else:
                                                    st.session_state.cart[cart_item_key] = {
                                                        "dish_id": dish["id"],
                                                        "name": display_name,
                                                        "store": s_name,
                                                        "price": final_item_price,
                                                        "size": chosen_size,
                                                        "option": chosen_option,
                                                        "extra": chosen_extra,
                                                        "qty": 1,
                                                    }
                                                st.rerun()
                                st.write("")

        with col_cart_right:
            with st.container(border=True):
                st.markdown(f"#### 🛒 **點餐清單 (預訂日：{target_date_str})**")

                cart_total = 0

                if not st.session_state.cart:
                    st.caption("🛒 購物清單暫無品項，請點選左側餐點「＋ 點選加入」。")
                else:
                    for item_key, item_data in list(st.session_state.cart.items()):
                        subtotal = item_data["price"] * item_data["qty"]
                        cart_total += subtotal

                        c_name, c_qty, c_del = st.columns([3, 2, 1])
                        with c_name:
                            st.write(f"**{item_data['name']}**")
                            st.caption(
                                f"{item_data['store']} ｜ ${item_data['price']} × {item_data['qty']}"
                            )
                        with c_qty:
                            q1, q2 = st.columns(2)
                            if q1.button("－", key=f"minus_{item_key}"):
                                item_data["qty"] -= 1
                                if item_data["qty"] <= 0:
                                    del st.session_state.cart[item_key]
                                st.rerun()
                            if q2.button("＋", key=f"plus_{item_key}"):
                                if user_limit > 0 and (actual_available - item_data["price"]) < 0:
                                    st.toast("⚠️ 增加此份數將超過剩餘額度！")
                                else:
                                    item_data["qty"] += 1
                                    st.rerun()
                        with c_del:
                            if st.button("🗑️", key=f"del_{item_key}"):
                                del st.session_state.cart[item_key]
                                st.rerun()

                    st.divider()
                    st.markdown(
                        f"### 本次應付總額：<span class='price-badge'>NT$ {cart_total}</span>",
                        unsafe_allow_html=True,
                    )

                    if st.button("🧹 清空購物清單", use_container_width=True):
                        st.session_state.cart = {}
                        st.rerun()

                order_note = st.text_input(
                    "📝 中餐需求備註：", placeholder="例如：少油、不要酸菜、麵硬"
                )

                st.write("")
                btn_submit_label = f"✅ 確認送出【{target_date_str}】中餐訂單"
                if st.button(
                    btn_submit_label,
                    type="primary",
                    use_container_width=True,
                ):
                    if not has_selected_user:
                        st.error("❗ 請先於最上方「步驟一」下拉選單選擇「人員姓名」後再送出訂單！")
                    elif not st.session_state.cart:
                        st.error("❗ 購物清單目前尚無任何餐點，請先在左側挑選餐點並點擊「＋ 點選加入」！")
                    else:
                        current_hms = datetime.now().strftime("%H:%M:%S")
                        order_time_str = f"{target_date_str} {current_hms}"

                        conn = get_db_connection()
                        c = conn.cursor()

                        stores_in_cart = set(
                            item["store"] for item in st.session_state.cart.values()
                        )
                        summary_list = []
                        for s in stores_in_cart:
                            sub_items = [
                                item
                                for item in st.session_state.cart.values()
                                if item["store"] == s
                            ]
                            sub_total = sum(i["price"] * i["qty"] for i in sub_items)
                            summary_str = ", ".join(
                                [f"{i['name']}x{i['qty']}" for i in sub_items]
                            )
                            summary_list.append(f"【{s}】{summary_str}")
                            c.execute(
                                """
                                INSERT INTO orders (name, user_name, store_name, time, items, total, note, is_paid)
                                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                            """,
                                (
                                    selected_user,
                                    selected_user,
                                    s,
                                    order_time_str,
                                    summary_str,
                                    sub_total,
                                    order_note,
                                ),
                            )

                        conn.commit()
                        conn.close()

                        st.session_state.order_completed = True
                        st.session_state.last_order_info = {
                            "user": selected_user,
                            "date": target_date_str,
                            "items": " ； ".join(summary_list),
                            "total": cart_total,
                            "note": order_note,
                            "time": order_time_str,
                        }
                        st.session_state.cart = {}
                        st.rerun()

# ------------------------------------------
# 分頁 2: 中餐明細與收款確認 (核心升級：每人付款收錢確認)
# ------------------------------------------
with main_tab2:
    st.subheader("📊 每日中餐明細與每人付款收錢確認")

    col_date, col_refresh = st.columns([2, 1], gap="medium")

    with col_date:
        query_date = st.date_input(
            "📅 選擇欲對帳之日期：",
            value=date.today(),
            help="點選日曆圖示可切換查詢今天或預訂日期的收款狀態",
            key="query_date_picker",
        )
        query_date_str = query_date.strftime("%Y-%m-%d")

    with col_refresh:
        st.write(" ")
        st.write(" ")
        if st.button("🔄 即時同步最新收款狀態", use_container_width=True):
            st.rerun()

    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT id, user_name, store_name, time, items, total, note, is_paid
        FROM orders
        WHERE time LIKE ?
        ORDER BY id DESC
    """,
        (f"{query_date_str}%",),
    )
    rows = [dict(r) for r in c.fetchall()]
    conn.close()

    total_revenue = sum(r["total"] for r in rows) if rows else 0
    total_paid = sum(r["total"] for r in rows if r["is_paid"] == 1) if rows else 0
    total_unpaid = total_revenue - total_paid
    paid_count = sum(1 for r in rows if r["is_paid"] == 1)
    total_orders_count = len(rows)

    # ==========================================
    # 收款對帳儀表板 (已收、未收、應收總計)
    # ==========================================
    with st.container(border=True):
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric(label=f"【{query_date_str}】應收總額", value=f"NT$ {total_revenue}")
        with m2:
            st.metric(label="✅ 已收到金額", value=f"NT$ {total_paid}", delta=f"{paid_count} 筆已付")
        with m3:
            st.metric(label="⏳ 尚未收齊金額", value=f"NT$ {total_unpaid}", delta=f"{total_orders_count - paid_count} 筆未付", delta_color="inverse")
        with m4:
            collect_rate = f"{(total_paid / total_revenue * 100):.1f}%" if total_revenue > 0 else "100%"
            st.metric(label="📈 收款達成率", value=collect_rate)

    st.divider()

    if rows:
        col_t_title, col_btn = st.columns([3, 2])
        with col_t_title:
            st.markdown(f"#### 📋 {query_date_str} 訂單收費列表 (支援快速點選標記)")

        with col_btn:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(
                [
                    "訂單編號",
                    "人員姓名",
                    "店家名稱",
                    "下單時間",
                    "點餐明細",
                    "金額 (NTD)",
                    "備註",
                    "付款狀態",
                ]
            )
            for r in rows:
                pay_str = "已付款" if r.get("is_paid", 0) == 1 else "未付款"
                writer.writerow(
                    [
                        r["id"],
                        r["user_name"],
                        r["store_name"],
                        r["time"],
                        r["items"],
                        r["total"],
                        r["note"],
                        pay_str,
                    ]
                )
            writer.writerow([])
            writer.writerow(
                ["", "", "", "", f"{query_date_str} 中餐總金額合計", total_revenue, f"已收: {total_paid} / 未收: {total_unpaid}", ""]
            )

            csv_bytes = ("\ufeff" + output.getvalue()).encode("utf-8")
            st.download_button(
                label=f"📥 匯出【{query_date_str}】對帳 CSV 報表",
                data=csv_bytes,
                file_name=f"lunch_orders_{query_date_str}.csv",
                mime="text/csv",
                use_container_width=True,
                type="primary",
            )

        all_user_names = [u["name"] for u in get_all_users()]

        # 逐筆訂單明細與收款切換卡片
        for r in rows:
            is_paid = r.get("is_paid", 0) == 1
            status_html = (
                "<span class='status-paid'>✅ 已付款</span>"
                if is_paid
                else "<span class='status-unpaid'>⏳ 待收款</span>"
            )

            with st.container(border=True):
                c_info, c_action = st.columns([3, 1])

                with c_info:
                    st.markdown(
                        f"**單號 #{r['id']} ｜ 👤 {r['user_name']} ｜ 🏪 {r['store_name']} ｜ 金額：<span style='color:#dc2626; font-weight:bold;'>NT$ {r['total']}</span> ｜ {status_html}**",
                        unsafe_allow_html=True,
                    )
                    st.caption(f"餐點明細：{r['items']}")
                    if r.get("note"):
                        st.caption(f"備註：{r['note']}")
                    st.caption(f"下單時間：{r['time']}")

                with c_action:
                    # 一鍵切換付款狀態按鈕
                    btn_text = "標記為【未付款】" if is_paid else "💰 標記為【已付款】"
                    btn_type = "secondary" if is_paid else "primary"
                    if st.button(btn_text, key=f"pay_toggle_{r['id']}", use_container_width=True, type=btn_type):
                        toggle_payment_status(r["id"], r.get("is_paid", 0))
                        st.rerun()

                # 提供詳細修改折疊區塊
                with st.expander("✏️ 修改此筆訂單明細內容 / 刪除"):
                    with st.form(f"edit_order_form_{r['id']}"):
                        oc1, oc2 = st.columns([1, 1])
                        with oc1:
                            default_user_idx = (
                                all_user_names.index(r["user_name"])
                                if r["user_name"] in all_user_names
                                else 0
                            )
                            edit_order_user = st.selectbox(
                                "點餐人員：",
                                options=all_user_names if all_user_names else [r["user_name"]],
                                index=default_user_idx,
                                key=f"eou_{r['id']}",
                            )
                            edit_order_total = st.number_input(
                                "訂單金額 (NTD)：",
                                min_value=0,
                                step=5,
                                value=r["total"],
                                key=f"eot_{r['id']}",
                            )
                            edit_paid_status = st.selectbox(
                                "付款狀態：",
                                options=[0, 1],
                                format_func=lambda x: "已付款" if x == 1 else "未付款",
                                index=1 if is_paid else 0,
                                key=f"eop_{r['id']}",
                            )
                        with oc2:
                            edit_order_items = st.text_input(
                                "點餐明細內容：",
                                value=r["items"],
                                key=f"eoi_{r['id']}",
                            )
                            edit_order_note = st.text_input(
                                "需求備註：",
                                value=r["note"] if r["note"] else "",
                                key=f"eon_{r['id']}",
                            )

                        btn_save_order, _ = st.columns([1, 2])
                        with btn_save_order:
                            if st.form_submit_button("💾 儲存修改內容", type="primary", use_container_width=True):
                                update_order_item(
                                    r["id"],
                                    edit_order_user,
                                    edit_order_items.strip(),
                                    edit_order_total,
                                    edit_order_note.strip(),
                                    edit_paid_status,
                                )
                                st.success(f"訂單 #{r['id']} 修改完成！")
                                st.rerun()

                    if st.button("❌ 刪除此筆訂單", key=f"del_order_{r['id']}", type="secondary"):
                        delete_order_item(r["id"])
                        st.warning(f"訂單 #{r['id']} 已成功刪除！")
                        st.rerun()

    else:
        st.info(f"💡 【{query_date_str}】查無任何中餐點單紀錄。")

# ------------------------------------------
# 分頁 3: 人員名單管理
# ------------------------------------------
with main_tab3:
    st.subheader("👥 人員名單與中餐消費限額管理")
    col_u_add, col_u_list = st.columns([1, 1], gap="large")

    with col_u_add:
        st.markdown("**➕ 新增人員姓名與每日中餐上限**")
        with st.form("add_user_form", clear_on_submit=True):
            new_u_name = st.text_input("人員姓名：", placeholder="例如：林專員")
            new_u_limit = st.number_input(
                "每日中餐金額上限 (NTD，填 0 代表不限額)：",
                min_value=0,
                step=10,
                value=100,
            )
            if st.form_submit_button("新增 / 更新人員"):
                if new_u_name.strip():
                    conn = get_db_connection()
                    c = conn.cursor()
                    c.execute(
                        """
                        INSERT INTO users (name, daily_limit)
                        VALUES (?, ?)
                        ON CONFLICT(name) DO UPDATE SET daily_limit = excluded.daily_limit
                    """,
                        (new_u_name.strip(), new_u_limit),
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"已儲存人員【{new_u_name.strip()}】！")
                    st.rerun()
                else:
                    st.error("姓名不可為空白！")

    with col_u_list:
        st.markdown("**現有人員名單：**")
        users = get_all_users()
        for u in users:
            c1, c2, c3 = st.columns([3, 2, 1])
            c1.write(f"👤 **{u['name']}**")
            c2.write(f"每日限額：NT$ {u['daily_limit']}" if u['daily_limit'] > 0 else "無限制")
            if c3.button("刪除", key=f"del_user_{u['name']}"):
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("DELETE FROM users WHERE name = ?", (u['name'],))
                conn.commit()
                conn.close()
                st.rerun()

# ------------------------------------------
# 分頁 4: 店家與菜單維護 (含備份與還原功能)
# ------------------------------------------
with main_tab4:
    st.subheader("🏪 店家管理與中餐菜單維護 (含圖片設定)")
    col_s_add, col_s_manage = st.columns([1, 2], gap="large")

    with col_s_add:
        st.markdown("**➕ 建立新店家**")
        with st.form("add_store_form", clear_on_submit=True):
            new_store_name = st.text_input("店家名稱：", placeholder="例如：古早味麵食")
            if st.form_submit_button("新增店家"):
                if new_store_name.strip():
                    try:
                        conn = get_db_connection()
                        c = conn.cursor()
                        c.execute(
                            "INSERT INTO stores (name) VALUES (?)",
                            (new_store_name.strip(),),
                        )
                        conn.commit()
                        conn.close()
                        st.success(f"已新增店家：{new_store_name}")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("店家名稱已存在！")
                else:
                    st.error("名稱不可為空白！")

    with col_s_manage:
        st.markdown("**🛠️ 店家清單修正與刪除**")
        stores_data = get_all_stores()
        if not stores_data:
            st.info("尚未建立任何店家。")
        else:
            for s in stores_data:
                s_id, s_name = s["id"], s["name"]
                with st.expander(f"🏪 {s_name} (編輯名稱 / 刪除店家)"):
                    c_edit, c_del = st.columns([3, 1])
                    with c_edit:
                        new_name_input = st.text_input(
                            f"修改名稱：", value=s_name, key=f"ren_{s_id}"
                        )
                        if st.button("💾 儲存修改", key=f"btn_ren_{s_id}"):
                            if new_name_input.strip() and new_name_input.strip() != s_name:
                                ok, msg = update_store_name(s_name, new_name_input.strip())
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                    with c_del:
                        st.write(" ")
                        st.write(" ")
                        if st.button("🗑️ 刪除", key=f"btn_del_{s_id}"):
                            delete_store(s_name)
                            st.warning(f"已刪除【{s_name}】！")
                            st.rerun()

    st.divider()

    col_d_add, col_d_list = st.columns([1, 2], gap="large")
    current_stores = [s["name"] for s in get_all_stores()]

    with col_d_add:
        st.markdown("**➕ 新增餐點品項 (圖片選填)**")
        if not current_stores:
            st.caption("請先在上方建立店家。")
        else:
            with st.form("add_dish_form", clear_on_submit=True):
                target_store = st.selectbox("選擇所屬店家：", current_stores)
                dish_category = st.text_input("品項分類：", value="主食", placeholder="例如：麵食類、飯類、湯品、飲料")
                dish_name = st.text_input("餐點名稱：", placeholder="例如：三寶牛肉麵")
                
                c_p1, c_p2 = st.columns(2)
                with c_p1:
                    dish_price = st.number_input("小碗/基礎價格 (NTD)：", min_value=0, step=5, value=70)
                with c_p2:
                    dish_price_large = st.number_input("大碗價格 (無大碗填 0)：", min_value=0, step=5, value=85)

                dish_options = st.text_input(
                    "可選麵類 (選填，以逗號分隔)：",
                    placeholder="例如：拉麵,陽春麵,細麵",
                )

                c_e1, c_e2 = st.columns(2)
                with c_e1:
                    dish_extra_type = st.text_input(
                        "加量類型 (選填，以逗號分隔)：",
                        placeholder="例如：加麵,加飯",
                    )
                with c_e2:
                    dish_extra_price = st.number_input(
                        "加量加價 (元，免費填 0)：", min_value=0, step=5, value=10
                    )

                dish_image_url = st.text_input(
                    "餐點圖片網址 (選填，沒放圖片就不會顯示)：",
                    placeholder="例如：https://example.com/food.jpg (留白則不顯示圖片)",
                )

                if st.form_submit_button("＋ 上架餐點"):
                    if dish_name.strip():
                        conn = get_db_connection()
                        c = conn.cursor()
                        c.execute(
                            """
                            INSERT INTO menu (store_name, category, name, price, price_large, options, extra_type, extra_price, image_url) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                target_store,
                                dish_category.strip() if dish_category.strip() else "主食",
                                dish_name.strip(),
                                dish_price,
                                dish_price_large,
                                dish_options.strip(),
                                dish_extra_type.strip(),
                                dish_extra_price,
                                dish_image_url.strip(),
                            ),
                        )
                        conn.commit()
                        conn.close()
                        st.success(f"已新增至【{target_store}】：{dish_name}")
                        st.rerun()
                    else:
                        st.error("餐點名稱不可為空白！")

    with col_d_list:
        st.markdown("**📋 菜單檢視、圖片與品項編輯**")
        if current_stores:
            admin_store_tabs = st.tabs([f"📋 {s}" for s in current_stores])
            for idx, s in enumerate(current_stores):
                with admin_store_tabs[idx]:
                    items = get_menu_by_store(s)
                    if not items:
                        st.caption("尚無餐點。")
                    for it in items:
                        with st.expander(f"🍴 [{it['category']}] {it['name']} - NT$ {it['price']}{' / 大 NT$ ' + str(it['price_large']) if it['price_large'] > 0 else ''}"):
                            with st.form(f"edit_dish_form_{it['id']}"):
                                ec1, ec2 = st.columns(2)
                                with ec1:
                                    edit_cat = st.text_input("分類：", value=it["category"], key=f"ecat_{it['id']}")
                                    edit_name = st.text_input("名稱：", value=it["name"], key=f"ename_{it['id']}")
                                    edit_opt = st.text_input("麵類選項：", value=it["options"] or "", key=f"eopt_{it['id']}")
                                    edit_img = st.text_input("圖片網址 (留白則不顯示圖片)：", value=it["image_url"] or "", key=f"eimg_{it['id']}")
                                with ec2:
                                    edit_p = st.number_input("小碗價格：", min_value=0, step=5, value=it["price"], key=f"ep_{it['id']}")
                                    edit_pl = st.number_input("大碗價格 (無則填 0)：", min_value=0, step=5, value=it["price_large"], key=f"epl_{it['id']}")
                                    edit_et = st.text_input("加量類型：", value=it["extra_type"] or "", key=f"eet_{it['id']}")
                                    edit_ep = st.number_input("加量加價：", min_value=0, step=5, value=it["extra_price"], key=f"eep_{it['id']}")

                                cur_img = (it.get("image_url") or "").strip()
                                if cur_img:
                                    st.caption("當前餐點圖片預覽：")
                                    try:
                                        st.image(cur_img, width=150)
                                    except Exception:
                                        st.caption("⚠️ 圖片網址無效無法載入。")
                                else:
                                    st.caption("ℹ️ 目前無設定圖片（前台點餐將直接不顯示圖片區塊）。")

                                btn_c1, btn_c2 = st.columns([2, 1])
                                with btn_c1:
                                    if st.form_submit_button("💾 儲存修改", type="primary", use_container_width=True):
                                        if edit_name.strip():
                                            update_menu_item(
                                                it["id"],
                                                edit_cat.strip() if edit_cat.strip() else "主食",
                                                edit_name.strip(),
                                                edit_p,
                                                edit_pl,
                                                edit_opt.strip(),
                                                edit_et.strip(),
                                                edit_ep,
                                                edit_img.strip(),
                                            )
                                            st.success(f"【{edit_name}】已成功更新！")
                                            st.rerun()
                                        else:
                                            st.error("餐點名稱不可為空白！")

                            if st.button("🗑️ 刪除此餐點", key=f"del_menu_{it['id']}", type="secondary"):
                                conn = get_db_connection()
                                c = conn.cursor()
                                c.execute("DELETE FROM menu WHERE id = ?", (it["id"],))
                                conn.commit()
                                conn.close()
                                st.warning(f"已刪除【{it['name']}】！")
                                st.rerun()

    st.divider()
    st.markdown("### 📦 **店家與菜單永久備份與一鍵還原**")
    st.caption("無論系統重新整理、重開伺服器或重新佈署，下載備份後皆可隨時一鍵完整恢復！")
    
    col_bak1, col_bak2 = st.columns(2, gap="large")
    with col_bak1:
        st.markdown("**1. 匯出下載菜單備份**")
        menu_backup_json = export_menu_backup()
        st.download_button(
            label="📥 下載店家與菜單備份檔案 (JSON)",
            data=menu_backup_json.encode("utf-8"),
            file_name="menu_backup.json",
            mime="application/json",
            use_container_width=True,
            type="primary",
        )

    with col_bak2:
        st.markdown("**2. 上傳還原菜單備份**")
        uploaded_backup = st.file_uploader(
            "上傳 menu_backup.json 檔案進行還原：", type=["json"], key="menu_uploader"
        )
        if uploaded_backup is not None:
            if st.button("🔄 立即還原店家與菜單", use_container_width=True):
                content = uploaded_backup.getvalue().decode("utf-8")
                ok, msg = import_menu_backup(content)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
