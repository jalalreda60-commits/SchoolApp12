# 🏫 Private School Management System (SGS)

[![Build Windows Executable](https://github.com/REPLACE_USER/REPLACE_REPO/actions/workflows/build-windows-exe.yml/badge.svg)](https://github.com/REPLACE_USER/REPLACE_REPO/actions/workflows/build-windows-exe.yml)

Application de bureau professionnelle pour la gestion d'un établissement scolaire privé,
développée en **Python** avec **CustomTkinter**, **SQLite**, **Pandas** et **Matplotlib**.

> Remplacez `REPLACE_USER/REPLACE_REPO` ci-dessus par le chemin de votre dépôt GitHub
> (ex : `johndoe/sgs-school-manager`) pour activer le badge de build.

---

## ✨ Fonctionnalités principales

### 📊 Tableau de bord (Dashboard)
- 6 indicateurs clés (KPI) : élèves inscrits, pré-inscrits pour l'année suivante,
  nouvelles inscriptions du mois, élèves utilisant le transport, revenus
  d'inscription, revenus du mois sélectionné.
- 8 graphiques dynamiques :
  1. Élèves par classe (Bar)
  2. Inscriptions mensuelles (Line)
  3. Progression des réinscriptions (Donut)
  4. Départs par mois (Line)
  5. Transport par classe (Pie)
  6. Évolution des revenus mensuels — Inscription / Mensualité / Transport (Bar empilé)
  7. Répartition des statuts de paiement — Payé / Impayé / Non inscrit (Donut)
  8. Revenus par classe (Bar)
- Filtres par année scolaire, classe et mois — mise à jour instantanée,
  y compris pour les indicateurs financiers.

### 🎓 Gestion des Élèves
- Tableau professionnel avec recherche, filtres multiples (année / classe / statut),
  tri par colonne et pagination.
- Actions : voir, modifier, supprimer, imprimer la fiche élève.
- Import / Export Excel intégré.
- Double-clic sur une ligne pour ouvrir le profil complet.

### 📝 Nouvelle Inscription
- Formulaire moderne avec génération automatique du matricule.
- Validation des champs obligatoires.
- Enregistrement instantané en base de données avec notification de succès.

### 🔁 Réinscription
- Liste de tous les élèves actifs de l'année en cours.
- Sélection individuelle ou globale (Tout sélectionner / désélectionner).
- Génération automatique des dossiers pour l'année suivante en conservant
  toutes les informations de l'élève.
- Statistiques : total éligibles, sélectionnés, déjà réinscrits.

### 💰 Gestion des Paiements
- Bouton **"Ajouter Paiement"** : recherche d'élève par matricule, nom,
  prénom ou classe.
- Affichage automatique des informations de l'élève (Matricule, Nom, Prénom,
  Classe, Inscription, Transport, Mensualité, Total à payer, Total payé,
  Reste à payer).
- Grille de statut mensuel (Septembre → Juin) avec couleurs :
  - 🟢 **Vert** = Payé
  - 🔴 **Rouge** = Impayé (case vide)
  - ⚪ **Gris** = Non inscrit (valeur "NAN")
- Détection automatique du **premier mois impayé** (en ignorant les mois
  "NAN" et "Payé"), proposé automatiquement dans le formulaire.
- Formulaire de paiement : type (Inscription / Mensualité / Transport),
  mois (auto-suggéré), montant, date, notes.
- À l'enregistrement :
  - Sauvegarde du paiement en base de données.
  - Mise à jour du statut du mois concerné → "Payé".
  - Mise à jour du total payé / reste à payer.
  - **Génération automatique d'un reçu PDF professionnel** (numéro de reçu
    unique, infos élève, détails du paiement, zone de signature).
  - Le reçu est ouvert automatiquement et enregistré dans
    `exports/receipts/`.
- Historique complet des paiements par élève (mois, type, montant, date,
  numéro de reçu).
- Import Excel de l'historique de paiements (création/mise à jour
  automatique des élèves, grille de statuts mensuels, sans doublons).

### ⚙️ Paramètres
- Bascule Mode Clair / Sombre.
- Configuration des années scolaires (courante / suivante).
- Informations de l'établissement.
- Sauvegarde manuelle de la base de données (copie horodatée).

---


## 🗂️ Structure du projet

```
school_management/
├── main.py                     # Point d'entrée de l'application
├── requirements.txt            # Dépendances Python
├── database/
│   ├── db_manager.py            # Connexion SQLite + création du schéma
│   └── school.db                # Base de données (créée au premier lancement)
├── models/
│   ├── student.py               # Modèle Élève + requêtes statistiques
│   └── payment.py               # Modèle Paiement (statuts, historique, KPIs)
├── controllers/
│   ├── student_controller.py    # Logique métier (validation, réinscription...)
│   ├── excel_controller.py      # Import / Export Excel (élèves)
│   ├── payment_controller.py    # Logique métier paiements + reçus
│   └── payment_excel_controller.py  # Import Excel (paiements)
├── views/
│   ├── dashboard_view.py
│   ├── gestion_eleves_view.py
│   ├── nouvelle_inscription_view.py
│   ├── reinscription_view.py
│   ├── gestion_paiements_view.py
│   ├── settings_view.py
│   └── components/
│       ├── sidebar.py
│       ├── kpi_card.py
│       ├── charts.py
│       ├── student_profile_dialog.py
│       ├── student_search_dialog.py
│       ├── payment_status_grid.py
│       ├── import_dialog.py
│       └── payment_import_dialog.py
├── utils/
│   ├── theme.py                 # Palette de couleurs, polices, constantes
│   ├── helpers.py                # Notifications, dialogues de confirmation...
│   └── receipt_generator.py      # Génération PDF des reçus (ReportLab)
├── sample_data/
│   ├── eleves_exemple.xlsx          # Fichier Excel d'exemple élèves (30)
│   ├── template_eleves_vide.xlsx    # Modèle Excel vide (élèves)
│   ├── paiements_exemple.xlsx       # Fichier Excel d'exemple paiements (15)
│   └── template_paiements_vide.xlsx # Modèle Excel vide (paiements)
├── exports/                     # Fiches élèves (HTML) + reçus PDF (receipts/)
└── backups/                      # Sauvegardes de la base de données
```

---

## 📋 Colonnes du fichier Excel d'import / export (Élèves)

| Colonne Excel       | Champ base de données |
|---------------------|------------------------|
| Matricule           | matricule              |
| Eleve Nom           | eleve_nom              |
| Eleve Prénom        | eleve_prenom           |
| Mere                | mere                   |
| Père                | pere                   |
| Date of birth       | date_of_birth          |
| City of birth       | city_of_birth          |
| Adress              | adresse                |
| Père telephone      | pere_telephone         |
| Mere telephone      | mere_telephone         |
| Classe              | classe                 |
| Inscription         | inscription            |
| Transport (Y/N)     | transport_yn           |
| Transport           | transport              |
| Mensualité          | mensualite             |
| Note/Date           | note_date              |

L'import détecte automatiquement les doublons (matricule + année scolaire) :
si un élève existe déjà pour l'année, ses informations sont mises à jour ;
sinon un nouvel enregistrement est créé.

---

## 💰 Colonnes du fichier Excel d'import (Paiements)

| Colonne Excel    | Description |
|------------------|-------------|
| Matricule        | Identifiant unique de l'élève |
| Nom              | Nom de famille |
| Prénom           | Prénom |
| Classe           | Classe de l'élève |
| Inscription      | Frais d'inscription (DH) |
| Transport        | Frais de transport (DH) |
| Mensualité       | Montant mensuel (DH) |
| Total a payé     | Total attendu (Inscription + Transport) |
| Note/Date        | Remarque libre |
| Year             | Année scolaire (ex : `2025/2026`) |
| Septembre … Juin | Statut mensuel : `"Payé"`, vide, ou `"NAN"` |

**Interprétation des cellules mensuelles :**

| Valeur Excel | Signification | Couleur |
|--------------|----------------|---------|
| `Payé`       | L'élève a payé ce mois | 🟢 Vert |
| *(vide)*     | Élève inscrit, paiement en attente | 🔴 Rouge |
| `NAN`        | Élève non inscrit ce mois (pas de paiement attendu) | ⚪ Gris |

Le **prochain mois à payer** est calculé en ignorant les mois `NAN` et
`Payé`, et en sélectionnant le premier mois vide (`Impayé`) dans l'ordre
Septembre → Juin.

L'import crée automatiquement les élèves manquants, met à jour les
élèves existants (par matricule + année scolaire), reconstruit la grille
de statuts mensuels, et affiche un résumé (créés / mis à jour / ignorés /
erreurs). Les paiements déjà enregistrés dans l'historique ne sont jamais
dupliqués lors d'une réimportation.

---

## 🎨 Palette de couleurs

| Usage      | Couleur   |
|------------|-----------|
| Primaire   | `#2563EB` |
| Secondaire | `#3B82F6` |
| Succès     | `#22C55E` |
| Avertissement | `#F59E0B` |
| Arrière-plan | `#F8FAFC` |

---

## 🚀 Démarrage rapide

Voir [INSTALLATION.md](INSTALLATION.md) pour les instructions détaillées.

```bash
pip install -r requirements.txt
python main.py
```

Au premier lancement, la base de données SQLite (`database/school.db`) est créée
automatiquement avec les tables et les paramètres par défaut.

---

## 💾 Obtenir l'application Windows (.exe)

Ce dépôt contient un workflow **GitHub Actions** qui génère automatiquement
un exécutable Windows (`SGS_School_Manager.exe`) à chaque push sur `main`.

1. Allez dans l'onglet **Actions** du dépôt GitHub.
2. Ouvrez la dernière exécution de **"Build Windows Executable"**.
3. Téléchargez l'artefact **`SGS_School_Manager-windows`** (zip contenant l'`.exe`).

### Publier une version (Release)

Pour générer une release complète avec l'`.exe` + les dossiers de données
(`database/`, `sample_data/`, etc.) sous forme de zip téléchargeable :

```bash
git tag v1.0.0
git push origin v1.0.0
```

Le workflow détecte le tag `vX.Y.Z`, construit l'exécutable et crée
automatiquement une **GitHub Release** avec `SGS_School_Manager_Windows.zip`
en pièce jointe.

### Construire l'exécutable localement (Windows)

```bash
pip install -r requirements-build.txt
pyinstaller --noconfirm build.spec
```

L'exécutable est généré dans `dist/SGS_School_Manager.exe`. Au premier
lancement, un dossier `data/` est créé automatiquement à côté de l'exécutable
pour stocker la base de données, les sauvegardes et les exports.

---

## 🧩 Architecture (MVC)

- **Models** (`models/`) : accès aux données et requêtes SQL.
- **Controllers** (`controllers/`) : logique métier, validation, règles
  de gestion (matricule automatique, réinscription, import/export).
- **Views** (`views/`) : interface utilisateur CustomTkinter, organisée
  en pages et composants réutilisables.

---

## 🛡️ Sauvegarde des données

La base de données peut être sauvegardée à tout moment depuis la page
**Paramètres** → **Sauvegarde**. Une copie horodatée est créée dans le
dossier `backups/`.

---

## 📄 Licence

© 2026 - Tous droits réservés.
