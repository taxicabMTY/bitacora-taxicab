"""Pruebas de las partes de enviar_bitacora.py que cambian según el sistema.

Correr desde esta carpeta:  python3 -m unittest -v
"""
import unittest
from pathlib import Path

import enviar_bitacora as eb


class BuscarNavegador(unittest.TestCase):
    def test_mac_usa_chrome_de_applications(self):
        ruta = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        self.assertEqual(
            eb.buscar_navegador("Darwin", existe=lambda p: p == ruta, which=lambda n: None, env={}),
            ruta,
        )

    def test_windows_prefiere_chrome_y_cae_a_edge(self):
        env = {"ProgramFiles": r"C:\Program Files", "ProgramFiles(x86)": r"C:\Program Files (x86)"}
        edge = str(Path(r"C:\Program Files (x86)") / "Microsoft/Edge/Application/msedge.exe")
        self.assertEqual(
            eb.buscar_navegador("Windows", existe=lambda p: p == edge, which=lambda n: None, env=env),
            edge,
        )

    def test_windows_con_los_dos_elige_chrome(self):
        env = {"ProgramFiles": r"C:\Program Files", "ProgramFiles(x86)": r"C:\Program Files (x86)"}
        chrome = str(Path(r"C:\Program Files") / "Google/Chrome/Application/chrome.exe")
        self.assertEqual(
            eb.buscar_navegador("Windows", existe=lambda p: True, which=lambda n: None, env=env),
            chrome,
        )

    def test_linux_busca_en_el_path(self):
        self.assertEqual(
            eb.buscar_navegador("Linux", existe=lambda p: False,
                                which=lambda n: "/usr/bin/chromium" if n == "chromium" else None, env={}),
            "/usr/bin/chromium",
        )

    def test_la_variable_NAVEGADOR_manda_sobre_todo(self):
        self.assertEqual(
            eb.buscar_navegador("Windows", existe=lambda p: True, which=lambda n: None,
                                env={"NAVEGADOR": r"D:\mi\brave.exe"}),
            r"D:\mi\brave.exe",
        )

    def test_sin_navegador_devuelve_None(self):
        self.assertIsNone(eb.buscar_navegador("Windows", existe=lambda p: False, which=lambda n: None, env={}))


class Rutas(unittest.TestCase):
    def test_reportes_por_defecto_en_documentos_del_usuario(self):
        self.assertEqual(
            eb.reportes_por_defecto(Path("/home/ana")),
            Path("/home/ana/Documents/TaxiCab-Notas/Reportes"),
        )

    def test_url_de_archivo_vale_en_windows_y_mac(self):
        self.assertTrue(eb.url_de_archivo(Path("/tmp/a b.html")).startswith("file:///"))
        self.assertIn("a%20b.html", eb.url_de_archivo(Path("/tmp/a b.html")))


class CargarEnv(unittest.TestCase):
    def test_lee_comillas_comentarios_y_bom_de_windows(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".env"
            p.write_bytes('\ufeff# c\nA="uno"\r\nB=dos tres\r\n'.encode("utf-8"))
            self.assertEqual(eb.cargar_env(p), {"A": "uno", "B": "dos tres"})


if __name__ == "__main__":
    unittest.main()
