import streamlit as st
import pandas as pd
import random
import zipfile
import os
import base64
import time

st.set_page_config(page_title="Kasvioppi", layout="centered")

# --- МАКСИМАЛЬНО ЖЕСТКИЙ CSS ДЛЯ ФИКСАЦИИ ИНТЕРФЕЙСА ---
st.markdown("""
    <style>
    header, footer, #MainMenu {visibility: hidden;}
    
    /* Контейнер приложения */
    .main .block-container {
        max-width: 500px !important;
        padding: 1rem !important;
        margin: 0 auto !important;
    }

    /* ЦЕНТРИРОВАНИЕ ВСЕГО НА ПЕРВОМ ЭКРАНЕ */
    .stImage > img {
        width: 100% !important;
        max-width: 500px !important;
        height: auto !important;
        border-radius: 20px;
        margin-bottom: 20px;
    }

    /* Кнопка Старт: Центрирование через Flex */
    .start-wrapper {
        display: flex;
        justify-content: center;
        width: 100%;
        margin-top: 20px;
    }
    
    /* Стилизация кнопок */
    button[kind="primary"] {
        width: 100% !important;
        height: 75px !important;
        font-size: 1.5em !important;
        background-color: #2e7d32 !important;
        color: white !important;
        border-radius: 20px !important;
        border: none !important;
    }

    /* ИГРОВЫЕ КНОПКИ: ЖЕСТКИЙ РЯД */
    [data-testid="stHorizontalBlock"] {
        display: grid !important;
        grid-template-columns: 1fr 1fr 1fr !important;
        gap: 8px !important;
        width: 100% !important;
    }
    
    .stButton > button:not([kind="primary"]) {
        width: 100% !important;
        height: 4em !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        border: 2px solid #2e7d32 !important;
        font-size: 0.85em !important;
        white-space: nowrap !important; /* ЗАПРЕТ ПЕРЕНОСА СЛОВ */
        overflow: hidden;
        background-color: white !important;
    }

    /* Фото в игре */
    .main-img {
        border-radius: 15px;
        width: 100%;
        max-height: 45vh;
        object-fit: contain;
        background-color: #f8f9fa;
    }
    .image-box { position: relative; width: 100%; text-align: center; margin-bottom: 10px;}
    
    .hint-label {
        position: absolute;
        bottom: 10px; left: 50%; transform: translateX(-50%);
        background: rgba(255, 255, 255, 0.95);
        padding: 6px 12px; border-radius: 12px;
        font-weight: bold; font-size: 0.9em; width: 85%;
        border: 2px solid #2e7d32; color: #2e7d32;
    }
    
    /* Сообщение об ошибке/успехе по центру */
    .stAlert {
        text-align: center !important;
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

# --- ЭКРАН 1: ОБЛОЖКА ---
if not st.session_state.started:
    if os.path.exists("cover.jpg"): st.image("cover.jpg", use_container_width=True)
    elif os.path.exists("cover.png"): st.image("cover.png", use_container_width=True)
    
    # Кнопка СТАРТ через обертку для центрирования
    st.markdown('<div class="start-wrapper">', unsafe_allow_html=True)
    if st.button("ALOITA HARJOITUS 🚀", type="primary"):
        st.session_state.started = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- ЭКРАН 2: ТРЕНАЖЕР ---
elif st.session_state.data:
    it = st.session_state.item
    st.markdown(f"<p style='text-align: center; font-weight: bold; margin: 0;'>Pisteet: {st.session_state.score} / {st.session_state.total}</p>", unsafe_allow_html=True)
    
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

    ans = st.text_input("Vastaus", key=f"v_{st.session_state.widget_key}", label_visibility="collapsed", placeholder="Nimi Latina...", autocomplete="one-time-code")

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
            else:
                st.error("Väärin! Korjaa или подсказка.")

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
