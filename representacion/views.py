from django.shortcuts import render

from .forms import ConversionForm, TextoForm
from .services import MAX_CARACTERES_TEXTO, VALOR_MAXIMO


def index(request):
    """Página única con los dos formularios.

    Cada formulario envía un campo ``accion`` ("numero" o "texto") para saber
    cuál se procesó; el otro se muestra vacío.
    """
    form_numero = ConversionForm()
    form_texto = TextoForm()
    resultado = None
    filas = None

    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "numero":
            form_numero = ConversionForm(request.POST)
            if form_numero.is_valid():
                resultado = form_numero.resultado
        elif accion == "texto":
            form_texto = TextoForm(request.POST)
            if form_texto.is_valid():
                filas = form_texto.filas

    total_bytes = sum(f.cantidad_bytes for f in filas) if filas else 0

    contexto = {
        "form_numero": form_numero,
        "form_texto": form_texto,
        "resultado": resultado,
        "filas": filas,
        "total_bytes": total_bytes,
        "valor_maximo": f"{VALOR_MAXIMO:,}".replace(",", " "),
        "max_caracteres": MAX_CARACTERES_TEXTO,
        "accion": request.POST.get("accion") if request.method == "POST" else "",
    }
    return render(request, "representacion/index.html", contexto)
