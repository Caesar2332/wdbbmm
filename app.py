import streamlit as st
from supabase import ClientOptions, create_client, Client
import streamlit.components.v1 as components
import time
from streamlit_lottie import st_lottie
from datetime import datetime
import requests

# --- КОНФИГУРАЦИЯ ---
try:
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
    WEDDING_CODE = st.secrets["supabase"]["wedding_code"]
except:
    st.error("Secrets not found in .streamlit/secrets.toml")
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

# --- СЛОВАРЬ ПЕРЕВОДОВ (DICTIONARY) ---
TRANS = {
    "ru": {
        "title": "Малика & Бейбарыс",
        "header": "Приглашаем на свадьбу",
        "date_str": "08 | 08 | 2026",
        "days": "Дней", "hours": "Часов", "mins": "Минут",
        "login_header": "Вход для гостей",
        "tab_login": "Войти", "tab_reg": "Регистрация", "tab_code": "Код?",
        "email": "Email", "pass": "Пароль", "name": "Имя и Фамилия", "code": "Код свадьбы",
        "btn_login": "Войти", "btn_reg": "Создать аккаунт", "btn_get_code": "Получить код", "btn_enter_code": "Войти по коду",
        "hint_reg": "Введите код с приглашения", "hint_otp": "Email для восстановления", "hint_otp_code": "Код из письма",
        "welcome": "Добро пожаловать",
        "menu_prog": "Программа", "menu_map": "Карта", "menu_rsvp": "Анкета (RSVP)", "menu_prof": "Профиль",
        "prog_1": "Сбор гостей", "prog_2": "Церемония бракосочетания", "prog_3": "Праздничный банкет", "prog_4": "Завершение вечера",
        "rsvp_q": "Будете ли вы с нами?",
        "rsvp_food": "Аллергии / Пожелания",
        "btn_save": "Отправить ответ",
        "btn_logout": "Выйти",
        "change_pass": "Сменить пароль", "new_pass": "Новый пароль", "btn_save_pass": "Сохранить",
        "success_reg": "Регистрация успешна!", "err_user_exist": "Пользователь уже существует",
        "success_otp": "Код отправлен!", "success_login": "Успешный вход!", "success_saved": "Ответ сохранен!",
        "err_code": "Неверный код свадьбы",
        # Опции RSVP (Важно: порядок должен совпадать во всех языках!)
        "rsvp_opts": ['Я приду', 'Не смогу', 'Думаю'] 
    },
    "kz": {
        "title": "Малика & Бейбарыс",
        "header": "Үйлену тойына шақырамыз",
        "date_str": "08 | 08 | 2026",
        "days": "Күн", "hours": "Сағат", "mins": "Минут",
        "login_header": "Қонақтарға кіру",
        "tab_login": "Кіру", "tab_reg": "Тіркелу", "tab_code": "Код?",
        "email": "Email", "pass": "Құпия сөз", "name": "Аты-жөні", "code": "Той коды",
        "btn_login": "Кіру", "btn_reg": "Тіркелу", "btn_get_code": "Код алу", "btn_enter_code": "Кодпен кіру",
        "hint_reg": "Шақырудағы кодты енгізіңіз", "hint_otp": "Email енгізіңіз", "hint_otp_code": "Хаттағы код",
        "welcome": "Қош келдіңіз",
        "menu_prog": "Бағдарлама", "menu_map": "Карта", "menu_rsvp": "Жауап (RSVP)", "menu_prof": "Профиль",
        "prog_1": "Қонақтардың жиналуы", "prog_2": "Неке қию рәсімі", "prog_3": "Мерекелік банкет", "prog_4": "Кештің аяқталуы",
        "rsvp_q": "Сіз келесіз бе?",
        "rsvp_food": "Аллергия / Тілектер",
        "btn_save": "Жіберу",
        "btn_logout": "Шығу",
        "change_pass": "Құпия сөзді өзгерту", "new_pass": "Жаңа құпия сөз", "btn_save_pass": "Сақтау",
        "success_reg": "Тіркелу сәтті өтті!", "err_user_exist": "Бұл қолданушы тіркелген",
        "success_otp": "Код жіберілді!", "success_login": "Сәтті кірдіңіз!", "success_saved": "Жауап сақталды!",
        "err_code": "Той коды қате",
        "rsvp_opts": ['Мен келемін', 'Келе алмаймын', 'Ойланудамын']
    },
    "en": {
        "title": "Malika & Beibarys",
        "header": "Wedding Invitation",
        "date_str": "August 08, 2026",
        "days": "Days", "hours": "Hours", "mins": "Minutes",
        "login_header": "Guest Login",
        "tab_login": "Log In", "tab_reg": "Register", "tab_code": "Code?",
        "email": "Email", "pass": "Password", "name": "Full Name", "code": "Wedding Code",
        "btn_login": "Log In", "btn_reg": "Sign Up", "btn_get_code": "Get Code", "btn_enter_code": "Enter with Code",
        "hint_reg": "Enter code from invitation", "hint_otp": "Recovery Email", "hint_otp_code": "Code from email",
        "welcome": "Welcome",
        "menu_prog": "Program", "menu_map": "Map", "menu_rsvp": "RSVP", "menu_prof": "Profile",
        "prog_1": "Gathering", "prog_2": "Wedding Ceremony", "prog_3": "Banquet", "prog_4": "Closing",
        "rsvp_q": "Will you attend?",
        "rsvp_food": "Allergies / Preferences",
        "btn_save": "Submit",
        "btn_logout": "Log Out",
        "change_pass": "Change Password", "new_pass": "New Password", "btn_save_pass": "Save",
        "success_reg": "Registration successful!", "err_user_exist": "User already exists",
        "success_otp": "Code sent!", "success_login": "Login successful!", "success_saved": "Answer saved!",
        "err_code": "Invalid wedding code",
        "rsvp_opts": ['I will come', 'I cannot come', 'Thinking']
    }
}

def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200: return None
    return r.json()

# --- НОВЫЙ ДИЗАЙН (CSS) ---
def local_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600&family=Great+Vibes&family=Montserrat:wght@300;400&display=swap');

    .stApp {
        background-color: #F7F5F0;
        background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png");
    }

    h1 {
        font-family: 'Great Vibes', cursive !important;
        color: #8B7E66 !important;
        font-size: 3.5rem !important;
        font-weight: 400 !important;
        text-align: center;
        padding-bottom: 0px;
        line-height: 1.2;
    }

    h2, h3, h4, h5 {
        font-family: 'Cormorant Garamond', serif !important;
        color: #5E503F !important;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    p, div, label, span, input, textarea {
        font-family: 'Montserrat', sans-serif;
        color: #5E503F;
    }

    .stButton>button {
        background-color: #8B7E66;
        color: white;
        border-radius: 30px;
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

    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: rgba(255, 255, 255, 0.6);
        border: 1px solid #D6CFC7;
        border-radius: 10px;
        color: #5E503F;
    }

    /* Настройка Tabs */
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
        width: 100%;
        max-width: 400px;
        border-radius: 10px;
        display: block;
        margin: 0 auto 20px auto;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- ЛОГИКА АУТЕНТИФИКАЦИИ ---

def sign_up(email, password, name, lang):
    try:
        res = supabase.auth.sign_up({
            "email": email, "password": password,
            "options": {"data": {"full_name": name}}
        })
        if res.user: return True, TRANS[lang]["success_reg"]
        if res.user and not res.user.identities: return False, TRANS[lang]["err_user_exist"]
    except Exception as e: return False, str(e)
    return False, "Error"

def sign_in(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.user:
            st.session_state['user'] = res.user
            st.session_state['session'] = res.session
            return True
    except Exception as e: st.error(f"Error: {e}")
    return False

def send_otp(email, lang):
    try:
        supabase.auth.sign_in_with_otp({"email": email})
        return True, TRANS[lang]["success_otp"]
    except Exception as e: return False, str(e)

def verify_otp_login(email, token, lang):
    try:
        res = supabase.auth.verify_otp({"email": email, "token": token, "type": "email"})
        if res.user:
            st.session_state['user'] = res.user
            st.session_state['session'] = res.session
            return True, TRANS[lang]["success_login"]
    except Exception as e: return False, str(e)
    return False, "Error"

def update_rsvp(status, food, lang):
    try:
        # ВАЖНО: Мы сохраняем в базу РУССКИЙ статус, потому что база ожидает именно его
        # Мы находим индекс выбранного ответа в текущем языке и берем соответствующий русский текст
        idx = TRANS[lang]["rsvp_opts"].index(status)
        db_status = TRANS["ru"]["rsvp_opts"][idx]
        
        supabase.table("guests").update({"attendance_status": db_status, "food_preference": food}).eq("id", st.session_state['user'].id).execute()
        st.success(TRANS[lang]["success_saved"])
    except Exception as e: st.error(f"Error: {e}")

def change_password(new_password, lang):
    try:
        supabase.auth.update_user({"password": new_password})
        st.success(TRANS[lang]["success_saved"])
    except Exception as e: st.error(f"Error: {e}")

# --- ТАЙМЕР ---

def display_countdown(lang):
    wedding_date = datetime(2026, 8, 8, 17, 0, 0)
    now = datetime.now()
    delta = wedding_date - now
    
    if delta.days > 0:
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds // 60) % 60
        
        t_days = TRANS[lang]["days"]
        t_hours = TRANS[lang]["hours"]
        t_mins = TRANS[lang]["mins"]
        
        st.markdown(f"""
        <div style="display: flex; justify-content: center; gap: 20px; margin: 30px 0; color: #5E503F;">
            <div style="text-align: center;">
                <span style="font-size: 2rem; font-family: 'Cormorant Garamond'; font-weight: bold;">{days}</span><br>
                <span style="font-size: 0.8rem; text-transform: uppercase;">{t_days}</span>
            </div>
            <div style="text-align: center;">
                <span style="font-size: 2rem; font-family: 'Cormorant Garamond'; font-weight: bold;">{hours}</span><br>
                <span style="font-size: 0.8rem; text-transform: uppercase;">{t_hours}</span>
            </div>
             <div style="text-align: center;">
                <span style="font-size: 2rem; font-family: 'Cormorant Garamond'; font-weight: bold;">{minutes}</span><br>
                <span style="font-size: 0.8rem; text-transform: uppercase;">{t_mins}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- MAIN APP ---

def main():
    st.set_page_config(page_title="Малика & Бейбарыс", page_icon="🤍")
    local_css()
    lottie_wedding = load_lottieurl("https://lottie.host/ddad6988-31e9-4738-9b02-7652f7c760f8/mD8u28PSqI.json") # Вставьте ваш URL
    # Отображаем
    st_lottie(
        lottie_wedding,
        speed=1,
        reverse=False,
        loop=True,
        quality="low", # "low" иногда помогает убрать артефакты фона
        height=300,
        width=300,
        key="wedding_anim"
    )
    # --- ВЫБОР ЯЗЫКА ---
    # Размещаем в углу или в начале
    col_l1, col_l2 = st.columns([8, 2])
    with col_l2:
        lang_code = st.selectbox("Language / Тіл", ["KZ", "RU", "EN"], label_visibility="collapsed")
        
    lang = lang_code.lower() # kz, ru, en

    # --- ЗАГОЛОВОК ---
    st.markdown('<img src="https://www.brides.com/thmb/fJSfAbT8DxJs4dW79wcWZEQZgJs=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/must-take-wedding-photos-bride-groom-walk-clary-prfeiffer-photography-0723-primary-b4221bcb1a2b43e6b0820a8c3e3bce52.jpg" class="intro-image">', unsafe_allow_html=True)
    
    st.markdown(f"<h3>{TRANS[lang]['header']}</h3>", unsafe_allow_html=True)
    st.title(TRANS[lang]['title'])
    
    st.markdown(f"<p style='text-align: center; font-size: 1.2rem; letter-spacing: 3px;'>{TRANS[lang]['date_str']}</p>", unsafe_allow_html=True)
    st.markdown('<img src="https://designer.kz/wp-content/uploads/2023/05/IMG_2415w.jpg" class="divider-img">', unsafe_allow_html=True)

    # --- ТАЙМЕР ---
    display_countdown(lang)

    # Проверка сессии
    if 'user' not in st.session_state: st.session_state['user'] = None

    # --- КОНТЕЙНЕР АВТОРИЗАЦИИ ---
    
    if st.session_state['user'] is None:
        st.markdown("<div style='background-color: rgba(255,255,255,0.7); padding: 30px; border-radius: 15px; margin-top: 20px;'>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='margin-bottom: 20px;'>{TRANS[lang]['login_header']}</h3>", unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs([TRANS[lang]['tab_login'], TRANS[lang]['tab_reg'], TRANS[lang]['tab_code']])

        with tab1:
            email = st.text_input(TRANS[lang]['email'], key="l_email")
            pwd = st.text_input(TRANS[lang]['pass'], type="password", key="l_pass")
            if st.button(TRANS[lang]['btn_login'], use_container_width=True):
                if sign_in(email, pwd): st.rerun()

        with tab2:
            st.caption(TRANS[lang]['hint_reg'])
            r_name = st.text_input(TRANS[lang]['name'])
            r_email = st.text_input(TRANS[lang]['email'], key="r_email")
            r_pass = st.text_input(TRANS[lang]['pass'], type="password", key="r_pass")
            r_code = st.text_input(TRANS[lang]['code'], type="password")
            if st.button(TRANS[lang]['btn_reg'], use_container_width=True):
                if r_code == WEDDING_CODE:
                    ok, msg = sign_up(r_email, r_pass, r_name, lang)
                    if ok: st.success(msg)
                    else: st.error(msg)
                else: st.error(TRANS[lang]['err_code'])

        with tab3:
            st.caption(TRANS[lang]['hint_otp'])
            otp_email = st.text_input(TRANS[lang]['email'], key="o_email")
            if st.button(TRANS[lang]['btn_get_code']):
                ok, msg = send_otp(otp_email, lang)
                if ok: st.success(msg)
            
            otp_code = st.text_input(TRANS[lang]['hint_otp_code'], key="o_code")
            if st.button(TRANS[lang]['btn_enter_code']):
                ok, msg = verify_otp_login(otp_email, otp_code, lang)
                if ok: st.rerun()
                else: st.error(msg)
        
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        # --- ПОЛЬЗОВАТЕЛЬ АВТОРИЗОВАН ---
        try:
            u_id = st.session_state['user'].id
            data = supabase.table("guests").select("*").eq("id", u_id).execute().data[0]
        except: data = {}

        st.markdown(f"<p style='text-align: center; margin-top: 20px;'>{TRANS[lang]['welcome']}, {data.get('full_name', 'Guest')}!</p>", unsafe_allow_html=True)

        m1, m2, m3, m4 = st.tabs([TRANS[lang]['menu_prog'], TRANS[lang]['menu_map'], TRANS[lang]['menu_rsvp'], TRANS[lang]['menu_prof']])

        with m1:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px;">
                <p><b>14:00</b> — {TRANS[lang]['prog_1']}</p>
                <p><b>15:00</b> — {TRANS[lang]['prog_2']}</p>
                <p><b>17:00</b> — {TRANS[lang]['prog_3']}</p>
                <p><b>23:00</b> — {TRANS[lang]['prog_4']}</p>
            </div>
            """, unsafe_allow_html=True)
            st.image("https://images.unsplash.com/photo-1519225421980-715cb0202128?auto=format&fit=crop&w=1000&q=80", use_container_width=True)

        with m2:
            st.markdown("<br>", unsafe_allow_html=True)
            lat, lon = 42.923482, 71.419786
            static_url = f"https://static.maps.2gis.com/1.0?center={lon},{lat}&zoom=16&size=600,300"
            st.image(static_url, caption="Restoraunt")
            st.link_button("📍 2GIS", f"https://2gis.kz/taraz/firm/70000001100842703", type="primary", use_container_width=True)

        with m3:
            st.markdown("<div style='background-color: white; padding: 20px; border-radius: 10px;'>", unsafe_allow_html=True)
            st.write(TRANS[lang]['rsvp_q'])
            
            # --- ХИТРАЯ ЛОГИКА ДЛЯ RSVP ---
            # 1. Получаем текущий статус из базы (он всегда на русском)
            current_db_status = data.get('attendance_status', 'Думаю')
            
            # 2. Находим его индекс (0, 1 или 2)
            try:
                status_index = TRANS['ru']['rsvp_opts'].index(current_db_status)
            except:
                status_index = 2
            
            # 3. Показываем опции на ВЫБРАННОМ языке
            display_options = TRANS[lang]['rsvp_opts']
            
            # 4. Выбор пользователя (текст на выбранном языке)
            status_selection = st.selectbox("", display_options, index=status_index)
            
            food = st.text_area(TRANS[lang]['rsvp_food'], value=data.get('food_preference', ''))
            
            if st.button(TRANS[lang]['btn_save'], use_container_width=True):
                update_rsvp(status_selection, food, lang)
                time.sleep(1)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with m4:
            with st.expander(TRANS[lang]['change_pass']):
                np = st.text_input(TRANS[lang]['new_pass'], type="password")
                if st.button(TRANS[lang]['btn_save_pass']): change_password(np, lang)
            
            if st.button(TRANS[lang]['btn_logout'], type="secondary", use_container_width=True):
                supabase.auth.sign_out()
                st.session_state['user'] = None
                st.rerun()

if __name__ == "__main__":
    main()