"""
TramaPos · Pruebas de autenticación: hash de contraseñas y JWT.
No necesitan base de datos, son pruebas puras de lógica.
"""

from app.core.security import (
    crear_access_token,
    decodificar_access_token,
    hashear_password,
    verificar_password,
)


def test_password_se_hashea_y_verifica_correctamente():
    hash_generado = hashear_password("miClaveSegura123")

    assert hash_generado != "miClaveSegura123"  # nunca en texto plano
    assert verificar_password("miClaveSegura123", hash_generado) is True
    assert verificar_password("claveIncorrecta", hash_generado) is False


def test_token_jwt_se_crea_y_decodifica_correctamente():
    token = crear_access_token({"sub": "42", "rol": "ADMIN"})
    payload = decodificar_access_token(token)

    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["rol"] == "ADMIN"


def test_token_invalido_no_se_puede_decodificar():
    assert decodificar_access_token("esto-no-es-un-token-valido") is None