import streamlit as st
import pandas as pd
import random
import zipfile
import os
import base64
import time

st.set_page_config(page_title="Kasvioppi", layout="centered")

# --- СТИЛИ (CSS) ---
st.markdown("""
    <style>
    header, footer, #MainMenu {visibility: hidden;}
    .block-container { padding-top: 1rem; max-width: 500px; }
    
    /* Кнопка на обложке большая */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.8em;
        font-weight: bold;
        font-size: 1.1em;
    }

    /* Фото и подсказка */
    .image-container {
        position: relative;
        text-align: center;
        margin-bottom: 10px;
    }
    .main-img {
        border-radius: 15px;
        width: 100%;
        max-height: 42vh;
        object-fit: contain;
        background-color: #f9f9f9;
    }
    .hint-overlay {
        position: absolute;
        bottom: 10px;
        left: 50%;
        transform: translateX(-50%);
        background-color: rgba(255, 249, 196, 0.95);
        padding: 5px 15px;
        border-radius: 15px;
        font-weight: bold;
        font-size: 0.9em;
        width: 85%;
        border: 1px solid #fbc02d;
        color: #5d4037;
    }

    /* Кнопки в ряд на мобильном */
    [data-testid="column"] {
        width: 33.33% !important;
        flex: 1 1 0% !important;
        min-width: 0px !important;
    }
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
    }

    /* Центрированные сообщения */
    .status-box {
        text-align: center;
        padding: 10px;
        border-radius: 10px;
        margin-top: 10px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ФУНКЦИИ ---
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

# --- СОСТОЯНИЕ (Session State) ---
if 'started' not in st.session_state:
    st.session_state.started = False
if 'data' not in st.session_state:
    st.session_state.data = load_data()
    st.session_state.score, st.session_state.total = 0, 0
    st.session_state.hint_letters, st.session_state.widget_key = 0, 0
if 'item' not in st.session_state and st.session_state.data:
    st.session_state.item = random.choice(st.session_state.data)

def next_q():
    st.session_state.item = random.choice(st.session_state.data)
    st.session_state.hint_letters = 0
    st.session_state.widget_key += 1

# --- ИНТЕРФЕЙС ---

# 1. ОБЛОЖКА
if not st.session_state.started:
    if os.path.exists("cover.jpg"): st.image("cover.jpg", use_container_width=True)
    elif os.path.exists("cover.png"): st.image("cover.png", use_container_width=True)
    
    st.write(" ") # Пробел
    col_l, col_m, col_r = st.columns([1, 4, 1])
    with col_m:
        if st.button("ALOITA 🚀"):
            st.session_state.started = True
            st.rerun()

# 2. ИГРА
elif st.session_state.data:
    it = st.session_state.item
    st.markdown(f"<p style='text-align: center; font-weight: bold;'>Pisteet: {st.session_state.score} / {st.session_state.total}</p>", unsafe_allow_html=True)
    
    # Картинка
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
    ans = st.text_input("Vastaus:", key=f"v_{st.session_state.widget_key}", label_visibility="collapsed", placeholder="Nimi Latina")

    # Кнопки
    c1, c2, c3 = st.columns(3)
    
    if c1.button("Tarkista"):
        st.session_state.total += 1
        if ans.lower() == it['ans'].lower():
            st.session_state.score += 1
            st.balloons()
            st.markdown("<div class='status-box' style='color: green; background: #e8f5e9;'>Oikein! Hienoa!</div>", unsafe_allow_html=True)
            time.sleep(1.5)
            next_q()
            st.rerun()
        else:
            st.markdown("<div class='status-box' style='color: red; background: #ffebee;'>Väärin! Korjaa vastaus tai käytä vihjettä.</div>", unsafe_allow_html=True)

    if c2.button("Vihje"):
        if st.session_state.hint_letters < len(it['ans']):
            st.session_state.hint_letters += 1
            st.rerun()

    if c3.button("Luovuta"):
        st.session_state.show_ans = True

    if st.session_state.get('show_ans'):
        st.info(f"Oikea: {it['ans']}")
        if st.button("Seuraava →"):
            st
