import hashlib
from cryptography.fernet import Fernet
from datetime import datetime
from aifc import Error

from account.api.filters import StudentFilter
from account.models import User
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, parser_classes
from course.models import Course, Module, Enrollment, Coupon, Subject, ModuleFile, Payment, Zoom, CKEditor5
from account.models import TeacherProfile,StudentProfile
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from account.api.serializer import StudentProfileSerializer
from course.api.serializer import (CourseSerializer,
                                   CourseDetailSerializer,
                                   CourseCreateSerializer,
                                   ModuleSerializer,
                                   CourseEnrollSerializer,
                                   EnrolledCourseSerializer,
                                   MycoursesSerializer,
                                   CouponSerializer,
                                   SubjectSerializer,
                                   SerializerForCourse,
                                   SubjectViewSerializer, ModuleFileSerializer, ZoomSerializer, CKEditor5Serializer)
from rest_framework.generics import( ListAPIView,
                                     RetrieveAPIView,
                                     CreateAPIView,
                                     RetrieveUpdateAPIView,
                                     UpdateAPIView,
                                     ListCreateAPIView)
from rest_framework.permissions import IsAuthenticated
from .filters import SubjectFilter,CourseFilter,EnrollCourseFilter
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page


# Views for Unauthenticated Users

# List all Courses

class ListCourse(ListAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

# course info

class CourseRetrieve(RetrieveAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseDetailSerializer
    permission_classes = (IsAuthenticated,)


# views for authenticated users



# creating courses and modules

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def CreateCourse(request,pk,upk):
    teacher = TeacherProfile.objects.get(user_id=upk)
    subject = Subject.objects.get(id=pk)
    if subject.author.user.id == teacher.user.id:
        course = Course(author=teacher,subject=subject)
        serializer = CourseCreateSerializer(course,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)
    return Response({"message":"you're not authorized to access this Subject"}, status=403)


# updating courses and modules within the course
class UpdateCourse(RetrieveUpdateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseCreateSerializer
    permission_classes = [IsAuthenticated]


# delete course

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def DeleteCourse(request,pk):
    course=Course.objects.get(id=pk)
    course.delete()
    return Response("Course Successfully Deleted")


# get list of courses related to the teacher
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def TeacherCourses(request,upk):
    teacher = TeacherProfile.objects.get(user_id=upk)
    courses = Course.objects.filter(author=teacher).order_by('-id')
    serializer = CourseDetailSerializer(courses,many=True)
    return Response(serializer.data)

# creating a separate module

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def CreateModule(request,pk):
    course = Course.objects.get(id=pk)
    if course.author.user.id == request.user.id:
        module = Module(course=course)
        if request.method == "POST":
            serializer = ModuleSerializer(module, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors,status=500)
    return Response({"message":"you're not authorized"},status=403)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([FormParser, MultiPartParser])
def CreateModuleFile(request,pk):
    module = Module.objects.get(id=pk)
    if module.course.author.user.id == request.user.id:
        try:
            for file in request.FILES.getlist('files'):
                ModuleFile.objects.create(module=module, file=file, file_name=file.name)
            return Response({"message":"successfully uploaded"})
        except Error:
            return Response({"message": "Unable to create the bulk of files"},status=500)
        else:
            return Response({"message": "Unable to create the bulk of files"},status=500)
    return Response({"message":"you're not authorized"},status=403)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def DeleteModuleFile(request,pk):
    file = ModuleFile.objects.get(id=pk)
    file.delete()
    return Response({"message": "Module file Successfully Deleted"})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def GetModuleFiles(request,pk):
    files = ModuleFile.objects.filter(module_id=pk)
    serializer = ModuleFileSerializer(files, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def GetModules(request,pk):
    course = Course.objects.get(id=pk)
    user = User.objects.get(id=request.user.id)
    if user.is_teacher == False:
        e = Enrollment.objects.filter(course=course, student__user=user)
        if not e:
            return Response({"message":"You have not enrolled for this course"}, status=403)
    module = Module.objects.filter(course=course).order_by('id')
    serializer = ModuleSerializer(module, many=True)
    return Response(serializer.data)


# update Module

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def UpdateModule(request,pk):
    module=Module.objects.get(id=pk)
    serializer = ModuleSerializer(instance=module,data=request.data)
    if serializer.is_valid():
        serializer.save()
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def SingleModule(request,pk):
    module = Module.objects.get(id=pk)
    if module.course.author.user.id == request.user.id:
        serializer = ModuleSerializer(module)
        return Response(serializer.data)
    else:
        return Response({"message":"you're unauthorized"},status=403)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def UpdateModuleFile(request,pk):
    modulefile=ModuleFile.objects.get(id=pk)
    serializer = ModuleFileSerializer(instance=modulefile,data=request.data)
    if serializer.is_valid():
        serializer.save()
    return Response(serializer.data)


# Delete Module

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def DeleteModule(request,pk):
    module=Module.objects.get(id=pk)
    module.delete()
    return Response({"message":"Module Successfully Deleted"})


# views for Students

# course Enroll

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def EnrollCourse(request,pk,upk):
    course = Course.objects.get(id=pk)
    student = StudentProfile.objects.get(user_id=upk)
    couponList = Coupon.objects.filter(course=course)
    for c in couponList:
        if str(request.data['coupon_key'])==str(c.coupon_key):
            enroll = Enrollment(course=course,student=student, enroll_key=request.data['coupon_key'])
            condition = c.isValid==True and c.isIssued==True
            if request.method == "POST":
                if condition:
                    e = Enrollment.objects.filter(course=course, student=student).first()
                    if not e:
                        serializer = CourseEnrollSerializer(enroll, data=request.data)
                        if serializer.is_valid():
                            serializer.save()
                            couponSerializer = CouponSerializer(instance=c, data=request.data)
                            if couponSerializer.is_valid():
                                couponSerializer.save(isValid=False)
                            return Response(serializer.data)
                        return Response(serializer.errors,status=403)
                    return Response({"message":"You have already enrolled this course..."},status=403)
                return Response({"message":"Coupon is not valid"},status=403)

    return Response({"message":"coupon is not found"},status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def EnrollCourseByPayment(request,pk,upk):
    course = Course.objects.get(id=pk)
    student = StudentProfile.objects.get(user_id=upk)
    print("before before")
    enrollment = Enrollment.objects.filter(student=student, course=course).first()
    print("before running")
    if not enrollment:
        print("running")
        c = Coupon.objects.create(course=course, coupon_key="", isValid=False, isIssued=True)
        print(c.id)
        serializer = CouponSerializer(instance=c, data=request.data)
        if serializer.is_valid():
            coupon = str(c.id) + ":" + str(c.course.id)
            coupon_key = hashlib.shake_256(coupon.encode()).hexdigest(5)
            serializer.save(coupon_key=coupon_key)
            enroll = Enrollment(course=course, student=student, enroll_key=coupon_key, is_payment=True)
            enroll_serializer = CourseEnrollSerializer(enroll, data=request.data)
            if enroll_serializer.is_valid():
                enroll_serializer.save()
                return Response(enroll_serializer.data)
            return Response(enroll_serializer.errors)
        return Response(serializer.errors)
    else:
        return Response({'message':'You have already enrolled'}, status=403)


# Listing Enrolled Courses
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def MyCourses(request):
    student = StudentProfile.objects.get(user_id=request.user.id)
    courses_enrolled = Enrollment.objects.filter(student=student).order_by('-id')
    filterset = EnrollCourseFilter(request.GET, queryset=courses_enrolled)
    if filterset.is_valid():
        queryset = filterset.qs
        paginator = PageNumberPagination()
        paginator.page_size=5
        result_page = paginator.paginate_queryset(queryset,request)
        serializer = MycoursesSerializer(result_page,many=True)
        return paginator.get_paginated_response(serializer.data)

  # filterset = SubjectFilter(request.GET, queryset=subjects)
  #   if filterset.is_valid():
  #        queryset = filterset.qs
  #   paginator = PageNumberPagination()
  #   paginator.page_size=5
  #   result_page = paginator.paginate_queryset(queryset, request)
  #   serializer = SubjectViewSerializer(result_page, many=True)
  #   return paginator.get_paginated_response(serializer.data)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def MySubjects(request):
    student = StudentProfile.objects.get(user_id=request.user.id)
    courses_enrolled = Enrollment.objects.filter(student=student).order_by('-id')
    subjects = []
    for c in courses_enrolled:
        if c.course.subject not in subjects:
            subjects.append(c.course.subject)
    serializer = SubjectSerializer(subjects,many=True)
    for i in range(len(serializer.data)):
        serializer.data[i]['author']['user'].pop('password')
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def Students(request,pk):
    course = Course.objects.get(id=pk)
    courses_enrolled = Enrollment.objects.filter(course=course).order_by('-id')
    student_ids = []
    for c in courses_enrolled:
        if c.student.id not in student_ids:
            student_ids.append(c.student.id)
    students = StudentProfile.objects.filter(id__in=student_ids)
    filterset = StudentFilter(request.GET, queryset=students)
    if filterset.is_valid():
        queryset = filterset.qs
        paginator = PageNumberPagination()
        paginator.page_size = 10
        result_page = paginator.paginate_queryset(queryset, request)
        serializer = StudentProfileSerializer(result_page,many=True)
        for i in range(len(serializer.data)):
            serializer.data[i]['user'].pop('password')
        return paginator.get_paginated_response(serializer.data)
    return Response({"message": "not found"}, status=404)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def Students_report(request,pk):
    course = Course.objects.get(id=pk)
    courses_enrolled = Enrollment.objects.filter(course=course).order_by('-id')
    student_ids = []
    for c in courses_enrolled:
        if c.student.id not in student_ids:
            student_ids.append(c.student.id)
    students = StudentProfile.objects.filter(id__in=student_ids)
    # filterset = StudentFilter(request.GET, queryset=students)
    # if filterset.is_valid():
    #     queryset = filterset.qs
    #     paginator = PageNumberPagination()
    #     paginator.page_size = 10
    #     result_page = paginator.paginate_queryset(queryset, request)
    serializer = StudentProfileSerializer(students,many=True)
    for i in range(len(serializer.data)):
        serializer.data[i]['user'].pop('password')
    return Response(serializer.data)
    # return Response({"message": "not found"}, status=404)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def DashboardDetails(request):
    teacher = TeacherProfile.objects.get(user_id=request.user.id)
    courses_enrolled = Enrollment.objects.filter(course__author=teacher).order_by('-id')
    students = []
    for c in courses_enrolled:
        if c.student not in students:
            students.append(c.student)
    subjects = Subject.objects.filter(author__user=request.user).count()
    courses = Course.objects.filter(author__user=request.user).count()
    details = {
        'student_count': len(students),
        'subject-count' : subjects,
        'course-count' : courses
    }
    return Response(details, status=200)


# accessing enrolled courses
class ViewEnrolledCourse(RetrieveAPIView):
    serializer_class = (EnrolledCourseSerializer)
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated]



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def CouponGenerator(request, count, pk):
    course = Course.objects.filter(id=pk).first()
    try:
        Coupon.objects.bulk_create(
            [
                Coupon(course=course, coupon_key="")
                for __ in range(count)
            ]
        )
        couponL = Coupon.objects.filter(coupon_key="")
        for c in list(couponL):
            serializer = CouponSerializer(instance=c, data=request.data)
            if serializer.is_valid():
                coupon = str(c.id) + ":" + str(c.course.id)
                coupon_key = hashlib.shake_256(coupon.encode()).hexdigest(5)
                serializer.save(coupon_key=coupon_key)
        return Response({"message":"successfully created"})
    except Error:
        return  Response({"message":"Unable to create the bulk of coupons"})
    else:
        return Response({"message":"Something went wrong"})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def AvailableCoupon(request, pk):
    course = Course.objects.get(id=pk)
    couponList = Coupon.objects.filter(isValid=True, isIssued=False, course=course )
    # for i in range(len(couponList)):
    #     coupon = str(couponList[i].id)+":"+str(couponList[i].course.id)
    #     couponList[i].coupon_key = hashlib.shake_256(coupon.encode()).hexdigest(5)

    serializer = CouponSerializer(couponList, many=True)
    return Response(serializer.data)

# Issued Coupons
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def IssuedCoupon(request, pk):
    course = Course.objects.get(id=pk)
    couponList = Coupon.objects.filter(isValid=True, isIssued=True, course=course )
    serializer = CouponSerializer(couponList, many=True)
    return Response(serializer.data)




# issue coupons
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def IssueCoupon(request):
    for i in range(len(request.data['issued_coupons'])):
        coupon = Coupon.objects.get(id=request.data['issued_coupons'][i])
        serializer = CouponSerializer(instance=coupon,data=request.data)
        if serializer.is_valid():
            serializer.save(isIssued=True)
    return Response({"message":"successfully issued"})

# create subject

@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def CreateSubject(request,pk):
    author = TeacherProfile.objects.get(user_id=pk)
    serializer = SubjectSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(author=author)
    return Response(serializer.data)

# view subject

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ViewSubject(request,pk):
    subject = Subject.objects.get(id=pk)
    if subject.author.user.id == request.user.id:
        serializer = SubjectSerializer(subject)
        return Response(serializer.data)
    else:
        return Response({"message":"you're unauthorized"},status=403)

#view subject in student side
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ViewSubjectStudent(request,pk):
    subject = Subject.objects.get(id=pk)
    serializer = SubjectSerializer(subject)
    return Response(serializer.data)


# update subject

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def UpdateSubject(request,pk):
    subject = Subject.objects.get(id=pk)
    serializer = SubjectSerializer(instance=subject, data=request.data)
    if serializer.is_valid():
        serializer.save()
    return Response(serializer.data)

# delete subject

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def DeleteSubject(request,pk):
    subject = Subject.objects.get(id=pk)
    subject.delete()
    return Response("Subject Successfully Deleted")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def SubjectList(request):
    subjects = Subject.objects.all().order_by('-id')
    filterset = SubjectFilter(request.GET, queryset=subjects)
    if filterset.is_valid():
         queryset = filterset.qs
    paginator = PageNumberPagination()
    paginator.page_size=5
    result_page = paginator.paginate_queryset(queryset, request)
    serializer = SubjectViewSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)



# subject list of teacher

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def TeacherSubject(request):
    teacher = TeacherProfile.objects.get(user_id=request.user.id)
    subject = Subject.objects.filter(author=teacher).order_by('-id')
    print(subject)
    filterset = SubjectFilter(request.GET,queryset=subject)
    if filterset.is_valid():
         queryset = filterset.qs
    paginator = PageNumberPagination()
    paginator.page_size = 5
    result_page = paginator.paginate_queryset(queryset, request)
    serializer = SubjectSerializer(result_page ,many=True)
    for i in range(len(serializer.data)):
        serializer.data[i]['author']['user'].pop('password')
    return paginator.get_paginated_response(serializer.data)

@api_view(['GET'])
def coursecount(request):
    courses = Course.objects.count()
    print(request.user)
    return Response({'count':courses})

@api_view(['GET'])
def studentcount(request):
    students = StudentProfile.objects.count()
    print(request.user)
    return Response({'count':students})

@api_view(['GET'])
def teachercount(request):
    teachers = TeacherProfile.objects.count()
    print(request.user)
    return Response({'count':teachers})


# courses inside a subject

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def CoursesIntheSubject(request,pk):
    subject = Subject.objects.get(id=pk)
    courses = Course.objects.filter(subject=subject).order_by('-id')
    filterset = CourseFilter(request.GET, queryset=courses)
    if filterset.is_valid():
        queryset = filterset.qs
    paginator = PageNumberPagination()
    paginator.page_size = 5
    result_page = paginator.paginate_queryset(queryset, request)
    serializer = SerializerForCourse(result_page, many=True)
    i = 0
    for d in serializer.data:
        e = Enrollment.objects.filter(course__id=d['id'], student__user=request.user)
        if e:
            serializer.data[i]['is_enrolled'] = True
        i = i+1

    return paginator.get_paginated_response(serializer.data)
    # serializer = SerializerForCourse(courses, many=True)
    # return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def MyCoursesInTheSubject(request,pk):
    subject = Subject.objects.get(id=pk)
    student = StudentProfile.objects.get(user=request.user)
    enrollments = Enrollment.objects.filter(student=student, course__subject=subject)
    filterset = EnrollCourseFilter(request.GET, queryset=enrollments)
    if filterset.is_valid():
        queryset = filterset.qs
        paginator = PageNumberPagination()
        paginator.page_size = 10
        result_page = paginator.paginate_queryset(queryset, request)
        serializer = MycoursesSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def SavePayments(request):
    student = StudentProfile.objects.get(user=request.user)
    course = Course.objects.get(id=request.data['order_id'])
    amount = request.data['amount']
    p = Payment.objects.create(student=student, course=course, amount=amount)
    return Response({"message":"Saved successfully"})

@api_view(['GET'])
def Statistics(request):
    student_count = StudentProfile.objects.count()
    teacher_count = TeacherProfile.objects.count()
    subject_count = Subject.objects.count()
    course_count = Course.objects.count()
    counts = {
        "students" : student_count,
        "teachers" : teacher_count,
        "subjects" : subject_count,
        "courses" : course_count
    }
    return Response(counts, 200)


@api_view(['GET'])
def LatestSubjects(request):
    subjects = Subject.objects.order_by("-id")[:3]
    serializer = SubjectSerializer(subjects,many=True)
    for i in range(len(serializer.data)):
        serializer.data[i]['author']['user'].pop('password')
    return Response(serializer.data)

# Subjects for index page

@api_view(['GET'])
def SubjectListIndex(request):
    subjects = Subject.objects.all()
    paginator = PageNumberPagination()
    paginator.page_size = 10
    result_page = paginator.paginate_queryset(subjects, request)
    serializer = SubjectSerializer(result_page, many=True)
    for i in range(len(serializer.data)):
        serializer.data[i]['author']['user'].pop('password')
    return paginator.get_paginated_response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def TeacherStat(request):
    subjects = Subject.objects.filter(author__user=request.user).count()
    courses = Course.objects.filter(author__user=request.user).count()
    students =[]
    enrollments = Enrollment.objects.filter(course__author__user=request.user)
    for e in enrollments:
        if e.student not in students:
            students.append(e.student)
    data = {
        'students'  :   len(students),
        'courses'   :   courses,
        'subjects'  :   subjects
    }
    return Response(data, status=200)



@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def Unenroll(request, sid, cid):
    student = StudentProfile.objects.get(id=sid)
    course = Course.objects.get(id=cid)
    enrollment = Enrollment.objects.filter(course=course, student=student).first()
    if enrollment:
        enrollment.delete()
        return Response({'message' : 'Unenrolled successfully'}, status=200)
    else:
        return Response({'message': 'Enrollment not found'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def EnrollCourseByTeacher(request,pk):
    course = Course.objects.get(id=pk)
    res = []
    for username in request.data['students']:
        student = StudentProfile.objects.filter(user__username=username).first()
        if student:
            e = Enrollment.objects.filter(course=course, student=student).first()
            if not e:
                enroll = Enrollment(course=course, student=student, enroll_key="Enrolled by teacher")
                serializer = CourseEnrollSerializer(enroll, data= request.data)
                if serializer.is_valid():
                    serializer.save()
                    res.append({
                        "username" : student.user.username,
                        "email" : student.user.email,
                        "status" : "enrolled successfully",
                        "success": True
                    })
                else:
                    res.append({
                        "username": student.user.username,
                        "email": student.user.email,
                        "status": "something is wrong",
                        "success": False
                    })
            else:
                res.append({
                    "username": student.user.username,
                    "email": student.user.email,
                    "status": "already enrolled for this course",
                    "success": False
                })
        else:
            res.append({
                "username": username,
                "email": "",
                "status": "student not found",
                "success": False
            })

    return Response(res, status=200)


#free enroll
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def FreeEnroll(request,cid,sid):
    course = Course.objects.get(id=cid)
    student = StudentProfile.objects.get(user_id=sid)
    enrollment = Enrollment.objects.filter(student=student, course=course).first()
    if not enrollment:
        enroll = Enrollment(course=course, student=student, enroll_key="Free")
        enroll_serializer = CourseEnrollSerializer(enroll, data=request.data)
        if enroll_serializer.is_valid():
            enroll_serializer.save()
            return Response(enroll_serializer.data)
        return Response(enroll_serializer.errors)
    else:
        return Response({'message': 'You have already enrolled'}, status=403)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def CreateZoomModule(request,pk):
    course = Course.objects.get(id=pk)
    if course.author.user.id == request.user.id:
        module = Module(course=course)
        if request.method == "POST":
            serializer = ModuleSerializer(module, data=request.data)
            if serializer.is_valid():
                serializer.save(is_meeting=True)
                return Response(serializer.data)
            return Response(serializer.errors,status=500)
    return Response({"message":"you're not authorized"},status=403)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def CreateZoomMeeting(request,pk):
    module = Module.objects.get(id=pk)
    zoom = Zoom(module=module)
    if module.course.author.user.id == request.user.id:
        serializer = ZoomSerializer(zoom, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response({"message":"Zoom meeting was not created"})
    return Response({"message":"you're not authorized"},status=403)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def UpdateZoomMeeting(request,pk):
    meeting = Zoom.objects.get(id=pk)
    module = Module.objects.get(id=meeting.module.id)
    serializer = ZoomSerializer(instance=meeting, data=request.data)
    module_serializer = ModuleSerializer(instance=module, data=request.data)
    if module_serializer.is_valid():
        module_serializer.save(is_meeting=True)
    if serializer.is_valid():
        serializer.save()
    return Response(serializer.data)



@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def DeleteZoomMeeting(request,pk):
    meeting = Zoom.objects.get(id=pk)
    module = Module.objects.get(id=meeting.module.id)
    meeting.delete()
    module.delete()
    return Response("Meeting Successfully Deleted")

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def GetZoomMeeting(request,pk):
    meeting = Zoom.objects.get(module_id=pk)
    serializer = ZoomSerializer(meeting)
    return Response(serializer.data)


@api_view(['POST'])
def Upload(request):
    ck = CKEditor5.objects.create(upload=request.FILES['upload'])
    cks = CKEditor5Serializer(ck)
    return Response({
        "uploaded": True,
        "url": cks.data['upload']
    })


@api_view(['GET'])
def freesubjects(request):
    subjects = Subject.objects.filter(subject_type="free")
    serializer = SubjectViewSerializer(subjects,many=True)
    return Response(serializer.data,status=200)
