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

# --- СТИЛИ CSS ---
st.markdown("""
    <style>
    /* Прячем служебные элементы */
    header, footer, #MainMenu {visibility: hidden;}
    .block-container { padding-top: 1rem; padding-bottom: 0rem; max-width: 500px; }

    /* Кнопка на обложке: по центру и большая */
    .start-btn-container {
        display: flex;
        justify-content: center;
        margin-top: 20px;
    }
    
    /* Контейнер для фото и подсказки */
    .image-container {
        position: relative;
        text-align: center;
        margin-bottom: 10px;
        width: 100%;
    }
    
    .main-img {
        border-radius: 15px;
        width: 100%;
        max-height: 45vh; /* Ограничение высоты, чтобы всё влезло */
        object-fit: contain;
        background-color: #f0f0f0;
    }
    
    .hint-overlay {
        position: absolute;
        bottom: 10px;
        left: 50%;
        transform: translateX(-50%);
        background-color: rgba(255, 249, 196, 0.95);
        color: #5d4037;
        padding: 5px 15px;
        border-radius: 15px;
        font-weight: bold;
        font-size: 0.9em;
        width: 85%;
        border: 1px solid #fbc02d;
        pointer-events: none;
    }

    /* ФИКС КНОПОК В ОДНУ ЛИНИЮ */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 5px !important;
    }
    [data-testid="column"] {
        width: 33% !important;
        flex: 1 1 auto !important;
        min-width: 0px !important;
    }

    .stButton>button {
        width: 100% !important;
        border-radius: 10px !important;
        height: 3.5em !important;
        font-weight: bold !important;
        background-color: #e8f5e9 !important;
        border: 2px solid #2e7d32 !important;
        color: #2e7d32 !important;
    }
    
    /* Статистика */
    .stat-text { font-size: 1em; text-align: center; font-weight: bold; margin-bottom: 5px; color: #444; }
    </style>
    """, unsafe_allow_html=True)

# --- ЛОГИКА ---
def load_data():
    if not os.path.exists("kasvit.xlsx") or not os.path.exists("kuvat.zip"):
        return None
    try:
        df = pd.read_excel("kasvit.xlsx")
        df.columns = [str(c).strip().upper() for c in df.columns]
        df['ID'] = df['ID'].astype(str).str.split('.').str[0].str.zfill(3)
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

if 'started' not in st.session_state:
    st.session_state.started = False
if 'data' not in st.session_state:
    st.session_state.data = load_data()
    st.session_state.score, st.session_state.total = 0, 0
    st.session_state.hint_letters, st.session_state.widget_key = 0, 0
    st.session_state.correct_mode = False
    if st.session_state.data:
        st.session_state.item = random.choice(st.session_state.data)

def next_q():
    st.session_state.item = random.choice(st.session_state.data)
    st.session_state.hint_letters = 0
    st.session_state.widget_key += 1
    st.session_state.correct_mode = False

# --- ЭКРАН 1: ОБЛОЖКА ---
if not st.session_state.started:
    if os.path.exists("cover.jpg"): st.image("cover.jpg", use_container_width=True)
    elif os.path.exists("cover.png"): st.image("cover.png", use_container_width=True)
    
    st.markdown('<div class="start-btn-container">', unsafe_allow_html=True)
    if st.button("ALOITA HARJOITUS 🚀", use_container_width=True):
        st.session_state.started = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

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

    # Кнопки
    c1, c2, c3 = st.columns(3)
    
    # Чтобы шарики летели и экран не дергался, при успехе меняем кнопку
    if not st.session_state.correct_mode:
        if c1.button("Tarkista"):
            st.session_state.total += 1
            if usr_ans.lower() == it['ans'].lower():
                st.session_state.score += 1
                st.session_state.correct_mode = True
                st.balloons()
                st.rerun()
            else:
                st.error("Väärin!")
    else:
        if c1.button("✅ Seuraava"):
            next_q()
            st.rerun()

    if c2.button("Vihje"):
        if st.session_state.hint_letters < len(it['ans']):
            st.session_state.hint_letters += 1
            st.rerun()

    if c3.button("Luovuta"):
        st.session_state.show_ans = True

    if st.session_state.get('show_ans'):
        st.info(it['ans'])
        if st.button("Jatka →"):
            st.session_state.total += 1
            st.session_state.show_ans = False
            next_q()
            st.rerun()
