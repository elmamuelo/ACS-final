"""
Suite de Pruebas Automatizadas Backend (Pytest / Django TestCase)
Caso Práctico Final - Aseguramiento de la Calidad (ACS) - ITM
Sistema Bajo Prueba: InvenTree v1.7.0 (src/backend/InvenTree)
Integrantes:
  - Emanuel Ortiz (Stock, Serialización, Helpers)
  - Manuela Sánchez (Partes, Órdenes de Venta, Validadores)
  - Juan Torres (Autenticación, RBAC, Seguridad de Exportación)
"""

from decimal import Decimal
import pytest
from django.core.exceptions import ValidationError

from InvenTree.helpers import (
    INT_CLIP_MAX,
    clean_decimal,
    constructPathString,
    escape_export_value,
    extract_int,
    extract_serial_numbers,
    sanitize_token,
    strip_html_tags,
)
from InvenTree.validators import validate_currency_code, invalid_site_url_hint


class TestInvenTreeACSAutomatedSuite:
    """Casos de prueba automatizados aplicando Partición de Equivalencia y Valores Límite."""

    def test_cp_aut_01_extract_serial_numbers_ep_bva(self):
        """CP-AUT-01 (Emanuel Ortiz): Extracción de seriales y límite máximo de 1000."""
        # Partición válida: rango secuencial y operador +
        assert extract_serial_numbers("SN001-SN005", 5) == [
            "SN001",
            "SN002",
            "SN003",
            "SN004",
            "SN005",
        ]
        assert extract_serial_numbers("A10+3", 4) == ["A10", "A11", "A12", "A13"]

        # BVA: Frontera superior válida = 1000
        serials_1000 = extract_serial_numbers("1+", 1000)
        assert len(serials_1000) == 1000

        # BVA: Frontera superior inválida = 1001
        with pytest.raises(ValidationError):
            extract_serial_numbers("1+", 1001)

    def test_cp_aut_02_clean_decimal_partitions(self):
        """CP-AUT-02 (Manuela Sánchez): Normalización decimal y separadores de miles."""
        assert clean_decimal("1.250,75") == Decimal("1250.75")
        assert clean_decimal("1,250.75") == Decimal("1250.75")
        assert clean_decimal("") == Decimal(0)
        assert clean_decimal(None) == Decimal(0)
        # Defecto DEF-04: Múltiples separadores de miles sin decimales ("1,234,567")
        assert clean_decimal("1,234,567") == Decimal("1234567")

    def test_cp_aut_03_currency_and_site_url_validators(self):
        """CP-AUT-03 (Manuela Sánchez): Validación de códigos ISO 4217 y URLs."""
        validate_currency_code("USD")
        validate_currency_code("COP")
        with pytest.raises(ValidationError):
            validate_currency_code("INVALID_CURR")

        hint = invalid_site_url_hint("http://warehouse:8000")
        assert "INVE-E17" in hint

    def test_cp_aut_05_escape_export_value_owasp_csv_injection(self):
        """CP-AUT-05 (Juan Torres): Mitigación de CSV Formula Injection (OWASP)."""
        assert escape_export_value("=1+1") == "'=1+1"
        assert escape_export_value("=CMD|' /C calc'!A0") == "'=CMD|' /C calc'!A0"
        assert escape_export_value("@SUM(A1:A10)") == "'@SUM(A1:A10)"
        assert escape_export_value("-222") == "-222"
        assert escape_export_value("+1.5") == "+1.5"
        assert escape_export_value(100) == 100

    def test_cp_aut_06_sanitize_token_boundary_back_zero(self):
        """CP-AUT-06 (Juan Torres): Valor límite back=0 en sanitize_token (Detecta DEF-02)."""
        secret = "inv-9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a"
        masked = sanitize_token(secret, front=8, back=0)
        # El token completo jamás debe filtrarse en la salida sanitizada
        assert secret not in masked

    def test_cp_aut_07_extract_int_negative_clipping(self):
        """CP-AUT-07 (Emanuel Ortiz): Acotamiento de enteros con allow_negative=False (Detecta DEF-03)."""
        assert extract_int("12345", clip=100000, allow_negative=False) == 12345
        assert extract_int("-50", clip=100, allow_negative=False) == 50
        # Valor límite: entrada < -clip con allow_negative=False debe ser >= 0
        assert extract_int("-500", clip=100, allow_negative=False) >= 0

    def test_cp_aut_08_strip_html_tags_and_pathstring(self):
        """CP-AUT-08 (Juan Torres): Sanitización XSS con nh3 y truncamiento de rutas."""
        with pytest.raises(ValidationError):
            strip_html_tags("<script>alert(1)</script>Resistor", raise_error=True)
        assert strip_html_tags("<b> Capacitor </b>", raise_error=False) == "Capacitor"

        short_path = constructPathString(["Almacen", "EstanteA", "Caja1"], max_chars=250)
        assert short_path == "Almacen/EstanteA/Caja1"

