from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.models import  UserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
# Group Imports
from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.models import Group
from io import BytesIO
from PIL import Image
import os
from django.core.files.base import ContentFile
from django.db.models import Q


# Custom User Model

class MyAccountManager(BaseUserManager):
    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError("Users must have an email address")
        if not username:
            raise ValueError("Users must have an username")
        user = self.model(
            email=self.normalize_email(email),
            username=username,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password):
        user = self.create_user(
            email=self.normalize_email(email),
            username=username,
            password=password,
        )

        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser,PermissionsMixin):
    email = models.EmailField(verbose_name='email', max_length=80, unique=True)
    username = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=100,null=True)
    last_name = models.CharField(max_length=100,null=True)
    phone_no = models.CharField(max_length=12, null=True)
    date_joined = models.DateField(
        verbose_name='date joined', auto_now_add=True)
    last_login = models.DateField(verbose_name='last login', auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    address = models.CharField(max_length=500, null=True, blank=True)
    telegram_number = models.CharField(max_length=12,null=True)
    parent_number = models.CharField(max_length=12,null=True)
    district = models.CharField(max_length=255,null=True)


    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = MyAccountManager()

    def __str__(self):
        return self.email

    # def has_perm(self, perm, obj=None):
    #     return self.is_admin

    def has_module_perms(self, app_label):
        return True



class TeacherProfile(models.Model):
    def upload_location(instance, filename):
        return "teacher_images/%s/%s" % (instance.user.username, filename)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to=upload_location,null=True,blank=True,default="teacher_images/default.png")
    description = models.CharField(max_length=500,null=True,blank=True)
    education1 = models.CharField(max_length=255,null=True,blank=True)
    education2 = models.CharField(max_length=255,null=True,blank=True)
    education3 = models.CharField(max_length=255,null=True,blank=True)
    experience1 = models.CharField(max_length=255,null=True,blank=True)
    experience2 = models.CharField(max_length=255,null=True,blank=True)
    experience3 = models.CharField(max_length=255,null=True,blank=True)



    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        if self.profile_pic:
            im = Image.open(self.profile_pic)
            im = im.convert('RGB')
            # create a BytesIO object
            im_io = BytesIO()
            # save image to BytesIO object
            im.save(im_io, 'JPEG', quality=10)

            temp_name = os.path.split(self.profile_pic.name)[1]
            self.profile_pic.save(temp_name, content=ContentFile(im_io.getvalue()), save=False)

            super().save(*args, **kwargs)


class StudentProfile(models.Model):
    def upload_location(instance, filename):
        return "student_images/%s/%s" % (instance.user.username, filename)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to=upload_location, null=True, blank=True,default='student_images/default.png')
    description = models.TextField(null=True,blank=True)

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        if self.profile_pic:
            im = Image.open(self.profile_pic)
            im = im.convert('RGB')
            # create a BytesIO object
            im_io = BytesIO()
            # save image to BytesIO object
            im.save(im_io, 'JPEG', quality=10)

            temp_name = os.path.split(self.profile_pic.name)[1]
            self.profile_pic.save(temp_name, content=ContentFile(im_io.getvalue()), save=False)

            super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def createprofile(sender, instance, created, **kwargs):
    print("///////", created)
    if instance.is_teacher and not instance.is_superuser:
        TeacherProfile.objects.get_or_create(user=instance)
    elif not instance.is_superuser:
        StudentProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def saveprofile(sender, instance, **kwargs):
    print('Saved')
    if instance.is_teacher and not instance.is_superuser:
        instance.teacherprofile.save()
    elif not instance.is_superuser:
        print("status",instance.is_superuser)
        StudentProfile.objects.get_or_create(user=instance)



User = get_user_model()


# Create ModelForm based on the Group model.
class GroupAdminForm(forms.ModelForm):
    class Meta:
        model = Group
        exclude = []

    # Add the users field.
    users = forms.ModelMultipleChoiceField(
         queryset=User.objects.all(),
         required=False,
         # Use the pretty 'filter_horizontal widget'.
         widget=FilteredSelectMultiple('users', False)
    )

    def __init__(self, *args, **kwargs):
        # Do the normal form initialisation.
        super(GroupAdminForm, self).__init__(*args, **kwargs)
        # If it is an existing group (saved objects have a pk).
        if self.instance.pk:
            # Populate the users field with the current Group users.
            self.fields['users'].initial = self.instance.user_set.all()

    def save_m2m(self):
        # Add the users to the Group.
        self.instance.user_set.set(self.cleaned_data['users'])

    def save(self, *args, **kwargs):
        # Default save
        instance = super(GroupAdminForm, self).save()
        # Save many-to-many data
        self.save_m2m()
        return instance



class StaffManager(UserManager):
    def get_queryset(self):
        qs = super().get_queryset()
        a = qs.filter(Q(is_teacher=False, is_staff=False))
        return a



class StaffProxyModel(User):
    objects = StaffManager()
    class Meta:
        proxy = True
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
