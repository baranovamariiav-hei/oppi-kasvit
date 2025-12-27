import streamlit as st
import pandas as pd
import random
import zipfile
import os
import base64
import time

# 1. Базовые настройки
st.set_page_config(page_title="Kasvioppi", layout="centered")

# 2. Чистый и стабильный CSS
st.markdown("""
    <style>
    header, footer, #MainMenu {visibility: hidden;}
    .block-container { padding-top: 1rem; max-width: 500px; }

    /* Кнопка на обложке: Большая и по центру */
    .stButton > button[kind="primary"] {
        display: block;
        margin: 0 auto;
        width: 100% !important;
        height: 80px !important;
        font-size: 1.5em !important;
        background-color: #2e7d32 !important;
        color: white !important;
        border-radius: 20px !important;
    }

    /* ФИКС КНОПОК: Только в один ряд */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 5px !important;
    }
    [data-testid="column"] {
        width: 33% !important;
        flex: 1 1 0% !important;
        min-width: 0px !important;
    }
    .stButton > button {
        width: 100% !important;
        height: 3.5em !important;
        font-weight: bold !important;
        border-radius: 10px !important;
        border: 2px solid #2e7d32 !important;
        font-size: 0.85em !important;
    }

    /* Картинка */
    .main-img {
        border-radius: 15px;
        width: 100%;
        max-height: 45vh;
        object-fit: contain;
        background-color: #f0f0f0;
    }
    .image-box { position: relative; width: 100%; text-align: center; margin-bottom: 10px;}
    
    /* Подсказка поверх фото */
    .hint-label {
        position: absolute;
        bottom: 10px; left: 50%; transform: translateX(-50%);
        background: rgba(255, 255, 255, 0.95);
        padding: 5px 10px; border-radius: 12px;
        font-weight: bold; font-size: 0.9em; width: 85%;
        border: 2px solid #2e7d32; color: #2e7d32;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Логика загрузки
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

# 4. Состояние сессии
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
    if os.path.exists("cover.jpg"): st.image("cover.jpg", use_container_width=True)
    elif os.path.exists("cover.png"): st.image("cover.png", use_container_width=True)
    
    # Кнопка СТАРТ (Primary делает её зеленой и большой по CSS)
    if st.button("ALOITA HARJOITUS 🚀", type="primary"):
        st.session_state.started = True
        st.rerun()

elif st.session_state.data:
    it = st.session_state.item
    st.markdown(f"<p style='text-align: center; font-weight: bold; margin: 0;'>Pisteet: {st.session_state.score} / {st.session_state.total}</p>", unsafe_allow_html=True)
    
    # Фото и подсказка
    b64 = base64.b64encode(it['img']).decode()
    hint_html = ""
    if st.session_state.hint_letters > 0:
        txt = it['ans'][:st.session_state.hint_letters]
        suff = "..." if st.session_state.hint_letters < len(it['ans']) else ""
        hint_html = f"<div class='hint-label'>{txt}{suff}</div>"
        
    st.markdown(f"""
        <div class="image-box">
            <img src="data:image/jpeg;base64,{b64}" class="main-img">
            {hint_html}
        </div>
    """, unsafe_allow_html=True)

    # Поле ввода (autocomplete="one-time-code" отключает словари на iPhone/Android)
    ans = st.text_input(
        "Vastaus", 
        key=f"v_{st.session_state.widget_key}", 
        label_visibility="collapsed",
        placeholder="Nimi Latina...",
        autocomplete="one-time-code"
    )

    # Кнопки
    c1, c2, c3 = st.columns(3)
    
    with c1:
        if st.button("Tarkista"):
            st.session_state.total += 1
            if ans.lower().strip() == it['ans'].lower():
                st.session_state.score += 1
                st.balloons()
                st.success("Oikein!")
                time.sleep(1.5)
                next_q()
                st.rerun()
            else:
                st.error("Väärin! Korjaa или используй подсказку.")

    with c2:
        if st.button("Vihje"):
            if st.session_state.hint_letters < len(it['ans']):
                st.session_state.hint_letters += 1
                st.rerun()

    with col3 if 'col3' in locals() else c3: # Безопасный вызов колонки
        if st.button("Luovuta"):
            st.session_state.show_ans = True

    if st.session_state.get('show_ans'):
        st.info(f"Oikea: {it['ans']}")
        if st.button("Seuraava →"):
            st.session_state.total += 1
            st.session_state.show_ans = False
            next_q()
            st.rerun()
