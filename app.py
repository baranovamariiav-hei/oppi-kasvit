import streamlit as st
import pandas as pd
import random
import zipfile
import io
import time
import os

# Настройка страницы
st.set_page_config(page_title="Kasvioppi", layout="centered")

# Ультра-компактный дизайн
st.markdown("""
    <style>
    /* Прячем лишние элементы Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    
    /* Контейнер для фото и подсказки */
    .image-container {
        position: relative;
        text-align: center;
        margin-bottom: 10px;
    }
    
    .main-img {
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        width: 100%;
        max-height: 50vh; /* Ограничение высоты фото */
        object-fit: cover;
    }
    
    /* Подсказка ПОВЕРХ картинки */
    .hint-overlay {
        position: absolute;
        bottom: 10px;
        left: 50%;
        transform: translateX(-50%);
        background-color: rgba(255, 249, 196, 0.9);
        color: #5d4037;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9em;
        width: 80%;
        border: 1px solid #fbc02d;
    }

    /* Кнопки в одну линию на мобильном */
    div[data-testid="column"] {
        flex: 1 !important;
        min-width: 0px !important;
        padding: 0 2px !important;
    }
    
    .stButton>button {
        font-size: 0.8em !important;
        height: 3em !important;
        padding: 0px !important;
        border-radius: 10px !important;
    }
    
    .stat-text { font-size: 0.9em; text-align: center; color: #666; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# Загрузка данных
def load_data_from_folder():
    excel_name = "kasvit.xlsx"
    zip_name = "kuvat.zip"
    if not os.path.exists(excel_name) or not os.path.exists(zip_name):
        return None
    try:
        df = pd.read_excel(excel_name)
        df.columns = [str(c).strip().upper() for c in df.columns]
        df['ID'] = df['ID'].astype(str).str.split('.').str[0].str.zfill(3)
        photos = {}
        with zipfile.ZipFile(zip_name) as z:
            for f_info in z.infolist():
                fname = f_info.filename.split('/')[-1]
                if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                    photos[fname[:3]] = f.read() if (f := z.open(f_info)) else None
        
        combined = []
        for _, row in df.iterrows():
            if row['ID'] in photos:
                combined.append({
                    'full_answer': f"{str(row['NIMI']).strip()} {str(row.get('LATINA', '')).strip()}".strip(),
                    'image': photos[row['ID']]
                })
        return combined
    except: return None

# Инициализация
if 'started' not in st.session_state:
    st.session_state.started = False
if 'data' not in st.session_state:
    st.session_state.data = load_data_from_folder()
    st.session_state.score = 0
    st.session_state.total = 0
    st.session_state.hint_letters = 0
    st.session_state.widget_key = 0
    if st.session_state.data:
        st.session_state.current_item = random.choice(st.session_state.data)

def next_question():
    st.session_state.current_item = random.choice(st.session_state.data)
    st.session_state.hint_letters = 0
    st.session_state.widget_key += 1

# --- ЭКРАН 1: ЗАСТАВКА ---
if not st.session_state.started:
    if os.path.exists("cover.jpg"):
        st.image("cover.jpg", use_container_width=True)
    elif os.path.exists("cover.png"):
        st.image("cover.png", use_container_width=True)
    
    st.write("") # Отступ
    if st.button("ALOITA HARJOITUS 🚀"):
        st.session_state.started = True
        st.rerun()

# --- ЭКРАН 2: ТРЕНАЖЕР ---
else:
    item = st.session_state.current_item
    
    # Компактный счетчик
    st.markdown(f"<div class='stat-text'>Pisteet: {st.session_state.score} / {st.session_state.total}</div>", unsafe_allow_html=True)
    
    # Фото с наложенной подсказкой
    import base64
    img_base64 = base64.b64encode(item['image']).decode()
    
    hint_html = ""
    if st.session_state.hint_letters > 0:
        hint_txt = item['full_answer'][:st.session_state.hint_letters]
        suffix = "..." if st.session_state.hint_letters < len(item['full_answer']) else ""
        hint_html = f"<div class='hint-overlay'>{hint_txt}{suffix}</div>"
        
    st.markdown(f"""
        <div class="image-container">
            <img src="data:image/jpeg;base64,{img_base64}" class="main-img">
            {hint_html}
        </div>
    """, unsafe_allow_html=True)

    # Поле ввода
    ans = st.text_input("Vastaus:", key=f"i_{st.session_state.widget_key}", label_visibility="collapsed")

    # Кнопки в ряд
    c1, c2, c3 = st.columns(3)
    
    if c1.button("OK"):
        st.session_state.total += 1
        if ans.lower() == item['full_answer'].lower():
            st.session_state.score += 1
            st.balloons()
            next_question()
            st.rerun()
        else:
            st.error("Väärin!")

    if c2.button("Vihje"):
        if st.session_state.hint_letters < len(item['full_answer']):
            st.session_state.hint_letters += 1
            st.rerun()

    if c3.button("Oikea"):
        st.info(item['full_answer'])
        if st.button("Seuraava →"):
            st.session_state.total += 1
            next_question()
            st.rerun()
