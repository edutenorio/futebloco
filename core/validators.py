from django.core.exceptions import ValidationError
from django.core.validators import BaseValidator
from django.utils.translation import gettext_lazy as _
from validate_docbr import CPF


def cpf_validator(value):
    if not CPF().validate(value):
        raise ValidationError(_('CPF inválido.'), code='invalid')
