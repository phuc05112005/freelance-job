from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer
from .models import CV, KINHNGHIEM, HocVan

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        return redirect('/accounts/register/')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {'token': token.key, 'user': UserSerializer(user, context={'request': request}).data},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return redirect('/accounts/login/')

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user': UserSerializer(user, context={'request': request}).data})


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user, context={'request': request}).data)

@login_required
def Tao_CV(request):
    if request.method == "POST":
        cv_new = CV.objects.create(
            user = request.user,
            tieude = request.POST.get('tieude'),
            hoten = request.POST.get('hoten'),
            gioitinh = request.POST.get('gioitinh'),
            ngaysinh = request.POST.get('ngaysinh'),
            avatar = request.FILES.get('avatar'),
            email = request.POST.get('email'),
            sdt = request.POST.get('sdt'),
            diachi =  request.POST.get('diachi'),
            muctieu = request.POST.get('muctieu'),
            kynang = request.POST.get('kynang'),
        )
        kn_congty = request.POST.getlist('kn_congty[]')
        kn_vitri = request.POST.getlist('kn_vitri[]')
        kn_batdat = request.POST.getlist('kn_batdau[]')
        kn_kethuc = request.POST.getlist('kn_kethuc[]')
        kn_mota = request.POST.getlist('kn_mota[]')
        hv_truong = request.POST.getlist('hv_truong[]')
        hv_nganh = request.POST.getlist('hv_nganh[]')
        hv_batdau = request.POST.getlist('hv_batdau[]')
        hv_kethuc = request.POST.getlist('hv_kethuc[]')
        for i in range(len(kn_congty)):
            KINHNGHIEM.objects.create(
                cv = cv_new,
                congty = kn_congty[i],
                vitri = kn_vitri[i],
                batdau = kn_batdat[i],
                ketthuc = kn_kethuc[i],
                mota = kn_mota[i]
            )
        
        for i in range(len(hv_truong)):
            HocVan.objects.create(
                cv = cv_new,
                truong = hv_truong[i],
                nganh = hv_nganh[i],
                batdau = hv_batdau[i],
                ketthuc = hv_kethuc[i]
            )
        return redirect('quanlycv')
    return render(request, 'CV/taocv.html')

@login_required
def quanlycv(request):
    cv_list = CV.objects.filter(user=request.user)
    context = {'cv_list': cv_list}
    return render(request, 'CV/quanly.html', context)

@login_required
def xoacv(request, cv_id):
    cv = get_object_or_404(CV, id=cv_id, user=request.user)
    if request.method == 'POST':
        cv.delete()
    return redirect('quanlycv')

@login_required
def suacv(request, cv_id):
    cv_new = CV.objects.get(id = cv_id, user = request.user)
    kinhnghiem = KINHNGHIEM.objects.filter(cv = cv_new)
    hocvan = HocVan.objects.filter(cv = cv_new)
    if request.method == 'POST':
        cv_new.hoten = request.POST.get('hoten')
        cv_new.gioitinh = request.POST.get('gioitinh')
        cv_new.ngaysinh = request.POST.get('ngaysinh')
        cv_new.tieude = request.POST.get('tieude')
        cv_new.email = request.POST.get('email')
        cv_new.sdt = request.POST.get('sdt')
        cv_new.diachi = request.POST.get('diachi')
        cv_new.muctieu = request.POST.get('muctieu')
        cv_new.kynang = request.POST.get('kynang')
        if request.POST.get('delete_avatar') == 'true':
            cv_new.avatar.delete(save=False)
            cv_new.avatar = None
        if request.FILES.get('avatar'):
            cv_new.avatar = request.FILES.get('avatar')

        KINHNGHIEM.objects.filter(cv = cv_new).delete()
        kn_congty = request.POST.getlist('kn_congty[]')
        kn_vitri = request.POST.getlist('kn_vitri[]')
        kn_batdat = request.POST.getlist('kn_batdau[]')
        kn_kethuc = request.POST.getlist('kn_kethuc[]')
        kn_mota = request.POST.getlist('kn_mota[]')
        for i in range(len(kn_congty)):
            KINHNGHIEM.objects.create(
                cv = cv_new,
                congty = kn_congty[i],
                vitri = kn_vitri[i],
                batdau = kn_batdat[i],
                ketthuc = kn_kethuc[i],
                mota = kn_mota[i]
            )

        HocVan.objects.filter(cv = cv_new).delete()
        hv_truong = request.POST.getlist('hv_truong[]')
        hv_nganh = request.POST.getlist('hv_nganh[]')
        hv_batdau = request.POST.getlist('hv_batdau[]')
        hv_kethuc = request.POST.getlist('hv_kethuc[]')
        for i in range(len(hv_truong)):
            HocVan.objects.create(
                cv = cv_new,
                truong = hv_truong[i],
                nganh = hv_nganh[i],
                batdau = hv_batdau[i],
                ketthuc = hv_kethuc[i]
            )
        cv_new.save()
        return redirect('quanlycv')
    
    context = {'cv':cv_new, 'kinhnghiem':kinhnghiem, 'hocvan':hocvan}
    return render(request, 'CV/suacv.html', context)

@login_required
def chitietcv(request, cv_id):
    cv = get_object_or_404(CV, id = cv_id)
    kinhnghiem = KINHNGHIEM.objects.filter(cv= cv)
    hocvan = HocVan.objects.filter(cv=cv)
    context = {'cv':cv, 'kinhnghiem':kinhnghiem, 'hocvan':hocvan}
    return render(request, 'CV/chitietcv.html', context)
