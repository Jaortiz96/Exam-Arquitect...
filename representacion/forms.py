from django import forms

from .services import (
    BASES_VALIDAS,
    ErrorDeValidacion,
    analizar_texto,
    convertir_numero,
)

OPCIONES_BASE = [
    (2, "Binaria (base 2)"),
    (8, "Octal (base 8)"),
    (10, "Decimal (base 10)"),
    (16, "Hexadecimal (base 16)"),
]


class ConversionForm(forms.Form):
    """Número + base de origen. La validación real vive en ``services``."""

    numero = forms.CharField(label="Número", required=False)
    base = forms.TypedChoiceField(
        label="Base de origen",
        choices=OPCIONES_BASE,
        coerce=int,
        initial=10,
        error_messages={
            "required": "Selecciona una base de origen: 2, 8, 10 o 16.",
            "invalid_choice": "Selecciona una base válida: 2, 8, 10 o 16.",
        },
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resultado = None

    def clean(self):
        datos = super().clean()
        base = datos.get("base")
        if base in BASES_VALIDAS:
            try:
                self.resultado = convertir_numero(datos.get("numero", ""), base)
            except ErrorDeValidacion as error:
                self.add_error("numero", str(error))
        return datos


class TextoForm(forms.Form):
    """Texto de hasta 20 caracteres. No se recortan los espacios: cuentan."""

    texto = forms.CharField(label="Texto", required=False, strip=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filas = None

    def clean(self):
        datos = super().clean()
        try:
            self.filas = analizar_texto(datos.get("texto", ""))
        except ErrorDeValidacion as error:
            self.add_error("texto", str(error))
        return datos
