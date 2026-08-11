from .models import GarageSettings

def garage_settings(request):
    try:
        return {'garage_settings': GarageSettings.get_settings()}
    except Exception:
        return {'garage_settings': None}
