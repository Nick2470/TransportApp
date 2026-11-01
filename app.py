from flask import Flask, request, send_file
from datetime import date
import sqlite3
import os
import pandas as pd
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Database aanmaken
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS ritten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    datum TEXT,
    voertuig TEXT,
    Klant TEXT,
    vertrek_depot TEXT,
    aankomst_laden TEXT,
    vertrek_laden TEXT,
    aankomst_lossen TEXT,
    vertrek_lossen TEXT,
    aankomst_depot TEXT,
    startadres TEXT,
    laadadres TEXT,
    losadres TEXT,
    km_vertrek INTEGER,
    km_aankomst INTEGER,
    foto TEXT
)
""")

conn.commit()
conn.close()


@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

         foto = request.files.get("foto")
        
         bestandsnaam = ""
        
         if foto and foto.filename:
                
             bestandsnaam = secure_filename(foto.filename)

             os.makedirs(
                 "static/uploads",
                 exist_ok=True
             )
        
             foto.save(
                os.path.join(
                    "static/uploads",
                     bestandsnaam
                 )
            )    

         conn = sqlite3.connect("database.db")
         cursor = conn.cursor()

         cursor.execute("""
         INSERT INTO ritten (
            datum,
            voertuig,
            klant,
            vertrek_depot,
            aankomst_laden,
            vertrek_laden,
            aankomst_lossen,
            vertrek_lossen,
            aankomst_depot,
            startadres,
            laadadres,
            losadres,
            km_vertrek,
            km_aankomst,
            foto
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form.get("datum", ""),
            request.form.get("voertuig", ""),
            request.form.get("klant", ""),
            request.form.get("vertrek_depot", ""),
            request.form.get("aankomst_laden", ""),
            request.form.get("vertrek_laden", ""),
            request.form.get("aankomst_lossen", ""),
            request.form.get("vertrek_lossen", ""),
            request.form.get("aankomst_depot", ""),
            request.form.get("startadres", ""),
            request.form.get("laadadres", ""),
            request.form.get("losadres", ""),
            request.form.get("km_vertrek", 0),
            request.form.get("km_aankomst", 0),
            bestandsnaam
         ))

         conn.commit()

         df = pd.read_sql_query(
            "SELECT * FROM ritten",
            conn
         )

         df.to_excel(
            "ritten.xlsx",
            index=False
         )

         conn.close()

         return """
         <h2>✅ Rit opgeslagen</h2>
         <a href="/">Nieuwe rit</a>
         """
         

    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <style>
        body{
            font-family: Arial, sans-serif;
            max-width: 500px;
            margin:auto;
            padding:15px;
            background:#f4f4f4;
        }

        .kaart{
            background:white;
            padding:15px;
            border-radius:10px;
            margin-bottom:15px;
        }

        input, select{
            width:100%;
            padding:12px;
            margin-top:5px;
            margin-bottom:12px;
            box-sizing:border-box;
            font-size:16px;
        }

        button{
            width:100%;
            padding:16px;
            font-size:18px;
            background:#0066cc;
            color:white;
            border:none;
            border-radius:8px;
        }

        h1{
            text-align:center;
        }
        </style>
    </head>

    <body>

    <h1>🚛 Digitaal Rittenblad</h1>

    <form method="post" enctype="multipart/form-data">

        <div class="kaart">

        Datum
        <input type="date" name="datum" value="{date.today()}">

        Voertuig
        <input type="text" name="voertuig" value="2-JNU-629">
        
       Klant

<input type="text" name="klant" list="klanten">

<datalist id="klanten">
  <option value="Jansens">
  <option value="Molse Bouwmachines">
</datalist>

        </div>

        <div class="kaart">

        <h3>⏰ Tijden</h3>

        Vertrek depot
        <input type="time" name="vertrek_depot">

        Aankomst laden
        <input type="time" name="aankomst_laden">

        Vertrek laden
        <input type="time" name="vertrek_laden">

        Aankomst lossen
        <input type="time" name="aankomst_lossen">

        Vertrek lossen
        <input type="time" name="vertrek_lossen">

        Aankomst depot
        <input type="time" name="aankomst_depot">

        </div>

        <div class="kaart">

        Startadres
        <input type="text" name="startadres">

        Laadadres
        <input type="text" name="laadadres">

        Losadres
        <input type="text" name="losadres">

        </div>

        <div class="kaart">

        KM vertrek
        <input type="number" name="km_vertrek">

        KM aankomst
        <input type="number" name="km_aankomst">

        </div>

        <h3>📸 Foto</h3>

        <input
        type="file"
        name="foto"
        accept="image/*"
        capture="environment">

        <button type="submit">
            💾 Rit opslaan
        </button>

    </form>

    

    <a href="/ritten">📋 Bekijk ritten</a>

    <br><br>

    <a href="/excel" target="_blank">📊 Excel downloaden</a>

    </body>
    </html>
    """


@app.route("/ritten")
def ritten():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT datum, voertuig, laadadres, losadres, foto
    FROM ritten
    ORDER BY id DESC
    """)

    resultaten = cursor.fetchall()

    conn.close()

    html = "<h1>Overzicht ritten</h1>"

    for rit in resultaten:
        html += f"""
        <p>
        {rit[0]} |
        {rit[1]} |
        {rit[2]} → {rit[3]}
        </p>

        <img src="/static/uploads/{rit[4]}"
            width="250">

        <br><br>
        """

    html += "<a href='/'>Terug</a>"

    return html

@app.route("/excel")
def excel():

    conn = sqlite3.connect("database.db")

    df = pd.read_sql_query(
        "SELECT * FROM ritten",
        conn
    )

    bestand = "ritten.xlsx"

    df.to_excel(
        bestand,
        index=False
    )

    conn.close()

    return send_file(
    bestand,
    as_attachment=True
    )


if __name__ == "__main__":
    import os
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )
