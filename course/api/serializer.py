from rest_framework import serializers
from course.models import Course, Module, Enrollment, Coupon, Subject, ModuleFile, Zoom, CKEditor5
from account.models import TeacherProfile



# Serializers for Unauthenticated users


# List all courses

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id','course_cover','course_description','course_name','is_freeze']


# More info about courses


class CourseDetailSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id','course_name','author','course_cover','course_description','subject','created_at','price','duration','is_freeze']

    def get_author(self, obj):
        return str(obj.author.user.username)

# serializer for authenticated users

# serializer for courses inside subject

class SerializerForCourse(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ["id","course_name","course_description","course_cover","created_at","price","duration","author", "is_enrolled","is_freeze"]
        depth = 2

    def get_author(self, obj):
        return str(obj.author.user.username)



# Serializer setup for Creating course and adding modules
class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = "__all__"
#
class ModuleFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleFile
        fields = "__all__"


# serializer for course Enrollment
class CourseEnrollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = "__all__"
        # depth =2

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = "__all__"

class MycoursesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Enrollment
        fields = ['id','course','enroll_key','student','is_payment']
        depth = 1




class CourseCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Course
        fields = ['course_name','id','course_description','created_at','course_cover','subject','price','duration','is_freeze']
        depth = 3

    # def create(self, validated_data):
    #     module_data = validated_data.pop('modules')
    #     course = Course.objects.create(**validated_data)
    #     for module_data in module_data:
    #         Module.objects.create(course=course, **module_data)
    #     return course
    #
    # def update(self,instance,validated_data):
    #     module_data = validated_data.pop('modules')
    #     course = (instance.modules).all()
    #     course = list(course)
    #     print(course)
    #     instance.course_name = validated_data.get('course_name',instance.course_name)
    #     instance.course_description = validated_data.get('course_description',instance.course_description)
    #     instance.save()
    #
    #     for module_data in module_data:
    #         module = course.pop(0)
    #         module.module_name = module_data.get('module_name',module.module_name)
    #         module.module_content = module_data.get('module_content',module.module_content)
    #         module.save()
    #     return instance

class EnrolledCourseSerializer(serializers.ModelSerializer):
    #modules=ModuleSerializer(many=True)

    class Meta:
        model = Course
        fields = "__all__"

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'

        depth = 2

class SubjectViewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subject
        fields = ['id','subject_name','subject_cover','subject_type','class_type','author','short_description','created_at']

        depth = 2

class ZoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zoom
        fields = "__all__"

        depth = 1


class CKEditor5Serializer(serializers.ModelSerializer):
    class Meta:
        model = CKEditor5
        fields = "__all__"
