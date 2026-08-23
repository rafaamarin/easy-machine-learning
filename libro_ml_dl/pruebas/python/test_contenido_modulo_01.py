import os
import runpy
import sys
import unittest
import warnings
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import numpy as np

from scripts import validar_contenido

os.environ.setdefault("MPLBACKEND", "Agg")
BOOK_ROOT = Path(__file__).resolve().parents[2]
LAB_ROOT = BOOK_ROOT / "contenido_fuente" / "01_datos_y_formas" / "labs"


class Module01ContentTests(unittest.TestCase):
    def test_shapes_lab_exposes_five_rows_and_three_features(self) -> None:
        namespace = runpy.run_path(LAB_ROOT / "01_formas.py")
        self.assertEqual(namespace["entrenamientos"].shape, (5, 3))
        self.assertEqual(
            namespace["columnas"],
            ("distancia_km", "duracion_min", "fc_media"),
        )

    def test_manual_center_and_dispersion_match_numpy(self) -> None:
        namespace = runpy.run_path(LAB_ROOT / "02_centro_dispersion.py")
        self.assertAlmostEqual(namespace["media_manual"], 45.4)
        self.assertAlmostEqual(
            namespace["desviacion_manual"],
            np.std([29, 45, 55, 34, 64]),
        )
        self.assertGreater(
            namespace["desviacion_con_error"],
            namespace["desviacion_manual"],
        )

    def test_standardized_columns_have_zero_mean_and_unit_std(self) -> None:
        namespace = runpy.run_path(LAB_ROOT / "03_escala.py")
        standardized = namespace["datos_estandarizados"]
        np.testing.assert_allclose(standardized.mean(axis=0), 0, atol=1e-12)
        np.testing.assert_allclose(standardized.std(axis=0), 1, atol=1e-12)

    def test_center_dispersion_figure_compares_sessions_from_zero(self) -> None:
        namespace = runpy.run_path(LAB_ROOT / "02_centro_dispersion.py")
        figure = namespace["fig"]
        axis = figure.axes[0]
        self.assertEqual(len(figure.axes), 1)
        self.assertEqual(axis.get_ylim()[0], 0)
        self.assertIn("dato extremo", axis.get_title().lower())
        self.assertEqual(len(axis.containers), 2)
        self.assertEqual(namespace["dato_modificado"].get_label(), "dato modificado")

    def test_scale_figure_labels_original_units_and_z_score(self) -> None:
        namespace = runpy.run_path(LAB_ROOT / "03_escala.py")
        figure = namespace["fig"]
        original_axis, standardized_axis = figure.axes
        self.assertEqual(len(figure.axes), 2)
        self.assertEqual(original_axis.get_ylim()[0], 0)
        self.assertIn("unidades distintas", original_axis.get_title().lower())
        self.assertEqual(standardized_axis.get_title(), "z-score")
        self.assertFalse(original_axis.get_legend())
        self.assertFalse(standardized_axis.get_legend())
        self.assertTrue(
            any(
                np.allclose(line.get_ydata(), [0, 0])
                for line in standardized_axis.lines
            )
        )

    def test_plot_labs_run_without_agg_warnings(self) -> None:
        with warnings.catch_warnings(record=True) as captured_warnings:
            warnings.simplefilter("always")
            runpy.run_path(LAB_ROOT / "02_centro_dispersion.py")
            runpy.run_path(LAB_ROOT / "03_escala.py")
        self.assertFalse(
            any(
                "FigureCanvasAgg is non-interactive" in str(warning.message)
                for warning in captured_warnings
            )
        )

    def test_miniinspector_uses_population_std_for_consistency(self) -> None:
        namespace = runpy.run_path(LAB_ROOT / "04_miniinspector.py")
        expected_columns = ["media", "desviacion", "minimo", "maximo"]
        self.assertEqual(list(namespace["resumen"].columns), expected_columns)
        self.assertAlmostEqual(namespace["resumen"].loc["duracion_min", "media"], 45.4)

    def test_source_has_every_pedagogical_marker(self) -> None:
        source_path = BOOK_ROOT / "contenido_fuente" / "01_datos_y_formas" / "index.md"
        source = source_path.read_text(encoding="utf-8")
        markers = (
            "reto",
            "observa",
            "matematica",
            "modifica",
            "desde_cero",
            "con_herramienta",
            "depura",
            "comprueba",
        )
        for marker in markers:
            self.assertIn(f'data-pedagogy="{marker}"', source)
        self.assertGreaterEqual(source.count("data-solution"), 3)
        self.assertEqual(source.count("<py-lab "), 4)
        self.assertEqual(source.count("data-static-output-for="), 4)


class LearningSourceValidationTests(unittest.TestCase):
    def _validate(self, source: str) -> list[str]:
        with TemporaryDirectory() as temporary_directory:
            book_root = Path(temporary_directory)
            source_path = book_root / "contenido_fuente" / "modulo" / "index.md"
            source_path.parent.mkdir(parents=True)
            source_path.write_text(source, encoding="utf-8")
            return validar_contenido.validate_learning_source(
                source_path,
                {"reto"},
                book_root,
            )

    def test_rejects_missing_required_pedagogical_marker(self) -> None:
        errors = self._validate(
            '<details data-solution></details><input data-progress-id="one">'
        )
        self.assertTrue(any("data-pedagogy=reto" in error for error in errors))

    def test_rejects_malformed_py_lab_tag(self) -> None:
        errors = self._validate(
            '<h2 data-pedagogy="reto"></h2><details data-solution></details>'
            '<input data-progress-id="one"><py-lab data-lab-id="bad"></py-lab>'
        )
        self.assertTrue(any("etiqueta py-lab mal formada" in error for error in errors))

    def test_rejects_lab_without_static_fallback(self) -> None:
        errors = self._validate(
            '<h2 data-pedagogy="reto"></h2><details data-solution></details>'
            '<input data-progress-id="one">'
            '<py-lab data-lab-id="lab" data-src="labs/lab.py" '
            'data-packages="numpy" data-title="Lab"></py-lab>'
        )
        self.assertTrue(
            any("falta salida estática para lab" in error for error in errors)
        )

    def test_skips_pedagogical_read_for_source_outside_book(self) -> None:
        manifest = {
            "modules": [
                {
                    "id": "escaped",
                    "status": "disponible",
                    "source": "../outside.md",
                }
            ]
        }
        with TemporaryDirectory() as temporary_directory:
            book_root = Path(temporary_directory) / "libro_ml_dl"
            book_root.mkdir()
            with patch.object(
                validar_contenido,
                "validate_learning_source",
                side_effect=AssertionError("unsafe read"),
            ) as validator:
                errors = validar_contenido.validate_available_learning_sources(
                    manifest,
                    book_root,
                )
        self.assertEqual(errors, [])
        validator.assert_not_called()

    def test_validator_loads_when_executed_as_a_direct_file(self) -> None:
        script_path = BOOK_ROOT / "scripts" / "validar_contenido.py"
        original_path = sys.path.copy()
        cached_modules = {
            name: sys.modules.pop(name)
            for name in ("scripts", "scripts.modelo_contenido")
            if name in sys.modules
        }
        sys.path[:] = [
            str(script_path.parent),
            *(
                path
                for path in original_path
                if Path(path or ".").resolve() != BOOK_ROOT.resolve()
            ),
        ]
        try:
            spec = spec_from_file_location("direct_validator", script_path)
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)
            module = module_from_spec(spec)
            spec.loader.exec_module(module)
        finally:
            sys.path[:] = original_path
            sys.modules.update(cached_modules)
        self.assertTrue(callable(module.main))
