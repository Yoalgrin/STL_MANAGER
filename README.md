# STL Manager

STL Manager est une application Windows légère pour cataloguer, rechercher et gérer de grandes collections de fichiers STL réparties sur plusieurs disques.

Le catalogue SQLite reste disponible même lorsqu'un disque est déconnecté. L'application détecte les volumes Windows présents, affiche les sources en ligne/hors ligne, scanne une source à la demande et repère les doublons exacts.

## Fonctionnalités

- Détection des volumes connectés indépendamment de leur lettre de lecteur.
- Catalogue persistant des sources, y compris lorsqu'elles sont hors ligne.
- Scan des fichiers `.zip`, `.rar`, `.7z`, `.stl` et `.3mf`.
- Création automatique du fichier `.stlmanager` lors du premier scan d'une source reconnue qui n'en possède pas encore.
- Recherche dans l'ensemble du catalogue.
- Détection et consultation des doublons exacts.
- Ouverture d'un fichier ou de son dossier depuis l'interface.
- Suppression sécurisée d'une copie via la Corbeille Windows.
- Configuration des noms de dossiers à rechercher (`STL` et `3D Print` par défaut).

## Sources et fichier `.stlmanager`

Une source configurée possède à la racine du dossier détecté un fichier `.stlmanager`, par exemple :

```text
source=3D print 3
role=A_TRIER
sous_dossier=A trier
```

Si le fichier `.stlmanager` est absent lors du scan d'une source connue et connectée, STL Manager le crée automatiquement puis lance le scan.

L'état **En ligne / Hors ligne** dépend de la présence physique du volume Windows et non du contenu du dossier ou du fichier `.stlmanager`.

## Source vide

Lorsqu'un scan ne trouve aucun fichier compatible, STL Manager ne remplace pas automatiquement l'ancien catalogue. L'utilisateur peut choisir de supprimer uniquement les anciennes entrées de cette source dans la base de données. Aucun fichier physique n'est alors supprimé.

## Doublons exacts

Les doublons sont regroupés à partir du nom normalisé, de la partie et de la taille du fichier. Une suppression depuis STL Manager envoie uniquement la copie sélectionnée dans la Corbeille Windows.

Restaurer ensuite un fichier depuis la Corbeille restaure le fichier physique, mais pas son entrée dans SQLite : il faut rescanner la source concernée.

## Installation depuis les sources

Prérequis : Python 3 sous Windows.

```powershell
pip install -r requirements.txt
python interface.py
```

## Base de données

STL Manager utilise `stl_manager.db`. Elle est créée automatiquement si elle n'existe pas.

La version actuelle utilise un chemin relatif : lancer l'application depuis son dossier afin qu'elle retrouve toujours la même base. La base personnelle n'est volontairement pas incluse dans le dépôt Git.

## Sécurité

- Un disque déconnecté n'est pas interprété comme une source vide.
- Un scan vide ne supprime pas silencieusement l'ancien catalogue.
- La suppression d'une copie utilise la Corbeille Windows via `Send2Trash`.

## Structure du dépôt

```text
STL_Manager/
├── main.py
├── interface.py
├── README.md
├── requirements.txt
└── .gitignore
```

Les scripts d'analyse/migration utilisés pendant le développement, les bases SQLite personnelles, les exports CSV et les fichiers de build ne font pas partie de la version publique propre.

## Système

Windows.
