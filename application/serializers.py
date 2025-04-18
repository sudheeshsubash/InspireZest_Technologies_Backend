from rest_framework import serializers
from mainapp.models import User, Task, Leaves
from mainapp.utils.serializers import DynamicFieldsBaseModelSerializer


"""
DynamicFieldsBaseModelSerializer is a custom subclass of Django REST Framework's ModelSerializer that allows you to dynamically control
which fields are included, excluded, or made read-only at runtime. When initializing the serializer
"""

class UserSerializer(DynamicFieldsBaseModelSerializer):
    class Meta:
        model = User
        fields = ['username','email','password','salary','OTP','is_verified','role']
        extra_kwargs = {
            'email': {'required': True},
        }
        
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class TaskSerializer(DynamicFieldsBaseModelSerializer):
    class Meta:
        model = Task
        fields = ['title','description','deadline','priority','user','status']



class LeavesSerializer(DynamicFieldsBaseModelSerializer):
    class Meta:
        model = Leaves
        fields = ['user','leave_type','start_date','end_date','reason','status']

