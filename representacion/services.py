"""Lógica pura de conversión y análisis (sin dependencias de Django).

Se mantiene separada de las vistas y formularios para poder probarla
fácilmente y para que las reglas de negocio queden en un solo lugar.
"""
from dataclasses import dataclass

BASES_VALIDAS = (2, 8, 10, 16)
VALOR_MINIMO = 0
VALOR_MAXIMO = 65_535
MAX_CARACTERES_TEXTO = 20
MAX_LARGO_NUMERO = 64  # evita procesar entradas absurdamente largas

DIGITOS = "0123456789ABCDEF"
NOMBRES_BASE = {2: "binaria", 8: "octal", 10: "decimal", 16: "hexadecimal"}


class ErrorDeValidacion(ValueError):
    """Error de entrada con un mensaje pensado para mostrarse al usuario."""


@dataclass(frozen=True)
class ResultadoNumero:
    valor: int
    decimal: str
    binario: str          # completado al siguiente límite de byte, sin espacios
    binario_agrupado: str  # el mismo binario separado en grupos de 8 bits
    octal: str
    hexadecimal: str
    bits_significativos: int
    bytes_necesarios: int

    @property
    def bits_totales(self) -> int:
        return self.bytes_necesarios * 8

    @property
    def bytes_binarios(self) -> list[dict]:
        """Un elemento por byte, con sus bits marcados como relleno o significativos.

        Sirve solo para dibujar el resultado: los bits de relleno son los ceros
        a la izquierda que se agregaron para completar el byte.
        """
        relleno = len(self.binario) - self.bits_significativos
        resultado = []
        for inicio in range(0, len(self.binario), 8):
            grupo = self.binario[inicio:inicio + 8]
            celdas = [
                (bit, inicio + posicion < relleno)
                for posicion, bit in enumerate(grupo)
            ]
            resultado.append({"celdas": celdas, "hex": f"{int(grupo, 2):02X}"})
        return resultado


@dataclass(frozen=True)
class FilaCaracter:
    caracter: str
    visible: str          # representación legible (p. ej. "(espacio)")
    decimal: int
    punto_codigo: str     # U+00F1
    hexadecimal: str      # 0xF1
    bytes_utf8: str       # C3 B1
    cantidad_bytes: int


def _digitos_permitidos(base: int) -> str:
    return DIGITOS[:base]


def convertir_numero(texto: str, base: int) -> ResultadoNumero:
    """Valida ``texto`` en ``base`` y devuelve sus representaciones."""
    if base not in BASES_VALIDAS:
        raise ErrorDeValidacion("Selecciona una base válida: 2, 8, 10 o 16.")

    texto = (texto or "").strip()
    if not texto:
        raise ErrorDeValidacion("Ingresa un número. El campo no puede estar vacío.")

    if texto.startswith("-"):
        raise ErrorDeValidacion(
            "No se aceptan valores negativos. Ingresa un número entre 0 y 65 535."
        )

    if len(texto) > MAX_LARGO_NUMERO:
        raise ErrorDeValidacion(
            f"El número es demasiado largo (máximo {MAX_LARGO_NUMERO} dígitos)."
        )

    permitidos = _digitos_permitidos(base)
    invalidos = []
    for caracter in texto.upper():
        if caracter not in permitidos and caracter not in invalidos:
            invalidos.append(caracter)
    if invalidos:
        lista = ", ".join(f"'{c}'" for c in invalidos)
        etiqueta = "El dígito" if len(invalidos) == 1 else "Los dígitos"
        verbo = "no es válido" if len(invalidos) == 1 else "no son válidos"
        raise ErrorDeValidacion(
            f"{etiqueta} {lista} {verbo} en base {base} "
            f"({NOMBRES_BASE[base]}). Dígitos permitidos: {_formatear_permitidos(permitidos)}."
        )

    valor = int(texto, base)
    if valor > VALOR_MAXIMO:
        raise ErrorDeValidacion(
            f"El valor {valor} está fuera del rango permitido "
            f"({VALOR_MINIMO} a {VALOR_MAXIMO:,}).".replace(",", " ")
        )

    return _construir_resultado(valor)


def _formatear_permitidos(permitidos: str) -> str:
    if len(permitidos) <= 2:
        return " y ".join(permitidos)
    return f"{permitidos[0]}–{permitidos[-1]}"


def _construir_resultado(valor: int) -> ResultadoNumero:
    # El 0 se representa con 1 bit significativo ("0").
    bits = max(1, valor.bit_length())
    bytes_necesarios = (bits + 7) // 8
    binario = format(valor, "b").zfill(bytes_necesarios * 8)
    agrupado = " ".join(binario[i:i + 8] for i in range(0, len(binario), 8))
    return ResultadoNumero(
        valor=valor,
        decimal=str(valor),
        binario=binario,
        binario_agrupado=agrupado,
        octal=format(valor, "o"),
        hexadecimal=format(valor, "X"),
        bits_significativos=bits,
        bytes_necesarios=bytes_necesarios,
    )


_NOMBRES_VISIBLES = {
    " ": "(espacio)",
    "\t": "(tabulador)",
    "\n": "(salto de línea)",
    "\r": "(retorno de carro)",
    "\u00a0": "(espacio duro)",
}


def _visible(caracter: str) -> str:
    if caracter in _NOMBRES_VISIBLES:
        return _NOMBRES_VISIBLES[caracter]
    if ord(caracter) < 32 or ord(caracter) == 127:
        return "(control)"
    return caracter


def analizar_texto(texto: str) -> list[FilaCaracter]:
    """Devuelve una fila por carácter (punto de código) del texto."""
    if not texto:
        raise ErrorDeValidacion("Ingresa un texto. El campo no puede estar vacío.")
    if len(texto) > MAX_CARACTERES_TEXTO:
        raise ErrorDeValidacion(
            f"El texto es demasiado largo: tiene {len(texto)} caracteres y el "
            f"máximo es {MAX_CARACTERES_TEXTO}."
        )

    filas = []
    for caracter in texto:
        codigo = ord(caracter)
        try:
            codificado = caracter.encode("utf-8")
        except UnicodeEncodeError:
            raise ErrorDeValidacion(
                "El texto contiene un carácter que no se puede codificar en UTF-8."
            ) from None
        filas.append(
            FilaCaracter(
                caracter=caracter,
                visible=_visible(caracter),
                decimal=codigo,
                punto_codigo=f"U+{codigo:04X}",
                hexadecimal=f"0x{codigo:X}",
                bytes_utf8=" ".join(f"{b:02X}" for b in codificado),
                cantidad_bytes=len(codificado),
            )
        )
    return filas
