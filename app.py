import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# --- 1. KONFIGURACJA ---
st.set_page_config(page_title="Grafik Ekipy", layout="wide")

EKIPA = ["Michał", "Tomek", "Kamil", "Marek", "Łukasz"]

# Możliwe kombinacje zadań w jednej komórce (dla wygody klikania z listy)
OPCJE_ETAPOW = [
    "",
    "Montaż",
    "Realizacja",
    "Demontaż",
    "Montaż + Realizacja",
    "Realizacja + Demontaż",
    "Montaż + Demontaż",
    "Montaż + Realizacja + Demontaż"
]

# --- 2. BAZA DANYCH ---
conn = sqlite3.connect('crew_interactive.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS wydarzenia (id INTEGER PRIMARY KEY AUTOINCREMENT, nazwa TEXT, data_od DATE, data_do DATE)''')
c.execute('''CREATE TABLE IF NOT EXISTS harmonogram (id INTEGER PRIMARY KEY AUTOINCREMENT, wydarzenie_id INTEGER, osoba TEXT, data DATE, etap TEXT, FOREIGN KEY(wydarzenie_id) REFERENCES wydarzenia(id))''')
conn.commit()

st.title("🎛️ Interaktywny Grafik")

# --- 3. GÓRNY PANEL: TWORZENIE WYDARZEŃ ---
with st.expander("➕ Utwórz nowe wydarzenie (kliknij, aby rozwinąć)", expanded=False):
    with st.form("form_wyd"):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1: nazwa_wyd = st.text_input("Nazwa wydarzenia")
        with col2: data_od = st.date_input("Od")
        with col3: data_do = st.date_input("Do", data_od + timedelta(days=2))
        
        if st.form_submit_button("Dodaj do bazy"):
            if nazwa_wyd and data_od <= data_do:
                c.execute("INSERT INTO wydarzenia (nazwa, data_od, data_do) VALUES (?, ?, ?)", (nazwa_wyd, str(data_od), str(data_do)))
                conn.commit()
                st.success("Dodano wydarzenie!")
                st.rerun()

st.divider()

# --- 4. GŁÓWNY PANEL: INTERAKTYWNA SIATKA (EXCEL-LIKE) ---
df_wyd = pd.read_sql("SELECT * FROM wydarzenia ORDER BY data_od DESC", conn)

if df_wyd.empty:
    st.info("Baza jest pusta. Utwórz pierwsze wydarzenie w panelu powyżej.")
else:
    # Wybór wydarzenia do edycji
    wyd_dict = {row['id']: f"{row['nazwa']} ({row['data_od']} do {row['data_do']})" for _, row in df_wyd.iterrows()}
    col_sel, col_del = st.columns([4, 1])
    with col_sel:
        wybrane_wyd_id = st.selectbox("Wybierz wydarzenie do zaplanowania:", options=list(wyd_dict.keys()), format_func=lambda x: wyd_dict[x])
    with col_del:
        st.write("")
        st.write("")
        if st.button("🗑️ Usuń to wydarzenie"):
            c.execute("DELETE FROM wydarzenia WHERE id=?", (wybrane_wyd_id,))
            c.execute("DELETE FROM harmonogram WHERE wydarzenie_id=?", (wybrane_wyd_id,))
            conn.commit()
            st.rerun()

    # Logika budowania siatki dni
    wyd_info = df_wyd[df_wyd['id'] == wybrane_wyd_id].iloc[0]
    start_date = datetime.strptime(wyd_info['data_od'], "%Y-%m-%d").date()
    end_date = datetime.strptime(wyd_info['data_do'], "%Y-%m-%d").date()
    
    # Generowanie listy dni trwania wydarzenia
    dni_wydarzenia = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
    dni_str = [d.strftime("%Y-%m-%d") for d in dni_wydarzenia]
    dni_kolumny = [d.strftime("%d.%m (%a)") for d in dni_wydarzenia] # Ładne nagłówki
    
    # Pobranie aktualnego harmonogramu z bazy
    aktualny_harm = pd.read_sql("SELECT osoba, data, etap FROM harmonogram WHERE wydarzenie_id=?", conn, params=(wybrane_wyd_id,))
    
    # Przetworzenie danych na płaską strukturę tabeli (Pivot)
    mapa_wpisow = {}
    for _, row in aktualny_harm.iterrows():
        klucz = (row['osoba'], row['data'])
        if klucz not in mapa_wpisow:
            mapa_wpisow[klucz] = []
        mapa_wpisow[klucz].append(row['etap'])
        
    # Tworzymy czysty DataFrame dla edytora
    df_grid = pd.DataFrame(index=EKIPA, columns=dni_str)
    df_grid.fillna("", inplace=True)
    
    # Wypełniamy DataFrame aktualnymi danymi (łączenie etapów plusem)
    for (osoba, data), etapy in mapa_wpisow.items():
        if data in dni_str and osoba in df_grid.index:
            # Sortowanie, żeby kolejność była logiczna (Montaż przed Realizacją itd.)
            etapy_sorted = sorted(etapy, key=lambda x: ["Montaż", "Realizacja", "Demontaż"].index(x) if x in ["Montaż", "Realizacja", "Demontaż"] else 99)
            df_grid.at[osoba, data] = " + ".join(etapy_sorted)

    # Przygotowanie konfiguracji kolumn dla st.data_editor (każda kolumna z datą to Selectbox)
    kolumny_konfig = {}
    for data_key, naglowek in zip(dni_str, dni_kolumny):
        kolumny_konfig[data_key] = st.column_config.SelectboxColumn(
            naglowek,
            help=f"Wybierz zadania na dzień {naglowek}",
            options=OPCJE_ETAPOW,
            width="medium"
        )

    st.markdown("### 🗓️ Harmonogram (kliknij dwukrotnie w komórkę, aby edytować)")
    
    # WYŚWIETLENIE INTERAKTYWNEGO EDYTORA
    edytowany_df = st.data_editor(
        df_grid,
        column_config=kolumny_konfig,
        use_container_width=True,
        key=f"editor_{wybrane_wyd_id}"
    )

    # ZAPISYWANIE ZMIAN
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 Zapisz zmiany w grafiku", type="primary", use_container_width=True):
        # 1. Najpierw usuwamy stary grafik dla tego wydarzenia
        c.execute("DELETE FROM harmonogram WHERE wydarzenie_id=?", (wybrane_wyd_id,))
        
        # 2. Iterujemy po wyedytowanej tabeli z ekranu i wrzucamy do bazy
        for osoba, wiersz in edytowany_df.iterrows():
            for data_str, wartosc in wiersz.items():
                if wartosc: # Jeśli komórka nie jest pusta
                    # Rozbijamy np. "Montaż + Realizacja" na dwa osobne wpisy do bazy
                    wybrane_etapy = [e.strip() for e in wartosc.split("+")]
                    for etap in wybrane_etapy:
                        c.execute("INSERT INTO harmonogram (wydarzenie_id, osoba, data, etap) VALUES (?, ?, ?, ?)",
                                  (wybrane_wyd_id, osoba, data_str, etap))
        
        conn.commit()
        st.success("✅ Grafik został pomyślnie zaktualizowany!")
        st.balloons()