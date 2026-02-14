import streamlit as st
from supabase import ClientOptions, create_client, Client
import streamlit.components.v1 as components
import time
from datetime import datetime

# --- КОНФИГУРАЦИЯ ---
try:
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
    WEDDING_CODE = st.secrets["supabase"]["wedding_code"]
except:
    st.error("Не настроены секреты в .streamlit/secrets.toml")
    st.stop()

# Инициализация клиента
@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY,
        options=ClientOptions(
            postgrest_client_timeout=60,
            storage_client_timeout=60,
            schema="public",
        ))

supabase: Client = init_connection()

# --- НОВЫЙ ДИЗАЙН (CSS) ---
def local_css():
    st.markdown("""
    <style>
    /* 1. Подключение шрифтов Google */
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600&family=Great+Vibes&family=Montserrat:wght@300;400&display=swap');

    /* 2. Основной фон приложения (Бежевый/Кремовый) */
    .stApp {
        background-color: #F7F5F0;
        background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png"); /* Текстура бумаги */
    }

    /* 3. Типографика */
    h1 {
        font-family: 'Great Vibes', cursive !important; /* Шрифт для имен */
        color: #8B7E66 !important; /* Золотисто-коричневый */
        font-size: 3.5rem !important;
        font-weight: 400 !important;
        text-align: center;
        padding-bottom: 0px;
        line-height: 1.2;
    }

    h2, h3 {
        font-family: 'Cormorant Garamond', serif !important;
        color: #5E503F !important; /* Темно-коричневый */
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    p, div, label, span {
        font-family: 'Montserrat', sans-serif;
        color: #5E503F;
    }

    /* 4. Стилизация кнопок */
    .stButton>button {
        background-color: #8B7E66;
        color: white;
        border-radius: 30px; /* Закругленные кнопки */
        border: 1px solid #8B7E66;
        font-family: 'Cormorant Garamond', serif;
        text-transform: uppercase;
        letter-spacing: 1px;
        padding: 10px 25px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #5E503F;
        border-color: #5E503F;
        color: #FFF;
    }

    /* 5. Поля ввода */
    .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.6);
        border: 1px solid #D6CFC7;
        border-radius: 10px;
        color: #5E503F;
    }

    /* 6. Карточки/Табы */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 20px;
        color: #8B7E66;
        font-family: 'Cormorant Garamond', serif;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: white !important;
        color: #5E503F !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }

    /* 7. Декоративные элементы */
    .divider-img {
        display: block;
        margin-left: auto;
        margin-right: auto;
        width: 150px;
        opacity: 0.8;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    
    .intro-image {
        width: 200px;
        display: block;
        margin: 0 auto 20px auto;
    }

    </style>
    """, unsafe_allow_html=True)

# --- ЛОГИКА АУТЕНТИФИКАЦИИ (БЕЗ ИЗМЕНЕНИЙ) ---

def sign_up(email, password, name):
    try:
        res = supabase.auth.sign_up({
            "email": email, "password": password,
            "options": {"data": {"full_name": name}}
        })
        if res.user: return True, "Регистрация успешна!"
        if res.user and not res.user.identities: return False, "Пользователь уже существует."
    except Exception as e: return False, str(e)
    return False, "Ошибка"

def sign_in(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.user:
            st.session_state['user'] = res.user
            st.session_state['session'] = res.session
            return True
    except Exception as e: st.error(f"Ошибка: {e}")
    return False

def send_otp(email):
    try:
        supabase.auth.sign_in_with_otp({"email": email})
        return True, "Код отправлен!"
    except Exception as e: return False, str(e)

def verify_otp_login(email, token):
    try:
        res = supabase.auth.verify_otp({"email": email, "token": token, "type": "email"})
        if res.user:
            st.session_state['user'] = res.user
            st.session_state['session'] = res.session
            return True, "Успех!"
    except Exception as e: return False, str(e)
    return False, "Ошибка"

def update_rsvp(status, food):
    try:
        supabase.table("guests").update({"attendance_status": status, "food_preference": food}).eq("id", st.session_state['user'].id).execute()
        st.success("Ответ сохранен!")
    except Exception as e: st.error(f"Ошибка: {e}")

def change_password(new_password):
    try:
        supabase.auth.update_user({"password": new_password})
        st.success("Пароль изменен!")
    except Exception as e: st.error(f"Ошибка: {e}")

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ИНТЕРФЕЙСА ---

def display_countdown():
    # Дата свадьбы: 8 Августа 2026, 17:00
    wedding_date = datetime(2026, 8, 8, 17, 0, 0)
    now = datetime.now()
    delta = wedding_date - now
    
    if delta.days > 0:
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds // 60) % 60
        
        st.markdown(f"""
        <div style="display: flex; justify-content: center; gap: 20px; margin: 30px 0; color: #5E503F;">
            <div style="text-align: center;">
                <span style="font-size: 2rem; font-family: 'Cormorant Garamond'; font-weight: bold;">{days}</span><br>
                <span style="font-size: 0.8rem; text-transform: uppercase;">Дней</span>
            </div>
            <div style="text-align: center;">
                <span style="font-size: 2rem; font-family: 'Cormorant Garamond'; font-weight: bold;">{hours}</span><br>
                <span style="font-size: 0.8rem; text-transform: uppercase;">Часов</span>
            </div>
             <div style="text-align: center;">
                <span style="font-size: 2rem; font-family: 'Cormorant Garamond'; font-weight: bold;">{minutes}</span><br>
                <span style="font-size: 0.8rem; text-transform: uppercase;">Минут</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- MAIN APP ---

def main():
    st.set_page_config(page_title="Малика & Бейбарыс", page_icon="🤍")
    local_css()

    # --- ЗАГОЛОВОК (Header) ---
    # Бисмилля (картинка)
    st.markdown('<img src="https://www.brides.com/thmb/fJSfAbT8DxJs4dW79wcWZEQZgJs=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/must-take-wedding-photos-bride-groom-walk-clary-prfeiffer-photography-0723-primary-b4221bcb1a2b43e6b0820a8c3e3bce52.jpg" class="intro-image">', unsafe_allow_html=True)
    
    st.markdown("<h3>Приглашаем на свадьбу</h3>", unsafe_allow_html=True)
    st.title("Малика & Бейбарыс")
    
    # Дата и Декоративная линия
    st.markdown("<p style='text-align: center; font-size: 1.2rem; letter-spacing: 3px;'>08 | 08 | 2026</p>", unsafe_allow_html=True)
    st.markdown('<img src="https://designer.kz/wp-content/uploads/2023/05/IMG_2415w.jpg" class="divider-img">', unsafe_allow_html=True)

    # --- ТАЙМЕР ---
    display_countdown()

    # Проверка сессии
    if 'user' not in st.session_state: st.session_state['user'] = None

    # --- КОНТЕЙНЕР АВТОРИЗАЦИИ / КОНТЕНТА ---
    
    if st.session_state['user'] is None:
        st.markdown("<div style='background-color: rgba(255,255,255,0.7); padding: 30px; border-radius: 15px; margin-top: 20px;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='margin-bottom: 20px;'>Вход для гостей</h3>", unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["Войти", "Регистрация", "Код?"])

        with tab1:
            email = st.text_input("Email", key="l_email")
            pwd = st.text_input("Пароль", type="password", key="l_pass")
            if st.button("Войти", use_container_width=True):
                if sign_in(email, pwd): st.rerun()

        with tab2:
            st.caption("Введите код с приглашения")
            r_name = st.text_input("Имя и Фамилия")
            r_email = st.text_input("Email", key="r_email")
            r_pass = st.text_input("Пароль", type="password", key="r_pass")
            r_code = st.text_input("Код свадьбы", type="password")
            if st.button("Создать аккаунт", use_container_width=True):
                if r_code == WEDDING_CODE:
                    ok, msg = sign_up(r_email, r_pass, r_name)
                    if ok: st.success(msg)
                    else: st.error(msg)
                else: st.error("Неверный код")

        with tab3:
            # Восстановление
            otp_email = st.text_input("Email", key="o_email")
            if st.button("Получить код входа"):
                ok, msg = send_otp(otp_email)
                if ok: st.success(msg)
            
            otp_code = st.text_input("Код из письма", key="o_code")
            if st.button("Войти по коду"):
                ok, msg = verify_otp_login(otp_email, otp_code)
                if ok: st.rerun()
                else: st.error(msg)
        
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        # --- ПОЛЬЗОВАТЕЛЬ АВТОРИЗОВАН ---
        try:
            u_id = st.session_state['user'].id
            data = supabase.table("guests").select("*").eq("id", u_id).execute().data[0]
        except: data = {}

        st.markdown(f"<p style='text-align: center; margin-top: 20px;'>Добро пожаловать, {data.get('full_name', 'Гость')}!</p>", unsafe_allow_html=True)

        # Меню вкладок
        m1, m2, m3, m4 = st.tabs(["Программа", "Карта", "Анкета (RSVP)", "Профиль"])

        with m1:
            st.markdown("""
            <div style="text-align: center; padding: 20px;">
                <p><b>14:00</b> — Сбор гостей</p>
                <p><b>15:00</b> — Церемония бракосочетания</p>
                <p><b>17:00</b> — Праздничный банкет</p>
                <p><b>23:00</b> — Завершение вечера</p>
            </div>
            """, unsafe_allow_html=True)
            st.image("https://images.unsplash.com/photo-1519225421980-715cb0202128?auto=format&fit=crop&w=1000&q=80", use_container_width=True)

        with m2:
            st.markdown("<br>", unsafe_allow_html=True)
            # 2GIS Карта
            lat, lon = 42.923482, 71.419786
            static_url = f"https://static.maps.2gis.com/1.0?center={lon},{lat}&zoom=16&size=600,300"
            st.image(static_url, caption="Ресторан 'Счастье'")
            st.link_button("📍 Открыть навигатор (2GIS)", f"https://2gis.kz/taraz/firm/70000001100842703", type="primary", use_container_width=True)

        with m3:
            st.markdown("<div style='background-color: white; padding: 20px; border-radius: 10px;'>", unsafe_allow_html=True)
            st.write("Будете ли вы с нами?")
            status = st.selectbox("Ваш ответ:", ['Я приду', 'Не смогу', 'Думаю'], index=['Я приду', 'Не смогу', 'Думаю'].index(data.get('attendance_status', 'Думаю')))
            food = st.text_area("Аллергии / Пожелания", value=data.get('food_preference', ''))
            if st.button("Отправить ответ", use_container_width=True):
                update_rsvp(status, food)
                time.sleep(1)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with m4:
            with st.expander("Сменить пароль"):
                np = st.text_input("Новый пароль", type="password")
                if st.button("Сохранить"): change_password(np)
            
            if st.button("Выйти", type="secondary", use_container_width=True):
                supabase.auth.sign_out()
                st.session_state['user'] = None
                st.rerun()

if __name__ == "__main__":
    main()
