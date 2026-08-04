import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# 1. KONFIGURACJA STRONY I ZMIENNE
st.set_page_config(page_title="Grafik Ekipy", layout="wide", initial_sidebar_state="expanded")

EKIPA = ["Michał", "Tomek", "Kamil", "Marek", "Łukasz"]
ETAPY = ["Montaż", "Realizacja", "Demontaż"]

# 2. BAZA DANYCH
conn = sqlite3.connect('montaze_v4.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS wydarzenia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nazwa TEXT,
        data_od DATE,
        data_do DATE
    )
''')
c.execute('''
    CREATE TABLE IF NOT EXISTS harmonogram (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        wydarzenie_id INTEGER,
        osoba TEXT,
        data DATE,
        etap TEXT,
        FOREIGN KEY(wydarzenie_id) REFERENCES wydarzenia(id)
    )
''')
conn.commit()

# 3. CSS - ŚWIECĄCE KAFELKI I KARTY WYDARZEŃ
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: #e2e8f0; }
    header {visibility: hidden;}
    
    .event-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .event-title {
        color: #f8fafc;
        margin-top: 0;
        margin-bottom: 5px;
        font-size: 22px;
        font-weight: 600;
    }
    .event-dates {
        color: #94a3b8;
        font-size: 14px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .grid-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0 8px;
    }
    .grid-table th {
        color: #64748b;
        font-size: 12px;
        text-transform: uppercase;
        font-weight: 600;
        text-align: center;
        padding-bottom: 10px;
        border-bottom: 1px solid #334155;
    }
    .grid-table th:first-child { text-align: left; }
    
    .grid-table td {
        background-color: #0f172a;
        padding: 12px;
        text-align: center;
        vertical-align: middle;
    }
    .grid-table td:first-child {
        text-align: left;
        border-top-left-radius: 8px;
        border-bottom-left-radius: 8px;
        font-weight: 500;
        color: #cbd5e1;
        width: 20%;
    }
    .grid-table td:last-child {
        border-top-right-radius: 8px;
        border-bottom-right-radius: 8px;
    }
    
    /* Główne Kafelki */
    .glow-pill {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: bold;
        text-align: center;
        letter-spacing: 0.5px;
        margin: 2px;
    }
    .glow-montaz { 
        background-color: rgba(59, 130, 246, 0.2); 
        color: #60a5fa; 
        border: 1px solid #3b82f6;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.4);
    } 
    .glow-realizacja { 
        background-color: rgba(245, 158, 11, 0.2); 
        color: #fbbf24; 
        border: 1px solid #f59e0b;
        box-shadow: 0 0 10px rgba(245, 158, 11, 0.4);
    } 
    .glow-demontaz { 
        background-color: rgba(239, 68, 68, 0.2); 
        color: #f87171; 
        border: 1px solid #ef4444;
        box-shadow: 0 0 10px rgba(239, 68, 68, 0.4);
    } 
    .pill-dim { 
        background-color: transparent; 
        color: #334155; 
        border: 1px dashed #334155;
    } 
    
    .date-tag {
        font-size: 10px;
        opacity: 0.8;
        display: block;
        margin-top: 2px;
        font-weight: normal;
    }
</style>
""", unsafe_allow_html=True)


# 4. POBRANIE DANYCH
df_wydarzenia = pd.read_sql("SELECT * FROM wydarzenia ORDER BY data_od ASC", conn)
df_harmonogram = pd.read_sql("SELECT * FROM harmonogram", conn)

# 5. WIDOK GŁÓWNY - KARTY WYDARZEŃ
st.markdown("<h2 style='text-align: center; color: white; margin-bottom: 40px;'>🛠️ Zarządzanie Ekipą</h2>", unsafe_allow_html=True)

if df_wydarzenia.empty:
    st.info("Brak zaplanowanych wydarzeń. Dodaj pierwsze z lewej strony.")
else:
    for _, wyd in df_wydarzenia.iterrows():
        wyd_id = wyd['id']
        nazwa = wyd['nazwa']
        d_od = datetime.strptime(wyd['data_od'], "%Y-%m-%d").strftime("%d.%m.%Y")
        d_do = datetime.strptime(wyd['data_do'], "%Y-%m-%d").strftime("%d.%m.%Y")
        
        harm_wyd = df_harmonogram[df_harmonogram['wydarzenie_id'] == wyd_id]
        
        # NOWY SPOSÓB BUDOWANIA HTML - bez wcięć psujących Markdowna
        html = ""
        html += "<div class='event-card'>"
        html += f"<h3 class='event-title'>📍 {nazwa}</h3>"
        html += f"<div class='event-dates'>📅 {d_od} - {d_do}</div>"
        html += "<table class='grid-table'>"
        html += "<thead><tr><th>Ekipa</th><th>Montaż</th><th>Realizacja</th><th>Demontaż</th></tr></thead>"
        html += "<tbody>"
        
        for osoba in EKIPA:
            html += f"<tr><td>{osoba}</td>"
            wpisy_osoby = harm_wyd[harm_wyd['osoba'] == osoba]
            
            for etap in ETAPY:
                wpisy_etapu = wpisy_osoby[wpisy_osoby['etap'] == etap]
                
                if not wpisy_etapu.empty:
                    pills = ""
                    if etap == 'Montaż': class_name = "glow-montaz"
                    elif etap == 'Realizacja': class_name = "glow-realizacja"
                    else: class_name = "glow-demontaz"
                    
                    for _, w in wpisy_etapu.iterrows():
                        data_short = datetime.strptime(w['data'], "%Y-%m-%d").strftime("%d.%m")
                        pills += f"<div class='glow-pill {class_name}'>{etap.upper()}<span class='date-tag'>{data_short}</span></div>"
                    
                    html += f"<td>{pills}</td>"
                else:
                    html += "<td><div class='glow-pill pill-dim'>-</div></td>"
                    
            html += "</tr>"
            
        html += "</tbody></table></div>"
        
        st.markdown(html, unsafe_allow_html=True)


# 6. PANEL BOCZNY - ZAKŁADKI UX
tab1, tab2 = st.sidebar.tabs(["📝 Planowanie", "⚙️ Zarządzanie"])

with tab1:
    st.markdown("### 1. Utwórz Wydarzenie")
    with st.form("form_wydarzenie", clear_on_submit=True):
        nazwa_wyd = st.text_input("Nazwa / Miejsce", placeholder="np. Spodek - FOH / System")
        col_od, col_do = st.columns(2)
        with col_od: data_od = st.date_input("Od", datetime.today())
        with col_do: data_do = st.date_input("Do", datetime.today() + timedelta(days=2))
        
        if st.form_submit_button("Dodaj do bazy"):
            if nazwa_wyd and data_od <= data_do:
                c.execute("INSERT INTO wydarzenia (nazwa, data_od, data_do) VALUES (?, ?, ?)", (nazwa_wyd, str(data_od), str(data_do)))
                conn.commit()
                st.rerun()
            else:
                st.error("Błędne daty lub brak nazwy.")

    st.markdown("---")
    st.markdown("### 2. Obsadź Ekipę")
    if not df_wydarzenia.empty:
        wyd_dict = {row['id']: f"{row['nazwa']} ({row['data_od']} - {row['data_do']})" for _, row in df_wydarzenia.iterrows()}
        wybrane_wyd_id = st.selectbox("Wybierz wydarzenie", options=list(wyd_dict.keys()), format_func=lambda x: wyd_dict[x])
        
        wyd_info = df_wydarzenia[df_wydarzenia['id'] == wybrane_wyd_id].iloc[0]
        start_d = datetime.strptime(wyd_info['data_od'], "%Y-%m-%d").date()
        end_d = datetime.strptime(wyd_info['data_do'], "%Y-%m-%d").date()
        
        with st.form("form_obsada", clear_on_submit=True):
            osoba = st.selectbox("Osoba", EKIPA)
            data_przydzialu = st.date_input("Dzień", value=start_d, min_value=start_d, max_value=end_d)
            etapy = st.multiselect("Zadanie na ten dzień", ETAPY)
            
            if st.form_submit_button("Zapisz przydział"):
                if etapy:
                    for e in etapy:
                        c.execute("INSERT INTO harmonogram (wydarzenie_id, osoba, data, etap) VALUES (?, ?, ?, ?)",
                                  (wybrane_wyd_id, osoba, str(data_przydzialu), e))
                    conn.commit()
                    st.rerun()
                else:
                    st.error("Wybierz co najmniej jeden etap!")
    else:
        st.info("Najpierw utwórz wydarzenie wyżej.")

with tab2:
    st.markdown("### 🗑️ Usuń przydział")
    wszystkie_wpisy = pd.read_sql("""
        SELECT h.id, w.nazwa, h.data, h.osoba, h.etap 
        FROM harmonogram h 
        JOIN wydarzenia w ON h.wydarzenie_id = w.id 
        ORDER BY h.data DESC
    """, conn)
    
    if not wszystkie_wpisy.empty:
        opcje = {row['id']: f"{row['data']} | {row['nazwa']} ({row['osoba']} - {row['etap']})" for _, row in wszystkie_wpisy.iterrows()}
        wpis_del = st.selectbox("Wybierz wpis", options=list(opcje.keys()), format_func=lambda x: opcje[x])
        if st.button("Usuń przydział"):
            c.execute("DELETE FROM harmonogram WHERE id = ?", (wpis_del,))
            conn.commit()
            st.rerun()
            
    st.markdown("---")
    st.markdown("### ⚠️ Usuń wydarzenie")
    if not df_wydarzenia.empty:
        wyd_del = st.selectbox("Wybierz wydarzenie", options=list(wyd_dict.keys()), format_func=lambda x: wyd_dict[x], key="wyd_del")
        if st.button("Usuń całkowicie"):
            c.execute("DELETE FROM wydarzenia WHERE id = ?", (wyd_del,))
            c.execute("DELETE FROM harmonogram WHERE wydarzenie_id = ?", (wyd_del,))
            conn.commit()
            st.rerun()