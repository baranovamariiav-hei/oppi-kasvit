import streamlit as st
import pandas as pd
import random
import zipfile
import os
import io

st.set_page_config(page_title="Kasvioppi Treenaaja", layout="centered")

# Дизайн
st.markdown("""
    <style>
    .main { background-color: #f7f9f7; }
    .stButton>button { width: 100%; border-radius: 15px; height: 3em; background-color: #e8f5e9; border: 1px solid #2e7d32; color: #2e7d32; font-weight: bold; }
    .stButton>button:hover { background-color: #2e7d32; color: white; }
    img { border-radius: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

if 'data' not in st.session_state:
    st.session_state.data = None
    st.session_state.current_item = None
    st.session_state.score = 0
    st.session_state.total = 0
    st.session_state.feedback = ""
    st.session_state.show_hint = False

def load_data(table_file, zip_file):
    try:
        # Читаем таблицу
        if table_file.name.endswith('.csv'):
            df = pd.read_csv(table_file)
        else:
            df = pd.read_excel(table_file)
        
        # Очищаем заголовки от пробелов и приводим к ВЕРХНЕМУ регистру
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Проверяем наличие колонок
        required = ['ID', 'NIMI', 'LATINA']
        for col in required:
            if col not in df.columns:
                st.error(f"Virhe: Saraketta '{col}' ei löydy! Tarkista Excel.")
                return None

        # Форматируем ID как 001
        df['ID'] = df['ID'].astype(str).str.split('.').str[0].str.zfill(3)
        
        # Читаем фото из ZIP
        photos = {}
        with zipfile.ZipFile(zip_file) as z:
            for file_info in z.infolist():
                fname = os.path.basename(file_info.filename)
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
                    'latin': str(row['LATINA']).strip(),
                    'image': photos[curr_id]
                })
        
        if not combined:
            st.warning("Kuvia ei löytynyt! Varmista, että kuvan nimi alkaa ID-numerolla (esim. 001_kukka.jpg)")
        return combined
    except Exception as e:
        st.error(f"Yleinen virhe: {e}")
        return None

def next_question():
    if st.session_state.data:
        st.session_state.current_item = random.choice(st.session_state.data)
        st.session_state.feedback = ""
        st.session_state.show_hint = False

# --- ИНТЕРФЕЙС ---
with st.sidebar:
    st.header("⚙️ Asetukset")
    t_file = st.file_uploader("1. Lataa Excel", type=['xlsx', 'csv'])
    p_file = st.file_uploader("2. Lataa kuvat (ZIP)", type=['zip'])
    
    if st.button("🚀 Käynnistä / Aloita alusta"):
        if t_file and p_file:
            loaded = load_data(t_file, p_file)
            if loaded:
                st.session_state.data = loaded
                st.session_state.score = 0
                st.session_state.total = 0
                next_question()
                st.success(f"Ladattu {len(st.session_state.data)} kasvia!")

st.title("🌿 Kasvion harjoitus")

if st.session_state.current_item:
    item = st.session_state.current_item
    
    st.metric("Pisteet", f"{st.session_state.score} / {st.session_state.total}")
    st.image(item['image'], use_container_width=True)
    
    # Поле ввода
    ans = st.text_input("Mikä kasvi tämä on?", key="ans_input").strip()
    
    col1, col2, col3 = st.columns(3)
    
    if col1.button("Tarkista"):
        st.session_state.total += 1
        if ans.lower() == item['name'].lower():
            st.session_state.score += 1
            st.toast("✅ Oikein!", icon="🌱")
            next_question()
            st.rerun()
        else:
            st.session_state.feedback = f"❌ Väärin. Yritä uudelleen!"

    if col2.button("Vihje"):
        st.session_state.show_hint = True
        
    if col3.button("Seuraava →"):
        st.session_state.total += 1
        next_question()
        st.rerun()

    if st.session_state.show_hint:
        st.info(f"💡 Latina: {item['latin']} | Alkaa: {item['name'][0].upper()}...")
    
    if st.session_state.feedback:
        st.error(st.session_state.feedback)
        st.write(f"Vastaus oli: **{item['name']}**")
else:
    st.info("Lataa tiedot vasemmalta aloittaaksesi.")
