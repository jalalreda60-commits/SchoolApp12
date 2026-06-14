# 🛠️ Guide d'installation - Private School Management System

## Prérequis

- **Python 3.12** (ou version 3.10+) installé sur votre machine.
- Système d'exploitation : Windows, macOS ou Linux.
- Aucune base de données externe nécessaire (SQLite est intégré à Python).

Vérifiez votre version de Python :

```bash
python3 --version
```

---

## Étape 1 — Récupérer le projet

Copiez le dossier `school_management/` à l'emplacement de votre choix sur
votre ordinateur.

---

## Étape 2 — Créer un environnement virtuel (recommandé)

### Windows
```bash
cd school_management
python -m venv venv
venv\Scripts\activate
```

### macOS / Linux
```bash
cd school_management
python3 -m venv venv
source venv/bin/activate
```

---

## Étape 3 — Installer les dépendances

```bash
pip install -r requirements.txt
```

Cela installera :
- `customtkinter` — interface graphique moderne
- `pandas` — traitement des fichiers Excel
- `openpyxl` — lecture/écriture des fichiers `.xlsx`
- `matplotlib` — graphiques du tableau de bord

> 💡 Sur Linux, si `tkinter` n'est pas déjà installé, exécutez :
> `sudo apt-get install python3-tk`

---

## Étape 4 — Lancer l'application

```bash
python main.py
```

(sur certains systèmes : `python3 main.py`)

La fenêtre principale s'ouvre avec le tableau de bord. La base de données
`database/school.db` est créée automatiquement si elle n'existe pas.

---

## Étape 5 — Première configuration

1. Allez dans **Paramètres** ⚙️
2. Configurez l'**année scolaire courante** et l'**année scolaire suivante**
   (exemple : `2025/2026` et `2026/2027`).
3. Renseignez le **nom de votre établissement**.
4. Choisissez le **mode d'affichage** (Clair / Sombre).

---

## Étape 6 — Importer vos élèves

1. Allez dans **Gestion Élèves** 🎓
2. Cliquez sur **📥 Importer Excel**
3. Sélectionnez votre fichier `.xlsx` (utilisez `sample_data/template_eleves_vide.xlsx`
   comme modèle, ou `sample_data/eleves_exemple.xlsx` pour tester avec des données
   d'exemple).
4. Le résumé de l'import affiche le nombre de lignes créées, mises à jour
   et ignorées (avec le détail des erreurs s'il y en a).

---

## Étape 7 — Utilisation quotidienne

- **Nouvelle Inscription** : ajouter un nouvel élève avec matricule automatique.
- **Gestion Élèves** : rechercher, filtrer, modifier, imprimer les fiches.
- **Réinscription** : en fin d'année scolaire, sélectionnez les élèves à
  réinscrire et cliquez sur **Générer la Réinscription**.
- **Tableau de bord** : suivez vos statistiques en temps réel.

---

## ❓ Dépannage

| Problème | Solution |
|----------|----------|
| `ModuleNotFoundError: No module named 'customtkinter'` | Exécutez `pip install -r requirements.txt` dans l'environnement actif. |
| `ModuleNotFoundError: No module named 'tkinter'` (Linux) | `sudo apt-get install python3-tk` |
| Les graphiques ne s'affichent pas | Vérifiez que `matplotlib` est bien installé : `pip show matplotlib` |
| Erreur lors de l'import Excel | Vérifiez que les en-têtes de colonnes correspondent exactement au modèle fourni. |
| Base de données corrompue | Restaurez une sauvegarde depuis le dossier `backups/` (renommez le fichier `.db` en `school.db` dans `database/`). |

---

## 📦 Création d'un exécutable (optionnel)

Pour distribuer l'application sans installer Python, vous pouvez utiliser
**PyInstaller** :

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed main.py
```

L'exécutable sera généré dans le dossier `dist/`.

> ⚠️ Pensez à inclure manuellement les dossiers `database/`, `exports/`,
> `backups/` et `sample_data/` à côté de l'exécutable final, car
> PyInstaller ne les empaquette pas automatiquement.
