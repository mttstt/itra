import markdown
import os
from django.shortcuts import render
from django.conf import settings

def homepage_view(request):
    """
    Vista per la homepage che mostra il contenuto del README.md.
    """
    readme_path = os.path.join(settings.BASE_DIR, '..', 'README.md') # Percorso al README.md
    readme_content = ""
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()
    except FileNotFoundError:
        readme_content = "<h1>Errore: README.md non trovato.</h1><p>Assicurati che il file README.md sia nella directory radice del progetto (itra/).</p>"

    html_content = markdown.markdown(readme_content)
    return render(request, 'homepage/homepage.html', {'readme_html': html_content, 'title': 'ITRA - IT Risk Assessment'})