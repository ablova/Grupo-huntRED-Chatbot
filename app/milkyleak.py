from mega import Mega
import tweepy
import os
from django.shortcuts import render, get_object_or_404
from .models import MilkyLeak
from .tasks import post_image_task  # Importar la tarea de Celery


# Autenticación con Mega.nz
def authenticate_mega(milky_leak_instance):
    mega = Mega()
    return mega.login(milky_leak_instance.mega_email, milky_leak_instance.mega_password)


# Autenticación con la API de Twitter
def authenticate_twitter(milky_leak_instance):
    auth = tweepy.OAuthHandler(milky_leak_instance.twitter_api_key, milky_leak_instance.twitter_api_secret_key)
    auth.set_access_token(milky_leak_instance.twitter_access_token, milky_leak_instance.twitter_access_token_secret)
    return tweepy.API(auth)


# Función para descargar la imagen desde Mega.nz
def download_image_from_mega(m, milky_leak_instance, image_name):
    folder = m.find(milky_leak_instance.folder_location)
    if folder:
        # Buscar la imagen en la carpeta de Mega.nz
        file = m.find(image_name, folder)
        if file:
            # Descargar la imagen localmente en el servidor
            m.download(file, milky_leak_instance.local_directory)
            return os.path.join(milky_leak_instance.local_directory, image_name)
    return None


# Función para seleccionar la imagen en secuencia usando el contador desde Mega.nz
def get_image_from_mega(milky_leak_instance):
    m = authenticate_mega(milky_leak_instance)
    image_name = f"{milky_leak_instance.image_prefix}{milky_leak_instance.image_counter}.jpg"
    downloaded_image = download_image_from_mega(m, milky_leak_instance, image_name)
    if downloaded_image:
        # Incrementar el contador para la siguiente imagen
        milky_leak_instance.image_counter += 1
        milky_leak_instance.save()  # Guardar el nuevo valor del contador en la base de datos
        return downloaded_image
    return None


# Función para postear una imagen en Twitter
def post_image(milky_leak_instance, image_path, message):
    api = authenticate_twitter(milky_leak_instance)
    try:
        media = api.media_upload(image_path)
        api.update_status(status=message, media_ids=[media.media_id])
        print(f"Posted image {image_path} successfully!")
    except Exception as e:
        print(f"Error posting image: {e}")
    finally:
        # Borrar la imagen descargada después de postearla
        if os.path.exists(image_path):
            os.remove(image_path)


# Obtener los 25 principales followers
def get_top_followers(milky_leak_instance, limit=25):
    api = authenticate_twitter(milky_leak_instance)
    followers = api.followers(count=limit)
    top_followers = []

    for follower in followers:
        top_followers.append({
            'name': follower.name,
            'screen_name': follower.screen_name,
            'followers_count': follower.followers_count
        })

    return sorted(top_followers, key=lambda x: x['followers_count'], reverse=True)


# Obtener las 25 principales cuentas que sigo con más seguidores
def get_top_following(milky_leak_instance, limit=25):
    api = authenticate_twitter(milky_leak_instance)
    following = api.friends(count=limit)
    top_following = []

    for friend in following:
        top_following.append({
            'name': friend.name,
            'screen_name': friend.screen_name,
            'followers_count': friend.followers_count
        })

    return sorted(top_following, key=lambda x: x['followers_count'], reverse=True)


# Vista para la página principal de pruebas y el ejecutor de post
def index(request):
    # Cargar la primera configuración de MilkyLeak (puedes ajustar esto si hay más de una)
    milky_leak_instance = get_object_or_404(MilkyLeak, id=1)  # Cambia el ID si tienes varias instancias

    if request.method == 'POST':
        # Obtener el texto ingresado por el usuario desde el formulario
        post_text = request.POST.get('post_text')

        # Ejecutar la tarea de Celery para postear la imagen usando el modelo MilkyLeak
        post_image_task.delay(milky_leak_instance.id)

        # Redireccionar o mostrar un mensaje de éxito
        return render(request, 'index.html', {
            'milky_leak': milky_leak_instance,
            'success': True,
            'message': f"Post enviado con el texto: {post_text}"
        })

    # Obtener los top 25 followers y las 25 cuentas que sigo con más seguidores
    top_followers = get_top_followers(milky_leak_instance)
    top_following = get_top_following(milky_leak_instance)

    return render(request, 'index.html', {
        'milky_leak': milky_leak_instance,
        'top_followers': top_followers,
        'top_following': top_following
    })
