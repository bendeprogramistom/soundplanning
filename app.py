from datetime import datetime
import pandas as pd
import sqlite3
import streamlit as st

# Konfiguracja strony
st.set_page_config(
    page_title="Grafik Montaży", page_icon="🏗️", layout="wide"
)

# Inicjalizacja bazy danych SQLite
conn = sqlite3.connect("montaze.db", check_same_thread=False)
c = conn.cursor()
c.execute(
    """
    CREATE TABLE IF NOT EXISTS wydarzenia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nazwa TEXT,
        osoba TEXT,
        data DATE,
        etap TEXT
    )
"""
)
conn.commit()

st.title("🏗️ Grafik Pracy Ekipy Montażowej")

# --- PANEL BOCZNY: DODAWANIE WPISU ---
st.sidebar.header("➕ Dodaj / Planuj")
with st.sidebar.form("dodaj_form", clear_on_submit=True):
  nazwa = st.text_input("Nazwa wydarzenia / klienta")
  osoba = st.text_input("Kto (imię / ekipa)")
  data = st.date_input("Data", datetime.today())
  etap = st.selectbox("Etap", ["Montaż", "Realizacja", "Demontaż"])

  submit = st.form_submit_button("Zapisz w grafiku")
  if submit:
    if nazwa and osoba:
      c.execute(
          "INSERT INTO wydarzenia (nazwa, osoba, data, etap) VALUES (?, ?, ?,"
          " ?)",
          (nazwa, osoba, str(data), etap),
      )
      conn.commit()
      st.sidebar.success("Dodano pomyślnie!")
      st.rerun()
    else:
      st.sidebar.error("Wypełnij nazwę i osobę!")

# --- WIDOK GŁÓWNY: GRAFIK MIESIĘCZNY ---
st.subheader("📅 Aktualny Grafik")

# Pobranie danych
df = pd.read_sql("SELECT * FROM wydarzenia", conn)

if not df.empty:
  df["data"] = pd.to_datetime(df["data"])

  # Filtrowanie po miesiącu
  lata = sorted(df["data"].dt.year.unique())
  wybrany_rok = st.selectbox("Rok", lata, index=len(lata) - 1)

  miesiace = {
      1: "Styczeń",
      2: "Luty",
      3: "Marzec",
      4: "Kwiecień",
      5: "Maj",
      6: "Czerwiec",
      7: "Lipiec",
      8: "Sierpień",
      9: "Wrzesień",
      10: "Październik",
      11: "Listopad",
      12: "Grudzień",
  }

  wybrany_miesiac = st.selectbox(
      "Miesiąc",
      options=list(miesiace.keys()),
      format_func=lambda x: miesiace[x],
      index=datetime.now().month - 1,
  )

  filtered_df = df[
      (df["data"].dt.year == wybrany_rok)
      & (df["data"].dt.month == wybrany_miesiac]
  ]

  if not filtered_df.empty:
    # Sortowanie po dacie
    filtered_df = filtered_df.sort_values(by="data")

    # Wyświetlanie w formie ładnej tabeli z możliwością kolorowania etapów
    st.dataframe(
        filtered_df[["data", "nazwa", "osoba", "etap"]].rename(
            columns={
                "data": "Data",
                "nazwa": "Wydarzenie",
                "osoba": "Osoba / Ekipa",
                "etap": "Etap",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    # --- SEKCJA USUWANIA ---
    st.markdown("---")
    st.subheader("🗑️ Usuń wpis")
    wpis_do_usu = st.selectbox(
        "Wybierz pozycję do usunięcia",
        filtered_df["id"].tolist(),
        format_func=lambda x: f"{filtered_df[filtered_df['id'] == x]['data'].dt.strftime('%Y-%m-%d').values[0]} | {filtered_df[filtered_df['id'] == x]['nazwa'].values[0]} ({filtered_df[filtered_df['id'] == x]['osoba'].values[0]})",
    )
    if st.button("Usuń zaznaczone"):
      c.execute("DELETE FROM wydarzenia WHERE id = ?", (wpis_do_usu,))
      conn.commit()
      st.warning("Usunięto wpis.")
      st.rerun()

  else:
    st.info("Brak wpisów w wybranym miesiącu.")
else:
  st.info("Brak jakichkolwiek wpisów w bazie. Dodaj pierwszy po lewej stronie.")