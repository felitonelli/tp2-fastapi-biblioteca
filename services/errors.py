"""Errores de negocio. Los services los lanzan sin saber nada de HTTP;
main.py los traduce al código HTTP que corresponde."""


class NotFoundError(Exception):
    """Recurso inexistente → 404"""


class ConflictError(Exception):
    """Choca con el estado actual (duplicado, sin stock, ya devuelto...) → 409"""


class ForbiddenError(Exception):
    """La operación no está permitida para ese recurso (socio inactivo) → 403"""


class InvalidDataError(Exception):
    """Datos válidos en formato pero imposibles (devolver antes de prestar) → 422"""
