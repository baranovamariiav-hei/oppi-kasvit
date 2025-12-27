import streamlit as st
import pandas as pd
import random
import zipfile
import os
import base64
import time

st.set_page_config(page_title="Kasvioppi", layout="centered")

# --- ЧИСТЫЙ CSS ДЛЯ ГЕОМЕТРИИ ---
st.markdown("""
    <style>
    header, footer, #MainMenu {visibility: hidden;}
    
    .main .block-container {
        max-width: 500px !important;
        padding: 1.5rem 1rem !important;
        margin: 0 auto !important;
    }

    /* ФОТО НА ЗАСТАВКЕ */
    [data-testid="stImage"] {
        text-align: center !important;
    }
    [data-testid="stImage"] img {
        border-radius: 20px;
        width: 100% !important;
        max-width: 480px !important;
        height: auto !important;
    }

    /* КНОПКА СТАРТ: ЦЕНТР */
    div.stButton {
        text-align: center !important;
    }
    
    button[kind="primary"] {
        width: 90% !important;
        max-width: 300px !important;
        height: 70px !important;
        font-size: 1.4em !important;
        background-color: #2e7d32 !important;
        color: white !important;
        border-radius: 18px !important;
        margin-top: 20px !important;
    }

    /* РЯД КНОПОК БЕЗ КОЛОНОК */
    [data-testid="stHorizontalBlock"] {
        gap: 10px !important;
    }
    
    /* Универсальный стиль для 3 кнопок */
    .stButton > button:not([kind="primary"]) {
        width: 100% !important;
        height: 3.5em !important;
        font-weight: bold !important;
        border-radius: 10px !important;
        border: 2px solid #2e7d32 !important;
        font-size: 0.9em !important;
        background-color: white !important;
        padding: 0 10px !important;
        white-space: nowrap !important;
    }

    /* Фото в игре */
    .main-img {
        border-radius: 15px;
        width: 100%;
        max-height: 45vh;
        object-fit: contain;
        background-color: #f8f9fa;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ЛОГИКА ---
def load_data():
    if not os.path.exists("kasvit.xlsx") or not os.path.exists("kuvat.zip"):
        return None
    try:
        df = pd.read_excel("kasvit.xlsx")
        df.columns = [str(c).strip().upper() for c in df.columns]
        df['ID'] = df['ID'].astype(str).apply(lambda x: x.split('.')[0].zfill(3))
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

if 'started' not in st.session_state: st.session_state.started = False
if 'data' not in st.session_state:
    st.session_state.data = load_data()
    st.session_state.score, st.session_state.total = 0, 0
    st.session_state.hint_letters, st.session_state.widget_key = 0, 0
if 'item' not in st.session_state and st.session_state.data:
    st.session_state.item = random.choice(st.session_state.data)

def next_q():
    st.session_state.item = random.choice(st.session_state.data)
    st.session_state.hint_letters, st.session_state.widget_key = 0, st.session_state.widget_key + 1

# --- ИНТЕРФЕЙС ---

if not st.session_state.started:
    # Используем стандартный st.image, но CSS его отцентрирует
    if os.path.exists("cover.jpg"): st.image("cover.jpg")
    elif os.path.exists("cover.png"): st.image("cover.png")
    
    if st.button("ALOITA HARJOITUS 🚀", type="primary"):
        st.session_state.started = True
        st.rerun()

elif st.session_state.data:
    it = st.session_state.item
    st.markdown(f"<p style='text-align: center; font-weight: bold;'>Pisteet: {st.session_state.score} / {st.session_state.total}</p>", unsafe_allow_html=True)
    
    b64 = base64.b64encode(it['img']).decode()
    hint_html = ""
    if st.session_state.hint_letters > 0:
        txt = it['ans'][:st.session_state.hint_letters]
        suff = "..." if st.session_state.hint_letters < len(it['ans']) else ""
        hint_html = f"<div style='position:absolute; bottom:10px; left:50%; transform:translateX(-50%); background:white; padding:5px 12px; border-radius:10px; border:2px solid #2e7d32; font-weight:bold; width:85%; text-align:center;'>{txt}{suff}</div>"
        
    st.markdown(f"""
        <div style="position: relative; text-align: center;">
            <img src="data:image/jpeg;base64,{b64}" class="main-img">
            {hint_html}
        </div>
    """, unsafe_allow_html=True)

    ans = st.text_input("Vastaus", key=f"v_{st.session_state.widget_key}", label_visibility="collapsed", placeholder="Nimi Latina...", autocomplete="one-time-code")

    # Сетка кнопок (CSS превратит это в красивый ряд без "стаканчиков")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        if st.button("Tarkista"):
            st.session_state.total += 1
            if ans.lower().strip() == it['ans'].lower():
                st.session_state.score += 1
                st.balloons()
                st.success("Oikein!")
                time.sleep(1.2)
                next_q()
                st.rerun()
            else: st.error("Väärin!")

    with c2:
        if st.button("Vihje"):
            if st.session_state.hint_letters < len(it['ans']):
                st.session_state.hint_letters += 1
                st.rerun()

    with c3:
        if st.button("Luovuta"):
            st.session_state.show_ans = True

    if st.session_state.get('show_ans'):
        st.info(f"Oikea: {it['ans']}")
        if st.button("Seuraava →"):
            st.session_state.total += 1
            st.session_state.show_ans = False
            next_q()
            st.rerun()
