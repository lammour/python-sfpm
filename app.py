"""
Interface graphique pour le contrôle qualité scanner — Mesure NPS.

Utilise CustomTkinter pour l'interface et Matplotlib pour les graphiques.
"""

import threading
from tkinter import filedialog, messagebox

import customtkinter as ctk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from dicom_loader import SerieDicom, charger_dossier_dicom
from nps_calculator import analyser_nps, ResultatNPS

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")


# ---------------------------------------------------------------------------
# Widget : Visualiseur d'image CT
# ---------------------------------------------------------------------------

class VueCT(ctk.CTkFrame):
    """Affiche une coupe CT avec les ROIs NPS superposées."""

    def __init__(self, parent):
        super().__init__(parent)

        self.serie: SerieDicom | None = None
        self.positions_roi = []
        self.index_coupe = 0

        self.fig = Figure(figsize=(5, 5), facecolor="black")
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("black")
        self.ax.axis("off")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Slider de navigation entre coupes
        slider_frame = ctk.CTkFrame(self, fg_color="transparent")
        slider_frame.pack(fill="x", padx=10, pady=(0, 5))

        self.label_coupe = ctk.CTkLabel(slider_frame, text="Coupe : —")
        self.label_coupe.pack(side="left")

        self.slider = ctk.CTkSlider(
            slider_frame,
            from_=0, to=1,
            command=self._on_slider,
            state="disabled",
        )
        self.slider.pack(side="right", fill="x", expand=True, padx=(10, 0))

    def charger_serie(self, serie: SerieDicom):
        self.serie = serie
        self.index_coupe = serie.nb_coupes // 2
        self.positions_roi = []

        self.slider.configure(
            from_=0, to=serie.nb_coupes - 1,
            number_of_steps=serie.nb_coupes - 1,
            state="normal",
        )
        self.slider.set(self.index_coupe)
        self._afficher_coupe()

    def afficher_rois(self, positions_roi):
        self.positions_roi = positions_roi
        self._afficher_coupe()

    def _on_slider(self, valeur):
        if self.serie is None:
            return
        self.index_coupe = int(valeur)
        self.label_coupe.configure(text=f"Coupe : {self.index_coupe + 1}/{self.serie.nb_coupes}")
        self._afficher_coupe()

    def _afficher_coupe(self):
        if self.serie is None:
            return

        self.ax.clear()
        coupe = self.serie.coupes[self.index_coupe]

        # Fenêtrage tissu mou : centre=0 UH, largeur=400 UH
        self.ax.imshow(coupe.pixel_array, cmap="gray", vmin=-200, vmax=200)
        self.ax.set_title(f"Coupe {self.index_coupe + 1}/{self.serie.nb_coupes}"
                          f"  —  pixel : {coupe.pixel_size_mm:.3f} mm", fontsize=14)
        self.ax.axis("off")

        # Superposition des rectangles ROI
        for pos in self.positions_roi:
            demi = pos.taille // 2
            rect = Rectangle(
                (pos.x - demi, pos.y - demi), pos.taille, pos.taille,
                linewidth=1.5, edgecolor="lime", facecolor="none",
            )
            self.ax.add_patch(rect)

        self.fig.tight_layout()
        self.canvas.draw()


# ---------------------------------------------------------------------------
# Widget : Courbe NPS
# ---------------------------------------------------------------------------

class VueNPS(ctk.CTkFrame):
    """Affiche la courbe NPS 1D (brute et lissée)."""

    def __init__(self, parent):
        super().__init__(parent)

        self.fig = Figure(figsize=(5, 5))
        self.ax = self.fig.add_subplot(111)
        self._configurer_axes()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def _configurer_axes(self):
        self.ax.set_xlabel("Fréquence spatiale (cycles/mm)", fontsize=14)
        self.ax.set_ylabel("NPS (UH² · mm²)", fontsize=14)
        self.ax.set_title("Spectre de Puissance du Bruit (NPS)", fontsize=15)
        self.ax.tick_params(labelsize=13)
        self.ax.grid(True, linestyle="--", alpha=0.4)

    def afficher_resultats(self, resultat: ResultatNPS):
        self.ax.clear()
        self._configurer_axes()

        freq = resultat.frequences
        self.ax.plot(freq, resultat.nps_brut, alpha=0.4, linewidth=1, label="NPS brut")
        self.ax.plot(freq, resultat.nps_lisse, linewidth=2, label="NPS lissé (poly. 11)")

        # Marqueur de la fréquence moyenne
        f_moy = resultat.frequence_moyenne
        self.ax.axvline(f_moy, color="orange", linestyle="--", linewidth=1.2,
                        label=f"f̄ = {f_moy:.3f} cy/mm")

        self.ax.legend(fontsize=13)
        self.fig.tight_layout()
        self.canvas.draw()

    def effacer(self):
        self.ax.clear()
        self._configurer_axes()
        self.canvas.draw()


# ---------------------------------------------------------------------------
# Fenêtre principale
# ---------------------------------------------------------------------------

class ApplicationNPS(ctk.CTk):
    """Application principale de mesure NPS."""

    def __init__(self):
        super().__init__()

        self.title("Contrôle Qualité Scanner — Mesure NPS")
        self.geometry("1100x650")

        self.serie: SerieDicom | None = None  # série DICOM chargée, None si aucune

        self._construire_interface()

    def _construire_interface(self):
        self._construire_barre_outils()

        # Zone principale : image CT à gauche, NPS à droite
        corps = ctk.CTkFrame(self, fg_color="transparent")
        corps.pack(fill="both", expand=True, padx=10, pady=5)

        self.vue_ct = VueCT(corps)
        self.vue_ct.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.vue_nps = VueNPS(corps)
        self.vue_nps.pack(side="right", fill="both", expand=True)

    def _construire_barre_outils(self):
        # Ligne 1 : boutons et paramètres
        ligne1 = ctk.CTkFrame(self, fg_color="transparent")
        ligne1.pack(fill="x", padx=10, pady=(8, 2))

        self.btn_charger = ctk.CTkButton(
            ligne1, text="📂 Charger dossier DICOM",
            command=self._charger_dossier, width=200,
        )
        self.btn_charger.pack(side="left", padx=(0, 10))

        self.btn_analyser = ctk.CTkButton(
            ligne1, text="▶ Analyser NPS",
            command=self._lancer_analyse, width=140,
            state="disabled",
        )
        self.btn_analyser.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(ligne1, text="Coupes :").pack(side="left")
        self.entree_coupes = ctk.CTkEntry(ligne1, width=45)
        self.entree_coupes.insert(0, "10")
        self.entree_coupes.pack(side="left", padx=(2, 12))

        ctk.CTkLabel(ligne1, text="Taille ROI (px) :").pack(side="left")
        self.entree_roi = ctk.CTkEntry(ligne1, width=45)
        self.entree_roi.insert(0, "64")
        self.entree_roi.pack(side="left", padx=(2, 0))

        # Ligne 2 : statut (pleine largeur)
        ligne2 = ctk.CTkFrame(self, fg_color="transparent")
        ligne2.pack(fill="x", padx=10, pady=(0, 4))

        self.label_statut = ctk.CTkLabel(
            ligne2, text="Charger un dossier DICOM pour commencer.",
            font=("Helvetica", 13),
        )
        self.label_statut.pack(side="left")

    # --- Actions utilisateur ---

    def _charger_dossier(self):
        dossier = filedialog.askdirectory(title="Sélectionner un dossier DICOM")
        if not dossier:
            return

        self.label_statut.configure(text="Chargement en cours…")
        self.btn_charger.configure(state="disabled")

        # Le chargement DICOM se fait dans un thread secondaire pour ne pas
        # bloquer l'interface. Une fois terminé, self.after() repasse la main
        # au thread principal avant de mettre à jour l'affichage.
        def _charger():
            try:
                serie = charger_dossier_dicom(dossier)
                self.after(0, lambda: self._on_chargement_ok(serie))
            except Exception as e:
                message = f"Erreur : {e}"
                self.after(0, lambda: self._on_erreur(message))

        threading.Thread(target=_charger, daemon=True).start()

    def _on_chargement_ok(self, serie: SerieDicom):
        self.serie = serie
        self.vue_ct.charger_serie(serie)
        self.vue_nps.effacer()

        c = serie.get_coupe_centrale()
        self.label_statut.configure(
            text=f"{serie.nb_coupes} coupes  |  {c.manufacturer} {c.model_name}"
                 f"  |  kV={c.kvp:.0f}  mA={c.tube_current:.0f}  noyau={c.convolution_kernel}"
        )
        self.btn_charger.configure(state="normal")
        self.btn_analyser.configure(state="normal")

    def _lancer_analyse(self):
        if self.serie is None:
            return

        try:
            nb_coupes = int(self.entree_coupes.get())
            taille_roi = int(self.entree_roi.get())
        except ValueError:
            messagebox.showerror("Erreur", "Paramètres invalides.")
            return

        self.label_statut.configure(text="Analyse NPS en cours…")
        self.btn_analyser.configure(state="disabled")

        def _analyser():
            try:
                resultat = analyser_nps(self.serie, nb_coupes=nb_coupes, taille_roi=taille_roi)
                self.after(0, lambda: self._on_analyse_ok(resultat))
            except Exception as e:
                message = f"Erreur : {e}"
                self.after(0, lambda: self._on_erreur(message))

        threading.Thread(target=_analyser, daemon=True).start()

    def _on_analyse_ok(self, resultat: ResultatNPS):
        self.resultat = resultat
        self.vue_nps.afficher_resultats(resultat)
        self.vue_ct.afficher_rois(resultat.positions_roi)
        self.label_statut.configure(
            text=f"f̄ = {resultat.frequence_moyenne:.3f} cy/mm  |  "
                 f"NPS moyen = {resultat.nps_moyen:.2f} UH²·mm²  |  "
                 f"{resultat.nb_coupes} coupes × 8 ROIs"
        )
        self.btn_analyser.configure(state="normal")

    def _on_erreur(self, message: str):
        self.label_statut.configure(text=message)
        self.btn_charger.configure(state="normal")
        self.btn_analyser.configure(state="normal" if self.serie else "disabled")
        messagebox.showerror("Erreur", message)
