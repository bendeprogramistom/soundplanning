import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import calendar
import io

# 1. KONFIGURACJA STRONY
st.set_page_config(page_title="Grafik Ekipy", layout="wide", initial_sidebar_state="collapsed")

# 2. INICJALIZACJA BAZY DANYCH
conn = sqlite3.connect('montaze.db', check_same_thread=False)
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

# Obliczenia dat dla aktualnego widoku (od poniedziałku do niedzieli)
today = st.session_state.current_date
start_of_week = today - timedelta(days=today.weekday())
dates_of_week = [start_of_week + timedelta(days=i) for i in range(7)]
month_name = calendar.month_name[today.month]
year = today.year

# 4. CUSTOM CSS (Stylizacja na wzór ze zdjęcia)
st.markdown("""
<style>
    /* Ciemne tło dla całej aplikacji */
    .stApp { background-color: #0f172a; color: #e2e8f0; }
    
    /* Ukrycie standardowych nagłówków Streamlita */
    header {visibility: hidden;}
    
    /* Styl tabeli */
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
        padding: 12px 15px;
        border-bottom: 1px solid #334155;
        text-align: center;
        font-size: 14px;
        color: #cbd5e1;
    }
    .schedule-table .row-header {
        text-align: left;
        font-weight: 600;
        color: #38bdf8;
    }
    
    /* Kafelki (Pills) */
    .pill {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        min-width: 80px;
        text-align: center;
    }
    .pill-montaz { background-color: #3b82f6; color: white; } /* Niebieski */
    .pill-realizacja { background-color: #f59e0b; color: white; } /* Pomarańczowy */
    .pill-demontaz { background-color: #ef4444; color: white; } /* Czerwony */
    .pill-off { background-color: #334155; color: #94a3b8; } /* Szary (Wolne) */
</style>
""", unsafe_allow_html=True)

# 5. HEADER (Nawigacja i przyciski eksportu)
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown(f"<h3 style='text-align: center; color: white;'>{month_name} {year}</h3>", unsafe_allow_html=True)
    
    # Przyciski nawigacji
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1])
    with c2: st.button("❮ Poprzedni", on_click=change_week, args=(-7,))
    with c3: st.button("DZIŚ", on_click=go_today, use_container_width=True)
    with c4: st.button("Następny ❯", on_click=change_week, args=(7,))

# Pobranie danych z bazy dla aktualnego tygodnia
start_str = dates_of_week[0].strftime("%Y-%m-%d")
end_str = dates_of_week[6].strftime("%Y-%m-%d")
df = pd.read_sql(f"SELECT * FROM wydarzenia WHERE data BETWEEN '{start_str}' AND '{end_str}'", conn)

# Przycisk pobierania Excel
with col3:
    if not df.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Grafik')
        excel_data = output.getvalue()
        st.download_button(label="📥 Pobierz Excel", data=excel_data, file_name=f"Grafik_{start_str}.xlsx", mime="application/vnd.ms-excel")

# 6. GENEROWANIE TABELI HTML
days_headers = "".join([f"<th>{d.strftime('%a')}<br><span style='font-size:10px; color:#64748b;'>{d.strftime('%b %d, %Y')}</span></th>" for d in dates_of_week])

html_table = f"""
<table class="schedule-table">
    <thead>
        <tr>
            <th style="text-align: left;">WYDARZENIE</th>
            <th style="text-align: left;">EKIPA / OSOBA</th>
            {days_headers}
        </tr>
    </thead>
    <tbody>
"""

if df.empty:
    html_table += "<tr><td colspan='9' style='text-align:center; padding:30px;'>Brak wpisów w tym tygodniu. Dodaj coś w panelu bocznym.</td></tr>"
else:
    # Grupowanie po wydarzeniu i osobie
    wydarzenia = df['nazwa'].unique()
    for wyd in wydarzenia:
        df_wyd = df[df['nazwa'] == wyd]
        osoby = df_wyd['osoba'].unique()
        
        for idx, osoba in enumerate(osoby):
            html_table += "<tr>"
            # Komórka z nazwą wydarzenia (tylko w pierwszym wierszu grupy)
            if idx == 0:
                html_table += f"<td rowspan='{len(osoby)}' class='row-header'>{wyd}</td>"
            
            html_table += f"<td style='text-align: left;'>{osoba}</td>"
            
            # Generowanie kafelków dla poszczególnych dni
            for d in dates_of_week:
                d_str = d.strftime("%Y-%m-%d")
                wpis = df_wyd[(df_wyd['osoba'] == osoba) & (df_wyd['data'] == d_str)]
                
                if not wpis.empty:
                    etap = wpis.iloc[0]['etap']
                    if etap == 'Montaż': pill_class = 'pill-montaz'
                    elif etap == 'Realizacja': pill_class = 'pill-realizacja'
                    elif etap == 'Demontaż': pill_class = 'pill-demontaz'
                    else: pill_class = 'pill-off'
                    
                    html_table += f"<td><span class='pill {pill_class}'>{etap.upper()}</span></td>"
                else:
                    html_table += "<td><span class='pill pill-off'>WOLNE</span></td>"
                    
            html_table += "</tr>"

html_table += "</tbody></table>"

# Wyświetlenie wygenerowanej tabeli
st.markdown(html_table, unsafe_allow_html=True)


# 7. PANEL BOCZNY - DODAWANIE/USUWANIE WPISÓW
st.sidebar.markdown("### ➕ Zarządzaj grafikiem")
with st.sidebar.form("dodaj_form", clear_on_submit=True):
    nazwa = st.text_input("Wydarzenie / Klient")
    osoba = st.text_input("Kto (Osoba / Ekipa)")
    data = st.date_input("Data", today)
    etap = st.selectbox("Etap", ["Montaż", "Realizacja", "Demontaż"])
    
    if st.form_submit_button("Zapisz w grafiku"):
        if nazwa and osoba:
            c.execute("INSERT INTO wydarzenia (nazwa, osoba, data, etap) VALUES (?, ?, ?, ?)",
                      (nazwa, osoba, str(data), etap))
            conn.commit()
            st.rerun()
        else:
            st.error("Wypełnij nazwę i osobę!")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🗑️ Usuń wpis")
wszystkie = pd.read_sql("SELECT * FROM wydarzenia ORDER BY data DESC", conn)
if not wszystkie.empty:
    opcje = {row['id']: f"{row['data']} | {row['nazwa']} ({row['osoba']})" for _, row in wszystkie.iterrows()}
    wpis_del = st.sidebar.selectbox("Wybierz wpis do usunięcia", options=list(opcje.keys()), format_func=lambda x: opcje[x])
    if st.sidebar.button("Usuń wybrany"):
        c.execute("DELETE FROM wydarzenia WHERE id = ?", (wpis_del,))
        conn.commit()
        st.rerun()