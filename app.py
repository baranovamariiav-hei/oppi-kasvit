import streamlit as st
import pandas as pd
import random
import zipfile
import os
import base64
import time

st.set_page_config(page_title="Kasvioppi", layout="centered")

# --- СТИЛИ БЕЗ КОМПРОМИССОВ ---
st.markdown("""
    <style>
    header, footer, #MainMenu {visibility: hidden;}
    
    .main .block-container {
        max-width: 500px !important;
        padding: 1rem !important;
        margin: 0 auto !important;
    }

    /* ФОТО НА ПЕРВОМ ЭКРАНЕ */
    .cover-img {
        width: 100%;
        max-width: 500px;
        border-radius: 20px;
        display: block;
        margin: 0 auto 20px auto;
    }

    /* КНОПКА СТАРТ ПО ЦЕНТРУ */
    .center-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
    }
    
    /* ИГРОВЫЕ КНОПКИ: РАВНОМЕРНАЯ СЕТКА */
    [data-testid="stHorizontalBlock"] {
        display: grid !important;
        grid-template-columns: 1fr 1fr 1fr !important;
        gap: 6px !important;
        width: 100% !important;
    }

    .stButton > button {
        width: 100% !important;
        height: 3.8em !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        border: 2px solid #2e7d32 !important;
        font-size: 0.75rem !important; /* Чуть меньше, чтобы текст не резался */
        white-space: normal !important; /* Разрешаем перенос внутри кнопки, если слово очень длинное */
        line-height: 1.1;
        padding: 2px !important;
        background-color: white !important;
    }

    /* Кнопка Старт особенная */
    button[kind="primary"] {
        background-color: #2e7d32 !important;
        color: white !important;
        font-size: 1.3rem !important;
        height: 70px !important;
        max-width: 300px !important;
    }

    /* Фото в игре */
    .main-img {
        border-radius: 15px;
        width: 100%;
        max-height: 42vh;
        object-fit: contain;
        background-color: #f8f9fa;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ЛОГИКА ---
def get_base64(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def load_data():
    if not os.path.exists("kasvit.xlsx") or not os.path.exists("kuvat.zip"):
        return None
    try:
        df = pd.read_excel("kasvit.xlsx")
        df.columns = [str(c).strip().upper() for c in df.columns]
        df['ID'] = df['ID'].astype(str).split('.')[0].zfill(3) # Упрощенная логика ID
        photos = {}
        with zipfile.ZipFile("kuvat.zip") as z:
            for f_info in z.infolist():
                fname = f_info.filename.split('/')[-1]
                if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                    with z.open(f_info) as f:
                        photos[fname[:3]] = f.read()
        combined = []
        for _, row in df.iterrows():
            clean_id = str(row['ID']).split('.')[0].zfill(3)
            if clean_id in photos:
                combined.append({
                    'ans': f"{str(row['NIMI']).strip()} {str(row.get('LATINA', '')).strip()}".strip(),
                    'img': photos[clean_id]
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
    # Используем HTML для фото и центрирования кнопки
    img_path = "cover.jpg" if os.path.exists("cover.jpg") else "cover.png"
    if os.path.exists(img_path):
        b64_cover = get_base64(img_path)
        st.markdown(f'<img src="data:image/jpeg;base64,{b64_cover}" class="cover-img">', unsafe_allow_html=True)
    
    st.markdown('<div class="center-wrapper">', unsafe_allow_html=True)
    if st.button("ALOITA HARJOITUS 🚀", type="primary"):
        st.session_state.started = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.data:
    it = st.session_state.item
    st.markdown(f"<p style='text-align: center; font-weight: bold; margin: 0;'>Pisteet: {st.session_state.score} / {st.session_state.total}</p>", unsafe_allow_html=True)
    
    b64_img = base64.b64encode(it['img']).decode()
    hint_html = ""
    if st.session_state.hint_letters > 0:
        txt = it['ans'][:st.session_state.hint_letters]
        suff = "..." if st.session_state.hint_letters < len(it['ans']) else ""
        hint_html = f"<div style='position:absolute; bottom:10px; left:50%; transform:translateX(-50%); background:white; padding:5px 10px; border-radius:10px; border:2px solid #2e7d32; font-weight:bold; width:80%; text-align:center;'>{txt}{suff}</div>"
        
    st.markdown(f"""
        <div style="position: relative; text-align: center;">
            <img src="data:image/jpeg;base64,{b64_img}" class="main-img">
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
