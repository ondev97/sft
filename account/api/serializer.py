from rest_auth.serializers import TokenSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import TeacherProfile,StudentProfile

User = get_user_model()

class UserSerializerAPI(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username','email','password','first_name','last_name','phone_no','address','parent_number','district',"telegram_number"]
        extra_kwargs = {"password":{"write_only":True}}

        # def create(self,validated_data):
        #     username = validated_data['username']
        #     email = validated_data['email']
        #     password = validated_data['password']
        #     user_obj = User(
        #         username = username,
        #         email = email
        #     )
        #     user_obj.set_password(password)
        #     user_obj.save()
        #     return user_obj
        # def create(self,validated_data):
        #     user = User.objects.create(
        #         email = validated_data['email'],
        #         username = validated_data['username'],
        #         password = make_password(validated_data['password'])
        #     )
        #
        #     user.save()
        #     return user
        #


class UserTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'email','is_teacher')


class CustomTokenSerializer(TokenSerializer):
    user = UserTokenSerializer(read_only=True)

    class Meta(TokenSerializer.Meta):
        fields = ('key', 'user')


#
# class TeacherProfileSerializer(serializers.ModelSerializer):
#     user = UserSerializerAPI(many=True)
#     class Meta:
#         fields = ['id','profile_pic','description','education1','education2','education3','experience1','experience2','experience3','user']
#         model = TeacherProfile
#         depth = 1


class TeacherProfileSerializer(serializers.ModelSerializer):

    class Meta:
        fields = "__all__"
        model = TeacherProfile
        depth = 1

class StudentProfileSerializer(serializers.ModelSerializer):

    class Meta:
        fields = "__all__"
        model = StudentProfile
        depth = 1


