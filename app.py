import streamlit as st
import pandas as pd
import random
import zipfile
import io
import time
import os
import base64

# Настройка страницы
st.set_page_config(page_title="Kasvioppi", layout="centered")

# --- УЛУЧШЕННЫЕ СТИЛИ CSS ---
st.markdown("""
    <style>
    header, footer, #MainMenu {visibility: hidden;}
    .block-container { padding-top: 1rem; padding-bottom: 0rem; max-width: 500px; }

    /* Центрирование кнопки на обложке */
    .stButton { display: flex; justify-content: center; }
    
    /* Контейнер фото */
    .image-container {
        position: relative;
        text-align: center;
        margin-bottom: 10px;
        width: 100%;
    }
    
    .main-img {
        border-radius: 15px;
        width: 100%;
        max-height: 42vh; 
        object-fit: contain;
        background-color: #f0f0f0;
    }
    
    .hint-overlay {
        position: absolute;
        bottom: 8px;
        left: 50%;
        transform: translateX(-50%);
        background-color: rgba(255, 249, 196, 0.95);
        color: #5d4037;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: bold;
        font-size: 0.85em;
        width: 85%;
        border: 1px solid #fbc02d;
    }

    /* ФИКС КНОПОК В ОДНУ ЛИНИЮ (ДЛЯ МОБИЛЬНЫХ) */
    [data-testid="column"] {
        width: 33% !important;
        flex: 1 1 0% !important;
        min-width: 0px !important;
    }
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
    }

    .stButton>button {
        width: 100% !important;
        border-radius: 10px !important;
        height: 3.5em !important;
        font-weight: bold !important;
        background-color: #e8f5e9 !important;
        border: 2px solid #2e7d32 !important;
        color: #2e7d32 !important;
        font-size: 0.85em !important;
    }
    
    /* Центрированные уведомления */
    .status-msg {
        text-align: center;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
        font-weight: bold;
    }
    .error-msg { background-color: #ffebee; color: #c62828; border: 1px solid #ef9a9a; }
    .success-msg { background-color: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }
    
    .stat-text { font-size: 1em; text-align: center; font-weight: bold; margin-bottom: 5px; color: #444; }
    </style>
    """, unsafe_allow_html=True)

# --- ЛОГИКА ЗАГРУЗКИ ---
def load_data():
    if not os.path.exists("kasvit.xlsx") or not os.path.exists("kuvat.zip"):
        return None
    try:
        df = pd.read_excel("kasvit.xlsx")
        df.columns = [str(c).strip().upper() for c in df.columns]
        df['ID'] = df['ID'].astype(str).split('.').str[0].str.zfill(3)
        photos = {}
        with zipfile.ZipFile("kuvat.zip") as z:
            for f_info in z.infolist():
                fname = f_info.filename.split('/')[-1]
                if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                    with z.open(f_info) as f:
                        photos[fname[:3]] = f.read()
        combined = []
        for _, row in df.iterrows():
            if row['ID'] in photos:
                combined.append({
                    'ans': f"{str(row['NIMI']).strip()} {str(row.get('LATINA', '')).strip()}".strip(),
                    'img': photos[row['ID']]
                })
        return combined
    except: return None

# Инициализация
if 'started' not in st.session_state:
    st.session_state.started = False
if 'data' not in st.session_state:
    st.session_state.data = load_data()
    st.session_state.score, st.session_state.total = 0, 0
    st.session_state.hint_letters, st.session_state.widget_key = 0, 0
    if st.session_state.data:
        st.session_state.item = random.choice(st.session_state.data)

def next_q():
    st.session_state.item = random.choice(st.session_state.data)
    st.session_state.hint_letters = 0
    st.session_state.widget_key += 1

# --- ЭКРАН 1: ОБЛОЖКА ---
if not st.session_state.started:
    if os.path.exists("cover.jpg"): st.image("cover.jpg", use_container_width=True)
    elif os.path.exists("cover.png"): st.image("cover.png", use_container_width=True)
    
    if st.button("ALOITA HARJOITUS 🚀"):
        st.session_state.started = True
        st.rerun()

# --- ЭКРАН 2: ТРЕНАЖЕР ---
elif st.session_state.data:
    it = st.session_state.item
    st.markdown(f"<div class='stat-text'>Pisteet: {st.session_state.score} / {st.session_state.total}</div>", unsafe_allow_html=True)
    
    # Картинка и подсказка
    b64 = base64.b64encode(it['img']).decode()
    hint_html = ""
    if st.session_state.hint_letters > 0:
        txt = it['ans'][:st.session_state.hint_letters]
        suff = "..." if st.session_state.hint_letters < len(it['ans']) else ""
        hint_html = f"<div class='hint-overlay'>{txt}{suff}</div>"
        
    st.markdown(f"""
        <div class="image-container">
            <img src="data:image/jpeg;base64,{b64}" class="main-img">
            {hint_html}
        </div>
    """, unsafe_allow_html=True)

    # Поле ввода
    usr_ans = st.text_input("Vastaus:", key=f"v_{st.session_state.widget_key}", label_visibility="collapsed", placeholder="Nimi Latina")

    # Контейнер для центрированных сообщений
    status_placeholder = st.empty()

    # Кнопки
    c1, c2, c3 = st.columns(3)
    
    if c1.button("Tarkista"):
        st.session_state.total += 1
        if usr_ans.lower() == it['ans'].lower():
            st.session_state.score += 1
            st.balloons()
            status_placeholder.markdown("<div class='status-msg success-msg'>Oikein! Hienoa!</div>", unsafe_allow_html=True)
            time.sleep(1.5) # Ждем, пока летят шарики
            next_q()
            st.rerun()
        else:
            status_placeholder.markdown("<div class='status-msg error-msg'>Väärin! Korjaa vastaus tai käytä vihjettä.</div>", unsafe_allow_html=True)

    if c2.button("Vihje"):
        if st.session_state.hint_letters < len(it['ans']):
            st.session_state.hint_letters += 1
            st.rerun()

    if c3.button("Luovuta"):
        st.session_state.show_ans = True

    if st.session_state.get('show_ans'):
        st.info(f"Oikea vastaus: {it['ans']}")
        if st.button("Seuraava →"):
            st.session_state.total += 1
            st.session_state.show_ans = False
            next_q()
            st.rerun()
