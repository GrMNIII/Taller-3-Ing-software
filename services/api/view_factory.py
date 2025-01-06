from django.shortcuts import render

class ViewFactory:
    
    @staticmethod
    def get_renderer(request, role):
        templates = {
            'creador': 'creador_home.html',
            'participante': 'participante_home.html'
        }
        template = templates.get(role, 'login.html')
        return render(request, template)
    
    @staticmethod
    def get_renderer_result(request, role):
        templates = {
            'creador': 'resultados_creador.html',
            'participante': 'resultados_participante.html'
        }
        template = templates.get(role,'login.html') #revisar
        return render(request, template)