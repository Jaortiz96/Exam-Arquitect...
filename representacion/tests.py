from django.test import SimpleTestCase

from .services import (
    ErrorDeValidacion,
    analizar_texto,
    convertir_numero,
)


class ConversionesValidasTests(SimpleTestCase):
    def test_decimal_255_en_todas_las_bases(self):
        r = convertir_numero("255", 10)
        self.assertEqual(r.decimal, "255")
        self.assertEqual(r.binario, "11111111")
        self.assertEqual(r.octal, "377")
        self.assertEqual(r.hexadecimal, "FF")

    def test_hexadecimal_acepta_minusculas(self):
        self.assertEqual(convertir_numero("ff", 16).valor, 255)

    def test_binario_y_octal_de_origen(self):
        self.assertEqual(convertir_numero("101010", 2).valor, 42)
        self.assertEqual(convertir_numero("52", 8).valor, 42)

    def test_binario_se_completa_al_siguiente_byte(self):
        casos = {
            "1": ("00000001", 1, 1),
            "255": ("11111111", 8, 1),
            "256": ("0000000100000000", 9, 2),
            "65535": ("1111111111111111", 16, 2),
        }
        for entrada, (binario, bits, nbytes) in casos.items():
            with self.subTest(entrada=entrada):
                r = convertir_numero(entrada, 10)
                self.assertEqual(r.binario, binario)
                self.assertEqual(len(r.binario) % 8, 0)
                self.assertEqual(r.bits_significativos, bits)
                self.assertEqual(r.bytes_necesarios, nbytes)

    def test_cero_usa_un_bit_y_un_byte(self):
        r = convertir_numero("0", 10)
        self.assertEqual(r.binario, "00000000")
        self.assertEqual(r.bits_significativos, 1)
        self.assertEqual(r.bytes_necesarios, 1)

    def test_limites_del_rango_son_validos(self):
        self.assertEqual(convertir_numero("0", 10).valor, 0)
        self.assertEqual(convertir_numero("FFFF", 16).valor, 65535)


class ErroresDeValidacionTests(SimpleTestCase):
    def assertError(self, texto, base, fragmento):
        with self.assertRaises(ErrorDeValidacion) as contexto:
            convertir_numero(texto, base)
        self.assertIn(fragmento, str(contexto.exception))

    def test_entrada_vacia(self):
        self.assertError("", 10, "no puede estar vacío")
        self.assertError("   ", 10, "no puede estar vacío")

    def test_digito_invalido_en_base_2(self):
        self.assertError("1012", 2, "'2'")
        self.assertError("1012", 2, "base 2")

    def test_digito_invalido_en_base_8_y_10(self):
        self.assertError("789", 8, "base 8")
        self.assertError("12A", 10, "base 10")

    def test_letra_invalida_en_hexadecimal(self):
        self.assertError("FG", 16, "'G'")

    def test_valor_negativo(self):
        self.assertError("-5", 10, "negativos")

    def test_valor_fuera_de_rango(self):
        self.assertError("65536", 10, "fuera del rango")
        self.assertError("10000", 16, "fuera del rango")

    def test_base_no_permitida(self):
        self.assertError("10", 3, "base válida")


class AnalisisDeTextoTests(SimpleTestCase):
    def test_enie_utf8(self):
        (fila,) = analizar_texto("ñ")
        self.assertEqual(fila.caracter, "ñ")
        self.assertEqual(fila.decimal, 241)
        self.assertEqual(fila.punto_codigo, "U+00F1")
        self.assertEqual(fila.hexadecimal, "0xF1")
        self.assertEqual(fila.bytes_utf8, "C3 B1")
        self.assertEqual(fila.cantidad_bytes, 2)

    def test_ascii_ocupa_un_byte(self):
        (fila,) = analizar_texto("A")
        self.assertEqual(fila.punto_codigo, "U+0041")
        self.assertEqual(fila.bytes_utf8, "41")

    def test_una_fila_por_caracter(self):
        filas = analizar_texto("año")
        self.assertEqual([f.caracter for f in filas], ["a", "ñ", "o"])

    def test_texto_vacio(self):
        with self.assertRaises(ErrorDeValidacion):
            analizar_texto("")

    def test_limite_de_20_caracteres(self):
        self.assertEqual(len(analizar_texto("a" * 20)), 20)
        with self.assertRaises(ErrorDeValidacion):
            analizar_texto("a" * 21)


class VistaTests(SimpleTestCase):
    def test_pagina_inicial(self):
        respuesta = self.client.get("/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Analizador de representación de datos")

    def test_conversion_valida_muestra_resultados(self):
        respuesta = self.client.post(
            "/", {"accion": "numero", "numero": "FF", "base": "16"}
        )
        self.assertContains(respuesta, "11111111")
        self.assertContains(respuesta, "377")
        self.assertContains(respuesta, "Bytes necesarios")

    def test_error_de_validacion_se_muestra_al_usuario(self):
        respuesta = self.client.post(
            "/", {"accion": "numero", "numero": "102", "base": "2"}
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "no es válido en base 2")

    def test_texto_con_enie_muestra_bytes_utf8(self):
        respuesta = self.client.post("/", {"accion": "texto", "texto": "ñ"})
        self.assertContains(respuesta, "U+00F1")
        self.assertContains(respuesta, "C3 B1")
