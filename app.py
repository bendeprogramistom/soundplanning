import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import calendar
import io

# 1. KONFIGURACJA STRONY I ZMIENNE
st.set_page_config(page_title="Grafik Ekipy", layout="wide", initial_sidebar_state="expanded")

EKIPA = ["Michał", "Tomek", "Kamil", "Marek", "Łukasz"]

# 2. INICJALIZACJA RELACYJNEJ BAZY DANYCH
conn = sqlite3.connect('montaze_v3.db', check_same_thread=False)
c = conn.cursor()

# Tabela główna - Wydarzenia
c.execute('''
    CREATE TABLE IF NOT EXISTS wydarzenia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nazwa TEXT,
        data_od DATE,
        data_do DATE
    )
''')
# Tabela podrzędna - Harmonogram z kluczem obcym
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

# 3. ZARZĄDZANIE STANEM (Nawigacja po czasie)
if 'current_date' not in st.session_state:
    st.session_state.current_date = datetime.now()

def change_week(days):
    st.session_state.current_date += timedelta(days=days)

def go_today():
    st.session_state.current_date = datetime.now()

today = st.session_state.current_date
start_of_week = today - timedelta(days=today.weekday())
dates_of_week = [start_of_week + timedelta(days=i) for i in range(7)]
month_name = calendar.month_name[today.month]
year = today.year

# 4. CUSTOM CSS (Material Design, Ciemny motyw)
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: #e2e8f0; }
    header {visibility: hidden;}
    
    .schedule-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #1e293b;
        border-radius: 10px;
        overflow: hidden;
        margin-top: 20px;
    }
    .schedule-table th {
        background-color: #0f172a;
        color: #94a3b8;
        font-size: 12px;
        text-transform: uppercase;
        padding: 15px;
        border-bottom: 1px solid #334155;
    }
    .schedule-table td {
        padding: 8px 10px;
        border-bottom: 1px solid #334155;
        text-align: center;
        font-size: 14px;
        color: #cbd5e1;
        vertical-align: top;
    }
    .schedule-table .row-header {
        text-align: left;
        font-weight: 600;
        color: #38bdf8;
        vertical-align: middle;
    }
    
    /* Kafelki (Pills) */
    .pill {
        display: block;
        padding: 4px 8px;
        margin: 4px auto;
        border-radius: 6px;
        font-size: 11px;
        font-weight: bold;
        min-width: 80px;
        max-width: 100px;
        text-align: center;
        letter-spacing: 0.5px;
    }
    .pill-montaz { background-color: #3b82f6; color: white; } 
    .pill-realizacja { background-color: #f59e0b; color: white; } 
    .pill-demontaz { background-color: #ef4444; color: white; } 
    .pill-off { background-color: #334155; color: #64748b; font-weight: normal;} 
</style>
""", unsafe_allow_html=True)

# 5. HEADER (Nawigacja)
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown(f"<h3 style='text-align: center; color: white;'>{month_name} {year}</h3>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1])
    with c2: st.button("❮ Poprzedni", on_click=change_week, args=(-7,))
    with c3: st.button("DZIŚ", on_click=go_today, use_container_width=True)
    with c4: st.button("Następny ❯", on_click=change_week, args=(7,))

# Pobranie połączonych danych (JOIN)
start_str = dates_of_week[0].strftime("%Y-%m-%d")
end_str = dates_of_week[6].strftime("%Y-%m-%d")
query = f"""
    SELECT h.id, w.nazwa, h.osoba, h.data, h.etap 
    FROM harmonogram h
    JOIN wydarzenia w ON h.wydarzenie_id = w.id
    WHERE h.data BETWEEN '{start_str}' AND '{end_str}'
"""
df = pd.read_sql(query, conn)

# Eksport
with col3:
    if not df.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Grafik')
        excel_data = output.getvalue()
        st.download_button("📥 Pobierz Excel", data=excel_data, file_name=f"Grafik_{start_str}.xlsx", mime="application/vnd.ms-excel")

# 6. GENEROWANIE TABELI HTML
days_headers = "".join([f"<th>{d.strftime('%a')}<br><span style='font-size:10px; color:#64748b;'>{d.strftime('%d.%m')}</span></th>" for d in dates_of_week])

html_table = f"""
<table class="schedule-table">
    <thead>
        <tr>
            <th style="text-align: left;">WYDARZENIE</th>
            <th style="text-align: left;">EKIPA</th>
            {days_headers}
        </tr>
    </thead>
    <tbody>
"""

if df.empty:
    html_table += "<tr><td colspan='9' style='text-align:center; padding:30px;'>Brak wpisów w tym tygodniu.</td></tr>"
else:
    wydarzenia_unikalne = df['nazwa'].unique()
    for wyd in wydarzenia_unikalne:
        df_wyd = df[df['nazwa'] == wyd]
        osoby = df_wyd['osoba'].unique()
        
        for idx, osoba in enumerate(osoby):
            html_table += "<tr>"
            if idx == 0:
                html_table += f"<td rowspan='{len(osoby)}' class='row-header'>{wyd}</td>"
            
            html_table += f"<td style='text-align: left; vertical-align: middle;'>{osoba}</td>"
            
            for d in dates_of_week:
                d_str = d.strftime("%Y-%m-%d")
                wpisy_dnia = df_wyd[(df_wyd['osoba'] == osoba) & (df_wyd['data'] == d_str)]
                
                if not wpisy_dnia.empty:
                    pills_html = ""
                    for _, row in wpisy_dnia.iterrows():
                        etap = row['etap']
                        if etap == 'Montaż': pill_class = 'pill-montaz'
                        elif etap == 'Realizacja': pill_class = 'pill-realizacja'
                        elif etap == 'Demontaż': pill_class = 'pill-demontaz'
                        else: pill_class = 'pill-off'
                        pills_html += f"<div class='pill {pill_class}'>{etap.upper()}</div>"
                    
                    html_table += f"<td>{pills_html}</td>"
                else:
                    html_table += "<td><div class='pill pill-off'>-</div></td>"
                    
            html_table += "</tr>"

html_table += "</tbody></table>"
st.markdown(html_table, unsafe_allow_html=True)


# 7. PANEL BOCZNY - ZAKŁADKI UX
tab1, tab2 = st.sidebar.tabs(["📝 Planowanie", "⚙️ Zarządzanie"])

with tab1:
    st.markdown("### 1. Utwórz Wydarzenie")
    with st.form("form_wydarzenie", clear_on_submit=True):
        nazwa_wyd = st.text_input("Nazwa wydarzenia", placeholder="np. Festiwal - Scena Główna (Line Array)")
        col_od, col_do = st.columns(2)
        with col_od: data_od = st.date_input("Od", today)
        with col_do: data_do = st.date_input("Do", today + timedelta(days=2))
        
        if st.form_submit_button("Dodaj do bazy"):
            if nazwa_wyd and data_od <= data_do:
                c.execute("INSERT INTO wydarzenia (nazwa, data_od, data_do) VALUES (?, ?, ?)", (nazwa_wyd, str(data_od), str(data_do)))
                conn.commit()
                st.success("Dodano wydarzenie!")
                st.rerun()
            else:
                st.error("Błędne daty lub brak nazwy.")

    st.markdown("---")
    st.markdown("### 2. Obsadź Ekipę")
    wszystkie_wyd = pd.read_sql("SELECT * FROM wydarzenia ORDER BY data_od DESC", conn)
    
    if not wszystkie_wyd.empty:
        wyd_dict = {row['id']: f"{row['nazwa']} ({row['data_od']} do {row['data_do']})" for _, row in wszystkie_wyd.iterrows()}
        wybrane_wyd_id = st.selectbox("Wybierz wydarzenie z bazy", options=list(wyd_dict.keys()), format_func=lambda x: wyd_dict[x])
        
        # Pobranie limitów dat dla wybranego wydarzenia, żeby zablokować kalendarz
        wyd_info = wszystkie_wyd[wszystkie_wyd['id'] == wybrane_wyd_id].iloc[0]
        start_d = datetime.strptime(wyd_info['data_od'], "%Y-%m-%d").date()
        end_d = datetime.strptime(wyd_info['data_do'], "%Y-%m-%d").date()
        
        with st.form("form_obsada", clear_on_submit=True):
            osoba = st.selectbox("Osoba z ekipy", EKIPA)
            # Kalendarz ograniczony do czasu trwania wydarzenia
            data_przydzialu = st.date_input("Wybierz dzień", value=start_d, min_value=start_d, max_value=end_d)
            etapy = st.multiselect("Zadanie (można wiele)", ["Montaż", "Realizacja", "Demontaż"])
            
            if st.form_submit_button("Zapisz w harmonogramie"):
                if etapy:
                    for e in etapy:
                        c.execute("INSERT INTO harmonogram (wydarzenie_id, osoba, data, etap) VALUES (?, ?, ?, ?)",
                                  (wybrane_wyd_id, osoba, str(data_przydzialu), e))
                    conn.commit()
                    st.rerun()
                else:
                    st.error("Wybierz co najmniej jeden etap!")
    else:
        st.info("Najpierw utwórz wydarzenie w punkcie 1.")

with tab2:
    st.markdown("### 🗑️ Usuń wpis z grafiku")
    wszystkie_wpisy = pd.read_sql("""
        SELECT h.id, w.nazwa, h.data, h.osoba, h.etap 
        FROM harmonogram h 
        JOIN wydarzenia w ON h.wydarzenie_id = w.id 
        ORDER BY h.data DESC
    """, conn)
    
    if not wszystkie_wpisy.empty:
        opcje = {row['id']: f"{row['data']} | {row['nazwa']} ({row['osoba']} - {row['etap']})" for _, row in wszystkie_wpisy.iterrows()}
        wpis_del = st.selectbox("Wybierz wpis", options=list(opcje.keys()), format_func=lambda x: opcje[x])
        if st.button("Usuń przypisanie"):
            c.execute("DELETE FROM harmonogram WHERE id = ?", (wpis_del,))
            conn.commit()
            st.rerun()
            
    st.markdown("---")
    st.markdown("### ⚠️ Usuń całe wydarzenie")
    if not wszystkie_wyd.empty:
        wyd_del = st.selectbox("Wybierz wydarzenie", options=list(wyd_dict.keys()), format_func=lambda x: wyd_dict[x], key="wyd_del")
        if st.button("Usuń wydarzenie (skasuje też grafiki!)"):
            c.execute("DELETE FROM wydarzenia WHERE id = ?", (wyd_del,))
            c.execute("DELETE FROM harmonogram WHERE wydarzenie_id = ?", (wyd_del,))
            conn.commit()
            st.rerun()