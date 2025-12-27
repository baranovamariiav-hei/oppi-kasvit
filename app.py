import streamlit as st
import pandas as pd
import random
import zipfile
import os
import base64
import time

st.set_page_config(page_title="Kasvioppi", layout="centered")

# --- ГЛОБАЛЬНЫЕ СТИЛИ ---
st.markdown("""
    <style>
    header, footer, #MainMenu {visibility: hidden;}
    .block-container { padding-top: 1rem; max-width: 500px; margin: 0 auto; }
    
    /* Кнопка на обложке: Огромная, зеленая, по центру */
    div.stButton > button#start_btn {
        display: block;
        margin: 0 auto;
        width: 100% !important;
        height: 100px !important;
        font-size: 1.8em !important;
        background-color: #2e7d32 !important;
        color: white !important;
        border-radius: 20px !important;
        border: none !important;
    }

    /* ФИКС КНОПОК: Жесткий ряд через Flexbox */
    .button-group {
        display: flex !important;
        flex-direction: row !important;
        justify-content: space-between !important;
        gap: 5px !important;
        width: 100% !important;
    }
    
    /* Чтобы стандартные колонки Streamlit не схлопывались в столбик */
    [data-testid="column"] {
        width: 32% !important;
        flex: 1 1 0% !important;
        min-width: 0px !important;
    }
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
    }

    .stButton > button {
        width: 100% !important;
        height: 3.5em !important;
        font-weight: bold !important;
        font-size: 0.8em !important;
        border-radius: 10px !important;
        white-space: nowrap !important;
    }

    /* Оформление фото */
    .main-img {
        border-radius: 15px;
        width: 100%;
        max-height: 40vh;
        object-fit: contain;
        background-color: #f9f9f9;
        margin-bottom: 5px;
    }

    /* Подсказка поверх фото */
    .image-box { position: relative; width: 100%; text-align: center; }
    .hint-label {
        position: absolute;
        bottom: 10px; left: 50%; transform: translateX(-50%);
        background: rgba(255, 255, 255, 0.9);
        padding: 5px 15px; border-radius: 15px;
        font-weight: bold; font-size: 0.9em; width: 85%;
        border: 2px solid #2e7d32; color: #2e7d32;
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

# --- ИНТЕРФЕЙС ---

if not st.session_state.started:
    if os.path.exists("cover.jpg"): st.image("cover.jpg", use_container_width=True)
    elif os.path.exists("cover.png"): st.image("cover.png", use_container_width=True)
    
    # Кнопка СТАРТ (ID для CSS)
    if st.button("ALOITA HARJOITUS 🚀", key="start_btn"):
        st.session_state.started = True
        st.rerun()

elif st.session_state.data:
    it = st.session_state.item
    st.markdown(f"<p style='text-align: center; font-weight: bold; margin: 0;'>Pisteet: {st.session_state.score} / {st.session_state.total}</p>", unsafe_allow_html=True)
    
    # Фото
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

    # ПОЛЕ ВВОДА: Блокируем автозаполнение через атрибуты
    ans = st.text_input(
        "Vastaus", 
        key=f"v_{st.session_state.widget_key}", 
        label_visibility="collapsed",
        placeholder="Nimi Latina...",
        autocomplete="off" # Попытка №1
    )
    # Дополнительная защита от автозаполнения через JS-скрипт (инъекция в HTML)
    st.components.v1.html(f"""
        <script>
            var inputs = window.parent.document.querySelectorAll('input');
            inputs.forEach(input => {{
                input.setAttribute('autocomplete', 'off');
                input.setAttribute('autocorrect', 'off');
                input.setAttribute('autocapitalize', 'off');
                input.setAttribute('spellcheck', 'false');
            }});
        </script>
    """, height=0)

    # КНОПКИ В РЯД
    col1, col2, col3 = st.columns(3)
    
    if col1.button("Tarkista"):
        st.session_state.total += 1
        if ans.lower().strip() == it['ans'].lower():
            st.session_state.score += 1
            st.balloons()
            st.markdown("<p style='text-align: center; color: green; font-weight: bold;'>Oikein!</p>", unsafe_allow_html=True)
            time.sleep(1.5)
            next_q()
            st.rerun()
        else:
            st.markdown("<p style='text-align: center; color: red; font-weight: bold;'>Väärin! Korjaa tai katso vihje.</p>", unsafe_allow_html=True)

    if col2.button("Vihje"):
        if st.session_state.hint_letters < len(it['ans']):
            st.session_state.hint_letters += 1
            st.rerun()

    if col3.button("Luovuta"):
        st.session_state.show_ans = True

    if st.session_state.get('show_ans'):
        st.info(f"Oikea: {it['ans']}")
        if st.button("Seuraava →"):
            st.session_state.total += 1
            st.session_state.show_ans = False
            next_q()
            st.rerun()
