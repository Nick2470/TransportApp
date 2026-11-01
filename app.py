from flask import (
    Flask, request, redirect, url_for,
    render_template_string, send_file, abort
)
from datetime import date
import sqlite3
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)

app = Flask(__name__)
DB = "database.db"


# --------------------------------
# DATABASE
# --------------------------------

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS ritten (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        datum TEXT,
        voertuig TEXT,
        klant TEXT,
        vertrek_depot TEXT,
        aankomst_laden TEXT,
        vertrek_laden TEXT,
        aankomst_lossen TEXT,
        vertrek_lossen TEXT,
        aankomst_depot TEXT,
        startadres TEXT,
        laadadres TEXT,
        losadres TEXT,
        km_vertrek INTEGER DEFAULT 0,
        km_aankomst INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


init_db()


# --------------------------------
# HTML FORMULIER
# --------------------------------

FORM = """
<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>Digitaal Rittenblad</title>

<style>
* { box-sizing: border-box; }

body {
    font-family: Arial, sans-serif;
    max-width: 650px;
    margin: auto;
    padding: 15px;
    background: #eef1f5;
    color: #222;
}

h1 {
    text-align: center;
    color: #12345a;
}

.kaart {
    background: white;
    padding: 18px;
    border-radius: 12px;
    margin-bottom: 15px;
    box-shadow: 0 2px 8px #00000010;
}

h3 {
    color: #0757a5;
    margin-top: 0;
}

label {
    display: block;
    font-weight: bold;
    margin-top: 10px;
}

input {
    width: 100%;
    padding: 13px;
    margin-top: 5px;
    border: 1px solid #ccc;
    border-radius: 7px;
    font-size: 16px;
}

button, .knop {
    display: block;
    width: 100%;
    padding: 15px;
    border: none;
    border-radius: 8px;
    background: #0866c6;
    color: white;
    font-size: 17px;
    text-align: center;
    text-decoration: none;
    margin-top: 10px;
    cursor: pointer;
}

.secundair {
    background: #44566c;
}

.verwijder {
    background: #c62828;
}

.resultaat {
    background: #e4f4e8;
    padding: 12px;
    border-radius: 8px;
    font-weight: bold;
    margin-top: 10px;
}

a { color: #0757a5; }

@media(max-width: 400px) {
    body { padding: 9px; }
    .kaart { padding: 13px; }
}
</style>
</head>

<body>

<h1>🚛 Digitaal Rittenblad</h1>

<form method="post">

<div class="kaart">
<h3>📋 Algemene gegevens</h3>

<label>Datum</label>
<input type="date" name="datum"
value="{{ rit.datum if rit else vandaag }}" required>

<label>Voertuig</label>
<input type="text" name="voertuig"
value="{{ rit.voertuig if rit else '2-JNU-629' }}">

<label>Klant</label>
<input type="text" name="klant" list="klanten"
value="{{ rit.klant if rit else '' }}">

<datalist id="klanten">
<option value="Jansens">
<option value="Molse Bouwmachines">
</datalist>
</div>

<div class="kaart">
<h3>⏰ Tijden</h3>

<label>Vertrek depot</label>
<input type="time" name="vertrek_depot"
value="{{ rit.vertrek_depot if rit else '' }}">

<label>Aankomst laden</label>
<input type="time" name="aankomst_laden"
value="{{ rit.aankomst_laden if rit else '' }}">

<label>Vertrek laden</label>
<input type="time" name="vertrek_laden"
value="{{ rit.vertrek_laden if rit else '' }}">

<label>Aankomst lossen</label>
<input type="time" name="aankomst_lossen"
value="{{ rit.aankomst_lossen if rit else '' }}">

<label>Vertrek lossen</label>
<input type="time" name="vertrek_lossen"
value="{{ rit.vertrek_lossen if rit else '' }}">

<label>Aankomst depot</label>
<input type="time" name="aankomst_depot"
value="{{ rit.aankomst_depot if rit else '' }}">
</div>

<div class="kaart">
<h3>📍 Adressen</h3>

<label>Startadres</label>
<input type="text" name="startadres"
value="{{ rit.startadres if rit else '' }}">

<label>Laadadres</label>
<input type="text" name="laadadres"
value="{{ rit.laadadres if rit else '' }}">

<label>Losadres</label>
<input type="text" name="losadres"
value="{{ rit.losadres if rit else '' }}">
</div>

<div class="kaart">
<h3>🛣️ Kilometerstanden</h3>

<label>KM vertrek</label>
<input type="number" id="km_vertrek"
name="km_vertrek" min="0"
value="{{ rit.km_vertrek if rit else 0 }}"
oninput="berekenKM()">

<label>KM aankomst</label>
<input type="number" id="km_aankomst"
name="km_aankomst" min="0"
value="{{ rit.km_aankomst if rit else 0 }}"
oninput="berekenKM()">

<div class="resultaat" id="km_resultaat">
Gereden kilometers: 0 km
</div>
</div>

<button type="submit">💾 Rit opslaan</button>

</form>

<a class="knop secundair" href="{{ url_for('ritten') }}">
📋 Bekijk alle ritten
</a>

<script>
function berekenKM() {
    let vertrek = Number(document.getElementById("km_vertrek").value);
    let aankomst = Number(document.getElementById("km_aankomst").value);

    let verschil = aankomst - vertrek;

    document.getElementById("km_resultaat").innerText =
        "Gereden kilometers: " +
        (verschil >= 0 ? verschil : "Controleer kilometerstanden") +
        (verschil >= 0 ? " km" : "");
}

berekenKM();
</script>

</body>
</html>
"""


# --------------------------------
# NIEUWE RIT
# --------------------------------

VELDEN = [
    "datum",
    "voertuig",
    "klant",
    "vertrek_depot",
    "aankomst_laden",
    "vertrek_laden",
    "aankomst_lossen",
    "vertrek_lossen",
    "aankomst_depot",
    "startadres",
    "laadadres",
    "losadres",
]


def formulier_data():
    data = {
        veld: request.form.get(veld, "").strip()
        for veld in VELDEN
    }

    try:
        data["km_vertrek"] = int(request.form.get("km_vertrek", 0))
        data["km_aankomst"] = int(request.form.get("km_aankomst", 0))
    except ValueError:
        raise ValueError("Kilometerstanden moeten getallen zijn.")

    if data["km_vertrek"] < 0 or data["km_aankomst"] < 0:
        raise ValueError("Kilometerstanden mogen niet negatief zijn.")

    if data["km_aankomst"] < data["km_vertrek"]:
        raise ValueError("KM aankomst mag niet lager zijn dan KM vertrek.")

    return data


@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":
        try:
            data = formulier_data()
        except ValueError as fout:
            return f"<h3>{fout}</h3><a href='/'>Terug</a>", 400

        conn = get_db()

        kolommen = VELDEN + ["km_vertrek", "km_aankomst"]

        sql = f"""
        INSERT INTO ritten ({','.join(kolommen)})
        VALUES ({','.join(['?'] * len(kolommen))})
        """

        conn.execute(sql, [data[k] for k in kolommen])
        conn.commit()
        conn.close()

        return """
        <h2>✅ Rit succesvol opgeslagen!</h2>
        <a href="/">Nieuwe rit</a><br><br>
        <a href="/ritten">Ritten bekijken</a>
        """

    return render_template_string(
        FORM,
        rit=None,
        vandaag=date.today().isoformat()
    )


# --------------------------------
# RITTEN OVERZICHT + ZOEKEN
# --------------------------------

@app.route("/ritten")
def ritten():

    zoek = request.args.get("zoek", "").strip()
    vanaf = request.args.get("vanaf", "")
    tot = request.args.get("tot", "")

    conn = get_db()

    sql = "SELECT * FROM ritten WHERE 1=1"
    params = []

    if zoek:
        sql += """
        AND (
            klant LIKE ?
            OR voertuig LIKE ?
            OR laadadres LIKE ?
            OR losadres LIKE ?
        )
        """
        params.extend([f"%{zoek}%"] * 4)

    if vanaf:
        sql += " AND datum >= ?"
        params.append(vanaf)

    if tot:
        sql += " AND datum <= ?"
        params.append(tot)

    sql += " ORDER BY datum DESC, id DESC"

    resultaten = conn.execute(sql, params).fetchall()
    conn.close()

    html = """
    <!DOCTYPE html>
    <html lang="nl">
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Rittenoverzicht</title>
    <style>
    body {font-family:Arial;max-width:800px;margin:auto;padding:15px;background:#eef1f5}
    .kaart {background:white;padding:15px;margin-bottom:12px;border-radius:10px}
    input {width:100%;padding:12px;margin:5px 0;box-sizing:border-box}
    button,.knop {display:block;width:100%;padding:13px;background:#0866c6;color:white;border:0;border-radius:7px;text-align:center;text-decoration:none;margin:7px 0;box-sizing:border-box}
    .rood {background:#c62828}
    .grijs {background:#44566c}
    .klein {display:inline-block;width:auto;padding:9px}
    </style>
    </head>
    <body>
    <h1>📋 Overzicht ritten</h1>

    <div class="kaart">
    <form method="get">
    <label>Zoeken op klant, voertuig of adres</label>
    <input name="zoek" value="{{ zoek }}">

    <label>Vanaf datum</label>
    <input type="date" name="vanaf" value="{{ vanaf }}">

    <label>Tot datum</label>
    <input type="date" name="tot" value="{{ tot }}">

    <button>🔎 Zoeken</button>
    </form>

    <a class="knop grijs" href="/ritten">Filters wissen</a>
    <a class="knop" href="{{ pdf_url }}">📄 PDF overzicht downloaden</a>
    <a class="knop grijs" href="/">➕ Nieuwe rit</a>
    </div>

    <h3>{{ resultaten|length }} ritten gevonden</h3>

    {% for rit in resultaten %}
    <div class="kaart">
        <h3>{{ rit.datum }} - {{ rit.klant }}</h3>
        <p><b>Voertuig:</b> {{ rit.voertuig }}</p>
        <p><b>Start:</b> {{ rit.startadres }}</p>
        <p><b>Laden:</b> {{ rit.laadadres }}</p>
        <p><b>Lossen:</b> {{ rit.losadres }}</p>
        <p><b>KM:</b> {{ rit.km_vertrek }} → {{ rit.km_aankomst }}</p>
        <p><b>Gereden:</b> {{ rit.km_aankomst - rit.km_vertrek }} km</p>

        <a class="knop klein" href="/bewerken/{{ rit.id }}">✏️ Bewerken</a>
        <a class="knop klein grijs" href="/rit/{{ rit.id }}/pdf">📄 PDF</a>

        <form method="post" action="/verwijderen/{{ rit.id }}"
              onsubmit="return confirm('Deze rit verwijderen?')">
            <button class="rood">🗑️ Verwijderen</button>
        </form>
    </div>
    {% else %}
    <p>Geen ritten gevonden.</p>
    {% endfor %}

    </body>
    </html>
    """

    return render_template_string(
        html,
        resultaten=resultaten,
        zoek=zoek,
        vanaf=vanaf,
        tot=tot,
        pdf_url=url_for("pdf_overzicht", zoek=zoek, vanaf=vanaf, tot=tot)
    )


# --------------------------------
# RIT BEWERKEN
# --------------------------------

@app.route("/bewerken/<int:rit_id>", methods=["GET", "POST"])
def bewerken(rit_id):

    conn = get_db()
    rit = conn.execute(
        "SELECT * FROM ritten WHERE id=?",
        (rit_id,)
    ).fetchone()

    if rit is None:
        conn.close()
        abort(404)

    if request.method == "POST":

        try:
            data = formulier_data()
        except ValueError as fout:
            conn.close()
            return f"<h3>{fout}</h3><a href='/bewerken/{rit_id}'>Terug</a>", 400

        kolommen = VELDEN + ["km_vertrek", "km_aankomst"]

        sql = "UPDATE ritten SET " + ",".join(
            f"{k}=?" for k in kolommen
        ) + " WHERE id=?"

        conn.execute(
            sql,
            [data[k] for k in kolommen] + [rit_id]
        )

        conn.commit()
        conn.close()

        return redirect(url_for("ritten"))

    conn.close()

    html = FORM.replace(
        '<h1>🚛 Digitaal Rittenblad</h1>',
        '<h1>✏️ Rit bewerken</h1>'
    )

    html = html.replace(
        '<button type="submit">💾 Rit opslaan</button>',
        '<button type="submit">💾 Wijzigingen opslaan</button>'
    )

    return render_template_string(
        html,
        rit=rit,
        vandaag=date.today().isoformat()
    )


# --------------------------------
# RIT VERWIJDEREN
# --------------------------------

@app.route("/verwijderen/<int:rit_id>", methods=["POST"])
def verwijderen(rit_id):

    conn = get_db()
    conn.execute(
        "DELETE FROM ritten WHERE id=?",
        (rit_id,)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("ritten"))


# --------------------------------
# PDF MAKEN
# --------------------------------

def maak_pdf(resultaten, titel):

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=35,
        leftMargin=35,
        topMargin=35,
        bottomMargin=35
    )

    styles = getSampleStyleSheet()
    inhoud = []

    inhoud.append(Paragraph(titel, styles["Title"]))
    inhoud.append(Spacer(1, 15))

    for rit in resultaten:

        inhoud.append(Paragraph(
            f"Ritnummer: {rit['id']} - {rit['datum']}",
            styles["Heading2"]
        ))

        gegevens = [
            ["Gegeven", "Informatie"],
            ["Klant", rit["klant"] or ""],
            ["Voertuig", rit["voertuig"] or ""],
            ["Startadres", rit["startadres"] or ""],
            ["Laadadres", rit["laadadres"] or ""],
            ["Losadres", rit["losadres"] or ""],
            ["Vertrek depot", rit["vertrek_depot"] or ""],
            ["Aankomst laden", rit["aankomst_laden"] or ""],
            ["Vertrek laden", rit["vertrek_laden"] or ""],
            ["Aankomst lossen", rit["aankomst_lossen"] or ""],
            ["Vertrek lossen", rit["vertrek_lossen"] or ""],
            ["Aankomst depot", rit["aankomst_depot"] or ""],
            ["KM vertrek", str(rit["km_vertrek"])],
            ["KM aankomst", str(rit["km_aankomst"])],
            [
                "Gereden kilometers",
                str(rit["km_aankomst"] - rit["km_vertrek"])
            ]
        ]

        tabel = Table(gegevens, colWidths=[150, 350])

        tabel.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12345a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("PADDING", (0, 0), (-1, -1), 7),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
        ]))

        inhoud.append(tabel)
        inhoud.append(Spacer(1, 20))

    document.build(inhoud)

    buffer.seek(0)
    return buffer


@app.route("/rit/<int:rit_id>/pdf")
def pdf_rit(rit_id):

    conn = get_db()
    rit = conn.execute(
        "SELECT * FROM ritten WHERE id=?",
        (rit_id,)
    ).fetchone()
    conn.close()

    if rit is None:
        abort(404)

    buffer = maak_pdf([rit], "DIGITAAL RITTENBLAD")

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"rittenblad_{rit_id}.pdf",
        mimetype="application/pdf"
    )


@app.route("/ritten/pdf")
def pdf_overzicht():

    zoek = request.args.get("zoek", "").strip()
    vanaf = request.args.get("vanaf", "")
    tot = request.args.get("tot", "")

    sql = "SELECT * FROM ritten WHERE 1=1"
    params = []

    if zoek:
        sql += """
        AND (
            klant LIKE ?
            OR voertuig LIKE ?
            OR laadadres LIKE ?
            OR losadres LIKE ?
        )
        """
        params.extend([f"%{zoek}%"] * 4)

    if vanaf:
        sql += " AND datum >= ?"
        params.append(vanaf)

    if tot:
        sql += " AND datum <= ?"
        params.append(tot)

    sql += " ORDER BY datum DESC, id DESC"

    conn = get_db()
    resultaten = conn.execute(sql, params).fetchall()
    conn.close()

    buffer = maak_pdf(resultaten, "OVERZICHT VAN ALLE RITTEN")

    return send_file(
        buffer,
        as_attachment=True,
        download_name="ritten_overzicht.pdf",
        mimetype="application/pdf"
    )


# --------------------------------
# START
# --------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)