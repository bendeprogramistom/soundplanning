import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import calendar
import io

# 1. KONFIGURACJA STRONY I ZMIENNE
st.set_page_config(page_title="Grafik Ekipy", layout="wide", initial_sidebar_state="expanded")

# --- TUTAJ DEFINIUJESZ SWOJĄ EKIPĘ NA SZTYWNO ---
EKIPA = ["Mike", "Karol", "Marcin", "Kuba", "Mateusz", "Robert"]
# -----------------------------------------------

# 2. INICJALIZACJA BAZY DANYCH
conn = sqlite3.connect('montaze_v2.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS wydarzenia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nazwa TEXT,
        osoba TEXT,
        data DATE,
        etap TEXT
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

# 4. CUSTOM CSS (Ciemny motyw, kafelki i układ wielokrotny)
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
    
    /* Kafelki (Pills) - układ jeden pod drugim */
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

# Pobranie danych
start_str = dates_of_week[0].strftime("%Y-%m-%d")
end_str = dates_of_week[6].strftime("%Y-%m-%d")
df = pd.read_sql(f"SELECT * FROM wydarzenia WHERE data BETWEEN '{start_str}' AND '{end_str}'", conn)

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
    wydarzenia = df['nazwa'].unique()
    for wyd in wydarzenia:
        df_wyd = df[df['nazwa'] == wyd]
        osoby = df_wyd['osoba'].unique()
        
        for idx, osoba in enumerate(osoby):
            html_table += "<tr>"
            if idx == 0:
                html_table += f"<td rowspan='{len(osoby)}' class='row-header'>{wyd}</td>"
            
            html_table += f"<td style='text-align: left; vertical-align: middle;'>{osoba}</td>"
            
            # Kafelki dla dni
            for d in dates_of_week:
                d_str = d.strftime("%Y-%m-%d")
                wpisy_dnia = df_wyd[(df_wyd['osoba'] == osoba) & (df_wyd['data'] == d_str)]
                
                if not wpisy_dnia.empty:
                    pills_html = ""
                    # Obsługa wielu etapów w jednym dniu
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


# 7. PANEL BOCZNY (Nowa logika dodawania)
st.sidebar.markdown("### ➕ Planuj")
with st.sidebar.form("dodaj_form", clear_on_submit=True):
    nazwa = st.text_input("Wydarzenie / Klient")
    
    # Wybór osoby ze sztywnej listy
    osoba = st.selectbox("Kto (Osoba z ekipy)", EKIPA)
    data = st.date_input("Data", today)
    
    # Multiselect - można wybrać kilka etapów naraz
    etapy = st.multiselect("Etap (można wybrać kilka)", ["Montaż", "Realizacja", "Demontaż"])
    
    if st.form_submit_button("Zapisz w grafiku"):
        if nazwa and osoba and etapy:
            # Zapis każdego etapu jako osobny wpis w bazie, co pozwala na generowanie wielu kafelków
            for e in etapy:
                c.execute("INSERT INTO wydarzenia (nazwa, osoba, data, etap) VALUES (?, ?, ?, ?)",
                          (nazwa, osoba, str(data), e))
            conn.commit()
            st.rerun()
        else:
            st.error("Wypełnij wszystkie pola i wybierz co najmniej jeden etap!")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🗑️ Usuń wpis")
wszystkie = pd.read_sql("SELECT * FROM wydarzenia ORDER BY data DESC", conn)
if not wszystkie.empty:
    opcje = {row['id']: f"{row['data']} | {row['nazwa']} ({row['osoba']} - {row['etap']})" for _, row in wszystkie.iterrows()}
    wpis_del = st.sidebar.selectbox("Wybierz wpis do usunięcia", options=list(opcje.keys()), format_func=lambda x: opcje[x])
    if st.sidebar.button("Usuń wybrany"):
        c.execute("DELETE FROM wydarzenia WHERE id = ?", (wpis_del,))
        conn.commit()
        st.rerun()