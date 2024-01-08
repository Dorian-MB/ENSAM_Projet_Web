from flask import Flask, url_for, render_template, redirect, request
import sqlite3 as lite
from datetime import datetime
from pathlib import Path

# Connection avec la BDD ---------------------------------------------------
current_dirrectory = Path(__file__).parent
# Par exemple : 'user/Document/.../2A/GIE/OREXA/projet_web' (marche sur windows et mac)
BDD_PATH = str(current_dirrectory / "BDD.db")
# 'user/Document/.../2A/GIE/OREXA/projet_web/BDD.db'


def execute_sql(sql: str, parameters=(), bbd_path=BDD_PATH):
    con = lite.connect(bbd_path)
    con.row_factory = lite.Row
    cur = con.cursor()
    cur.execute(sql, parameters)  # par defaut `execute` parameters = ()
    table = cur.fetchall()
    con.close()
    return table


def commit_sql(sql: str, parameters=(), bbd_path=BDD_PATH):
    con = lite.connect(bbd_path)
    cur = con.cursor()
    cur.execute(sql, parameters)
    con.commit()  # .commit() est utilisée pour appliquer les modifications apportées à la base de données
    con.close()


def get_table_next_id(table: str):
    id_ = execute_sql(f"SELECT MAX(id) AS max FROM {table}")[0]["max"]
    id_ = 0 if id_ is None else id_ + 1
    # verifie si la table est vide (dans ce cas id_=None) (sinon id_ = 4 par exemple(int type))
    return id_


def insert_into_commande_agilean_table(values: dict):
    sql = """INSERT INTO commande_agilean 
            VALUES (:id, :etat_commande, 
                        :id_option, :id_chaissis, 
                        :nom, :prenom, 
                        :date_commande_client, :date_envoie_agilog, :date_reception_agilog, 
                        :date_expedition_client, :date_livraison_client)"""
    commit_sql(sql, values)


def insert_into_commande_agilog_table(values: dict):
    sql = """INSERT INTO commande_agilog 
    VALUES (:id, :id_commande, :id_piece, :quantiter,:etat_commande,
    :date_envoie_agigreen, :date_reception_agigreen, :date_envoie_agigreen)"""
    commit_sql(sql, values)


def insert_into_commande_agigreen_table(values: dict):
    sql = """INSERT INTO commande_agigreen
    VALUES (:id, :id_commande, :etat_commande, :date_expedition_agilog, :id_piece, :quantiter)"""
    commit_sql(sql, values)


# Usefull function ---------------------------------------------------
date_format = "%d/%m/%Y %Hh %Mmin %Ss"


def get_current_time():
    date = datetime.now().strftime(date_format)
    return str(date)


def get_datetime_type_from_date_str(date_str):
    return datetime.strptime(date_str, date_format)


# Common function ---------------------------------------------------
def stocks(sql, table_name, html_name, type_):
    stocks = execute_sql(sql)

    if request.method != "POST":
        # re-initilise les input html avec un champs vide
        return render_template(html_name, stocks=stocks, msg="")
    else:
        id_type = request.form.get(f"id_{type_}", "")
        nombre = request.form.get("nombre", "")
        mode = request.form.get("mode", "0")
        condition_1 = (id_type == "") or (nombre == "")
        condition_2 = (not id_type.isdigit()) or (not nombre.isdigit())
        if condition_1 and condition_2:
            return render_template(html_name, stocks=stocks, msg="Mauvaise saisie !")
        else:
            id_type = int(id_type)
            nombre = int(nombre)
            mode = int(mode)
            # Rq: else n'est pas utile (visuelle)

        table_name_id = execute_sql(f"SELECT id_{type_} FROM {table_name}")
        id_type_list = [ligne[f"id_{type_}"] for ligne in table_name_id]
        if id_type not in id_type_list:
            return render_template(html_name, stocks=stocks, msg="id non valide")

        # table_name n'est pas accesible pour l'utilisateur => pas de pb de securiter
        sql = f"SELECT quantiter FROM {table_name} WHERE id_{type_}=?"
        quantiter = execute_sql(sql, (id_type,))[0]["quantiter"]
        values = (quantiter + nombre, id_type) if mode == 0 else (nombre, id_type)

        sql_update = f"UPDATE {table_name} SET quantiter=? WHERE id_{type_}=?"
        commit_sql(sql_update, values)
        return redirect(url_for(table_name))


def maj_stock(id_commande, mode, agi_lean_ou_log: str):
    table_commande = f"commande_{agi_lean_ou_log}"
    table_stock = f"stock_{agi_lean_ou_log}"
    type_ = "chassis" if agi_lean_ou_log == "agilean" else "piece"
    id_ = "id" if agi_lean_ou_log == "agilean" else "id_commande"

    sql = f"""SELECT stock.quantiter, stock.id_{type_} 
    FROM {table_commande} AS cmd
    JOIN {table_stock} AS stock ON cmd.id_{type_}=stock.id_{type_} 
    WHERE cmd.{id_}=?"""
    table = execute_sql(sql, (id_commande,))
    for ligne in table:
        quantiter = ligne["quantiter"]
        id_type = ligne[f"id_{type_}"]
        if mode == "+":
            quantiter += 1
        elif mode == "-":
            quantiter -= 1

        values = (quantiter, id_type)
        sql_update = f"UPDATE {table_stock} SET quantiter=? WHERE id_{type_}=?"
        commit_sql(sql_update, values)


def create_app():  # pas obligatoire mais peux etre utile pour test le site (pytest par exemple), evite de verifier si tout fonction quand on fait des modifs
    app = Flask(__name__)

    # Index route : ---------------------------------------------------
    @app.route("/")
    def index():
        return render_template("index.html")

    # Agilean route : ---------------------------------------------------
    @app.route("/agilean", methods=["GET"])
    def agilean():
        return render_template("agilean.html")

    @app.route("/agilean/stocks", methods=["GET", "POST"])
    def stock_agilean():
        sql = "SELECT * FROM stock_agilean AS stock JOIN chassis ON stock.id_chassis = chassis.id_chassis"
        table_name = "stock_agilean"
        html_page = "stock_agilean.html"
        type_ = "chassis"
        return stocks(sql, table_name, html_page, type_)

    @app.route("/agilean/pieces-detachees", methods=["GET", "POST"])
    def pieces_detachees_agilean():
        liste_pieces = execute_sql("SELECT id_piece, nom_piece FROM pieces")
        if request.method != "POST":
            return render_template(
                "pieces_detachees_agilean.html", liste_pieces=liste_pieces, msg=""
            )

        quantiter = request.form.getlist("quantiter[]")
        pieces = request.form.getlist("pieces[]")

        commandes = []
        for id_piece in pieces:
            idx = int(id_piece)
            n = quantiter[idx]
            if not n.isdigit():  # verifie le formulaire
                return render_template(
                    "pieces_detachees_agilean.html",
                    liste_pieces=liste_pieces,
                    msg="Mauvaise selection",
                )
            commandes.append({"id_piece": id_piece, "quantiter": int(n)})

        id_commande = get_table_next_id("commande_agilean")
        for piece in commandes:
            id_ = get_table_next_id("commande_agilog")
            values = {
                "id": id_,
                "id_commande": id_commande,
                "id_piece": piece["id_piece"],
                "quantiter": piece["quantiter"],
                "etat_commande": None,
                "date_envoie_agigreen": None,
                "date_reception_agigreen": None,
                "date_expedition_agilean": None,
            }
            insert_into_commande_agilog_table(values)

        date = get_current_time()
        values = {
            "id": id_commande,
            "etat_commande": "commande de piece manquante",
            "id_option": None,
            "id_chaissis": None,
            "nom": None,
            "prenom": None,
            "date_commande_client": date,
            "date_envoie_agilog": date,
            "date_reception_agilog": None,
            "date_expedition_client": None,
            "date_livraison_client": None,
        }
        insert_into_commande_agilean_table(values)
        return redirect(url_for("suivi_commande_agilean"))

    @app.route("/agilean/suivi-commande", methods=["GET", "POST"])
    def suivi_commande_agilean():
        sql = "SELECT * FROM commande_agilean AS cmd LEFT JOIN chassis ON cmd.id_chassis=chassis.id_chassis"
        commandes = execute_sql(sql)
        if request.method != "POST":
            return render_template("suivi_commande_agilean.html", commandes=commandes)

        etat_commande = request.form.get("etat_commande", "")
        id_commande = request.form.get("id_commande", "")
        if etat_commande == "Commande expédiée au client":
            values = (get_current_time(), etat_commande, id_commande)
            sql = "UPDATE commande_agilean SET date_expedition_client = ?, etat_commande = ? WHERE id=?"
            maj_stock(id_commande, "-", "agilean")
        elif etat_commande == "Commande validé":
            values = (etat_commande, id_commande)
            sql = "UPDATE commande_agilean SET etat_commande = ? WHERE id=?"
            maj_stock(id_commande, "+", "agilean")
        else:
            values = (etat_commande, id_commande)
            sql = "UPDATE commande_agilean SET etat_commande = ? WHERE id=?"

        envoi_agilog = request.form.get("envoi_agilog", "")
        # Renvoi l'id de la commande
        if envoi_agilog != "":  # Click sur le boutton envoye a agilog
            id_commande = envoi_agilog
            date_livraison_agilog = get_current_time()
            etat_commande = "Commande envoyée à Agilog"
            values = (date_livraison_agilog, etat_commande, id_commande)
            sql = "UPDATE commande_agilean SET date_envoie_agilog = ?, etat_commande = ? WHERE id=?"
            sent_command_to_agilog_maj_bdd(id_commande)

        reception_agilog = request.form.get("reception_agilog", "")
        # Renvoi l'id de la commande
        if reception_agilog != "":
            id_commande = reception_agilog
            values = (get_current_time(), "Commande agilog recus", id_commande)
            sql = "UPDATE commande_agilean SET date_reception_agilog = ?, etat_commande = ? WHERE id=?"

        commit_sql(sql, values)
        return redirect(url_for("suivi_commande_agilean"))

    def sent_command_to_agilog_maj_bdd(id_commande):
        sql = "SELECT id_chassis, id_option FROM commande_agilean WHERE id=?"
        table = execute_sql(sql, (id_commande,))
        id_chassis, id_option = table[0]["id_chassis"], table[0]["id_option"]
        sql = """
        SELECT pic.id_piece, pic.quantiter
        FROM piece_in_chassis AS pic
        WHERE pic.id_chassis = ?
        UNION
        SELECT pio.id_piece, pio.quantiter
        FROM piece_in_option AS pio
        WHERE pio.id_option = ?
        """

        commandes_agilog = execute_sql(sql, (id_chassis, id_option))
        for ligne in commandes_agilog:
            id_ = get_table_next_id("commande_agilog")
            values = {
                "id": id_,
                "id_commande": id_commande,
                "id_piece": ligne["id_piece"],
                "quantiter": ligne["quantiter"],
                "etat_commande": None,
                "date_envoie_agigreen": None,
                "date_reception_agigreen": None,
                "date_expedition_agilean": None,
            }
            insert_into_commande_agilog_table(values)

    # Agilog route : ---------------------------------------------------
    @app.route("/agilog", methods=["GET"])
    def agilog():
        return render_template("agilog.html")

    @app.route("/agilog/stocks", methods=["GET", "POST"])
    def stock_agilog():
        sql = "SELECT * FROM stock_agilog JOIN pieces ON stock_agilog.id_piece = pieces.id_piece"
        table_name = "stock_agilog"
        html_page = "stock_agilog.html"
        type_ = "piece"
        return stocks(sql, table_name, html_page, type_)

    @app.route("/agilog/suivi-commande-to-agigreen", methods=["GET", "POST"])
    def suivi_commande_agilog_to_agigreen():
        sql = """
        SELECT * FROM commande_agilog AS log 
        JOIN pieces ON pieces.id_piece=log.id_piece
        WHERE log.date_envoie_agigreen IS NOT NULL
        -- group by id_commande
        """
        commandes = execute_sql(sql)
        if request.method != "POST":
            return render_template(
                "suivi_commande_agilog_to_agigreen.html", commandes=commandes
            )

        id_commande = request.form.get("id_cmd_reception_agigreen")
        sql = "UPDATE commande_agilog SET date_reception_agigreen=?, etat_commande=? WHERE id_commande=?"
        values = (get_current_time(), "Commande agigreen recus", id_commande)
        commit_sql(sql, values)
        maj_stock(id_commande, "+", "agilog")
        return redirect(url_for("suivi_commande_agilog_to_agigreen"))

    # todo : faire les kit
    @app.route("/agilog/suivi-commande-from-agilog", methods=["GET", "POST"])
    def suivi_commande_agilog_from_agilean():
        # si date_envoi_agilog != None => on affiche // ie: on affiche si agilean a envoyé la commande a agilog
        sql_agilean = """SELECT * FROM commande_agilean AS lean 
                        LEFT JOIN chassis ON lean.id_chassis=chassis.id_chassis 
                        WHERE date_envoie_agilog IS NOT NULL"""
        cmd_agilean = execute_sql(sql_agilean)
        sql_agilog = """SELECT MAX(log.date_envoie_agigreen) AS date_envoie_agigreen, log.etat_commande, date_expedition_agilean 
                        -- MAX() : si plusieurs dates differentes (a implementer si comprend le format datetime)
                        FROM commande_agilog AS log 
                        JOIN commande_agilean AS lean ON lean.id = log.id_commande
                        GROUP BY log.id_commande, log.etat_commande"""  # '--' commentaire sql
        cmd_agilog = execute_sql(sql_agilog)
        commandes = zip(cmd_agilean, cmd_agilog)

        if request.method != "POST":
            return render_template(
                "suivi_commande_agilog_from_agilean.html", commandes=commandes
            )

        sent_id_commande_to_agigreen = request.form.get(
            "sent_id_commande_to_agigreen", ""
        )
        if sent_id_commande_to_agigreen != "":
            id_commande = sent_id_commande_to_agigreen
            sql = "UPDATE commande_agilog SET date_envoie_agigreen=?, etat_commande=? WHERE id_commande=?"
            commit_sql(
                sql, (get_current_time(), "commande envoyée a agigreen", id_commande)
            )
            sent_commande_to_agigreen_maj_bdd(id_commande)
            return redirect(url_for("suivi_commande_agilog_from_agilean"))

        expedition_id_commande = request.form.get("expedition_id_commande", "")
        if expedition_id_commande != "":
            id_commande = expedition_id_commande
            sql = "UPDATE commande_agilog SET date_expedition_agilean=?, etat_commande=? WHERE id_commande=?"
            values = (get_current_time(), "Commande expedier a agilean", id_commande)
            commit_sql(sql, values)
            maj_stock(id_commande, "-", "agilog")
            return redirect(url_for("suivi_commande_agilog_from_agilean"))

    def sent_commande_to_agigreen_maj_bdd(id_commande):
        commandes = execute_sql(
            "SELECT id_piece, quantiter FROM commande_agilog WHERE id_commande=?",
            (id_commande,),
        )
        commit_sql("DELETE FROM commande_agigreen WHERE id_commande=?", (id_commande,))
        for ligne in commandes:
            id_ = get_table_next_id("commande_agigreen")
            values = {
                "id": id_,
                "id_commande": id_commande,
                "etat_commande": "En cours de traitement",
                "date_expedition_agilog": None,
                "id_piece": ligne["id_piece"],
                "quantiter": ligne["quantiter"],
            }
            insert_into_commande_agigreen_table(values)

    # Agigreen route : ---------------------------------------------------
    @app.route("/agigreen", methods=["GET", "POST"])
    def agigreen():
        commandes = execute_sql("SELECT * from commande_agigreen GROUP BY id_commande")
        if request.method != "POST":
            return render_template("agigreen.html", commandes=commandes)

        envoi_agilog_id_cmd = request.form.get("envoi_agilog_id_cmd", "")
        sql = "UPDATE commande_agigreen SET date_expedition_agilog=?, etat_commande=? WHERE id_commande=?"
        values = (get_current_time(), "Commande envoyée à Agilog", envoi_agilog_id_cmd)
        commit_sql(sql, values)
        return redirect(url_for("agigreen"))

    @app.route("/agigreen/preparer-commande", methods=["POST"])
    def preparer_commande_agigreen():
        id_commande = request.form.get("preparer_lot_id_cmd")
        sql = """
        SELECT green.id_piece, pieces.nom_piece, green.quantiter FROM commande_agigreen AS green
        JOIN pieces ON pieces.id_piece=green.id_piece
        WHERE green.id_commande=?
        """
        commandes = execute_sql(sql, (id_commande,))
        return render_template(
            "commande_agigreen.html", commandes=commandes, id_commande=id_commande
        )

    # Client route : ---------------------------------------------------
    @app.route("/client", methods=["GET"])
    def client():
        return render_template("client.html")

    @app.route("/client/commande-client", methods=["GET", "POST"])
    def commande_client():
        if request.method != "POST":
            return render_template("commande_client.html", msg="")
        nom = request.form.get("nom", "")
        prenom = request.form.get("prenom", "")
        id_chassis = request.form.get("id_chassis", "")
        options = request.form.getlist("option[]")

        condition = (
            (nom == "") or (prenom == "") or (id_chassis == "") or (options == [])
        )
        if condition:
            return render_template("commande_client.html", msg="Mauvaise saisie !")

        id_ = get_table_next_id("commande_agilean")
        options = str(sum([int(opt) for opt in options]))
        id_option = (
            ("0" + options if len(options) == 2 else "00" + options)
            if len(options) < 3
            else options
        )
        date_commande = get_current_time()
        values = {
            "id": id_,
            "etat_commande": None,
            "id_option": id_option,
            "id_chaissis": id_chassis,
            "nom": nom,
            "prenom": prenom,
            "date_commande_client": date_commande,
            "date_envoie_agilog": None,
            "date_reception_agilog": None,
            "date_expedition_client": None,
            "date_livraison_client": None,
        }
        insert_into_commande_agilean_table(values)
        return redirect(url_for("afficher_nouvelle_commande_client", id_commande=id_))

    @app.route("/client/suivi-commande-client-nouvelle-cmd", methods=["GET"])
    def afficher_nouvelle_commande_client():
        id_commande = request.args.get("id_commande", "")
        sql = """SELECT * FROM commande_agilean AS lean 
        LEFT JOIN chassis ON lean.id_chassis=chassis.id_chassis 
        LEFT JOIN option ON lean.id_option=option.id_option
        WHERE id=?"""
        values = (id_commande,)
        commandes = execute_sql(sql, values)
        return render_template("suivi_commande_client.html", commandes=commandes)

    @app.route("/client/suivi-commande-client-id", methods=["GET"])
    def suivi_commande_client_id():
        return render_template("suivi_commande_client_id.html", msg="")

    @app.route("/client/suivi-commande-client-del", methods=["POST"])
    def supprimer_commande_client():
        supprimer = request.form.get("supprimer", "")  # Renvoi l'id de la commande
        id_commande = supprimer  # pour la lisibilité
        if id_commande == "":
            return redirect(url_for("client"))

        table_nom_prenom = execute_sql(
            "SELECT nom, prenom FROM commande_agilean WHERE id=?", (id_commande,)
        )
        nom, prenom = table_nom_prenom[0]["nom"], table_nom_prenom[0]["prenom"]

        sql_lean = "DELETE FROM commande_agilean WHERE id=?"
        sql_log = "DELETE FROM commande_agilog WHERE id_commande=?"
        sql_green = "DELETE FROM commande_agigreen WHERE id_commande=?"
        commit_sql(sql_lean, (id_commande,))
        commit_sql(sql_log, (id_commande,))
        commit_sql(sql_green, (id_commande,))
        return redirect(url_for("actualise_commande_client", nom=nom, prenom=prenom))

    @app.route("/client/suivi-commande-client-maj", methods=["POST"])
    def maj_commande_client():
        id_commande = request.form.get("id_commande", "")
        etat_commande = request.form.get("etat_commande")
        date_livraison_client = get_current_time()
        sql = "UPDATE commande_agilean SET date_livraison_client = ?, etat_commande = ? WHERE id=?"
        values = (date_livraison_client, etat_commande, id_commande)
        commit_sql(sql, values)
        return redirect(url_for("actualise_commande_client", id_commande=id_commande))

    @app.route("/client/suivi-commande-client-actualise", methods=["GET"])
    def actualise_commande_client():
        id_commande = request.args.get("id_commande", "")
        if id_commande != "":
            table_nom_prenom = execute_sql(
                "SELECT nom, prenom FROM commande_agilean WHERE id=?", (id_commande,)
            )
            nom, prenom = table_nom_prenom[0]["nom"], table_nom_prenom[0]["prenom"]
        else:
            nom, prenom = request.args.get("nom"), request.args.get("prenom")
        commandes = get_table_commande_client(values=(nom, prenom))
        return render_template("suivi_commande_client.html", commandes=commandes)

    @app.route("/client/suivi-commande-client", methods=["POST"])
    def afficher_commande_client():
        id_commande = request.form.get("id_commande", "")
        if id_commande != "":
            list_id = execute_sql("SELECT id FROM commande_agilean")
            if not id_commande.isdigit() or id_commande not in [
                str(id_["id"]) for id_ in list_id
            ]:
                return render_template(
                    "suivi_commande_client_id.html", msg="Mauvaise saisie"
                )
            values = (id_commande,)
        else:
            nom, prenom = request.form.get("nom", ""), request.form.get("prenom", "")
            values = (nom, prenom)
        commandes = get_table_commande_client(
            values=values
        )  # commande client par nom et prenom
        return render_template("suivi_commande_client.html", commandes=commandes)

    def get_table_commande_client(values: tuple):
        if len(values) == 2:
            sql = """SELECT * FROM commande_agilean AS lean 
            JOIN chassis ON lean.id_chassis=chassis.id_chassis 
            JOIN option ON option.id_option=lean.id_option
            WHERE lean.nom=? AND lean.prenom=?
            """
        else:
            sql = """SELECT * FROM commande_agilean AS lean 
            LEFT JOIN chassis ON lean.id_chassis=chassis.id_chassis 
            LEFT JOIN option ON option.id_option=lean.id_option
            WHERE id=?
            """
        return execute_sql(sql, values)

    return app  # fonction create_app du debut


if __name__ == "__main__":  # important si utilise pytest (avec create_app)
    app = create_app()
    app.run(debug=True, port=5680)
