import streamlit as st
import pandas as pd
import random
import zipfile
import io

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

if 'data' not in st.session_state:
    st.session_state.data = None
    st.session_state.current_item = None
    st.session_state.score = 0
    st.session_state.total = 0
    st.session_state.show_answer = False
    st.session_state.hint_text = "" # Здесь храним текущую подсказку (правильное начало)

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
        st.session_state.show_answer = False
        st.session_state.hint_text = ""

# --- ИНТЕРФЕЙС ---
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

st.title("🌿 Kasvioppi: Treenaaja")

if st.session_state.current_item:
    item = st.session_state.current_item
    st.markdown(f"<div class='stat-box'><b>Pisteet:</b> {st.session_state.score} / {st.session_state.total}</div>", unsafe_allow_html=True)
    st.image(item['image'], use_container_width=True)
    
    # Поле ввода. Мы передаем в него значение из hint_text
    # Если hint_text изменится (нажата подсказка), поле обновится
    ans = st.text_input("Mikä kasvi tämä on?", value=st.session_state.hint_text, key="ans_input").strip()
    
    col1, col2, col3 = st.columns(3)
    
    if col1.button("Tarkista"):
        st.session_state.total += 1
        if ans.lower() == item['name'].lower():
            st.session_state.score += 1
            st.balloons()
            next_question()
            st.rerun()
        else:
            st.error("Väärin! Yritä uudelleen tai käytä vihjettä.")

    if col2.button("Vihje"):
        correct_name = item['name']
        current_input = ans
        
        # Логика определения правильной части
        match_len = 0
        for i in range(min(len(current_input), len(correct_name))):
            if current_input[i].lower() == correct_name[i].lower():
                match_len += 1
            else:
                break
        
        # Обрезаем до правильного и добавляем ОДНУ букву
        new_hint = correct_name[:match_len + 1]
        st.session_state.hint_text = new_hint
        st.rerun()

    if col3.button("Luovuta"):
        st.session_state.show_answer = True

    if st.session_state.show_answer:
        st.write(f"Oikea vastaus: **{item['name']}** (*{item['latin']}*)")
        if st.button("Seuraava →"):
            st.session_state.total += 1
            next_question()
            st.rerun()
else:
    st.info("Lataa tiedostot vasemmalta aloittaaksesi.")
