# views.py
import jwt
from django.shortcuts import render, redirect
from django.conf import settings
from services.api.client import APIClient
from services.api.view_factory import ViewFactory
import requests


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            return render(request, 'login.html', 
                        {'error': 'Correo electrónico y contraseña son obligatorios'})

        try:
            result = APIClient.login(email, password)

            if result.get("msg"):
                return render(request, 'login.html', {'error': result["msg"]})

            token = result.get('access_token')
            if not token:
                return render(request, 'login.html', {'error': 'No fue posible iniciar sesión. Intente más tarde.'})

            try:
                unverified = jwt.decode(token, options={"verify_signature": False})
                
                # Obtener el rol desde la estructura correcta del token
                user_data = unverified.get('sub', {})
                if isinstance(user_data, dict):
                    user_role = user_data.get('rol')
                else:
                    user_role = None

                # Guardar en sesión
                request.session['user_token'] = token
                request.session['user_role'] = user_role
                
               # Usar la fábrica simplificada
                return ViewFactory.get_renderer(request, user_role)
                
            except Exception as e:
                print(f"Error al iniciar sesión: {str(e)}")
                return render(request, 'login.html', 
                            {'error': 'Error procesando el inicio de sesión'})
                
        except requests.exceptions.RequestException as e:
            print(f"Error de request: {str(e)}")
            return render(request, 'login.html', 
                        {'error': 'Error al conectar con el servidor'})

    return render(request, 'login.html')


def crear_cuenta_view(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')

        # Validaciones básicas
        if not all([nombre, email, password, confirm_password]):
            return render(request, 'crear_cuenta.html', 
                        {'error': 'Todos los campos son obligatorios'})

        if password != confirm_password:
            return render(request, 'crear_cuenta.html', 
                        {'error': 'Las contraseñas no coinciden'})

        # Validación básica de formato de email
        if '@' not in email or '.' not in email:
            return render(request, 'crear_cuenta.html', 
                        {'error': 'Por favor ingrese un correo electrónico válido'})

        try:
            # Asumiendo que APIClient tiene un método register similar al login
            print(nombre, email, password)
            result = APIClient.registro(nombre, email, password)

            if result.get("msg"):
                return render(request, 'crear_cuenta.html', {'error': result["msg"]})

            # Si el registro fue exitoso, iniciar sesión automáticamente
            try:
                login_result = APIClient.login(email, password)
                token = login_result.get('access_token')

                if not token:
                    return render(request, 'login.html', 
                                {'error': 'Cuenta creada exitosamente. Por favor inicie sesión.'})

                # Decodificar el token para obtener información del usuario
                unverified = jwt.decode(token, options={"verify_signature": False})
                
                # Obtener el rol desde la estructura del token
                user_data = unverified.get('sub', {})
                if isinstance(user_data, dict):
                    user_role = user_data.get('rol')
                else:
                    user_role = None

                # Guardar en sesión
                request.session['user_token'] = token
                request.session['user_role'] = user_role
                
                # Usar la fábrica simplificada
                return ViewFactory.get_renderer(request, user_role)

            except Exception as e:
                print(f"Error al iniciar sesión después del registro: {str(e)}")
                return render(request, 'login.html', 
                            {'error': 'Cuenta creada exitosamente. Por favor inicie sesión.'})

        except requests.exceptions.RequestException as e:
            print(f"Error de request: {str(e)}")
            return render(request, 'crear_cuenta.html', 
                        {'error': 'Error al conectar con el servidor'})

    return render(request, 'crear_cuenta.html')

def logout_view(request):
    # Limpiar las variables de sesión
    request.session.pop('user_token', None)
    request.session.pop('user_role', None)
    request.session.flush()  # Limpia toda la sesión
    
    # Redirigir al login
    return redirect('login')



# Opcional: Decorator para proteger vistas según rol
from functools import wraps
from django.http import HttpResponseForbidden

# Ítalo: esta función la podemos utilizar para cuando queremos proteger una vista en base al rol.
# ver el ejemplo de la función de más abajo 'role_required'
def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user_role = request.session.get('user_role')
            if user_role not in allowed_roles:
                return HttpResponseForbidden("No tienes permiso para acceder a esta página")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# Ejemplo de uso del decorator
@role_required(['creador'])
def admin_only_view(request):
    return render(request, 'creador_home.html')


def get_survey(request):
    """
    Método que obtiene las encuestas para un usuario autenticado.

    Esta función verifica si el usuario está autenticado comprobando la presencia
    de un token en la sesión. Si no se encuentra el token, el usuario es redirigido
    a la página de inicio de sesión. Si el token está presente y el método de solicitud es 'GET',
    intenta obtener encuestas utilizando el APIClient. Si ocurre un error durante este proceso,
    se devuelve una lista vacía de encuestas.

    Args:
        request (HttpRequest): El objeto de solicitud HTTP que contiene metadatos sobre la solicitud.

    Returns:
        HttpResponse: Un objeto de respuesta que renderiza la plantilla 'encuestas.html' con las
                      encuestas recuperadas o una lista vacía si ocurrió un error.
    """
    if(request.session.get('user_token') == None):
        return redirect('login')
    
    if request.method == 'GET':
        try:
            encuestas = APIClient.encuestas(request.session.get('user_token'))
        except Exception as e:
            print(f"Error: {e}")
            encuestas= []   
    return render(request, 'encuestas.html', encuestas)
     
        
def votar(request, encuesta_id):
    if(request.session.get('user_token') == None):
        return redirect('login')
    if request.method == 'GET':
        try:
            encuesta_id = int(encuesta_id)
            encuestas_data = APIClient.encuestas(request.session.get('user_token'))
            encuestas = encuestas_data['encuestas']
            encuesta = next((e for e in encuestas if e['id'] == encuesta_id), None)
            
            if encuesta is None:
                encuesta = "No existe encuesta"
        except Exception as e:
            print(f"Error: {e}")
            encuesta = None
        return render(request, 'votar.html', {'encuesta': encuesta})
    
    elif request.method == "POST":
        opcion_id = request.POST.get('opcion')
        try:
            APIClient.votar(request.session.get('user_token'), encuesta_id, opcion_id)
            return redirect ('encuestas')
        except Exception as e:
            print(f"Error: {e}")
            return render(request, 'votar.html', {'mensaje': 'Error al enviar la respuesta'})
        
    return render(request, 'votar.html', {'encuesta': encuesta})

#def resultado_encuestas(request, encuesta_id):
 #   if(request.session.get('user_token') == None):
  #      return redirect('login')
    
   # if
    
    

