from django.shortcuts import render
import markdown

def about_view(request):
    with open('ABOUT.md', 'r') as f:
        content = f.read()
    html_content = markdown.markdown(content)
    return render(request, 'pages/about.html', {'content': html_content})

def help_center_view(request):
    with open('HELP_CENTER.md', 'r') as f:
        content = f.read()
    html_content = markdown.markdown(content)
    return render(request, 'pages/help_center.html', {'content': html_content})

def privacy_policy_view(request):
    with open('PRIVACY_POLICY.md', 'r') as f:
        content = f.read()
    html_content = markdown.markdown(content)
    return render(request, 'pages/privacy_policy.html', {'content': html_content})

def terms_of_service_view(request):
    with open('TERMS_OF_SERVICE.md', 'r') as f:
        content = f.read()
    html_content = markdown.markdown(content)
    return render(request, 'pages/terms_of_service.html', {'content': html_content})