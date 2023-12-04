from flask_wtf import FlaskForm
from wtforms import IntegerField, FloatField, SelectField, StringField, PasswordField, DateTimeField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError
from app import app,models,db

class LoginForm(FlaskForm):
    email = StringField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])

class CreateAccountForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    institution = StringField('institution')

class EditUserForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired()])
    institution = StringField('institution')

class ChangePasswordForm(FlaskForm):
    oldPassword = PasswordField('oldPassword', validators=[DataRequired()])
    newPassword = PasswordField('newPassword', validators=[DataRequired()])

class CreateGroupForm(FlaskForm):
    title = StringField('title',  validators=[DataRequired()])
    topic = SelectField('topic', choices = ['English', 'Mathematics', 'Computing',
                                                'Biology', 'Chemistry', 'Physics', 'Engineering',
                                                'Languages', 'Medicine', 'Nursing', 'Vetenarian sciences',
                                                'Music', 'Geography', 'History', 'Geology', 'Psychology', 'Sociology',
                                                'Criminology', 'Media studies', 'Communications', 'Religous studies',
                                                'Philosophy', 'Business', 'Economics', 'Political studies', 
                                                'Law', 'Food sciences', 'Theatre studies'])
    description = TextAreaField('description',  validators=[DataRequired()])
    startDate = StringField('startDate', validators=[DataRequired()])
    startTime = StringField('startTime',  validators=[DataRequired()])
    capacity = IntegerField('capacity',  validators=[DataRequired(), NumberRange(min=2, max=200, message="Amount not within range")])
    institution = StringField('institution')

class CreateLocationForm(FlaskForm):
    locationTitle = StringField('title')
    locationDescription = TextAreaField('description')
    accessible = BooleanField('accessible')

class FilterGroupsForm(FlaskForm):
    topic = SelectField('topic', choices = ['None', 'English', 'Mathematics', 'Computing',
                                                'Biology', 'Chemistry', 'Physics', 'Engineering',
                                                'Languages', 'Medicine', 'Nursing', 'Vetenarian sciences',
                                                'Music', 'Geography', 'History', 'Geology', 'Psychology', 'Sociology',
                                                'Criminology', 'Media studies', 'Communications', 'Religous studies',
                                                'Philosophy', 'Business', 'Economics', 'Political studies', 
                                                'Law', 'Food sciences', 'Theatre studies'])
    accessible = BooleanField('accessible')
    institution = BooleanField('institution')

    
