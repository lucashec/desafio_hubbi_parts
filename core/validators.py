from django.core.exceptions import ValidationError


def validate_positive_number(value):
    """
    Valida se o número é positivo.
    """
    if value < 0:
        raise ValidationError("Número deve ser positivo.")


def validate_csv_file(file):
    """
    Valida se o arquivo é CSV.
    """
    if not file.name.endswith(".csv"):
        raise ValidationError("Arquivo deve ser do tipo CSV.")


def validate_email(email):
    """
    Valida formato de email (básico).
    """
    if "@" not in email or "." not in email.split("@")[1]:
        raise ValidationError("Email inválido.")
