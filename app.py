import streamlit as st
import pandas as pd
import random
import zipfile
import io
import time
import os

st.set_page_config(page_title="Kasvioppi Treenaaja", layout="centered")

# Дизайн остается тем же
st.markdown("""
    <style>
    .main { background-color: #f7f9f7; }
    .stButton>button { 
        width: 100%; border-radius: 15px; height: 3.5em; 
        background-color: #e8f5e9; border: 2px solid #2e7d32; 
        color: #2e7d32; font-weight: bold; 
    }
    .stButton>button:hover { background-color: #2e7d32; color: white; }
    img { border-radius: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); margin-bottom: 20px; }
    .stat-box { padding: 10px; border-radius: 10px; background-color: white; border: 1px solid #eee; margin-bottom: 10px; text-align: center; }
    .hint-box { 
        padding: 15px; background-color: #fff9c4; border-left: 5px solid #fbc02d; 
        border-radius: 5px; margin-bottom: 20px; font-size: 1.1em; font-weight: bold; color: #5d4037;
    }
    </style>
    """, unsafe_allow_html=True)

# Функция загрузки БЕЗ кеша для проверки
def load_data_from_folder():
    excel_name = "kasvit.xlsx"
    zip_name = "kuvat.zip"
    
    # Проверка наличия файлов
    if not os.path.exists(excel_name):
        return None, f"Tiedostoa {excel_name} ei löydy palvelimelta!"
    if not os.path.exists(zip_name):
        return None, f"Tiedostoa {zip_name} ei löydy palvelimelta!"

    try:
        df = pd.read_excel(excel_name)
        df.columns = [str(c).strip().upper() for c in df.columns]
        df['ID'] = df['ID'].astype(str).str.split('.').str[0].str.zfill(3)
        
        photos = {}
        with zipfile.ZipFile(zip_name) as z:
            for file_info in z.infolist():
                fname = file_info.filename.split('/')[-1]
                if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                    file_id = fname[:3]
                    with z.open(file_info) as f:
                        photos[file_id] = f.read()
        
        combined = []
        for _, row in df.iterrows():
            curr_id = row['ID']
            if curr_id in photos:
                full_name = f"{str(row['NIMI']).strip()} {str(row.get('LATINA', '')).strip()}".strip()
                combined.append({'id': curr_id, 'full_answer': full_name, 'image': photos[curr_id]})
        
        if not combined:
            return None, "Yhtään kasvia ei löytynyt (tarkista ID:t Excelissä ja ZIP:issä)"
            
        return combined, None
    except Exception as e:
        return None, f"Virhe tiedoston käsittelyssä: {str(e)}"

# Инициализация сессии
if 'data' not in st.session_state:
    data, err = load_data_from_folder()
    if data:
        st.session_state.data = data
        st.session_state.current_item = random.choice(data)
        st.session_state.score = 0
        st.session_state.total = 0
        st.session_state.show_answer = False
        st.session_state.hint_letters = 0
        st.session_state.widget_key = 0
    else:
        st.error(err) # ТУТ МЫ УВИДИМ ОШИБКУ НА МОБИЛЬНОМ
        st.stop()

def next_question():
    if st.session_state.data:
        st.session_state.current_item = random.choice(st.session_state.data)
        st.session_state.show_answer = False
        st.session_state.hint_letters = 0
        st.session_state.widget_key += 1

# --- ГЛАВНЫЙ ЭКРАН ---
st.title("🌿 Kasvioppi: Treenaaja")

item = st.session_state.current_item
st.markdown(f"<div class='stat-box'><b>Pisteet:</b> {st.session_state.score} / {st.session_state.total}</div>", unsafe_allow_html=True)
st.image(item['image'], use_container_width=True)

if st.session_state.hint_letters > 0:
    hint_text = item['full_answer'][:st.session_state.hint_letters]
    suffix = "..." if st.session_state.hint_letters < len(item['full_answer']) else ""
    st.markdown(f"<div class='hint-box'>Vihje: {hint_text}{suffix}</div>", unsafe_allow_html=True)

ans = st.text_input("Kirjoita suomalainen ja latinankielinen nimi:", key=f"input_{st.session_state.widget_key}").strip()

col1, col2, col3 = st.columns(3)

if col1.button("Tarkista"):
    if ans.lower() == item['full_answer'].lower():
        st.session_state.score += 1
        st.session_state.total += 1
        st.balloons()
        st.success("Oikein!")
        time.sleep(1.2)
        next_question()
        st.rerun()
    else:
        st.session_state.total += 1
        st.error("Väärin!")

if col2.button("Vihje"):
    if st.session_state.hint_letters < len(item['full_answer']):
        st.session_state.hint_letters += 1
        st.rerun()

if col3.button("Luovuta"):
    st.session_state.show_answer = True

if st.session_state.show_answer:
    st.warning(f"Oikea vastaus: **{item['full_answer']}**")
    if st.button("Seuraava →"):
        next_question()
        st.rerun()
