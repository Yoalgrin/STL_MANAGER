"""Interface graphique Tkinter de STL Manager.

Affiche le catalogue, les doublons et la configuration des dossiers,
et délègue la logique de scan et de stockage au module :mod:`main`.
"""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sqlite3
import os
from collections import defaultdict
from send2trash import send2trash

import main


BASE_DE_DONNEES = main.BASE_DE_DONNEES


# ============================================================
# PRÉPARATION DE LA BASE DE DONNÉES
# ============================================================

main.preparer_base()


# ============================================================
# FENÊTRE PRINCIPALE
# ============================================================

fenetre = tk.Tk()

fenetre.title("STL Manager")
fenetre.geometry("1250x800")
fenetre.minsize(1000, 650)


# ============================================================
# ONGLET PRINCIPAL
# ============================================================

notebook = ttk.Notebook(
    fenetre
)

notebook.pack(
    fill="both",
    expand=True
)


onglet_catalogue = ttk.Frame(
    notebook
)

onglet_doublons = ttk.Frame(
    notebook
)

onglet_configuration = ttk.Frame(
    notebook
)


notebook.add(
    onglet_catalogue,
    text="📚 Catalogue"
)

notebook.add(
    onglet_doublons,
    text="⚠ Doublons exacts"
)

notebook.add(
    onglet_configuration,
    text="⚙ Configuration"
)


# ============================================================
# BARRE D'ÉTAT GLOBALE
# ============================================================

texte_statut = tk.StringVar()
texte_statut.set("Prêt.")

barre_statut = ttk.Label(
    fenetre,
    textvariable=texte_statut,
    anchor="w"
)

barre_statut.pack(
    fill="x",
    padx=10,
    pady=5
)


# ============================================================
# OUTILS COMMUNS
# ============================================================

def convertir_go(octets):

    if octets is None:
        return ""

    return round(
        octets / (1024 ** 3),
        2
    )


def ouvrir_fichier(chemin):

    if not chemin:
        return

    if os.path.exists(chemin):

        os.startfile(
            chemin
        )

    else:

        messagebox.showwarning(
            "Fichier indisponible",
            (
                "Le fichier n'est pas actuellement accessible.\n\n"
                "Le disque qui le contient est probablement hors ligne."
            )
        )


def ouvrir_dossier(chemin):

    if not chemin:
        return

    dossier = os.path.dirname(
        chemin
    )

    if os.path.exists(dossier):

        os.startfile(
            dossier
        )

    else:

        messagebox.showwarning(
            "Dossier indisponible",
            "Le dossier n'est pas actuellement accessible."
        )


# ============================================================
# ============================================================
# ONGLET CATALOGUE
# ============================================================
# ============================================================


# ============================================================
# TITRE
# ============================================================

titre_catalogue = tk.Label(
    onglet_catalogue,
    text="STL MANAGER",
    font=(
        "Segoe UI",
        22,
        "bold"
    )
)

titre_catalogue.pack(
    pady=15
)


# ============================================================
# SOURCES
# ============================================================

cadre_sources = ttk.LabelFrame(
    onglet_catalogue,
    text="Disques / Sources"
)

cadre_sources.pack(
    fill="x",
    padx=15,
    pady=10
)


colonnes_sources = (
    "etat",
    "source",
    "role",
    "archives",
    "dernier_scan"
)


table_sources = ttk.Treeview(
    cadre_sources,
    columns=colonnes_sources,
    show="tree headings",
    height=7
)


for colonne, titre, largeur in [

    ("etat", "État", 80),
    ("source", "Source", 130),
    ("role", "Rôle", 90),
    ("archives", "Archives", 75),
    ("dernier_scan", "Dernier scan", 145)

]:

    table_sources.heading(
        colonne,
        text=titre
    )

    table_sources.column(
        colonne,
        width=largeur,
        minwidth=largeur,
        anchor="center",
        stretch=False
    )


table_sources.pack(
    fill="x",
    padx=10,
    pady=10
)

table_sources.heading(
    "#0",
    text=""
)

table_sources.column(
    "#0",
    width=28,
    minwidth=28,
    stretch=False,
    anchor="center"
)


# Voyants natifs du Treeview : vrai vert / vrai gris.
def creer_voyant(couleur):

    image = tk.PhotoImage(
        width=12,
        height=12
    )

    pixels = []

    for y in range(12):

        ligne = []

        for x in range(12):

            dx = x - 5.5
            dy = y - 5.5

            if dx * dx + dy * dy <= 20:
                ligne.append(couleur)
            else:
                ligne.append("")

        pixels.append(ligne)

    for y, ligne in enumerate(pixels):
        for x, couleur_pixel in enumerate(ligne):
            if couleur_pixel:
                image.put(
                    couleur_pixel,
                    (x, y)
                )

    return image


voyant_en_ligne = creer_voyant("#18A558")
voyant_hors_ligne = creer_voyant("#9A9A9A")


# ============================================================
# BOUTONS SOURCES
# ============================================================

cadre_boutons = ttk.Frame(
    onglet_catalogue
)

cadre_boutons.pack(
    fill="x",
    padx=15,
    pady=(0, 10)
)


bouton_scanner = ttk.Button(
    cadre_boutons,
    text="💾 Scanner la source sélectionnée"
)

bouton_scanner.pack(
    side="left"
)


# Labels superposés uniquement sur la colonne "État".
# ============================================================
# ACTUALISATION AUTOMATIQUE EN LIGNE / HORS LIGNE
# ============================================================

def actualiser_etat_sources():

    try:

        sources_en_ligne = obtenir_sources_en_ligne()

        for item in table_sources.get_children():

            valeurs = list(
                table_sources.item(item)["values"]
            )

            if not valeurs:
                continue

            nom_source = str(valeurs[1])

            if nom_source.lower() in sources_en_ligne:
                nouvel_etat = "En ligne"
                nouveau_voyant = voyant_en_ligne
            else:
                nouvel_etat = "Hors ligne"
                nouveau_voyant = voyant_hors_ligne

            if str(valeurs[0]) != nouvel_etat:

                valeurs[0] = nouvel_etat

                table_sources.item(
                    item,
                    image=nouveau_voyant,
                    values=valeurs
                )

    finally:

        fenetre.after(
            3000,
            actualiser_etat_sources
        )


# ============================================================
# RECHERCHE
# ============================================================

cadre_recherche = ttk.LabelFrame(
    onglet_catalogue,
    text="Recherche"
)

cadre_recherche.pack(
    fill="x",
    padx=15,
    pady=10
)


champ_recherche = ttk.Entry(
    cadre_recherche,
    font=(
        "Segoe UI",
        12
    )
)

champ_recherche.pack(
    side="left",
    fill="x",
    expand=True,
    padx=10,
    pady=10
)


bouton_recherche = ttk.Button(
    cadre_recherche,
    text="🔍 Rechercher"
)

bouton_recherche.pack(
    side="left",
    padx=10
)


# ============================================================
# RÉSULTATS RECHERCHE
# ============================================================

cadre_resultats = ttk.LabelFrame(
    onglet_catalogue,
    text="Résultats"
)

cadre_resultats.pack(
    fill="both",
    expand=True,
    padx=15,
    pady=10
)


colonnes_resultats = (
    "nom",
    "source",
    "taille",
    "chemin"
)


table_resultats = ttk.Treeview(
    cadre_resultats,
    columns=colonnes_resultats,
    show="headings"
)


for colonne, titre, largeur in [

    ("nom", "Nom", 320),
    ("source", "Source", 140),
    ("taille", "Taille", 100),
    ("chemin", "Chemin", 500)

]:

    table_resultats.heading(
        colonne,
        text=titre
    )

    table_resultats.column(
        colonne,
        width=largeur
    )


table_resultats.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)


# ============================================================
# ÉTAT DES SOURCES
# ============================================================

def obtenir_sources_en_ligne():

    disques_detectes = (
        main.detecter_disques()
    )

    return set(
        disques_detectes.keys()
    )


# ============================================================
# CHARGER SOURCES
# ============================================================

def charger_sources():

    for ligne in table_sources.get_children():

        table_sources.delete(
            ligne
        )


    if not os.path.exists(
        BASE_DE_DONNEES
    ):

        texte_statut.set(
            "Base de données introuvable."
        )

        return


    # --------------------------------------------------------
    # COULEURS DES SOURCES
    # --------------------------------------------------------

    # --------------------------------------------------------
    # SOURCES PHYSIQUEMENT DÉTECTÉES
    # --------------------------------------------------------

    sources_en_ligne = (
        obtenir_sources_en_ligne()
    )


    # --------------------------------------------------------
    # LIRE LE CATALOGUE
    # --------------------------------------------------------

    connexion = sqlite3.connect(
        BASE_DE_DONNEES
    )

    curseur = connexion.cursor()


    curseur.execute("""
    SELECT
        s.nom_source,
        s.role_source,
        s.dernier_scan,
        COUNT(a.id) AS nombre_archives_reel
    FROM sources AS s
    LEFT JOIN archives AS a
        ON a.source = s.nom_source
    GROUP BY
        s.nom_source,
        s.role_source,
        s.dernier_scan
    ORDER BY
        s.nom_source
    """)


    sources = (
        curseur.fetchall()
    )


    connexion.close()


    # --------------------------------------------------------
    # AFFICHAGE
    # --------------------------------------------------------

    for (
        nom_source,
        role,
        dernier_scan,
        nombre_archives
    ) in sources:


        if nom_source.lower() in sources_en_ligne:

            etat = "En ligne"
            tag_etat = ""

        else:

            etat = "Hors ligne"
            tag_etat = ""


        table_sources.insert(
            "",
            "end",
            image=(
                voyant_en_ligne
                if etat == "En ligne"
                else voyant_hors_ligne
            ),
            values=(
                etat,
                nom_source,
                role,
                nombre_archives,
                dernier_scan
            )
        )


    texte_statut.set(
        "Sources actualisées."
    )


# ============================================================
# RECHERCHE
# ============================================================

def rechercher():

    recherche = (
        champ_recherche
        .get()
        .strip()
    )

    for ligne in table_resultats.get_children():

        table_resultats.delete(
            ligne
        )

    if not recherche:
        return

    connexion = sqlite3.connect(
        BASE_DE_DONNEES
    )

    curseur = connexion.cursor()

    curseur.execute("""
    SELECT
        nom_original,
        source,
        taille_octets,
        chemin
    FROM archives
    WHERE
        nom_original LIKE ?
        OR nom_normalise LIKE ?
    ORDER BY nom_original
    LIMIT 500
    """,
    (
        f"%{recherche}%",
        f"%{recherche.lower()}%"
    ))

    resultats = curseur.fetchall()

    connexion.close()

    for nom, source, taille, chemin in resultats:

        table_resultats.insert(
            "",
            "end",
            values=(
                nom,
                source,
                f"{convertir_go(taille)} Go",
                chemin
            )
        )

    texte_statut.set(
        f"{len(resultats)} résultat(s)."
    )


# ============================================================
# SCAN SOURCE
# ============================================================

def scanner_source_selectionnee():

    selection = table_sources.selection()

    if not selection:

        messagebox.showwarning(
            "Aucune source",
            "Sélectionne une source."
        )

        return


    valeurs = table_sources.item(
        selection[0]
    )["values"]


    nom_source = valeurs[1]

    etat = str(
        valeurs[0]
    )


    # --------------------------------------------------------
    # SOURCE HORS LIGNE
    # --------------------------------------------------------

    if "Hors ligne" in etat:

        messagebox.showwarning(
            "Source hors ligne",
            f"{nom_source} n'est pas accessible."
        )

        return


    # --------------------------------------------------------
    # CONFIRMATION
    # --------------------------------------------------------

    if not messagebox.askyesno(
        "Confirmer",
        (
            f"Scanner uniquement :\n\n"
            f"{nom_source} ?"
        )
    ):

        return


    # --------------------------------------------------------
    # LANCEMENT DU SCAN
    # --------------------------------------------------------

    texte_statut.set(
        f"Scan de {nom_source}..."
    )

    fenetre.update_idletasks()


    resultat = main.scanner_une_source(
        nom_source
    )


    # --------------------------------------------------------
    # SCAN RÉUSSI
    # --------------------------------------------------------

    if resultat:

        charger_sources()
        charger_doublons()

        messagebox.showinfo(
            "Scan terminé",
            f"{nom_source} a été actualisé."
        )


    # --------------------------------------------------------
    # AUCUN FICHIER TROUVÉ
    # --------------------------------------------------------

    else:

        charger_sources()

        supprimer_ancien_catalogue = (
            messagebox.askyesno(
                "Source vide",
                (
                    f"Aucun fichier compatible n'a été trouvé dans "
                    f"{nom_source}.\n\n"
                    "Voulez-vous supprimer de la base de données "
                    "les anciennes entrées de cette source ?\n\n"
                    "Oui : le catalogue de cette source sera vidé.\n"
                    "Non : l'ancien catalogue sera conservé."
                )
            )
        )

        if supprimer_ancien_catalogue:

            if main.vider_catalogue_source(
                nom_source
            ):

                charger_sources()
                charger_catalogue()
                charger_doublons()

                messagebox.showinfo(
                    "Catalogue actualisé",
                    (
                        f"Le catalogue de {nom_source} a été vidé.\n\n"
                        "Aucun fichier physique n'a été supprimé."
                    )
                )

            else:

                messagebox.showerror(
                    "Erreur",
                    (
                        f"Impossible de vider le catalogue de "
                        f"{nom_source}.\n\n"
                        "Aucune modification n'a été enregistrée."
                    )
                )


# ============================================================
# DOUBLE CLIC RECHERCHE
# ============================================================

def double_clic_resultat(evenement):

    selection = table_resultats.selection()

    if not selection:
        return "break"

    valeurs = table_resultats.item(
        selection[0]
    )["values"]

    chemin = valeurs[3]

    colonne = table_resultats.identify_column(
        evenement.x
    )

    if colonne == "#1":

        ouvrir_fichier(
            chemin
        )

        return "break"

    elif colonne == "#4":

        ouvrir_dossier(
            chemin
        )

        return "break"

    return "break"


# ============================================================
# ============================================================
# ONGLET DOUBLONS EXACTS
# ============================================================
# ============================================================

titre_doublons = tk.Label(
    onglet_doublons,
    text="DOUBLONS EXACTS",
    font=(
        "Segoe UI",
        22,
        "bold"
    )
)

titre_doublons.pack(
    pady=15
)


# ============================================================
# RECHERCHE DANS LES DOUBLONS
# ============================================================

cadre_recherche_doublons = ttk.Frame(
    onglet_doublons
)

cadre_recherche_doublons.pack(
    fill="x",
    padx=15,
    pady=(0, 5)
)


champ_recherche_doublons = ttk.Entry(
    cadre_recherche_doublons
)

champ_recherche_doublons.pack(
    side="left",
    fill="x",
    expand=True,
    padx=(0, 10)
)


bouton_recherche_doublons = ttk.Button(
    cadre_recherche_doublons,
    text="🔍 Rechercher"
)

bouton_recherche_doublons.pack(
    side="left"
)


# ============================================================
# TABLE GROUPES
# ============================================================

cadre_groupes = ttk.LabelFrame(
    onglet_doublons,
    text="Groupes de doublons exacts"
)

cadre_groupes.pack(
    fill="both",
    expand=True,
    padx=15,
    pady=10
)


colonnes_groupes = (
    "numero",
    "nom",
    "partie",
    "copies",
    "taille",
    "gain"
)


cadre_table_groupes = ttk.Frame(
    cadre_groupes
)

cadre_table_groupes.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)


table_groupes = ttk.Treeview(
    cadre_table_groupes,
    columns=colonnes_groupes,
    show="headings",
    height=12
)


for colonne, titre, largeur in [

    ("numero", "#", 60),
    ("nom", "Nom logique", 470),
    ("partie", "Partie", 100),
    ("copies", "Copies", 80),
    ("taille", "Taille/copie", 110),
    ("gain", "Gain potentiel", 120)

]:

    table_groupes.heading(
        colonne,
        text=titre
    )

    table_groupes.column(
        colonne,
        width=largeur
    )


scroll_vertical_groupes = ttk.Scrollbar(
    cadre_table_groupes,
    orient="vertical",
    command=table_groupes.yview
)


scroll_horizontal_groupes = ttk.Scrollbar(
    cadre_table_groupes,
    orient="horizontal",
    command=table_groupes.xview
)


table_groupes.configure(
    yscrollcommand=scroll_vertical_groupes.set,
    xscrollcommand=scroll_horizontal_groupes.set
)


table_groupes.grid(
    row=0,
    column=0,
    sticky="nsew"
)


scroll_vertical_groupes.grid(
    row=0,
    column=1,
    sticky="ns"
)


scroll_horizontal_groupes.grid(
    row=1,
    column=0,
    sticky="ew"
)


cadre_table_groupes.rowconfigure(
    0,
    weight=1
)


cadre_table_groupes.columnconfigure(
    0,
    weight=1
)


# ============================================================
# DÉTAIL DES COPIES
# ============================================================

cadre_copies = ttk.LabelFrame(
    onglet_doublons,
    text="Copies du groupe sélectionné"
)

cadre_copies.pack(
    fill="both",
    expand=True,
    padx=15,
    pady=10
)


colonnes_copies = (
    "source",
    "nom",
    "taille",
    "chemin",
    "corbeille"
)


cadre_table_copies = ttk.Frame(
    cadre_copies
)

cadre_table_copies.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)


table_copies = ttk.Treeview(
    cadre_table_copies,
    columns=colonnes_copies,
    show="headings",
    height=8
)


for colonne, titre, largeur in [

    ("source", "Source", 150),
    ("nom", "Nom du fichier", 350),
    ("taille", "Taille", 100),
    ("chemin", "Chemin", 550),
    ("corbeille", "🗑 Corbeille", 100)

]:

    table_copies.heading(
        colonne,
        text=titre
    )

    table_copies.column(
        colonne,
        width=largeur
    )


scroll_vertical_copies = ttk.Scrollbar(
    cadre_table_copies,
    orient="vertical",
    command=table_copies.yview
)


scroll_horizontal_copies = ttk.Scrollbar(
    cadre_table_copies,
    orient="horizontal",
    command=table_copies.xview
)


table_copies.configure(
    yscrollcommand=scroll_vertical_copies.set,
    xscrollcommand=scroll_horizontal_copies.set
)


table_copies.grid(
    row=0,
    column=0,
    sticky="nsew"
)


scroll_vertical_copies.grid(
    row=0,
    column=1,
    sticky="ns"
)


scroll_horizontal_copies.grid(
    row=1,
    column=0,
    sticky="ew"
)


cadre_table_copies.rowconfigure(
    0,
    weight=1
)


cadre_table_copies.columnconfigure(
    0,
    weight=1
)


# ============================================================
# BOUTONS DOUBLONS
# ============================================================

cadre_boutons_doublons = ttk.Frame(
    onglet_doublons
)

cadre_boutons_doublons.pack(
    fill="x",
    padx=15,
    pady=(0, 10)
)


bouton_ouvrir_archive = ttk.Button(
    cadre_boutons_doublons,
    text="📦 Ouvrir l'archive"
)

bouton_ouvrir_archive.pack(
    side="left",
    padx=(0, 10)
)


bouton_ouvrir_dossier = ttk.Button(
    cadre_boutons_doublons,
    text="📁 Ouvrir le dossier"
)

bouton_ouvrir_dossier.pack(
    side="left",
    padx=(0, 10)
)


bouton_actualiser_doublons = ttk.Button(
    cadre_boutons_doublons,
    text="🔄 Actualiser les doublons"
)

bouton_actualiser_doublons.pack(
    side="left"
)


# ============================================================
# STOCKAGE MÉMOIRE DES GROUPES
# ============================================================

groupes_doublons = []


# ============================================================
# CHARGER DOUBLONS
# ============================================================

def charger_doublons():

    global groupes_doublons

    for ligne in table_groupes.get_children():

        table_groupes.delete(
            ligne
        )

    for ligne in table_copies.get_children():

        table_copies.delete(
            ligne
        )

    connexion = sqlite3.connect(
        BASE_DE_DONNEES
    )

    curseur = connexion.cursor()

    curseur.execute("""
    SELECT
        id,
        source,
        nom_original,
        nom_normalise,
        taille_octets,
        chemin,
        partie
    FROM archives
    WHERE role_source = 'CLASSE'
    """)

    archives = curseur.fetchall()

    connexion.close()

    groupes = defaultdict(
        list
    )

    for (
        id_archive,
        source,
        nom_original,
        nom_normalise,
        taille_octets,
        chemin,
        partie
    ) in archives:

        cle = (
            nom_normalise,
            partie,
            taille_octets
        )

        groupes[cle].append(
            {
                "id": id_archive,
                "source": source,
                "nom_original": nom_original,
                "taille": taille_octets,
                "chemin": chemin
            }
        )

    groupes_doublons = []

    for cle, copies in groupes.items():

        copies_uniques = {}

        for copie in copies:

            copies_uniques[
                copie["chemin"]
            ] = copie

        copies = list(
            copies_uniques.values()
        )

        if len(copies) < 2:
            continue

        nom_normalise = cle[0]
        partie = cle[1]
        taille = cle[2]

        gain = (
            taille
            * (len(copies) - 1)
        )

        groupes_doublons.append(
            {
                "nom": nom_normalise,
                "partie": partie,
                "taille": taille,
                "gain": gain,
                "copies": copies
            }
        )

    groupes_doublons.sort(
        key=lambda groupe:
            groupe["gain"],
        reverse=True
    )

    afficher_liste_doublons(
        groupes_doublons
    )

    texte_statut.set(
        (
            f"{len(groupes_doublons)} "
            "groupe(s) de doublons exacts."
        )
    )


# ============================================================
# AFFICHAGE DE LA LISTE DES DOUBLONS
# ============================================================

def afficher_liste_doublons(groupes):

    for ligne in table_groupes.get_children():

        table_groupes.delete(
            ligne
        )

    for groupe in groupes:

        index_reel = groupes_doublons.index(
            groupe
        )

        table_groupes.insert(
            "",
            "end",
            iid=str(
                index_reel
            ),
            values=(
                index_reel + 1,
                groupe["nom"],
                groupe["partie"]
                if groupe["partie"]
                else "",
                len(
                    groupe["copies"]
                ),
                f"{convertir_go(groupe['taille'])} Go",
                f"{convertir_go(groupe['gain'])} Go"
            )
        )


# ============================================================
# AFFICHER COPIES DU GROUPE
# ============================================================

def afficher_copies(evenement=None):

    selection = table_groupes.selection()

    if not selection:
        return

    index = int(
        selection[0]
    )

    groupe = groupes_doublons[
        index
    ]

    for ligne in table_copies.get_children():

        table_copies.delete(
            ligne
        )

    for copie in groupe["copies"]:

        table_copies.insert(
            "",
            "end",
            iid=str(copie["id"]),
            values=(
                copie["source"],
                copie["nom_original"],
                f"{convertir_go(copie['taille'])} Go",
                copie["chemin"],
                "🗑 Corbeille"
            )
        )


# ============================================================
# OUVRIR COPIE SÉLECTIONNÉE
# ============================================================

def ouvrir_copie_selectionnee():

    selection = table_copies.selection()

    if not selection:

        messagebox.showwarning(
            "Aucune copie",
            "Sélectionne une copie."
        )

        return

    valeurs = table_copies.item(
        selection[0]
    )["values"]

    chemin = valeurs[3]

    ouvrir_fichier(
        chemin
    )


# ============================================================
# OUVRIR DOSSIER COPIE
# ============================================================

def ouvrir_dossier_copie():

    selection = table_copies.selection()

    if not selection:

        messagebox.showwarning(
            "Aucune copie",
            "Sélectionne une copie."
        )

        return

    valeurs = table_copies.item(
        selection[0]
    )["values"]

    chemin = valeurs[3]

    ouvrir_dossier(
        chemin
    )


# ============================================================
# DOUBLE CLIC COPIE
# ============================================================

def double_clic_copie(evenement):

    ligne = table_copies.identify_row(
        evenement.y
    )

    if not ligne:
        return "break"

    valeurs = table_copies.item(
        ligne
    )["values"]

    chemin = valeurs[3]

    colonne = table_copies.identify_column(
        evenement.x
    )

    if colonne == "#2":

        ouvrir_fichier(
            chemin
        )

        return "break"

    elif colonne == "#4":

        ouvrir_dossier(
            chemin
        )

        return "break"

    return "break"


# ============================================================
# RECHERCHE DANS LES DOUBLONS
# ============================================================

def rechercher_doublons():

    texte = (
        champ_recherche_doublons
        .get()
        .strip()
        .lower()
    )

    if not texte:

        afficher_liste_doublons(
            groupes_doublons
        )

        texte_statut.set(
            (
                f"{len(groupes_doublons)} "
                "groupe(s) de doublons exacts."
            )
        )

        return

    groupes_filtres = [

        groupe

        for groupe in groupes_doublons

        if texte in groupe["nom"].lower()

    ]

    afficher_liste_doublons(
        groupes_filtres
    )

    texte_statut.set(
        (
            f"{len(groupes_filtres)} "
            "groupe(s) trouvé(s)."
        )
    )


# ============================================================
# TRI DES COLONNES
# ============================================================

ordre_tri = {}


def trier_table_groupes(colonne):

    inverse = ordre_tri.get(
        colonne,
        False
    )

    lignes = []

    for item in table_groupes.get_children():

        valeur = table_groupes.set(
            item,
            colonne
        )

        if colonne in (
            "numero",
            "copies"
        ):

            try:

                valeur_tri = int(
                    valeur
                )

            except ValueError:

                valeur_tri = 0

        elif colonne in (
            "taille",
            "gain"
        ):

            try:

                valeur_tri = float(
                    valeur.replace(
                        " Go",
                        ""
                    )
                )

            except ValueError:

                valeur_tri = 0

        else:

            valeur_tri = valeur.lower()

        lignes.append(
            (
                valeur_tri,
                item
            )
        )

    lignes.sort(
        key=lambda element:
            element[0],
        reverse=inverse
    )

    for position, (
        valeur,
        item
    ) in enumerate(
        lignes
    ):

        table_groupes.move(
            item,
            "",
            position
        )

    ordre_tri[colonne] = (
        not inverse
    )


# ============================================================
# BRANCHEMENT DU TRI
# ============================================================

for colonne in colonnes_groupes:

    table_groupes.heading(
        colonne,
        command=lambda c=colonne:
            trier_table_groupes(c)
    )


# ============================================================
# MISE À LA CORBEILLE
# ============================================================

def supprimer_copie(
    id_archive,
    chemin
):

    if not chemin:
        return

    if not os.path.exists(chemin):

        messagebox.showwarning(
            "Fichier introuvable",
            (
                "Le fichier n'est pas accessible.\n\n"
                f"{chemin}"
            )
        )

        return


    # --------------------------------------------------------
    # MÉMORISER LE GROUPE ACTUEL
    # --------------------------------------------------------

    selection_groupe = table_groupes.selection()

    groupe_actuel = None

    if selection_groupe:

        index_groupe = int(
            selection_groupe[0]
        )

        groupe = groupes_doublons[
            index_groupe
        ]

        groupe_actuel = (
            groupe["nom"],
            groupe["partie"],
            groupe["taille"]
        )


    # --------------------------------------------------------
    # CONFIRMATION
    # --------------------------------------------------------

    nom_fichier = os.path.basename(
        chemin
    )

    confirmation = messagebox.askyesno(
        "Confirmer la mise à la Corbeille",
        (
            "Mettre CE fichier dans la Corbeille ?\n\n"
            f"{nom_fichier}\n\n"
            f"{chemin}\n\n"
            "Le fichier pourra être restauré depuis la Corbeille Windows."
        )
    )

    if not confirmation:
        return


    try:

        # ----------------------------------------------------
        # FICHIER PHYSIQUE → CORBEILLE
        # ----------------------------------------------------

        send2trash(
            chemin
        )


        # ----------------------------------------------------
        # SUPPRESSION DE CETTE SEULE LIGNE SQLITE
        # ----------------------------------------------------

        connexion = sqlite3.connect(
            BASE_DE_DONNEES
        )

        curseur = connexion.cursor()

        curseur.execute(
            """
            DELETE FROM archives
            WHERE id = ?
            """,
            (
                id_archive,
            )
        )

        connexion.commit()
        connexion.close()


        # ----------------------------------------------------
        # RECHARGER LES DOUBLONS
        # ----------------------------------------------------

        charger_doublons()


        # ----------------------------------------------------
        # RETROUVER LE GROUPE
        # ----------------------------------------------------

        if groupe_actuel is not None:

            for index, groupe in enumerate(
                groupes_doublons
            ):

                cle_groupe = (
                    groupe["nom"],
                    groupe["partie"],
                    groupe["taille"]
                )

                if cle_groupe == groupe_actuel:

                    iid = str(
                        index
                    )

                    table_groupes.selection_set(
                        iid
                    )

                    table_groupes.see(
                        iid
                    )

                    afficher_copies()

                    break


        # ----------------------------------------------------
        # ACTUALISER AUSSI LES COMPTEURS SOURCES
        # ----------------------------------------------------

        charger_sources()


        # ----------------------------------------------------
        # STATUT
        # ----------------------------------------------------

        texte_statut.set(
            f"Fichier mis à la Corbeille : {nom_fichier}"
        )


    except Exception as erreur:

        messagebox.showerror(
            "Erreur",
            (
                "Impossible de mettre le fichier à la Corbeille.\n\n"
                f"{erreur}"
            )
        )


# ============================================================
# CLIC SUR LA COLONNE CORBEILLE
# ============================================================

def clic_table_copies(evenement):

    ligne = table_copies.identify_row(
        evenement.y
    )

    colonne = table_copies.identify_column(
        evenement.x
    )

    if not ligne:
        return


    if colonne == "#5":

        valeurs = table_copies.item(
            ligne
        )["values"]

        id_archive = int(
            ligne
        )

        chemin = valeurs[3]

        supprimer_copie(
            id_archive,
            chemin
        )


# ============================================================
# ============================================================
# ONGLET CONFIGURATION
# ============================================================
# ============================================================

titre_configuration = tk.Label(
    onglet_configuration,
    text="CONFIGURATION",
    font=("Segoe UI", 22, "bold")
)
titre_configuration.pack(pady=15)

texte_configuration = ttk.Label(
    onglet_configuration,
    text=(
        "Noms des dossiers que STL Manager doit rechercher "
        "à la racine des disques connectés."
    )
)
texte_configuration.pack(padx=15, pady=(0, 10))

cadre_detection = ttk.LabelFrame(
    onglet_configuration,
    text="Dossiers à détecter"
)
cadre_detection.pack(fill="x", padx=15, pady=10)

liste_dossiers_detection = tk.Listbox(
    cadre_detection,
    height=8,
    exportselection=False
)
liste_dossiers_detection.pack(fill="x", padx=10, pady=10)

cadre_ajout_detection = ttk.Frame(cadre_detection)
cadre_ajout_detection.pack(fill="x", padx=10, pady=(0, 10))

champ_dossier_detection = ttk.Entry(cadre_ajout_detection)
champ_dossier_detection.pack(
    side="left",
    fill="x",
    expand=True,
    padx=(0, 10)
)

bouton_ajouter_dossier = ttk.Button(
    cadre_ajout_detection,
    text="➕ Ajouter"
)
bouton_ajouter_dossier.pack(side="left", padx=(0, 10))

bouton_supprimer_dossier = ttk.Button(
    cadre_ajout_detection,
    text="➖ Supprimer"
)
bouton_supprimer_dossier.pack(side="left")


def charger_dossiers_detection():

    liste_dossiers_detection.delete(0, tk.END)

    for nom_dossier in main.obtenir_dossiers_detection():

        liste_dossiers_detection.insert(
            tk.END,
            nom_dossier
        )


def ajouter_dossier_detection_interface():

    nom_dossier = champ_dossier_detection.get().strip()

    if not nom_dossier:

        messagebox.showwarning(
            "Nom manquant",
            "Entre le nom d'un dossier à détecter."
        )
        return

    ajoute = main.ajouter_dossier_detection(nom_dossier)

    if ajoute:

        champ_dossier_detection.delete(0, tk.END)
        charger_dossiers_detection()
        charger_sources()

        texte_statut.set(
            f"Dossier de détection ajouté : {nom_dossier}"
        )

    else:

        messagebox.showinfo(
            "Déjà présent",
            f"Le dossier « {nom_dossier} » est déjà dans la configuration."
        )


def supprimer_dossier_detection_interface():

    selection = liste_dossiers_detection.curselection()

    if not selection:

        messagebox.showwarning(
            "Aucun dossier",
            "Sélectionne un dossier à supprimer."
        )
        return

    nom_dossier = liste_dossiers_detection.get(selection[0])

    confirmation = messagebox.askyesno(
        "Confirmer",
        (
            "Retirer ce nom de la détection ?\n\n"
            f"{nom_dossier}\n\n"
            "Cela ne supprime aucun fichier, aucune source "
            "et aucune archive du catalogue.\n"
            "STL Manager cessera simplement de rechercher "
            "ce nom de dossier."
        )
    )

    if not confirmation:
        return

    supprime = main.supprimer_dossier_detection(nom_dossier)

    if supprime:

        charger_dossiers_detection()
        charger_sources()

        texte_statut.set(
            f"Dossier de détection retiré : {nom_dossier}"
        )


bouton_ajouter_dossier.config(
    command=ajouter_dossier_detection_interface
)

bouton_supprimer_dossier.config(
    command=supprimer_dossier_detection_interface
)

champ_dossier_detection.bind(
    "<Return>",
    lambda evenement:
        ajouter_dossier_detection_interface()
)


# ============================================================
# COMMANDES
# ============================================================


bouton_scanner.config(
    command=scanner_source_selectionnee
)


bouton_recherche.config(
    command=rechercher
)


bouton_recherche_doublons.config(
    command=rechercher_doublons
)


bouton_actualiser_doublons.config(
    command=charger_doublons
)


bouton_ouvrir_archive.config(
    command=ouvrir_copie_selectionnee
)


bouton_ouvrir_dossier.config(
    command=ouvrir_dossier_copie
)


# ============================================================
# ÉVÉNEMENTS
# ============================================================

champ_recherche.bind(
    "<Return>",
    lambda evenement:
        rechercher()
)


champ_recherche_doublons.bind(
    "<Return>",
    lambda evenement:
        rechercher_doublons()
)


table_resultats.bind(
    "<Double-1>",
    double_clic_resultat
)


table_groupes.bind(
    "<<TreeviewSelect>>",
    afficher_copies
)


table_copies.bind(
    "<Double-1>",
    double_clic_copie
)


table_copies.bind(
    "<ButtonRelease-1>",
    clic_table_copies,
    add="+"
)


# ============================================================
# CHARGEMENT INITIAL
# ============================================================

charger_sources()

charger_doublons()

charger_dossiers_detection()

actualiser_etat_sources()


# ============================================================
# LANCEMENT
# ============================================================

fenetre.mainloop()