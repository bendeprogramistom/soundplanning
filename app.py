import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# --- 1. KONFIGURACJA I ZMIENNE GLOBALE ---
st.set_page_config(page_title="Crew Manager", page_icon="⚡", layout="centered")

EKIPA = ["Michał", "Tomek", "Kamil", "Marek", "Łukasz"]
ETAPY = ["Montaż", "Realizacja", "Demontaż"]

# --- 2. BAZA DANYCH ---
def init_db():
    conn = sqlite3.connect('crew_manager.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS wydarzenia (id INTEGER PRIMARY KEY AUTOINCREMENT, nazwa TEXT, data_od DATE, data_do DATE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS harmonogram (id INTEGER PRIMARY KEY AUTOINCREMENT, wydarzenie_id INTEGER, osoba TEXT, data DATE, etap TEXT, FOREIGN KEY(wydarzenie_id) REFERENCES wydarzenia(id))''')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- 3. NOWOCZESNY SYSTEM DESIGN (CSS) ---
# Używamy zmiennych CSS dla idealnej spójności, Flexboxa zamiast tabel i fontu z rodziny systemowej.
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp {
        background-color: #09090b; /* Bardzo głęboka czerń/grafit */
        color: #fafafa;
        font-family: 'Inter', sans-serif;
    }
    
    /* Ukrycie domyślnych śmieci Streamlita */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Zmienne kolorystyczne */
    :root {
        --bg-card: #18181b;
        --border-color: #27272a;
        --text-muted: #a1a1aa;
        --color-montaz: #3b82f6;
        --color-montaz-bg: rgba(59, 130, 246, 0.15);
        --color-realizacja: #f59e0b;
        --color-realizacja-bg: rgba(245, 158, 11, 0.15);
        --color-demontaz: #ef4444;
        --color-demontaz-bg: rgba(239, 68, 68, 0.15);
    }

    /* Karta Wydarzenia */
    .ev-card {
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .ev-card:hover {
        border-color: #3f3f46;
    }
    
    /* Nagłówek Karty */
    .ev-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
        padding-bottom: 16px;
        border-bottom: 1px solid var(--border-color);
    }
    .ev-title {
        font-size: 20px;
        font-weight: 600;
        margin: 0;
        color: #ffffff;
    }
    .ev-dates {
        font-size: 13px;
        color: var(--text-muted);
        background: #27272a;
        padding: 4px 10px;
        border-radius: 8px;
        font-weight: 500;
    }

    /* Lista Ekipy (Flexbox) */
    .crew-row {
        display: flex;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px dashed #27272a;
    }
    .crew-row:last-child {
        border-bottom: none;
        padding-bottom: 0;
    }
    .crew-name {
        width: 120px;
        font-weight: 500;
        font-size: 14px;
        color: #e4e4e7;
    }
    
    /* Kontener na zadania */
    .task-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        flex: 1;
    }

    /* Nowoczesne kafelki (Badges) */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.3px;
        text-transform: uppercase;
    }
    .badge .date {
        font-size: 10px;
        opacity: 0.7;
        font-weight: 400;
    }
    
    .b-montaz { background: var(--color-montaz-bg); color: var(--color-montaz); border: 1px solid rgba(59,130,246,0.3); }
    .b-realizacja { background: var(--color-realizacja-bg); color: var(--color-realizacja); border: 1px solid rgba(245,158,11,0.3); }
    .b-demontaz { background: var(--color-demontaz-bg); color: var(--color-demontaz); border: 1px solid rgba(239,68,68,0.3); }
    .b-empty { background: transparent; color: #52525b; font-weight: 400; font-size: 12px; }

</style>
""", unsafe_allow_html=True)

# --- 4. NAWIGACJA GŁÓWNA ---
st.title("⚡ Crew Manager")
menu = st.radio("Nawigacja", ["📋 Dashboard", "➕ Nowe Wydarzenie", "🛠️ Przydziel Ekipę", "🗑️ Zarządzaj"], horizontal=True, label_visibility="collapsed")
st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

# POBRANIE DANYCH GŁÓWNYCH
df_wyd = pd.read_sql("SELECT * FROM wydarzenia ORDER BY data_od ASC", conn)
df_harm = pd.read_sql("SELECT * FROM harmonogram", conn)

# --- 5. LOGIKA WIDOKÓW ---

if menu == "📋 Dashboard":
    if df_wyd.empty:
        st.info("Brak aktywnych wydarzeń. Przejdź do zakładki 'Nowe Wydarzenie'.")
    else:
        for _, wyd in df_wyd.iterrows():
            w_id = wyd['id']
            nazwa = wyd['nazwa']
            d_od = datetime.strptime(wyd['data_od'], "%Y-%m-%d").strftime("%d.%m")
            d_do = datetime.strptime(wyd['data_do'], "%Y-%m-%d").strftime("%d.%m.%Y")
            
            harm_wyd = df_harm[df_harm['wydarzenie_id'] == w_id]
            
            # Budowa HTML w jednej zmiennej ciągłej (aby uniknąć problemów z Markdownem)
            html = f"<div class='ev-card'><div class='ev-header'><h3 class='ev-title'>{nazwa}</h3><div class='ev-dates'>🗓️ {d_od} - {d_do}</div></div><div class='ev-body'>"
            
            for osoba in EKIPA:
                wpisy_osoby = harm_wyd[harm_wyd['osoba'] == osoba]
                
                html += f"<div class='crew-row'><div class='crew-name'>👤 {osoba}</div><div class='task-container'>"
                
                if wpisy_osoby.empty:
                    html += "<div class='b-empty'>Brak przydziału</div>"
                else:
                    # Sortujemy wpisy po dacie żeby było logicznie
                    wpisy_osoby = wpisy_osoby.sort_values(by="data")
                    for _, w in wpisy_osoby.iterrows():
                        etap = w['etap']
                        data_short = datetime.strptime(w['data'], "%Y-%m-%d").strftime("%d.%m")
                        
                        if etap == 'Montaż': c_class = "b-montaz"
                        elif etap == 'Realizacja': c_class = "b-realizacja"
                        else: c_class = "b-demontaz"
                        
                        html += f"<div class='badge {c_class}'>{etap} <span class='date'>{data_short}</span></div>"
                        
                html += "</div></div>" # Koniec zadania i wiersza
            
            html += "</div></div>" # Koniec body i karty
            st.markdown(html, unsafe_allow_html=True)


elif menu == "➕ Nowe Wydarzenie":
    st.subheader("Utwórz nowe wydarzenie")
    with st.container(border=True):
        with st.form("form_wydarzenie", clear_on_submit=True):
            nazwa_wyd = st.text_input("Nazwa / Miejsce (np. Spodek - FOH)")
            col1, col2 = st.columns(2)
            with col1: data_od = st.date_input("Od", datetime.today())
            with col2: data_do = st.date_input("Do", datetime.today() + timedelta(days=2))
            
            if st.form_submit_button("Zapisz Wydarzenie", use_container_width=True):
                if nazwa_wyd and data_od <= data_do:
                    c.execute("INSERT INTO wydarzenia (nazwa, data_od, data_do) VALUES (?, ?, ?)", (nazwa_wyd, str(data_od), str(data_do)))
                    conn.commit()
                    st.success("Dodano wydarzenie! Przejdź do zakładki 'Przydziel Ekipę'.")
                else:
                    st.error("Błędne daty lub brak nazwy.")


elif menu == "🛠️ Przydziel Ekipę":
    st.subheader("Ustaw harmonogram")
    if df_wyd.empty:
        st.warning("Najpierw utwórz wydarzenie.")
    else:
        wyd_dict = {row['id']: f"{row['nazwa']} ({row['data_od']} - {row['data_do']})" for _, row in df_wyd.iterrows()}
        wybrane_wyd_id = st.selectbox("Wybierz wydarzenie", options=list(wyd_dict.keys()), format_func=lambda x: wyd_dict[x])
        
        wyd_info = df_wyd[df_wyd['id'] == wybrane_wyd_id].iloc[0]
        start_d = datetime.strptime(wyd_info['data_od'], "%Y-%m-%d").date()
        end_d = datetime.strptime(wyd_info['data_do'], "%Y-%m-%d").date()
        
        with st.container(border=True):
            with st.form("form_obsada", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1: osoba = st.selectbox("Członek ekipy", EKIPA)
                with col2: data_przydzialu = st.date_input("Data przydziału", value=start_d, min_value=start_d, max_value=end_d)
                
                etapy = st.multiselect("Zadanie (można wybrać kilka)", ETAPY)
                
                if st.form_submit_button("Zapisz w grafiku", use_container_width=True):
                    if etapy:
                        for e in etapy:
                            c.execute("INSERT INTO harmonogram (wydarzenie_id, osoba, data, etap) VALUES (?, ?, ?, ?)",
                                      (wybrane_wyd_id, osoba, str(data_przydzialu), e))
                        conn.commit()
                        st.success(f"Zapisano wpis dla: {osoba}")
                    else:
                        st.error("Wybierz co najmniej jeden etap!")


elif menu == "🗑️ Zarządzaj":
    st.subheader("Usuwanie danych")
    
    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.markdown("#### Usuń pojedynczy wpis")
            wszystkie_wpisy = pd.read_sql("SELECT h.id, w.nazwa, h.data, h.osoba, h.etap FROM harmonogram h JOIN wydarzenia w ON h.wydarzenie_id = w.id ORDER BY h.data DESC", conn)
            
            if not wszystkie_wpisy.empty:
                opcje_wpisow = {row['id']: f"{row['data']} | {row['osoba']} - {row['etap']} ({row['nazwa']})" for _, row in wszystkie_wpisy.iterrows()}
                wpis_del = st.selectbox("Wybierz przydział", options=list(opcje_wpisow.keys()), format_func=lambda x: opcje_wpisow[x])
                if st.button("Usuń przydział", type="primary"):
                    c.execute("DELETE FROM harmonogram WHERE id = ?", (wpis_del,))
                    conn.commit()
                    st.rerun()
            else:
                st.caption("Brak wpisów w harmonogramie.")
                
    with col_b:
        with st.container(border=True):
            st.markdown("#### Usuń całe wydarzenie")
            if not df_wyd.empty:
                wyd_dict = {row['id']: row['nazwa'] for _, row in df_wyd.iterrows()}
                wyd_del = st.selectbox("Wybierz wydarzenie do skasowania", options=list(wyd_dict.keys()), format_func=lambda x: wyd_dict[x])
                if st.button("Skasuj wydarzenie", type="primary"):
                    c.execute("DELETE FROM wydarzenia WHERE id = ?", (wyd_del,))
                    c.execute("DELETE FROM harmonogram WHERE wydarzenie_id = ?", (wyd_del,))
                    conn.commit()
                    st.rerun()
            else:
                st.caption("Brak wydarzeń w bazie.")