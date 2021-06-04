import django_filters
from django.db.models import Q
from ..models import Subject,Course,Enrollment

class SubjectFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='custom_search')
    subtype = django_filters.CharFilter(method='subtype_search')
    clstype = django_filters.CharFilter(method='clstype_search')

    class Meta:
        model = Subject
        fields = ['search']

    def custom_search(self,queryset,name,value):
        return queryset.filter(
            Q(subject_name__icontains=value)
        )

    def clstype_search(self, queryset, name, value):
        return queryset.filter(
            Q(class_type__icontains=value)
        )

    def subtype_search(self, queryset, name, value):
        return queryset.filter(
            Q(subject_type__icontains=value)
        )


class CourseFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='custom_search')

    class Meta:
        model = Course
        fields = ['search']

    def custom_search(self,queryset,name,value):
        return queryset.filter(
            Q(course_name__icontains=value)
        )


class EnrollCourseFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='custom_search')

    class Meta:
        model = Enrollment
        fields = ['search']

    def custom_search(self,queryset,name,value):
        return queryset.filter(
            Q(course__course_name__icontains = value)
        )