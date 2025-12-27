import streamlit as st
import pandas as pd
import random
import zipfile
import io

# Настройка страницы
st.set_page_config(page_title="Kasvioppi Treenaaja", layout="centered")

# Дизайн
st.markdown("""
    <style>
    .main { background-color: #f7f9f7; }
    .stButton>button { width: 100%; border-radius: 15px; height: 3em; background-color: #e8f5e9; border: 1px solid #2e7d32; color: #2e7d32; font-weight: bold; }
    .stButton>button:hover { background-color: #2e7d32; color: white; }
    img { border-radius: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .stat-box { padding: 10px; border-radius: 10px; background-color: white; border: 1px solid #eee; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# Инициализация переменных в памяти браузера
if 'data' not in st.session_state:
    st.session_state.data = None
    st.session_state.current_item = None
    st.session_state.score = 0
    st.session_state.total = 0
    st.session_state.feedback = ""
    st.session_state.show_hint = False

def load_data(table_file, zip_file):
    try:
        # 1. Читаем таблицу
        if table_file.name.endswith('.csv'):
            df = pd.read_csv(table_file)
        else:
            df = pd.read_excel(table_file)
        
        # Приводим названия колонок к единому виду
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        if 'ID' not in df.columns or 'NIMI' not in df.columns:
            st.error("Virhe: Excelistä puuttuu sarake ID или NIMI!")
            return None

        # Форматируем ID как 001
        df['ID'] = df['ID'].astype(str).str.split('.').str[0].str.zfill(3)
        
        # 2. Читаем фото из ZIP
        photos = {}
        with zipfile.ZipFile(zip_file) as z:
            for file_info in z.infolist():
                # Берем только имя файла без пути к папке
                fname = file_info.filename.split('/')[-1]
                if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                    file_id = fname[:3] # Первые 3 символа
                    with z.open(file_info) as f:
                        photos[file_id] = f.read()
        
        # 3. Сопоставляем данные
        combined = []
        for _, row in df.iterrows():
            curr_id = row['ID']
            if curr_id in photos:
                combined.append({
                    'id': curr_id,
                    'name': str(row['NIMI']).strip(),
                    'latin': str(row.get('LATINA', '')).strip(), # Если нет латыни, будет пусто
                    'image': photos[curr_id]
                })
        return combined
    except Exception as e:
        st.error(f"Virhe tiedostojen luvussa: {e}")
        return None

def next_question():
    if st.session_state.data:
        st.session_state.current_item = random.choice(st.session_state.data)
        st.session_state.feedback = ""
        st.session_state.show_hint = False

# --- ИНТЕРФЕЙС (САЙДБАР) ---
with st.sidebar:
    st.header("⚙️ Asetukset")
    t_file = st.file_uploader("1. Lataa Excel", type=['xlsx', 'csv'])
    p_file = st.file_uploader("2. Lataa kuvat (ZIP)", type=['zip'])
    
    if st.button("🚀 Aloita harjoitus"):
        if t_file and p_file:
            loaded = load_data(t_file, p_file)
            if loaded:
                st.session_state.data = loaded
                st.session_state.score = 0
                st.session_state.total = 0
                next_question()
                st.success(f"Ladattu {len(st.session_state.data)} kasvia!")

# --- ГЛАВНЫЙ ЭКРАН ---
st.title("🌿 Kasvioppi: Treenaaja")

if st.session_state.current_item:
    item = st.session_state.current_item
    
    # Статистика
    st.markdown(f"""<div class='stat-box'><b>Pisteet:</b> {st.session_state.score} / {st.session_state.total}</div>""", unsafe_allow_html=True)
    
    # Картинка
    st.image(item['image'], use_container_width=True)
    
    # Ответ
    ans = st.text_input("Mikä kasvi tämä on?", key="ans_input").strip()
    
    col1, col2, col3 = st.columns(3)
    
    if col1.button("Tarkista"):
        st.session_state.total += 1
        if ans.lower() == item['name'].lower():
            st.session_state.score += 1
            st.balloons()
            st.session_state.feedback = "✅ OIKEIN!"
            st.success(st.session_state.feedback)
            next_question()
            st.rerun()
        else:
            st.session_state.feedback = f"❌ Väärin. Oikea vastaus: {item['name']}"

    if col2.button("Vihje"):
        st.session_state.show_hint = True
        
    if col3.button("Seuraava"):
        st.session_state.total += 1
        next_question()
        st.rerun()

    if st.session_state.show_hint:
        hint_text = f"💡 Alkaa: {item['name'][0].upper()}"
        if item['latin']:
            hint_text += f" | Latina: {item['latin']}"
        st.info(hint_text)
    
    if st.session_state.feedback and "❌" in st.session_state.feedback:
        st.error(st.session_state.feedback)

else:
    st.info("Lataa tiedostot vasemmalta aloittaaksesi.")
