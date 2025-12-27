import streamlit as st
import pandas as pd
import random
import zipfile
import os
import base64
import time

st.set_page_config(page_title="Kasvioppi", layout="centered")

# --- ГЕНЕРАЦИЯ КНОПОК-КАРТИНОК ЧЕРЕЗ CSS ---
st.markdown("""
    <style>
    header, footer, #MainMenu {visibility: hidden;}
    .main .block-container { max-width: 500px !important; padding: 1rem !important; margin: 0 auto !important; }

    /* Контейнер для наших кнопок-картинок */
    .img-button-row {
        display: flex !important;
        justify-content: space-between !important;
        gap: 10px !important;
        margin-top: 20px !important;
    }

    /* Сама "кнопка" (теперь это картинка-блок) */
    .fake-button {
        flex: 1;
        background-color: #2e7d32;
        color: white !important;
        text-align: center;
        padding: 15px 5px;
        border-radius: 12px;
        font-weight: bold;
        font-size: 14px;
        text-decoration: none !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.1s;
        border: none;
    }
    .fake-button:active { transform: translateY(2px); box-shadow: none; }

    .main-img { width: 100%; max-height: 400px; object-fit: contain; border-radius: 15px; background: #f0f0f0; }
    
    /* Кнопка Старт — оставим одну нормальную, она вроде не лагает */
    div.stButton > button[kind="primary"] {
        display: block !important; margin: 0 auto !important; width: 100% !important;
        height: 70px !important; background-color: #2e7d32 !important; color: white !important;
        border-radius: 20px !important; font-size: 1.5rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ЛОГИКА ЗАГРУЗКИ ---
def load_data():
    if not os.path.exists("kasvit.xlsx") or not os.path.exists("kuvat.zip"): return None
    try:
        df = pd.read_excel("kasvit.xlsx")
        df.columns = [str(c).strip().upper() for c in df.columns]
        df['ID'] = df['ID'].astype(str).apply(lambda x: x.split('.')[0].zfill(3))
        photos = {}
        with zipfile.ZipFile("kuvat.zip") as z:
            for f_info in z.infolist():
                fname = f_info.filename.split('/')[-1]
                if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                    with z.open(f_info) as f: photos[fname[:3]] = f.read()
        combined = []
        for _, row in df.iterrows():
            if row['ID'] in photos:
                combined.append({'ans': f"{str(row['NIMI']).strip()} {str(row.get('LATINA', '')).strip()}".strip(), 'img': photos[row['ID']]})
        return combined
    except: return None

# --- СОСТОЯНИЕ ---
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

# --- ЭКРАНЫ ---
if not st.session_state.started:
    if os.path.exists("cover.jpg"): st.image("cover.jpg")
    if st.button("ALOITA HARJOITUS 🚀", type="primary"):
        st.session_state.started = True
        st.rerun()

elif st.session_state.data:
    it = st.session_state.item
    st.markdown(f"<p style='text-align: center; font-weight: bold;'>Pisteet: {st.session_state.score} / {st.session_state.total}</p>", unsafe_allow_html=True)
    
    b64 = base64.b64encode(it['img']).decode()
    st.markdown(f'<div style="text-align:center; position:relative;"><img src="data:image/jpeg;base64,{b64}" class="main-img">', unsafe_allow_html=True)
    
    if st.session_state.hint_letters > 0:
        txt = it['ans'][:st.session_state.hint_letters]
        st.markdown(f"<div style='position:absolute; bottom:10px; left:50%; transform:translateX(-50%); background:white; padding:5px 10px; border-radius:10px; border:2px solid #2e7d32; font-weight:bold; width:80%;'>{txt}...</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    ans = st.text_input("Vastaus", key=f"v_{st.session_state.widget_key}", label_visibility="collapsed", placeholder="Kirjoita nimi...")

    # РЯД КНОПОК ЧЕРЕЗ СТАНДАРТНЫЙ STREAMLIT, НО С ОБМАННЫМ МАНЕВРОМ
    # Мы используем st.columns, но CSS сверху (.img-button-row) принудительно держит их в ряд!
    st.markdown('<div class="img-button-row">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Tarkista"):
            st.session_state.total += 1
            if ans.lower().strip() == it['ans'].lower():
                st.session_state.score += 1
                st.balloons()
                time.sleep(1)
                next_q()
                st.rerun()
            else: st.error("Väärin!")
    with col2:
        if st.button("Vihje"):
            st.session_state.hint_letters += 1
            st.rerun()
    with col3:
        if st.button("Luovuta"):
            st.session_state.show_ans = True
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.get('show_ans'):
        st.info(f"Oikea: {it['ans']}")
        if st.button("Seuraava →"):
            st.session_state.total += 1
            st.session_state.show_ans = False
            next_q()
            st.rerun()
