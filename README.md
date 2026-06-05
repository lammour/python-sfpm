# Mesure NPS en Python — Tutoriel de contrôle qualité scanner

Ce projet est le support du webinaire **"Python pour les physiciens médicaux"**.
Il montre comment automatiser la mesure de la **NPS (Noise Power Spectrum / Spectre de Puissance du Bruit)** sur des images scanner DICOM, avec une interface graphique simple.

L'algorithme est conforme à la décision ANSM du 18/12/2025 et basé sur le projet [cq-tdm](https://github.com/lammour/cq-tdm/).

---

## Ce que fait le logiciel

1. Charge une série d'images DICOM d'un fantôme eau
2. Détecte automatiquement le centre du fantôme
3. Positionne 8 ROIs en motif octogonal (standard ANSM)
4. Calcule la NPS 2D par FFT puis la moyenne radiale
5. Affiche la courbe NPS lissée et la fréquence centroïde

![Aperçu de l'interface](docs/screenshot.png)

---

## Prérequis

- Windows 10/11 (fonctionne aussi sur Linux/macOS)
- Python 3.12 ou plus récent
- Git (optionnel, pour cloner le dépôt)

---

## Installation pas à pas

### Étape 1 — Installer Python

1. Aller sur [python.org/downloads](https://www.python.org/downloads/)
2. Télécharger **Python 3.12** (Windows installer 64-bit)
3. Lancer l'installeur et **cocher "Add python.exe to PATH"** avant de cliquer sur Install

Vérifier l'installation dans PowerShell ou le terminal :
```
python --version
```

---

### Étape 2 — Récupérer le projet

**Option A — avec Git :**
```
git clone https://github.com/lammour/python-sfpm.git
cd python-sfpm
```

**Option B — sans Git :**
Télécharger le fichier ZIP depuis GitHub (bouton *Code → Download ZIP*), puis décompresser.

---

### Étape 3 — Créer l'environnement virtuel

Un environnement virtuel isole les bibliothèques de ce projet du reste de votre système.

Dans PowerShell, depuis le dossier du projet :
```
python -m venv .venv
.venv\Scripts\activate
```

Le terminal affiche maintenant `(.venv)` au début de chaque ligne — c'est normal, cela confirme que l'environnement est actif.

> **Sur Linux/macOS**, remplacer la deuxième commande par :
> ```
> source .venv/bin/activate
> ```

---

### Étape 4 — Installer les bibliothèques

```
pip install -r requirements.txt
```

Les bibliothèques installées sont :
| Bibliothèque | Rôle |
|---|---|
| `numpy` | Calculs numériques (tableaux, FFT) |
| `scipy` | Interpolation bilinéaire |
| `pydicom` | Lecture des fichiers DICOM |
| `matplotlib` | Affichage des courbes et images |
| `customtkinter` | Interface graphique |

---

### Étape 5 — Télécharger les images test

Les images DICOM de fantôme eau ne sont pas incluses dans le dépôt (trop volumineuses).
Télécharger l'archive **`20251229-controle-scanographie-banque-images-reference.zip`** et décompresser son contenu dans un dossier `images/` à la racine du projet :

```
images/
├── Serie_1/S1/      ← 233 coupes, 120 kV, noyau STANDARD
├── Serie_2/S2/      ← 151 coupes, 120 kV, noyau B
├── Serie_3a/S3a/    ← 132 coupes, 120 kV, noyau Hr38s
├── Serie_3b/S3b/    ←  43 coupes, 100 kV, noyau Br38f
└── Serie_4/S4/      ← 130 coupes, 100 kV, noyau BODY_SHARP
```

---

### Étape 6 — Lancer le logiciel

```
python main.py
```

L'interface s'ouvre. Pour lancer une analyse :
1. Cliquer sur **"Charger dossier DICOM"** et sélectionner un des dossiers `images/Serie_X/SX/`
2. Ajuster si besoin le nombre de coupes (défaut : 10) et la taille des ROIs (défaut : 64 px)
3. Cliquer sur **"Analyser NPS"**

Les 8 ROIs apparaissent en vert sur l'image CT et la courbe NPS s'affiche à droite.

---

## Structure du code

```
main.py            ← Point d'entrée : lance l'application
app.py             ← Interface graphique (CustomTkinter + Matplotlib)
nps_calculator.py  ← Algorithme NPS complet
dicom_loader.py    ← Chargement des fichiers DICOM
requirements.txt   ← Liste des bibliothèques nécessaires
```

### Fichier par fichier

#### `dicom_loader.py`
Lit les fichiers DICOM avec `pydicom`, convertit les valeurs brutes en unités Hounsfield
(`UH = pixel × slope + intercept`) et trie les coupes par position Z.

#### `nps_calculator.py`
Implémente l'algorithme NPS en 6 étapes :

```
1. detecter_centre_fantome()   → centroïde du masque eau (-100 à +100 UH)
2. calculer_positions_roi()    → 8 ROIs en motif octogonal
3. detrender_roi()             → suppression du fond par polynôme 2D
4. calculer_nps_2d()           → FFT 2D + normalisation
5. moyenne_radiale()           → 37 profils angulaires → NPS 1D
6. lisser_nps_polynome()       → ajustement polynôme degré 11
```

#### `app.py`
Trois classes CustomTkinter :
- `VueCT` — affiche les coupes CT avec le slider et les ROIs superposées
- `VueNPS` — affiche la courbe NPS (brute + lissée + fréquence centroïde)
- `ApplicationNPS` — fenêtre principale, boutons, gestion des threads

---

## Résultats attendus sur les séries test

| Série | kV | mA | Noyau | f̄ (cy/mm) | NPS moyen |
|-------|----|----|-------|-----------|-----------|
| Serie_1 | 120 | 350 | STANDARD | 0.242 | 27.7 |
| Serie_2 | 120 | 275 | B | 0.275 | 340.7 |
| Serie_3a | 120 | 182 | Hr38s | 0.259 | 12.2 |
| Serie_3b | 100 | 288 | Br38f | 0.254 | 27.1 |
| Serie_4 | 100 | 250 | BODY_SHARP | 0.324 | 59.1 |

La **fréquence centroïde** (f̄) augmente avec la dureté du noyau de reconstruction.
L'**amplitude** de la NPS diminue quand la dose augmente.

---

## Pour aller plus loin

- Modifier le fenêtrage de l'image CT (variables `vmin`/`vmax` dans `app.py`)
- Ajouter l'export des résultats en CSV
- Calculer d'autres métriques : CTF, bruit moyen, uniformité
- Adapter le code à vos propres images de fantôme

---

## Références

- Décision ANSM du 18/12/2025 relative au contrôle qualité des scanographes
- Projet cq-tdm : [github.com/lammour/cq-tdm](https://github.com/lammour/cq-tdm)
- Documentation pydicom : [pydicom.github.io](https://pydicom.github.io)
