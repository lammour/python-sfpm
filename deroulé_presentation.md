# Déroulé de la présentation — "Python pour les physiciens médicaux"

Présentation live en vidéoconférence sous Windows — durée estimée **60 minutes**.

---

## Phase 1 — Mise en place de l'environnement (15 min)

### 1.1 Installation de Python (~5 min)
- Aller sur **python.org → Downloads**
- Télécharger Python 3.12 (Windows installer 64-bit)
- ⚠️ Cocher **"Add python.exe to PATH"** avant d'installer
- Vérifier dans PowerShell :
  ```
  python --version
  pip --version
  ```

### 1.2 Installation de VS Code (~3 min)
- Télécharger sur **code.visualstudio.com**
- Installer l'extension **Python** (Microsoft)
- Ouvrir le dossier du projet

### 1.3 Création du projet (~5 min)
- Créer le dossier `cq_scanner/` sur le Bureau
- Créer l'environnement virtuel et l'activer :
  ```
  python -m venv .venv
  .venv\Scripts\activate
  ```
- Sélectionner l'interpréteur `.venv` dans VS Code (`Ctrl+Shift+P` → *Python: Select Interpreter*)
- Créer `requirements.txt`, installer les dépendances :
  ```
  pip install -r requirements.txt
  ```

### 1.4 Initialisation Git (~2 min)
- Dans le terminal VS Code :
  ```
  git init
  git add .
  git commit -m "premier commit"
  ```

---

## Phase 2 — Live coding (35 min)

Coder fichier par fichier, des briques les plus simples vers l'application complète.
Chaque étape se termine par un test dans le terminal.

### Étape 1 — `dicom_loader.py` (~10 min)
Objectif : charger un fichier DICOM et afficher l'image.

Coder live :
1. Les deux dataclasses `SliceDicom` et `SerieDicom`
2. La fonction `charger_dossier_dicom()`

Test dans le terminal :
```python
from dicom_loader import charger_dossier_dicom
serie = charger_dossier_dicom("images/Serie_1/S1")
print(serie.nb_coupes, serie.get_coupe_centrale().pixel_size_mm)
```

### Étape 2 — `nps_calculator.py` (~15 min)
Objectif : calculer la NPS et afficher la courbe.

Coder live dans l'ordre pédagogique :
1. `detecter_centre_fantome()` — montrer le seuillage en UH
2. `calculer_positions_roi()` — motif octogonal ANSM
3. `calculer_nps_2d()` — FFT 2D (moment fort : expliquer le lien FFT → fréquences spatiales)
4. `moyenne_radiale()` — passage 2D → 1D
5. `lisser_nps_polynome()` — ajustement polynômial
6. `analyser_nps()` — assemblage final

Test dans le terminal :
```python
from nps_calculator import analyser_nps
res = analyser_nps(serie)
print(f"f_moy = {res.frequence_moyenne:.3f} cy/mm")

import matplotlib.pyplot as plt
plt.plot(res.frequences, res.nps_lisse)
plt.show()
```

→ **Premier résultat visible avant même d'avoir une interface graphique.**

### Étape 3 — `app.py` + `main.py` (~10 min)
Objectif : habiller le calcul dans une interface.

Coder live les grandes lignes, en insistant sur la structure (pas sur chaque détail de mise en page) :
1. La classe `VueCT` — embarquer matplotlib dans un widget
2. La classe `VueNPS` — le graphique NPS
3. La classe `ApplicationNPS` — la fenêtre principale, les boutons, le thread de calcul
4. `main.py` — le point d'entrée

```
python main.py
```

---

## Phase 3 — Démo de l'application (10 min)

Charger et analyser les 5 séries test pour montrer l'effet des paramètres d'acquisition :

| Série | kV | mA | Noyau | Attente |
|-------|----|----|-------|---------|
| Serie_1 | 120 | 350 | STANDARD | NPS référence |
| Serie_2 | 120 | 275 | B | NPS plus élevée (moins de dose) |
| Serie_3a | 120 | 182 | Hr38s | Fréquence moyenne plus haute (noyau dur) |
| Serie_4 | 100 | 250 | BODY_SHARP | Fréquence encore plus haute |

Points à commenter en direct :
- L'effet du noyau de reconstruction sur la forme de la NPS
- L'effet de la dose (mAs) sur l'amplitude
- La fréquence centroïde comme indicateur de la résolution spatiale

---

## Conseils pratiques pour la démo live

- Avoir les **4 fichiers déjà ouverts** dans VS Code avant de commencer, vides mais prêts
- Avoir une **version de secours** du code complet disponible (si le live plante)
- Tester le partage d'écran à l'avance — VS Code en thème clair est plus lisible en vidéoconférence
- Augmenter la taille de police VS Code à **16pt** pour la démo (`Ctrl+,` → *Font Size*)
- Utiliser le **terminal intégré VS Code** plutôt qu'une fenêtre séparée
