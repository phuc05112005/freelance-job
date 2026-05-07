from django.shortcuts import render

def error_404_view(request, exception):
    return render(request, 'pages/404.html', status=404)
