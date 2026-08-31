import streamlit as st
import json
import os
import shutil
from datetime import datetime
import pandas as pd
import hmac

# ============================================================

# CONFIGURAZIONE

# ============================================================

st.set_page_config(
page_title="Källarlager – Vin & Öl",
page_icon="🍾",
layout="wide"
)

st.title("🍾 Källarlager – Vin & Öl")

DB_FILE = "inventario_cantina.json"
BACKUP_FILE = "inventario_cantina_backup.json"

ADMIN_PASSWORD = "Samuelmark123#"

STANDARD_KATEGORIER = {
"Röda viner": {},
"Vita viner": {},
"Mousserande / Spumante": {},
"Hantverksöl": {}
}

LAGERGRÄNS = 3

# ============================================================

# DATABASHANTERING

# ============================================================

def skapa_standarddata():
return {
"produkter": {
kategori: {}
for kategori in STANDARD_KATEGORIER
},
"historik": []
}

def konvertera_gammal_databas(gammal_data):
"""
Gör den gamla inventario_cantina.json kompatibel
med den nya databasen.
"""

```
if not isinstance(gammal_data, dict):
    return skapa_standarddata()

# Om databasen redan använder nya strukturen
if "produkter" in gammal_data:
    produkter = gammal_data.get("produkter", {})
    historik = gammal_data.get("historik", [])

    for kategori in STANDARD_KATEGORIER:
        produkter.setdefault(kategori, {})

    return {
        "produkter": produkter,
        "historik": historik
    }

# Gammal struktur
produkter = {}

for kategori in STANDARD_KATEGORIER:
    produkter[kategori] = gammal_data.get(kategori, {})

# Behåll eventuella extra kategorier
for kategori, innehall in gammal_data.items():
    if kategori not in produkter and isinstance(innehall, dict):
        produkter[kategori] = innehall

return {
    "produkter": produkter,
    "historik": []
}
```

def ladda_databas():

```
if not os.path.exists(DB_FILE):
    return skapa_standarddata()

try:
    with open(DB_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    return konvertera_gammal_databas(data)

except Exception:
    return skapa_standarddata()
```

def spara_databas(data, skapa_backup=True):

```
if skapa_backup and os.path.exists(DB_FILE):
    try:
        shutil.copy2(DB_FILE, BACKUP_FILE)
    except Exception:
        pass

with open(DB_FILE, "w", encoding="utf-8") as f:
    json.dump(
        data,
        f,
        indent=4,
        ensure_ascii=False
    )
```

def registrera_historik(
data,
kategori,
produkt,
typ,
antal,
före,
efter
):

```
data["historik"].append({
    "datum": datetime.now().strftime("%Y-%m-%d"),
    "tid": datetime.now().strftime("%H:%M:%S"),
    "kategori": kategori,
    "produkt": produkt,
    "typ": typ,
    "antal": int(antal),
    "före": int(före),
    "efter": int(efter)
})
```

def lagerstatus(antal):

```
if antal == 0:
    return "❌ SLUT"

if antal < LAGERGRÄNS:
    return "🚨 LÅGT LAGER"

return "🟢 OK"
```

# ============================================================

# LÄS DATABASE

# ============================================================

data = ladda_databas()

produkter = data["produkter"]

# ============================================================

# ADMIN LOGIN

# ============================================================

if "cantina_admin_logged_in" not in st.session_state:
st.session_state["cantina_admin_logged_in"] = False

st.sidebar.header("🔐 Administratör")

if not st.session_state["cantina_admin_logged_in"]:

```
lösenord = st.sidebar.text_input(
    "Administratörslösenord",
    type="password"
)

if st.sidebar.button(
    "🔓 Lås upp redigering",
    use_container_width=True
):

    if hmac.compare_digest(
        lösenord,
        ADMIN_PASSWORD
    ):

        st.session_state[
            "cantina_admin_logged_in"
        ] = True

        st.rerun()

    else:
        st.sidebar.error("❌ Fel lösenord.")
```

else:

```
st.sidebar.success(
    "🔓 Redigeringsläge aktivt"
)

if st.sidebar.button(
    "🔒 Lås och logga ut",
    use_container_width=True
):

    st.session_state[
        "cantina_admin_logged_in"
    ] = False

    st.rerun()
```

# ============================================================

# SIDOPANEL – STATISTIK

# ============================================================

st.sidebar.markdown("---")
st.sidebar.header("📊 Lageröversikt")

alla_produkter = []

for kategori, lista in produkter.items():

```
for produkt, antal in lista.items():

    alla_produkter.append({
        "kategori": kategori,
        "produkt": produkt,
        "antal": int(antal)
    })
```

antal_produkter = len(alla_produkter)

totalt_antal = sum(
x["antal"]
for x in alla_produkter
)

antal_slut = sum(
1
for x in alla_produkter
if x["antal"] == 0
)

antal_lågt = sum(
1
for x in alla_produkter
if 0 < x["antal"] < LAGERGRÄNS
)

st.sidebar.metric(
"🍾 Produkter",
antal_produkter
)

st.sidebar.metric(
"📦 Totalt antal enheter",
totalt_antal
)

st.sidebar.metric(
"❌ Slut",
antal_slut
)

st.sidebar.metric(
"🚨 Lågt lager",
antal_lågt
)

# ============================================================

# RESET DATABASE

# ============================================================

if st.session_state["cantina_admin_logged_in"]:

```
st.sidebar.markdown("---")

with st.sidebar.expander(
    "⚠️ Systemverktyg"
):

    st.warning(
        "Detta raderar hela lagret."
    )

    bekräfta = st.checkbox(
        "Jag bekräftar återställningen."
    )

    if st.button(
        "🗑️ ÅTERSTÄLL HELA LAGRET",
        use_container_width=True
    ):

        if not bekräfta:

            st.error(
                "❌ Bekräfta först."
            )

        else:

            if os.path.exists(DB_FILE):

                try:
                    shutil.copy2(
                        DB_FILE,
                        BACKUP_FILE
                    )
                except Exception:
                    pass

            ny_data = skapa_standarddata()

            spara_databas(
                ny_data,
                skapa_backup=False
            )

            st.success(
                "✅ Lagret har återställts."
            )

            st.rerun()
```

# ============================================================

# AKTUELLT LAGER

# ============================================================

st.header("📋 Aktuellt lager")

if not alla_produkter:

```
st.info(
    "Det finns inga produkter registrerade ännu."
)
```

else:

```
sökning = st.text_input(
    "🔎 Sök produkt eller producent",
    placeholder="t.ex. Chianti, Antinori, IPA..."
).strip().lower()


filtrerade_produkter = [

    x
    for x in alla_produkter

    if (
        not sökning
        or sökning in x["produkt"].lower()
        or sökning in x["kategori"].lower()
    )

]


if filtrerade_produkter:

    tabell = pd.DataFrame([

        {
            "Kategori": x["kategori"],
            "Produkt / Producent": x["produkt"],
            "Tillgängligt": f'{x["antal"]} st',
            "Status": lagerstatus(x["antal"])
        }

        for x in filtrerade_produkter

    ])


    st.dataframe(
        tabell,
        use_container_width=True,
        hide_index=True
    )

else:

    st.warning(
        "🔎 Ingen produkt hittades."
    )
```

# ============================================================

# ADMIN – LAGERÄNDRING

# ============================================================

if st.session_state["cantina_admin_logged_in"]:

```
st.markdown("---")

st.header(
    "📦 Registrera lagerändring"
)


kategorier = list(
    produkter.keys()
)


col1, col2, col3, col4 = st.columns(4)


with col1:

    kategori = st.selectbox(
        "1. Kategori",
        kategorier
    )


befintliga_produkter = list(
    produkter[kategori].keys()
)


produktalternativ = [
    "➕ NY PRODUKT"
] + befintliga_produkter


with col2:

    valt_produkt = st.selectbox(
        "2. Produkt",
        produktalternativ
    )


if valt_produkt == "➕ NY PRODUKT":

    produkt = st.text_input(
        "Produkt / Producent",
        placeholder="t.ex. Chianti Classico – Antinori"
    ).strip()

else:

    produkt = valt_produkt


with col3:

    typ = st.radio(
        "3. Operation",
        [
            "🟢 Inleverans (+)",
            "🔴 Uttag (-)"
        ]
    )


with col4:

    antal = st.number_input(
        "4. Antal",
        min_value=1,
        value=6,
        step=1
    )


nuvarande = 0

if produkt:

    nuvarande = int(
        produkter
        .get(kategori, {})
        .get(produkt, 0)
    )


    st.info(
        f"📦 **{produkt}** – "
        f"nuvarande lager: **{nuvarande} st**"
    )


if st.button(
    "💾 REGISTRERA LAGERÄNDRING",
    type="primary",
    use_container_width=True
):

    if not produkt:

        st.error(
            "⚠️ Ange ett produktnamn."
        )

    else:

        aktuell_data = ladda_databas()

        aktuell_data[
            "produkter"
        ].setdefault(
            kategori,
            {}
        )


        före = int(
            aktuell_data[
                "produkter"
            ][kategori].get(
                produkt,
                0
            )
        )


        # ----------------------------
        # INLEVERANS
        # ----------------------------

        if "Inleverans" in typ:

            efter = (
                före
                + int(antal)
            )

            historik_typ = "Inleverans"


        # ----------------------------
        # UTTAG
        # ----------------------------

        else:

            if int(antal) > före:

                st.error(
                    f"❌ Otillräckligt lager. "
                    f"Det finns bara {före} st."
                )

                st.stop()


            efter = (
                före
                - int(antal)
            )

            historik_typ = "Uttag"


        aktuell_data[
            "produkter"
        ][kategori][produkt] = efter


        registrera_historik(
            aktuell_data,
            kategori,
            produkt,
            historik_typ,
            antal,
            före,
            efter
        )


        spara_databas(
            aktuell_data
        )


        st.success(
            f"✅ {produkt}: "
            f"{före} → {efter} st"
        )


        st.rerun()
```

# ============================================================

# ADMIN – KORRIGERA LAGER

# ============================================================

if st.session_state["cantina_admin_logged_in"]:

```
st.markdown("---")

st.header(
    "✏️ Korrigera lagersaldo"
)


if alla_produkter:

    produktlista = [

        f'{x["kategori"]} – '
        f'{x["produkt"]} '
        f'({x["antal"]} st)'

        for x in alla_produkter
    ]


    vald = st.selectbox(
        "Välj produkt",
        produktlista
    )


    index = produktlista.index(
        vald
    )


    info = alla_produkter[index]


    ny_mängd = st.number_input(
        "Nytt faktiskt lagersaldo",
        min_value=0,
        value=int(info["antal"]),
        step=1
    )


    if st.button(
        "💾 SPARA KORRIGERING",
        use_container_width=True
    ):

        aktuell_data = ladda_databas()

        kategori = info["kategori"]
        produkt = info["produkt"]

        före = int(
            aktuell_data[
                "produkter"
            ][kategori][produkt]
        )

        efter = int(
            ny_mängd
        )


        if före != efter:

            aktuell_data[
                "produkter"
            ][kategori][produkt] = efter


            registrera_historik(
                aktuell_data,
                kategori,
                produkt,
                "Lagerkorrigering",
                abs(efter - före),
                före,
                efter
            )


            spara_databas(
                aktuell_data
            )


        st.success(
            "✅ Lagret har korrigerats."
        )

        st.rerun()
```

# ============================================================

# ADMIN – PRODUKTHANTERING

# ============================================================

if st.session_state["cantina_admin_logged_in"]:

```
st.markdown("---")

st.header(
    "🛠️ Produkthantering"
)


if alla_produkter:

    produktlista = [

        f'{x["kategori"]} – '
        f'{x["produkt"]}'

        for x in alla_produkter
    ]


    vald = st.selectbox(
        "Välj produkt",
        produktlista,
        key="hantera_produkt"
    )


    index = produktlista.index(
        vald
    )


    info = alla_produkter[index]


    col1, col2 = st.columns(2)


    with col1:

        nytt_namn = st.text_input(
            "Ändra produktnamn",
            value=info["produkt"]
        ).strip()


        if st.button(
            "💾 ÄNDRA NAMN",
            use_container_width=True
        ):

            if not nytt_namn:

                st.error(
                    "❌ Namnet får inte vara tomt."
                )

            elif (
                nytt_namn
                != info["produkt"]
                and nytt_namn
                in produkter[
                    info["kategori"]
                ]
            ):

                st.error(
                    "❌ Produkten finns redan."
                )

            else:

                aktuell_data = ladda_databas()

                gammalt_namn = info["produkt"]

                mängd = aktuell_data[
                    "produkter"
                ][
                    info["kategori"]
                ].pop(
                    gammalt_namn
                )


                aktuell_data[
                    "produkter"
                ][
                    info["kategori"]
                ][
                    nytt_namn
                ] = mängd


                spara_databas(
                    aktuell_data
                )


                st.success(
                    "✅ Produktnamnet har ändrats."
                )

                st.rerun()


    with col2:

        st.warning(
            "Permanent radering tar bort produkten."
        )


        if st.button(
            "🗑️ RADERA PRODUKT",
            use_container_width=True
        ):

            aktuell_data = ladda_databas()

            aktuell_data[
                "produkter"
            ][
                info["kategori"]
            ].pop(
                info["produkt"],
                None
            )


            spara_databas(
                aktuell_data
            )


            st.success(
                "✅ Produkten har raderats."
            )

            st.rerun()
```

# ============================================================

# HISTORIK

# ============================================================

st.markdown("---")

st.header(
"📜 Lagerhistorik"
)

historik = data.get(
"historik",
[]
)

if not historik:

```
st.info(
    "Ingen lagerhistorik finns ännu."
)
```

else:

```
historik = list(
    reversed(historik)
)


filter_historik = st.text_input(
    "🔎 Sök i historiken",
    placeholder="Produkt, kategori eller operation..."
).strip().lower()


if filter_historik:

    historik = [

        x
        for x in historik

        if (
            filter_historik
            in str(x).lower()
        )

    ]


df_historik = pd.DataFrame([

    {
        "Datum": x.get("datum", ""),
        "Tid": x.get("tid", ""),
        "Kategori": x.get("kategori", ""),
        "Produkt": x.get("produkt", ""),
        "Operation": x.get("typ", ""),
        "Antal": x.get("antal", 0),
        "Före": x.get("före", 0),
        "Efter": x.get("efter", 0)
    }

    for x in historik
])


st.dataframe(
    df_historik,
    use_container_width=True,
    hide_index=True
)
```

# ============================================================

# BESTÄLLNINGSLISTA

# ============================================================

st.markdown("---")

st.header(
"🚨 Beställningslista"
)

beställningslista = [

```
x
for x in alla_produkter
if x["antal"] < LAGERGRÄNS
```

]

if beställningslista:

```
df_beställning = pd.DataFrame([

    {
        "Kategori": x["kategori"],
        "Produkt / Producent": x["produkt"],
        "Tillgängligt": f'{x["antal"]} st',
        "Status": lagerstatus(x["antal"])
    }

    for x in beställningslista
])


st.dataframe(
    df_beställning,
    use_container_width=True,
    hide_index=True
)
```

else:

```
st.success(
    "✅ Inga produkter behöver beställas."
)
```
