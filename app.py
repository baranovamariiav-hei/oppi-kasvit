import streamlit as st
import pandas as pd
import random
import zipfile
import io
from PIL import Image

st.set_page_config(page_title="Kasvioppi Treenaaja", layout="centered")

# Дизайн интерфейса
st.markdown("""
    <style>
    .main { background-color: #f7f9f7; }
    .stButton>button { width: 100%; border-radius: 15px; height: 3em; background-color: #e8f5e9; border: 1px solid #2e7d32; color: #2e7d32; font-weight: bold; }
    .stButton>button:hover { background-color: #2e7d32; color: white; }
    img { border-radius: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .stat-box { padding: 15px; border-radius: 15px; background-color: #ffffff; border: 1px solid #ddd; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- ИНИЦИАЛИЗАЦИЯ ---
if 'data' not in st.session_state:
    st.session_state.data = None  # Тут храним сопоставленные данные
    st.session_state.current_item = None
    st.session_state.score = 0
    st.session_state.total = 0
    st.session_state.feedback = ""
    st.session_state.show_hint = False

def load_data(table_file, zip_file):
    # Читаем таблицу
    if table_file.name.endswith('.csv'):
        df = pd.read_csv(table_file)
    else:
        df = pd.read_excel(table_file)
    
    # Приводим ID к строке с ведущими нулями (001)
    df['ID'] = df['ID'].astype(str).str.zfill(3)
    
    # Распаковываем ZIP в память
    photos = {}
    with zipfile.ZipFile(zip_file) as z:
        for file_info in z.infolist():
            if file_info.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                # Берем первые 3 цифры из имени файла
                file_id = os.path.basename(file_info.filename)[:3]
                with z.open(file_info) as f:
                    photos[file_id] = f.read()
    
    # Сопоставляем
    combined = []
    for _, row in df.iterrows():
        if row['ID'] in photos:
            combined.append({
                'id': row['ID'],
                'name': str(row['Nimi']).strip(), # Название на финском
                'latin': str(row['Latina']).strip(),
                'image': photos[row['ID']]
            })
    return combined

def next_question():
    if st.session_state.data:
        st.session_state.current_item = random.choice(st.session_state.data)
        st.session_state.feedback = ""
        st.session_state.show_hint = False

# --- САЙДБАР ---
with st.sidebar:
    st.header("⚙️ Asetukset")
    t_file = st.file_uploader("1. Lataa taulukko (ID, Nimi, Latina)", type=['xlsx', 'csv'])
    p_file = st.file_uploader("2. Lataa kuvat (ZIP)", type=['zip'])
    
    if st.button("🚀 Käynnistä / Aloita alusta"):
        if t_file and p_file:
            st.session_state.data = load_data(t_file, p_file)
            st.session_state.score = 0
            st.session_state.total = 0
            next_question()
            st.success(f"Ladattu {len(st.session_state.data)} kasvia!")

# --- ОСНОВНОЙ ЭКРАН ---
st.title("🌿 Kasvion harjoitus")

if st.session_state.current_item:
    item = st.session_state.current_item
    
    # Статистика сверху
    cols = st.columns(3)
    cols[0].metric("Pisteet", st.session_state.score)
    cols[1].metric("Yhteensä", st.session_state.total)
    
    # Фото
    st.image(item['image'], use_container_width=True)
    
    # Ввод ответа
    answer = st.text_input("Mikä kasvi tämä on?", key="ans_input").strip()
    
    c1, c2, c3 = st.columns(3)
    
    if c1.button("Tarkista"):
        st.session_state.total += 1
        if answer.lower() == item['name'].lower():
            st.session_state.score += 1
            st.session_state.feedback = "✅ Oikein!"
            next_question()
            st.rerun()
        else:
            st.session_state.feedback = f"❌ Väärin. Yritä uudelleen vai katso vihje."

    if c2.button("Vihje"):
        st.session_state.show_hint = True
        
    if c3.button("Luovuta"):
        st.session_state.feedback = f"Oikea vastaus: {item['name']} ({item['latin']})"
        if st.button("Seuraava →"):
            next_question()
            st.rerun()

    # Вывод подсказки или фидбека
    if st.session_state.show_hint:
        st.info(f"💡 Latina: {item['latin']} | Alkaa: {item['name'][0]}")
    
    if st.session_state.feedback:
        st.write(st.session_state.feedback)

else:
    st.write("Lataa tiedot vasemmalta aloittaaksesi.")
