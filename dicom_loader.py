"""Chargement de séries DICOM pour le contrôle qualité scanner."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pydicom


# @dataclass génère automatiquement __init__, __repr__, etc. à partir des champs déclarés.
# C'est un raccourci pratique pour créer des classes qui stockent des données.

@dataclass
class SliceDicom:
    """Une coupe DICOM avec ses métadonnées essentielles."""
    pixel_array: np.ndarray       # Image en unités Hounsfield (UH)
    pixel_size_mm: float          # Taille d'un pixel en mm
    slice_location: float         # Position Z en mm
    instance_number: int          # Numéro de coupe
    rows: int
    columns: int
    # Infos scanner (avec valeurs par défaut si absentes du fichier DICOM)
    manufacturer: str = ""
    model_name: str = ""
    kvp: float = 0.0
    tube_current: float = 0.0
    convolution_kernel: str = ""
    study_date: str = ""


@dataclass
class SerieDicom:
    """Série de coupes DICOM triées par position Z."""
    coupes: list[SliceDicom]

    # @property permet d'utiliser nb_coupes comme un attribut (serie.nb_coupes)
    # plutôt que comme une méthode (serie.nb_coupes()).
    @property
    def nb_coupes(self) -> int:
        return len(self.coupes)

    def trier_par_position(self):
        # key=lambda c: c.slice_location signifie : "trier selon la position Z de chaque coupe"
        self.coupes.sort(key=lambda c: c.slice_location)

    def get_coupe_centrale(self) -> SliceDicom:
        return self.coupes[self.nb_coupes // 2]


def _charger_fichier_dicom(chemin: Path) -> SliceDicom | None:
    """Charge un fichier DICOM. Retourne None si le fichier n'est pas valide."""
    try:
        ds = pydicom.dcmread(str(chemin))

        if not hasattr(ds, "PixelData"):
            return None

        # Conversion des valeurs brutes en unités Hounsfield (UH)
        pixel_array = ds.pixel_array.astype(np.float32)
        slope = float(getattr(ds, "RescaleSlope", 1.0))
        intercept = float(getattr(ds, "RescaleIntercept", 0.0))
        pixel_array = pixel_array * slope + intercept

        # getattr(ds, "Attribut", valeur_par_defaut) lit un champ DICOM
        # et retourne la valeur par défaut si le champ est absent du fichier.
        pixel_spacing = getattr(ds, "PixelSpacing", [1.0, 1.0])
        pixel_size_mm = float(pixel_spacing[0])  # pixels supposés carrés

        return SliceDicom(
            pixel_array=pixel_array,
            pixel_size_mm=pixel_size_mm,
            slice_location=float(getattr(ds, "SliceLocation", 0.0)),
            instance_number=int(getattr(ds, "InstanceNumber", 0)),
            rows=int(ds.Rows),
            columns=int(ds.Columns),
            manufacturer=str(getattr(ds, "Manufacturer", "")),
            model_name=str(getattr(ds, "ManufacturerModelName", "")),
            kvp=float(getattr(ds, "KVP", 0.0)),
            tube_current=float(getattr(ds, "XRayTubeCurrent", 0.0)),
            convolution_kernel=str(getattr(ds, "ConvolutionKernel", "")),
            study_date=str(getattr(ds, "StudyDate", "")),
        )
    except Exception:
        # Si le fichier est illisible ou n'est pas un DICOM valide, on l'ignore.
        return None


def charger_dossier_dicom(chemin_dossier: str | Path) -> SerieDicom:
    """
    Charge tous les fichiers DICOM d'un dossier et retourne une série triée.

    Args:
        chemin_dossier: Chemin du dossier contenant les fichiers DICOM

    Returns:
        SerieDicom triée par position Z croissante

    Raises:
        ValueError: Si aucun fichier DICOM valide trouvé
    """
    dossier = Path(chemin_dossier)
    coupes = []

    for fichier in sorted(dossier.iterdir()):
        if fichier.is_file():
            coupe = _charger_fichier_dicom(fichier)
            if coupe is not None:
                coupes.append(coupe)

    if not coupes:
        raise ValueError(f"Aucun fichier DICOM valide trouvé dans : {dossier}")

    serie = SerieDicom(coupes=coupes)
    serie.trier_par_position()
    return serie
