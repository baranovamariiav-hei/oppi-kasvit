import streamlit as st
import pandas as pd
import random
import zipfile
import io

# Настройка страницы
st.set_page_config(page_title="TESTI", layout="centered")

# РАДИКАЛЬНЫЙ ДИЗАЙН ДЛЯ ПРОВЕРКИ
st.markdown("""
    <style>
    /* Красные кнопки для проверки */
    .stButton>button { 
        width: 100%; 
        border-radius: 0px; 
        height: 4em; 
        background-color: #ff4b4b !important; 
        color: white !important; 
        font-weight: bold;
        font-size: 20px;
        border: 3px solid black;
    }
    h1 { color: red !important; font-size: 50px !important; }
    </style>
    """, unsafe_allow_html=True)

if 'data' not in st.session_state:
    st.session_state.data = None
    st.session_state.current_item = None
    st.session_state.score = 0
    st.session_state.total = 0
    st.session_state.hint_letters = 0

def load_data(table_file, zip_file):
    try:
        if table_file.name.endswith('.csv'):
            df = pd.read_csv(table_file)
        else:
            df = pd.read_excel(table_file)
        df.columns = [str(c).strip().upper() for c in df.columns]
        df['ID'] = df['ID'].astype(str).str.split('.').str[0].str.zfill(3)
        photos = {}
        with zipfile.ZipFile(zip_file) as z:
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
                combined.append({
                    'id': curr_id,
                    'name': str(row['NIMI']).strip(),
                    'latin': str(row.get('LATINA', '')).strip(),
                    'image': photos[curr_id]
                })
        return combined
    except Exception as e:
        st.error(f"Virhe: {e}")
        return None

def next_question():
    if st.session_state.data:
        st.session_state.current_item = random.choice(st.session_state.data)
        st.session_state.hint_letters = 0

# --- СИСТЕМА ЗАГРУЗКИ ---
with st.sidebar:
    st.header("Lataa tiedostot")
    t_file = st.file_uploader("Excel", type=['xlsx', 'csv'])
    p_file = st.file_uploader("ZIP", type=['zip'])
    if st.button("KÄYNNISTÄ"):
        if t_file and p_file:
            loaded = load_data(t_file, p_file)
            if loaded:
                st.session_state.data = loaded
                next_question()
                st.rerun()

st.title("🔴 TESTI: ONKO PÄIVITYS?")

if st.session_state.current_item:
    item = st.session_state.current_item
    st.image(item['image'], use_container_width=True)
    
    # Текст подсказки прямо перед глазами
    if st.session_state.hint_letters > 0:
        st.warning(f"VIHJE: {item['name'][:st.session_state.hint_letters]}...")

    ans = st.text_input("Vastaus:", key="input").strip()
    
    col1, col2, col3 = st.columns(3)
    
    if col1.button("TARKISTA"):
        if ans.lower() == item['name'].lower():
            st.success("OIKEIN!")
            next_question()
            st.rerun()
        else:
            st.error("VÄÄRIN")

    if col2.button(f"VIHJE ({st.session_state.hint_letters})"):
        st.session_state.hint_letters += 1
        st.rerun()

    if col3.button("LUOVUTA"):
        st.info(f"{item['name']} ({item['latin']})")
else:
    st.write("Lataa tiedostot sivupalkista.")
