"""Moteur de STL Manager.

Gestion du catalogue SQLite, détection des volumes Windows, identification
des sources et scan sécurisé des fichiers pris en charge.
"""

import os
import re
import sqlite3
import subprocess
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DE_DONNEES = "stl_manager.db"


# ============================================================
# NORMALISATION DES NOMS
# ============================================================

def analyser_nom(nom_fichier):

    nom_sans_extension = os.path.splitext(
        nom_fichier
    )[0]

    nom = nom_sans_extension.lower()


    # --------------------------------------------------------
    # NORMALISATIONS CONNUES
    # --------------------------------------------------------

    nom = re.sub(
        r"\bnfsw\b",
        "nsfw",
        nom
    )

    nom = nom.replace(
        "e.s. monster",
        "es monster"
    )

    nom = nom.replace(
        "e.s monster",
        "es monster"
    )


    # --------------------------------------------------------
    # FOURNISSEURS À IGNORER
    # --------------------------------------------------------

    FOURNISSEURS_A_IGNORER = [
        "@pixel_3d_stl",
        "@stl_for_home",
        "@projectstl",
        "@stl_zone",
        "@stlsharehammer",
        "@stlftw",
        "t.me_moxomor_aka",
        "t.me moxomor aka"
    ]


    for fournisseur in FOURNISSEURS_A_IGNORER:

        nom = nom.replace(
            fournisseur,
            " "
        )


    # --------------------------------------------------------
    # TEXTES PARASITES À IGNORER
    # --------------------------------------------------------

    TEXTES_A_IGNORER = [
        "3d print model"
    ]


    for texte in TEXTES_A_IGNORER:

        nom = nom.replace(
            texte,
            " "
        )


    # --------------------------------------------------------
    # SÉPARATEURS
    # --------------------------------------------------------

    nom = nom.replace("_", " ")
    nom = nom.replace("-", " ")
    nom = nom.replace("–", " ")
    nom = nom.replace("—", " ")

    nom = nom.replace("@", " ")
    nom = nom.replace("+", " ")
    nom = nom.replace(",", " ")


    nom = re.sub(
        r"\s+",
        " ",
        nom
    )


    # --------------------------------------------------------
    # ARCHIVES MULTIPART
    # --------------------------------------------------------

    partie = None


    match_part = re.search(
        r"\bpart\s*(\d+)\b",
        nom
    )


    if match_part:

        numero_partie = (
            match_part.group(1)
        )

        partie = (
            f"part{numero_partie}"
        )


        nom = re.sub(
            r"\bpart\s*\d+\b",
            " ",
            nom
        )


    # --------------------------------------------------------
    # VARIANTES
    # --------------------------------------------------------

    mots_variantes = [

        "nsfw",
        "sfw",

        "nude",
        "naked",

        "bust",

        "supported",
        "unsupported",

        "presupported",
        "pre supported",

        "32mm",
        "40mm",
        "54mm",
        "75mm"
    ]


    variantes_trouvees = []


    for variante in mots_variantes:

        recherche = (
            rf"\b{re.escape(variante)}\b"
        )


        if re.search(
            recherche,
            nom
        ):

            variantes_trouvees.append(
                variante
            )


    # --------------------------------------------------------
    # NETTOYAGE FINAL
    # --------------------------------------------------------

    nom = re.sub(
        r"\s+",
        " ",
        nom
    )


    nom = nom.strip(
        " .-_"
    )


    return (
        nom,
        variantes_trouvees,
        partie
    )


# ============================================================
# DÉTECTION DES DISQUES WINDOWS
# ============================================================

def detecter_disques():

    disques = {}


    try:

        commande = [

            "powershell",

            "-NoProfile",

            "-Command",

            (
                "Get-Volume | "
                "Where-Object {$_.DriveLetter -ne $null} | "
                "Select-Object DriveLetter,FileSystemLabel | "
                "ConvertTo-Csv -NoTypeInformation"
            )
        ]


        resultat = subprocess.run(

            commande,

            capture_output=True,

            text=True,

            encoding="utf-8",

            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW
        )


        lignes = (
            resultat.stdout.splitlines()
        )


        for ligne in lignes[1:]:

            ligne = ligne.strip()


            if not ligne:
                continue


            morceaux = (

                ligne
                .replace('"', '')
                .split(",")

            )


            if len(morceaux) < 2:
                continue


            lettre = (
                morceaux[0].strip()
            )

            nom_volume = (
                morceaux[1].strip()
            )


            if lettre and nom_volume:

                disques[
                    nom_volume.lower()
                ] = (
                    lettre + ":"
                )


    except Exception as erreur:

        print(
            "Impossible de détecter les volumes Windows :",
            erreur
        )


    return disques

# ============================================================
# CONFIGURATION DES DOSSIERS À DÉTECTER
# ============================================================

def obtenir_dossiers_detection():

    preparer_base()

    connexion = sqlite3.connect(
        BASE_DE_DONNEES
    )

    curseur = connexion.cursor()


    curseur.execute("""
    SELECT nom_dossier
    FROM dossiers_detection
    ORDER BY nom_dossier
    """)


    resultats = (
        curseur.fetchall()
    )


    connexion.close()


    return [
        ligne[0]
        for ligne in resultats
    ]


def ajouter_dossier_detection(
    nom_dossier
):

    nom_dossier = (
        nom_dossier.strip()
    )


    if not nom_dossier:

        return False


    preparer_base()


    connexion = sqlite3.connect(
        BASE_DE_DONNEES
    )

    curseur = connexion.cursor()


    curseur.execute(
        """
        INSERT OR IGNORE INTO dossiers_detection
        (nom_dossier)
        VALUES (?)
        """,
        (
            nom_dossier,
        )
    )


    ajoute = (
        curseur.rowcount > 0
    )


    connexion.commit()
    connexion.close()


    return ajoute


def supprimer_dossier_detection(
    nom_dossier
):

    preparer_base()


    connexion = sqlite3.connect(
        BASE_DE_DONNEES
    )

    curseur = connexion.cursor()


    curseur.execute(
        """
        DELETE FROM dossiers_detection
        WHERE nom_dossier = ?
        """,
        (
            nom_dossier,
        )
    )


    supprime = (
        curseur.rowcount > 0
    )


    connexion.commit()
    connexion.close()


    return supprime
# ============================================================
# DÉTECTION DES DOSSIERS CONFIGURÉS
# ============================================================

def detecter_dossiers_stl():

    dossiers_trouves = []


    # --------------------------------------------------------
    # RÉCUPÉRER LES LETTRES DE LECTEURS WINDOWS
    # --------------------------------------------------------

    try:

        commande = [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                "Get-Volume | "
                "Where-Object {$_.DriveLetter -ne $null} | "
                "Select-Object -ExpandProperty DriveLetter"
            )
        ]


        resultat = subprocess.run(
            commande,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW
        )


        lettres = [
            ligne.strip()
            for ligne in resultat.stdout.splitlines()
            if ligne.strip()
        ]


    except Exception as erreur:

        print(
            "Impossible de rechercher les dossiers STL :",
            erreur
        )

        return dossiers_trouves


    # --------------------------------------------------------
    # CHERCHER LES NOMS CONFIGURÉS
    # --------------------------------------------------------

    for lettre in lettres:

        racine = lettre + ":\\"


        for nom_dossier in obtenir_dossiers_detection():

            chemin = os.path.join(
                racine,
                nom_dossier
            )


            if os.path.isdir(
                chemin
            ):

                dossiers_trouves.append({
                    "lecteur": lettre + ":",
                    "nom_dossier": nom_dossier,
                    "chemin": chemin
                })


    return dossiers_trouves


# ============================================================
# IDENTIFICATION DES SOURCES STL MANAGER
# ============================================================

NOM_FICHIER_IDENTITE = ".stlmanager"


def creer_identite_source(
    dossier_racine,
    nom_source,
    role="CLASSE",
    sous_dossier=""
):

    if not os.path.isdir(
        dossier_racine
    ):

        print(
            "Impossible de créer l'identité :",
            dossier_racine
        )

        return False


    chemin_identite = os.path.join(
        dossier_racine,
        NOM_FICHIER_IDENTITE
    )


    try:

        with open(
            chemin_identite,
            "w",
            encoding="utf-8"
        ) as fichier:

            fichier.write(
                f"source={nom_source}\n"
            )

            fichier.write(
                f"role={role}\n"
            )

            fichier.write(
                f"sous_dossier={sous_dossier}\n"
            )


        print(
            "Identité créée :",
            chemin_identite
        )

        return True


    except OSError as erreur:

        print(
            "Impossible de créer l'identité :",
            erreur
        )

        return False


def configurer_nouvelle_source(
    dossier_racine,
    nom_source,
    role="CLASSE",
    sous_dossier=""
):
    """
    Configure un dossier déjà détectable comme nouvelle source STL Manager.

    Cette fonction ne scanne rien et ne modifie aucun fichier d'archive.
    Elle crée uniquement le fichier .stlmanager dans le dossier racine.
    """

    dossier_racine = os.path.abspath(
        dossier_racine
    )

    nom_source = (
        nom_source.strip()
    )

    role = (
        role.strip().upper()
    )

    sous_dossier = (
        sous_dossier.strip()
    )


    # --------------------------------------------------------
    # CONTRÔLES DE BASE
    # --------------------------------------------------------

    if not os.path.isdir(
        dossier_racine
    ):

        return (
            False,
            "Le dossier racine n'existe pas."
        )


    if not nom_source:

        return (
            False,
            "Le nom de la source est obligatoire."
        )


    if role not in (
        "CLASSE",
        "A_TRIER"
    ):

        return (
            False,
            "Le rôle doit être CLASSE ou A_TRIER."
        )


    # --------------------------------------------------------
    # LE DOSSIER RACINE DOIT ÊTRE DANS LA CONFIGURATION
    # DE DÉTECTION
    # --------------------------------------------------------

    nom_dossier_racine = os.path.basename(
        os.path.normpath(
            dossier_racine
        )
    )


    dossiers_detection = {
        nom.lower()
        for nom in obtenir_dossiers_detection()
    }


    if nom_dossier_racine.lower() not in dossiers_detection:

        return (
            False,
            (
                f"Le dossier « {nom_dossier_racine} » n'est pas "
                "dans la liste des dossiers à détecter."
            )
        )


    # --------------------------------------------------------
    # NE PAS ÉCRASER UNE IDENTITÉ EXISTANTE
    # --------------------------------------------------------

    chemin_identite = os.path.join(
        dossier_racine,
        NOM_FICHIER_IDENTITE
    )


    if os.path.exists(
        chemin_identite
    ):

        return (
            False,
            "Ce dossier possède déjà un fichier .stlmanager."
        )


    # --------------------------------------------------------
    # VÉRIFIER LE SOUS-DOSSIER S'IL EST RENSEIGNÉ
    # --------------------------------------------------------

    if sous_dossier:

        # Un sous-dossier doit rester relatif au dossier racine.
        if os.path.isabs(
            sous_dossier
        ):

            return (
                False,
                "Le sous-dossier doit être un chemin relatif."
            )


        dossier_scan = os.path.abspath(
            os.path.join(
                dossier_racine,
                sous_dossier
            )
        )


        try:

            commun = os.path.commonpath(
                [
                    dossier_racine,
                    dossier_scan
                ]
            )

        except ValueError:

            return (
                False,
                "Sous-dossier invalide."
            )


        if os.path.normcase(
            commun
        ) != os.path.normcase(
            dossier_racine
        ):

            return (
                False,
                "Le sous-dossier doit rester dans le dossier racine."
            )


        if not os.path.isdir(
            dossier_scan
        ):

            return (
                False,
                (
                    "Le sous-dossier indiqué n'existe pas : "
                    f"{sous_dossier}"
                )
            )


    # --------------------------------------------------------
    # ÉVITER DEUX SOURCES EN LIGNE AVEC LE MÊME NOM
    # --------------------------------------------------------

    sources_existantes = (
        detecter_sources_stl_manager()
    )


    if nom_source in sources_existantes:

        return (
            False,
            (
                f"Une source en ligne nommée « {nom_source} » "
                "existe déjà."
            )
        )


    # --------------------------------------------------------
    # CRÉER L'IDENTITÉ
    # --------------------------------------------------------

    cree = creer_identite_source(
        dossier_racine,
        nom_source,
        role,
        sous_dossier
    )


    if not cree:

        return (
            False,
            "Impossible de créer le fichier .stlmanager."
        )


    return (
        True,
        "Source configurée."
    )


def lire_identite_source(
    dossier_racine
):

    chemin_identite = os.path.join(
        dossier_racine,
        NOM_FICHIER_IDENTITE
    )


    if not os.path.isfile(
        chemin_identite
    ):

        return None


    informations = {}


    try:

        with open(
            chemin_identite,
            "r",
            encoding="utf-8"
        ) as fichier:

            for ligne in fichier:

                ligne = ligne.strip()


                if not ligne:
                    continue


                if "=" not in ligne:
                    continue


                cle, valeur = ligne.split(
                    "=",
                    1
                )


                informations[
                    cle.strip()
                ] = (
                    valeur.strip()
                )


    except OSError as erreur:

        print(
            "Impossible de lire l'identité :",
            erreur
        )

        return None


    if "source" not in informations:

        return None


    return informations


# ============================================================
# DÉTECTION AUTOMATIQUE DES SOURCES STL MANAGER
# ============================================================

def detecter_sources_stl_manager():

    sources_trouvees = {}

    dossiers = (
        detecter_dossiers_stl()
    )


    for dossier_detecte in dossiers:

        dossier_racine = (
            dossier_detecte["chemin"]
        )


        identite = lire_identite_source(
            dossier_racine
        )


        # ----------------------------------------------------
        # DOSSIER TROUVÉ MAIS NON CONFIGURÉ
        # ----------------------------------------------------

        if identite is None:

            continue


        nom_source = identite.get(
            "source",
            ""
        ).strip()


        role = identite.get(
            "role",
            "CLASSE"
        ).strip()


        sous_dossier = identite.get(
            "sous_dossier",
            ""
        ).strip()


        if not nom_source:

            continue


        # ----------------------------------------------------
        # CONSTRUIRE LE DOSSIER RÉEL À SCANNER
        # ----------------------------------------------------

        if sous_dossier:

            dossier_scan = os.path.join(
                dossier_racine,
                sous_dossier
            )

        else:

            dossier_scan = (
                dossier_racine
            )


        sources_trouvees[
            nom_source
        ] = {

            "dossier_racine":
                dossier_racine,

            "dossier_scan":
                dossier_scan,

            "role":
                role,

            "lecteur":
                dossier_detecte[
                    "lecteur"
                ],

            "nom_dossier":
                dossier_detecte[
                    "nom_dossier"
                ]
        }


    return sources_trouvees


# ============================================================
# CRÉATION DES TABLES
# ============================================================

def preparer_base():

    connexion = sqlite3.connect(
        BASE_DE_DONNEES
    )

    curseur = connexion.cursor()


    # --------------------------------------------------------
    # TABLE ARCHIVES
    # --------------------------------------------------------

    curseur.execute("""
    CREATE TABLE IF NOT EXISTS archives (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        source TEXT NOT NULL,

        role_source TEXT NOT NULL,

        nom_original TEXT NOT NULL,

        nom_normalise TEXT NOT NULL,

        extension TEXT,

        taille_octets INTEGER,

        chemin TEXT NOT NULL,

        variante TEXT,

        partie TEXT,

        UNIQUE(source, chemin)
    )
    """)


    # --------------------------------------------------------
    # TABLE SOURCES
    # --------------------------------------------------------

    curseur.execute("""
    CREATE TABLE IF NOT EXISTS sources (

        nom_source TEXT PRIMARY KEY,

        role_source TEXT NOT NULL,

        chemin_scan TEXT,

        dernier_scan TEXT,

        nombre_archives INTEGER
    )
    """)


    # --------------------------------------------------------
    # TABLE DOSSIERS À DÉTECTER
    # --------------------------------------------------------

    curseur.execute("""
    CREATE TABLE IF NOT EXISTS dossiers_detection (

        nom_dossier TEXT PRIMARY KEY
    )
    """)


    # --------------------------------------------------------
    # CONFIGURATION PAR DÉFAUT
    # --------------------------------------------------------

    curseur.execute(
        """
        INSERT OR IGNORE INTO dossiers_detection
        (nom_dossier)
        VALUES (?)
        """,
        (
            "STL",
        )
    )


    curseur.execute(
        """
        INSERT OR IGNORE INTO dossiers_detection
        (nom_dossier)
        VALUES (?)
        """,
        (
            "3D Print",
        )
    )


    # --------------------------------------------------------
    # VALIDATION ET FERMETURE
    # --------------------------------------------------------

    connexion.commit()

    connexion.close()

# ============================================================
# MOTEUR DE SCAN SÉCURISÉ
# ============================================================

def scanner_source(
    nom_source,
    dossier,
    role
):

    print()
    print("----------------------------------------")
    print("Scan :", dossier)
    print("Rôle :", role)


    # --------------------------------------------------------
    # VÉRIFICATION DU DOSSIER
    # --------------------------------------------------------

    if not os.path.isdir(
        dossier
    ):

        print(
            "Dossier introuvable :",
            dossier
        )

        print(
            "Ancien catalogue conservé."
        )

        return 0


    # --------------------------------------------------------
    # CONSTRUIRE LE NOUVEAU CATALOGUE EN MÉMOIRE
    # --------------------------------------------------------

    nouvelles_archives = []


    try:

        for (
            chemin_actuel,
            sous_dossiers,
            fichiers
        ) in os.walk(
            dossier
        ):


            for fichier in fichiers:


                if not fichier.lower().endswith(
                    (
        ".zip",
        ".rar",
        ".7z",
        ".stl",
        ".3mf"
    )
                ):

                    continue


                chemin_complet = os.path.join(
                    chemin_actuel,
                    fichier
                )


                try:

                    taille = os.path.getsize(
                        chemin_complet
                    )


                except OSError:

                    print(
                        "Impossible de lire :",
                        chemin_complet
                    )

                    continue


                extension = os.path.splitext(
                    fichier
                )[1].lower()


                (
                    nom_normalise,
                    variantes,
                    partie
                ) = analyser_nom(
                    fichier
                )


                variante_texte = ", ".join(
                    variantes
                )


                nouvelles_archives.append(
                    (
                        nom_source,
                        role,
                        fichier,
                        nom_normalise,
                        extension,
                        taille,
                        chemin_complet,
                        variante_texte,
                        partie
                    )
                )


    except Exception as erreur:

        print(
            "Erreur pendant le scan :",
            erreur
        )

        print(
            "Ancien catalogue conservé."
        )

        return 0


    compteur = len(
        nouvelles_archives
    )


    # --------------------------------------------------------
    # SÉCURITÉ : NE PAS EFFACER UN CATALOGUE POUR UN DOSSIER VIDE
    # --------------------------------------------------------

    if compteur == 0:

        print(
            "Aucune archive trouvée."
        )

        print(
            "Ancien catalogue conservé."
        )

        return 0


    # --------------------------------------------------------
    # LE NOUVEAU SCAN EST PRÊT
    # MISE À JOUR ATOMIQUE DE SQLITE
    # --------------------------------------------------------

    connexion = None


    try:

        connexion = sqlite3.connect(
            BASE_DE_DONNEES
        )

        curseur = connexion.cursor()


        # ----------------------------------------------------
        # DÉBUT TRANSACTION
        # ----------------------------------------------------

        curseur.execute(
            "BEGIN"
        )


        # ----------------------------------------------------
        # SUPPRIMER L'ANCIEN INDEX DE CETTE SOURCE
        # ----------------------------------------------------

        curseur.execute(
            """
            DELETE FROM archives
            WHERE source = ?
            """,
            (
                nom_source,
            )
        )


        # ----------------------------------------------------
        # INSÉRER LE NOUVEAU CATALOGUE
        # ----------------------------------------------------

        curseur.executemany(
            """
            INSERT INTO archives
            (
                source,
                role_source,
                nom_original,
                nom_normalise,
                extension,
                taille_octets,
                chemin,
                variante,
                partie
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            nouvelles_archives
        )


        # ----------------------------------------------------
        # DATE DU SCAN
        # ----------------------------------------------------

        date_scan = datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )


        # ----------------------------------------------------
        # METTRE À JOUR LA SOURCE
        # ----------------------------------------------------

        curseur.execute(
            """
            INSERT OR REPLACE INTO sources
            (
                nom_source,
                role_source,
                chemin_scan,
                dernier_scan,
                nombre_archives
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                nom_source,
                role,
                dossier,
                date_scan,
                compteur
            )
        )


        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        connexion.commit()


    except Exception as erreur:

        if connexion is not None:

            connexion.rollback()


        print(
            "Erreur pendant la mise à jour SQLite :",
            erreur
        )

        print(
            "ROLLBACK effectué."
        )

        print(
            "Ancien catalogue conservé."
        )

        return 0


    finally:

        if connexion is not None:

            connexion.close()


    print(
        "Archives trouvées :",
        compteur
    )


    return compteur


# ============================================================
# SCANNER UNE SEULE SOURCE
# Nouveau système dynamique
# ============================================================


def vider_catalogue_source(
    nom_source
):

    preparer_base()

    connexion = sqlite3.connect(
        BASE_DE_DONNEES
    )

    curseur = connexion.cursor()

    try:

        curseur.execute(
            """
            DELETE FROM archives
            WHERE source = ?
            """,
            (
                nom_source,
            )
        )

        curseur.execute(
            """
            UPDATE sources
            SET
                nombre_archives = 0,
                dernier_scan = ?
            WHERE nom_source = ?
            """,
            (
                datetime.now().isoformat(
                    timespec="seconds"
                ),
                nom_source
            )
        )

        connexion.commit()
        return True

    except Exception:

        connexion.rollback()
        return False

    finally:

        connexion.close()


def scanner_une_source(
    nom_source
):

    preparer_base()


    # --------------------------------------------------------
    # DÉTECTER LES SOURCES STL MANAGER DÉJÀ CONFIGURÉES
    # --------------------------------------------------------

    sources_detectees = (
        detecter_sources_stl_manager()
    )


    # --------------------------------------------------------
    # SOURCE DÉJÀ CONFIGURÉE
    # --------------------------------------------------------

    if nom_source in sources_detectees:

        configuration = (
            sources_detectees[
                nom_source
            ]
        )


    # --------------------------------------------------------
    # PAS DE .stlmanager :
    # RETROUVER LE DISQUE PAR SON NOM DE VOLUME WINDOWS,
    # CRÉER L'IDENTITÉ, PUIS CONTINUER LE SCAN
    # --------------------------------------------------------

    else:

        disques = detecter_disques()

        lecteur = disques.get(
            nom_source.lower()
        )


        if not lecteur:

            print(
                "Source hors ligne ou introuvable :",
                nom_source
            )

            print(
                "Ancien catalogue conservé."
            )

            return False


        dossier_racine = None
        nom_dossier_detecte = None


        for nom_dossier in obtenir_dossiers_detection():

            chemin = os.path.join(
                lecteur + "\\",
                nom_dossier
            )


            if os.path.isdir(
                chemin
            ):

                dossier_racine = chemin
                nom_dossier_detecte = nom_dossier
                break


        if dossier_racine is None:

            print(
                "Aucun dossier configuré à scanner sur :",
                nom_source
            )

            print(
                "Ancien catalogue conservé."
            )

            return False


        if not creer_identite_source(
            dossier_racine,
            nom_source,
            "CLASSE",
            ""
        ):

            print(
                "Impossible de créer le fichier .stlmanager."
            )

            print(
                "Ancien catalogue conservé."
            )

            return False


        configuration = {
            "dossier_racine": dossier_racine,
            "dossier_scan": dossier_racine,
            "role": "CLASSE",
            "lecteur": lecteur,
            "nom_dossier": nom_dossier_detecte
        }


    # --------------------------------------------------------
    # CONFIGURATION DE LA SOURCE
    # --------------------------------------------------------

    dossier = (
        configuration[
            "dossier_scan"
        ]
    )


    role = (
        configuration[
            "role"
        ]
    )


    # --------------------------------------------------------
    # VÉRIFIER LE DOSSIER RÉEL
    # --------------------------------------------------------

    if not os.path.isdir(
        dossier
    ):

        print(
            "Dossier de scan introuvable :",
            dossier
        )

        print(
            "Ancien catalogue conservé."
        )

        return False


    # --------------------------------------------------------
    # SCAN
    # --------------------------------------------------------

    nombre_archives = scanner_source(
        nom_source,
        dossier,
        role
    )


    # scanner_source renvoie 0 lorsque le catalogue
    # n'a volontairement pas été remplacé.
    if nombre_archives == 0:

        return False


    return True

# ============================================================
# SCAN COMPLET — SYSTÈME DYNAMIQUE STL MANAGER
# ============================================================

def scanner_toutes_les_sources():

    preparer_base()


    print()
    print("========================================")
    print("DÉTECTION DES SOURCES STL MANAGER")
    print("========================================")


    # --------------------------------------------------------
    # DÉTECTER LES SOURCES ACTUELLEMENT CONNECTÉES
    # --------------------------------------------------------

    sources_detectees = (
        detecter_sources_stl_manager()
    )


    # --------------------------------------------------------
    # AUCUNE SOURCE DÉTECTÉE
    # --------------------------------------------------------

    if not sources_detectees:

        print()
        print(
            "Aucune source STL Manager détectée."
        )

        print(
            "Les catalogues existants sont conservés."
        )


    # --------------------------------------------------------
    # AFFICHER LES SOURCES DÉTECTÉES
    # --------------------------------------------------------

    else:

        print()

        for (
            nom_source,
            configuration
        ) in sources_detectees.items():

            print(
                "🟢",
                nom_source,
                "→",
                configuration["dossier_scan"],
                "|",
                configuration["role"]
            )


    total_scane = 0


    # ========================================================
    # SCANNER UNIQUEMENT LES SOURCES DÉTECTÉES
    # ========================================================

    for (
        nom_source,
        configuration
    ) in sources_detectees.items():


        print()
        print(
            "========================================"
        )

        print(
            "SOURCE :",
            nom_source
        )

        print(
            "========================================"
        )


        dossier = (
            configuration[
                "dossier_scan"
            ]
        )


        role = (
            configuration[
                "role"
            ]
        )


        # ----------------------------------------------------
        # LE DOSSIER DE SCAN A DISPARU
        # ----------------------------------------------------

        if not os.path.isdir(
            dossier
        ):

            print(
                "Dossier de scan introuvable :",
                dossier
            )

            print(
                "Ancien catalogue conservé."
            )

            continue


        # ----------------------------------------------------
        # SCAN SÉCURISÉ
        # ----------------------------------------------------

        nombre_scane = scanner_source(
            nom_source,
            dossier,
            role
        )


        total_scane += (
            nombre_scane
        )


    # ========================================================
    # RÉCUPÉRER L'ÉTAT COMPLET DU CATALOGUE
    # ========================================================

    connexion = sqlite3.connect(
        BASE_DE_DONNEES
    )

    curseur = connexion.cursor()


    curseur.execute(
        "SELECT COUNT(*) FROM archives"
    )


    total_catalogue = (
        curseur.fetchone()[0]
    )


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


    sources_connues = (
        curseur.fetchall()
    )


    connexion.close()


    # ========================================================
    # RÉSUMÉ
    # ========================================================

    print()
    print("========================================")
    print("SCAN TERMINÉ")
    print("========================================")

    print()


    print(
        "Archives scannées cette fois :",
        total_scane
    )


    print(
        "Archives dans le catalogue :",
        total_catalogue
    )


    print()

    print(
        "SOURCES DU CATALOGUE :"
    )

    print()


    noms_sources_detectees = set(
        sources_detectees.keys()
    )


    for source in sources_connues:

        nom_source = (
            source[0]
        )

        role_source = (
            source[1]
        )

        dernier_scan = (
            source[2]
        )

        nombre_archives = (
            source[3]
        )


        # ----------------------------------------------------
        # SOURCE ACTUELLEMENT CONNECTÉE
        # ----------------------------------------------------

        if nom_source in noms_sources_detectees:

            statut = (
                "🟢 EN LIGNE"
            )


        # ----------------------------------------------------
        # SOURCE ABSENTE MAIS CONSERVÉE DANS LE CATALOGUE
        # ----------------------------------------------------

        else:

            statut = (
                "🔵 HORS LIGNE"
            )


        print(
            statut,
            "|",
            nom_source,
            "|",
            role_source,
            "|",
            nombre_archives,
            "archives",
            "| dernier scan :",
            dernier_scan
        )


    print()

    print(
        "Base :",
        BASE_DE_DONNEES
    )


# ============================================================
# LANCEMENT DIRECT
# ============================================================
#
# python main.py
#       ↓
# scan complet
#
# import main
#       ↓
# aucun scan automatique
#
# ============================================================

if __name__ == "__main__":

    scanner_toutes_les_sources()