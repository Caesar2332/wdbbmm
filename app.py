import streamlit as st
from supabase import ClientOptions, create_client, Client
import streamlit.components.v1 as components
import time

# --- КОНФИГУРАЦИЯ ---
# В реальном проекте используйте st.secrets для ключей!
# Создайте файл .streamlit/secrets.toml с содержимым:
# [supabase]
# url = "ВАШ_SUPABASE_URL"
# key = "ВАШ_SUPABASE_ANON_KEY"
# wedding_code = "2026"

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
WEDDING_CODE = st.secrets["supabase"]["wedding_code"] # Простой код для верификации гостей


# Parameters
lat, lon = 42.923482 , 71.419786
zoom = 18
size = "600,450"

# Construct the URL
static_url = f"https://static.maps.2gis.com/1.0?center={lon},{lat}&zoom={zoom}&size={size}"

st.image(static_url, caption="Расположение места проведения свадьбы")

st.link_button("Открыть в 2GIS", url=f"https://2gis.kz/taraz/firm/70000001100842703?m=71.419786%2C42.923482%2F18", type="primary", use_container_width=True)    

# Инициализация клиента
@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY,
        options=ClientOptions(
            postgrest_client_timeout=60, # Ждать ответа базы до 60 секунд
            storage_client_timeout=60,
            schema="public",
        ))

supabase: Client = init_connection()

# --- CSS СТИЛИЗАЦИЯ (СВАДЕБНАЯ ТЕМА) ---
def local_css():
    st.markdown("""
    <style>
    .main {
        background-color: #fdfbf7;
        color: #4a4a4a;
    }
    h1 {
        font-family: 'Garamond', serif;
        color: #bfa05f;
        text-align: center;
        padding-bottom: 20px;
    }
    h2, h3 {
        font-family: 'Garamond', serif;
        color: #8c7b50;
    }
    .stButton>button {
        background-color: #bfa05f;
        color: white;
        border-radius: 10px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #a3864d;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        color: #155724;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ФУНКЦИИ АУТЕНТИФИКАЦИИ ---

def sign_up(email, password, name):
    # try:
        # Мы передаем 'data': {'full_name': name}
        # Supabase сохранит это в raw_user_meta_data, а наш SQL триггер заберет оттуда
        res = supabase.auth.sign_up({
            "email": email, 
            "password": password,
            "options": {
                "data": {"full_name": name}
            }
        })
        
        # Проверяем, создался ли пользователь
        if res.user:
            return True, "Регистрация успешна! Теперь войдите."
        
        # Если включено подтверждение email, user может быть создан, но сессии нет
        if res.user and res.user.identities and len(res.user.identities) == 0:
             return False, "Пользователь уже существует или требует подтверждения почты."

    # except Exception as e:
    #     return False, f"Ошибка: {str(e)}"
    
    # return False, "Неизвестная ошибка"

def sign_in(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.user:
            st.session_state['user'] = res.user
            st.session_state['session'] = res.session
            return True
    except Exception as e:
        st.error(f"Ошибка входа: {str(e)}")
    return False

def update_rsvp(status, food):
    user_id = st.session_state['user'].id
    try:
        supabase.table("guests").update({
            "attendance_status": status,
            "food_preference": food
        }).eq("id", user_id).execute()
        st.success("Ваш ответ сохранен!")
    except Exception as e:
        st.error(f"Ошибка сохранения: {e}")

def change_password(new_password):
    try:
        supabase.auth.update_user({"password": new_password})
        st.success("Пароль успешно изменен!")
    except Exception as e:
        st.error(f"Ошибка смены пароля: {e}")

# --- ИНТЕРФЕЙС ---

def main():
    st.set_page_config(page_title="Свадьба Малики & Бейбарыса", page_icon="💍")
    local_css()

    st.title("💍 Малика & Бейбарыс 💍")
    st.markdown("<h3 style='text-align: center;'>Приглашаем вас на нашу свадьбу!</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>8 Августа 2026 года • Тараз</p>", unsafe_allow_html=True)
    st.divider()

    # Проверка сессии
    if 'user' not in st.session_state:
        st.session_state['user'] = None

    # Если пользователь НЕ авторизован
    if st.session_state['user'] is None:
        tab1, tab2 = st.tabs(["Войти", "Регистрация"])

        with tab1:
            email_in = st.text_input("Email", key="login_email")
            pass_in = st.text_input("Пароль", type="password", key="login_pass")
            if st.button("Войти"):
                if sign_in(email_in, pass_in):
                    st.rerun()

        with tab2:
            st.info("Чтобы зарегистрироваться, введите код с пригласительного.")
            reg_name = st.text_input("Ваше Имя и Фамилия")
            reg_email = st.text_input("Email", key="reg_email")
            reg_pass = st.text_input("Придумайте пароль", type="password", key="reg_pass")
            reg_code = st.text_input("Секретный код свадьбы", type="password")

            if st.button("Зарегистрироваться"):
                if reg_code == WEDDING_CODE:
                    success, msg = sign_up(reg_email, reg_pass, reg_name)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.error("Неверный секретный код свадьбы!")

    # Если пользователь АВТОРИЗОВАН
    else:
        # Получаем данные гостя
        try:
            user_id = st.session_state['user'].id
            response = supabase.table("guests").select("*").eq("id", user_id).execute()
            guest_info = response.data[0] if response.data else {}
        except Exception:
            guest_info = {}

        st.markdown(f"### Привет, {guest_info.get('full_name', 'Гость')}!")
        
        menu_tab1, menu_tab2, menu_tab3 = st.tabs(["💌 Приглашение", "✍️ RSVP (Анкета)", "⚙️ Настройки"])

        with menu_tab1:
            st.image("https://images.unsplash.com/photo-1519741497674-611481863552?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80", caption="Ждем вас!")
            st.write("""
            Мы будем счастливы видеть вас в этот особенный день!
            
            **Программа:**
            * 14:00 - Сбор гостей
            * 15:00 - Церемония
            * 17:00 - Банкет
            
            **Адрес:** Усадьба "Счастье", ул. Лесная, д. 1.
            """)

        with menu_tab2:
            st.write("Пожалуйста, подтвердите ваше присутствие.")
            
            current_status = guest_info.get('attendance_status', 'Думаю')
            current_food = guest_info.get('food_preference', '')

            status_options = ['Я приду', 'Не смогу', 'Думаю']
            # Находим индекс для selectbox
            try:
                index_status = status_options.index(current_status)
            except:
                index_status = 2

            new_status = st.selectbox("Вы будете с нами?", status_options, index=index_status)
            new_food = st.text_area("Предпочтения в еде / Аллергии", value=current_food)

            if st.button("Сохранить ответ"):
                update_rsvp(new_status, new_food)
                time.sleep(1) # Даем время увидеть сообщение
                st.rerun()

        with menu_tab3:
            st.write("Управление аккаунтом")
            
            with st.expander("Сменить пароль"):
                st.write("Введите новый пароль ниже:")
                new_p = st.text_input("Новый пароль", type="password", key="new_p")
                conf_p = st.text_input("Подтвердите пароль", type="password", key="conf_p")
                
                if st.button("Изменить пароль"):
                    if new_p == conf_p and len(new_p) > 5:
                        change_password(new_p)
                    else:
                        st.error("Пароли не совпадают или слишком короткие.")

            if st.button("Выйти из системы"):
                supabase.auth.sign_out()
                st.session_state['user'] = None
                st.rerun()

if __name__ == "__main__":
    main()