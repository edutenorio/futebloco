from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
import stdimage
from icecream import ic

from futebloco.settings import EMAIL_HOST_USER
from .models import Person, Role, MatchEvent
from .validators import cpf_validator


class CustomUserCreationForm(UserCreationForm):
    password1 = forms.CharField(
        label=_('Password').capitalize(), strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=_('Password confirmation').capitalize(), strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        help_text=_('Enter the same password as before, for verification.'),
    )
    doc = forms.CharField(
        label='CPF', max_length=14, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control cpf', 'placeholder': '000.000.000-00'}),
        validators=[cpf_validator],
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'doc')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome de Usuário'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sobrenome'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'nome@email.com'}),
        }

    def is_valid(self):
        # Check normal form validity.
        form_valid = super().is_valid()
        # Check if a person with the informed document number already exists and has no user already associated
        if 'doc' not in self.cleaned_data:
            doc_valid = False
        else:
            try:
                person = Person.objects.get(doc=self.cleaned_data['doc'])
                if person.user_profile_id is not None:
                    self.add_error('doc', _('Esse CPF já está associado a um usuário.'))
                    doc_valid = False
                else:
                    doc_valid = True
            except Person.DoesNotExist:
                # A new person will be created in the save() function
                doc_valid = True
        return form_valid and doc_valid

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        # Check is there is a person to be associated with, or create one
        try:
            person = Person.objects.get(doc=self.cleaned_data['doc'])
        except Person.DoesNotExist:
            person = Person()
            person.name = f'{user.first_name} {user.last_name}'
            person.short = f'{user.first_name}'
            person.doc = self.cleaned_data['doc']
        person.email = user.email
        person.user_profile = user
        if commit:
            user.save()
            person.save()
        return user


class PersonForm(forms.ModelForm):

    doc = forms.CharField(
        label='CPF', max_length=14, required=True, validators=[cpf_validator],
        widget=forms.TextInput(attrs={'class': 'form-control cpf', 'placeholder': '000.000.000-00'}))

    class Meta:
        model = Person
        fields = ['name', 'short', 'summary', 'photo', 'hood', 'doc', 'dob', 'email', 'phone1', 'address', 'bankdata',
                  'roles', 'facebook', 'twitter', 'instagram']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'short': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Como gostaria de ser chamado'}),
            'summary': forms.Textarea(attrs={'class': 'form-control',
                                             'placeholder': _('Escreve um texto sobre você para aparecer no seu perfil.'
                                                              ' Em dois ou três parágrafos, conte sua história, de que '
                                                              'blocos você faz parte, o que você espera do '
                                                              'Futebloco esse ano.')}),
            # 'doc': forms.TextInput(attrs={'class': 'form-control cpf', 'placeholder': '000.000.000-00'}),
            'dob': forms.TextInput(attrs={'type': 'date', 'class': 'form-control'}),
            'email': forms.TextInput(attrs={'type': 'email', 'class': 'form-control', 'placeholder': 'nome@email.com'}),
            'phone1': forms.TextInput(attrs={
                'class': 'form-control phone9_with_ddd', 'placeholder': '(21) 99999-9999'}),
            'phone2': forms.TextInput(attrs={
                'class': 'form-control phone9_with_ddd', 'placeholder': '(21) 99999-9999'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Endereço Completo')}),
            'bankdata': forms.Textarea(attrs={'class': 'form-control', 'placeholder': _('Dados Bancários')}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'roles': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'facebook': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Perfil no Facebook')}),
            'twitter': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Perfil no Twitter (X)')}),
            'instagram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Perfil no Instagram')}),
            'hood': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Bairro ou Região')}),
        }
        labels = {
            'name': _('Nome Completo'),
            'short': _('Nome Curto (apelido)'),
            'summary': _('Descrição'),
            'dob': _('Data de Nascimento'),
            'email': _('E-mail'),
            'phone1': _('Telefone'),
            'phone2': _('Telefone 2'),
            'address': _('Endereço'),
            'bankdata': _('Dados Bancários'),
            'photo': _('Foto'),
            'roles': _('Função'),
            'hood': _('Bairro'),
        }

    def __init__(self, *args, **kwargs):
        super(PersonForm, self).__init__(*args, **kwargs)
        self.fields['roles'].queryset = Role.objects.exclude(name__startswith='admin')


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label=_('Email'), max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'})
    )


class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label=_('New password'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'})
    )
    new_password2 = forms.CharField(
        label=_('Confirm new password'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'})
    )


class MatchEventForm(forms.ModelForm):
    class Meta:
        model = MatchEvent
        fields = ['timestamp', 'matchtimeminutes', 'match', 'playerreg', 'teamreg', 'eventtype']
        widgets = {
            'timestamp': forms.DateTimeInput(attrs={'class': 'form-control'}),
            'matchtimeminutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'match': forms.Select(attrs={'class': 'form-control'}),
            'playerreg': forms.Select(attrs={'class': 'form-control'}),
            'teamreg': forms.Select(attrs={'class': 'form-control'}),
            'eventtype': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'timestamp': _('Dia e Hora'),
            'matchtimeminutes': _('Minutos'),
            'match': _('Partida'),
            'playerreg': _('Jogador(a)'),
            'teamreg': _('Time'),
            'eventtype': _('Evento'),
        }


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(max_length=100, required=True)
    subject = forms.CharField(max_length=100, required=True)
    body = forms.CharField(max_length=5000, required=True)

    class Meta:
        fields = ['name', 'email', 'subject', 'body']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def send_mail(self):
        name = self.cleaned_data['name']
        email = self.cleaned_data['email']
        subject = self.cleaned_data['subject']
        body = self.cleaned_data['body']
        content = f'Nome: {name}\nE-mail: {email}\nAssunto: {subject}\nMensagem: {body}'
        mail = EmailMessage(
            subject=f'Contato Site Futebloco de {name}',
            body=content,
            from_email=EMAIL_HOST_USER,
            to=[EMAIL_HOST_USER],
            headers={'Reply-To': email}
        )
        mail.send()

