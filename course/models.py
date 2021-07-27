from django.db import models
from account.models import TeacherProfile, StudentProfile
from django.utils.timezone import now
from io import BytesIO
from PIL import Image
import os
from django.core.files.base import ContentFile
from .compress import compress


class Subject(models.Model):
    def upload_location(instance, filename):
        return "subject_images/%s/%s" % (instance.subject_name, filename)

    subject_name = models.CharField(max_length=200, null=True)
    subject_cover = models.ImageField(null=True, blank=True, upload_to=upload_location,
                                      default="subject_images/default.png")
    description = models.CharField(max_length=500, null=True, blank=True)
    author = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, null=True, default=None)
    subject_type = models.CharField(max_length=255, null=True, blank=True)
    class_type = models.CharField(max_length=255, null=True, blank=True)
    short_description = models.CharField(max_length=300, blank=True, null=True)
    created_at = models.DateTimeField(default=now)

    def save(self, *args, **kwargs):
        if self.subject_cover:
            im = Image.open(self.subject_cover)
            im = im.convert('RGB')
            # create a BytesIO object
            im_io = BytesIO()
            # save image to BytesIO object
            im.save(im_io, 'JPEG', quality=30)

            temp_name = os.path.split(self.subject_cover.name)[1]
            self.subject_cover.save(temp_name, content=ContentFile(im_io.getvalue()), save=False)

            super().save(*args, **kwargs)

    def __str__(self):
        return self.subject_name


class Course(models.Model):
    def upload_location(instance, filename):
        return "course_images/%s/%s" % (instance.course_name, filename)

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, default=None)
    course_name = models.CharField(max_length=300, default=None)
    author = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, null=True, default=None)
    course_description = models.TextField(null=True)
    course_cover = models.ImageField(null=True, blank=True, upload_to=upload_location,
                                     default="course_images/default.png")
    created_at = models.DateTimeField(default=now)
    price = models.IntegerField(default=0, null=True, blank=True)
    duration = models.CharField(max_length=20, null=True, blank=True)
    is_enrolled = models.BooleanField(default=False)
    is_freeze = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.course_cover:
            im = Image.open(self.course_cover)
            im = im.convert('RGB')
            # create a BytesIO object
            im_io = BytesIO()
            # save image to BytesIO object
            im.save(im_io, 'JPEG', quality=30)

            temp_name = os.path.split(self.course_cover.name)[1]
            self.course_cover.save(temp_name, content=ContentFile(im_io.getvalue()), save=False)

            super().save(*args, **kwargs)

    def __str__(self):
        return self.course_name


class Module(models.Model):
    def upload_location(instance, filename):
        return "course_files/%s/%s" % (instance.course.course_name, filename)

    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, related_name='modules')
    module_name = models.CharField(max_length=100)
    module_content = models.TextField(null=True, blank=True)
    is_meeting = models.BooleanField(default=False)

    def __str__(self):
        return self.module_name + "" + " " + self.course.course_name


class ModuleFile(models.Model):
    def upload_location(instance, filename):
        return "course_files/%s/%s" % (instance.module.course.course_name, filename)

    file_name = models.CharField(max_length=300, blank=True, null=True)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, null=True, blank=True)
    file = models.FileField(null=True, upload_to=upload_location)

    def __str__(self):
        return self.module.module_name + " " + str(self.id)


class Enrollment(models.Model):
    enroll_key = models.CharField(max_length=100, default="Text here", null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, related_name='enrollment')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, null=True)
    is_payment = models.BooleanField(default=False)

    def __str__(self):
        return self.course.course_name


class Coupon(models.Model):
    coupon_key = models.CharField(max_length=100, null=True)
    isValid = models.BooleanField(default=True)
    isIssued = models.BooleanField(default=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.coupon_key + "  issued: " + str(self.isIssued)


class Payment(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.FloatField(default=0)
    date = models.DateTimeField(default=now)

    def __str__(self):
        return str(self.amount)


class Zoom(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, null=True, blank=True)
    meeting_name = models.CharField(max_length=600, null=True, blank=True)
    email = models.EmailField()
    meeting_id = models.CharField(max_length=600, blank=True, null=True)
    passcode = models.CharField(max_length=600, blank=True, null=True)
    date = models.CharField(max_length=300, null=True, blank=True)

    def __str__(self):
        return str(self.meeting_name)


class CKEditor5(models.Model):
    def upload_location(instance, filename):
        return "ckeditor_images/%s" % (filename)

    upload = models.ImageField(null=True, blank=True, upload_to=upload_location)
