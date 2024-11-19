import random
import logging
import time
import os
from io import BytesIO
from django.shortcuts import render, get_object_or_404
from .models import MilkyLeak
from .tasks import post_image_task  # Importar de Celery para manejar tareas asincrónicas
#from mega import Mega
import dropbox  # Añadido para manejar la API de Dropbox
import tweepy


# Configurar el logger
logger = logging.getLogger('milkyleak')

# Lista de frases aleatorias
PHRASES = [
    "Siguenos también en Instagram @MilkyLeak",
    "La belleza en lo erótico es infinita.",
    "El arte de lo sensual.",
    "La magia del cuerpo femenino en cada toma.",
    "Sutil, pero ...",
    "La perfección no está en lo que se ve, sino en lo que se siente.",
    "Erotismo es poesía visual.",
    "Explorando el lado más íntimo de la fotografía.",
    "Cada imagen cuenta una historia más profunda.",
    "La piel es el lienzo de nuestros deseos.",
    "La fotografía revela más que solo luz.",
    "Atrévete a ver más allá de lo evidente.",
    "El arte erótico es un viaje visual.",
    "La sensualidad es un arte.",
    "Desnudando el alma a través del lente.",
    "Lo sutil es lo que más impacta.",
    "#MilkyLeak - What a look!!",
    "Inspiration for today!", 
    "Another beautiful creation!", 
    "Tech and creativity combined.", 
    "Let the innovation flow.", 
    "A masterpiece worth sharing.", 
    "Hope this brightens your day!", 
    "What do you think of this?", 
    "Here’s something cool for you!", 
    "Art and code together.", 
    "Creativity knows no bounds!", 
    "Keep pushing boundaries.", 
    "Sharing some positivity.", 
    "Exploring new frontiers!", 
    "This one’s for all the dreamers.", 
    "Hope this inspires you!",
]

# Lista de hashtags populares
HASHTAGS = [
    "#MilkyLeak", "#ArtErotico", "#FotografiaErotica", "#SensualArt", "#NSFW", 
    "#EroticPhotography", "#FineArtNude", "#Boudoir", "#Sensual", "#NudeArt", 
    "#BodyPositivity", "#ArtisticNudes", "#EroticArt", "#Nudes", "#BoudoirPhotography"
]

MENTIONS = [
    "@RachelCook", "#ArtErotico", "#FotografiaErotica", "#SensualArt", "#NSFW", 
    "#EroticPhotography", "#FineArtNude", "#Boudoir", "#Sensual", "#NudeArt", 
    "#BodyPositivity", "#ArtisticNudes", "#EroticArt", "#Nudes", "#BoudoirPhotography",
    "@MiaMalkova", "@RileyReidx3", "@SashaGrey", "@Abella_Danger", "@Brandi_Love",
    "@EvaLovia", "@MiaKhalifa", "@TheAngelaWhite", "@Romi_Rain", "@TeannaTrump",
    "@JoannaAngel", "@LisaAnn", "@NicoleAniston", "@SunnyLeone", "@ToriBlack",
    "@LexiBelle", "@DillionHarper", "@MaddyOReillyxxx", "@SophieDee", "@ItsAbigailMac",
    "@LenaThePlug", "@TanaMongeau", "@BellaThorne", "@BlacChyna", "@CardiB",
    "@TrishaPaytas", "@OnlyFans", "@Amouranth", "@ItsTHELUCYPURR", "@ItsDaniDaniels",
    "@SophiaDiamond", "@SophieDee", "@RachelC00k", "@JemWolfie", "@MissRileyReid",
    "@AmberRose", "@KenzieTaylorXXX", "@EvaElfie", "@Brandi_Love", "@ItsLucyTyler",
    "@EvaLovia", "@MiaKhalifa", "@LenaThePlug", "@RileyReidx3", "@SashaGrey",
    "@TheAngelaWhite", "@Romi_Rain", "@DillionHarper", "@JoannaAngel", "@SophieDee",
    "@MaddyOReillyxxx", "@LisaAnn", "@ToriBlack", "@LexiBelle", "@NicoleAniston",
    "@SunnyLeone", "@Brandi_Love", "@TeannaTrump", "@Abella_Danger", "@ItsAbigailMac",
    "@glamour_nudes", "@theeroticarts", "@eroticarthub", "@eroticartists", "@BoudoirArt", 
    "@FineArtNudes", "@NudePhotography", "@sensual_photos", "@ArtErotique", "@BodyPositivityArt",
]


# Autenticación con la API de Twitter
def authenticate_twitter(milky_leak_instance):
    auth = tweepy.OAuthHandler(milky_leak_instance.twitter_api_key, milky_leak_instance.twitter_api_secret_key)
    auth.set_access_token(milky_leak_instance.twitter_access_token, milky_leak_instance.twitter_access_token_secret)
    try:
        api = tweepy.API(auth)
        api.verify_credentials()
        return api
    except Exception as e:
        logger.error(f"Error autenticando en Twitter: {e}")
        return None

# Verificar conexión con Twitter
def check_twitter_connection(milky_leak_instance):
    try:
        auth = tweepy.OAuthHandler(milky_leak_instance.twitter_api_key, milky_leak_instance.twitter_api_secret_key)
        auth.set_access_token(milky_leak_instance.twitter_access_token, milky_leak_instance.twitter_access_token_secret)
        api = tweepy.API(auth)
        api.verify_credentials()
        return True
    except Exception as e:
        logger.error(f"Error al conectar con Twitter: {e}")
        return False

# Autenticación con Mega.nz
def authenticate_mega(milky_leak_instance):
    mega = Mega()
    try:
        session = mega.login(milky_leak_instance.mega_email, milky_leak_instance.mega_password)
        return session
    except Exception as e:
        logger.error(f"Error autenticando en Mega.nz: {e}")
        return None

# Verificar conexión con Mega.nz
def check_mega_connection(milky_leak_instance):
    try:
        mega = Mega()
        m = mega.login(milky_leak_instance.mega_email, milky_leak_instance.mega_password)
        return True if m else False
    except Exception as e:
        logger.error(f"Error al conectar con Mega.nz: {e}")
        return False

# Autenticación con Dropbox
def authenticate_dropbox(milky_leak_instance):
    if not milky_leak_instance.dropbox_access_token:
        logger.error("Dropbox access token not set.")
        return None

    try:
        dbx = dropbox.Dropbox(milky_leak_instance.dropbox_access_token)
        # Intento de autenticación inicial
        dbx.users_get_current_account()  
        return dbx
    except dropbox.exceptions.AuthError as e:
        logger.error(f"Authentication error with Dropbox: {e}")
        return None

# Verificar conexión con Dropbox
def check_dropbox_connection(milky_leak_instance):
    """
    Verifica si la conexión a Dropbox es válida.
    """
    dbx = authenticate_dropbox(milky_leak_instance)
    if dbx is None:
        return False  # Conexión fallida

    try:
        dbx.users_get_current_account()  # Prueba de conexión
        return True
    except dropbox.exceptions.AuthError as e:
        logger.error(f"Error al conectar con Dropbox: {e}")
        return False

# Función para obtener la subcarpeta según el contador de imágenes
def get_subfolder_by_counter(image_counter):
    base = (image_counter // 1000) * 1000
    next_base = base + 999
    return f"{base}-{next_base}"

# Descargar imagen desde Mega.nz
def download_image_from_mega(m, milky_leak_instance, folder_link, image_name):
    try:
        folder = m.find(folder_link)
        if folder:
            file = m.find(image_name, folder)
            if file:
                m.download(file, milky_leak_instance.local_directory)
                return os.path.join(milky_leak_instance.local_directory, image_name)
    except Exception as e:
        logger.error(f"Error al descargar la imagen desde Mega.nz: {e}")
    return None

# Descargar imagen desde Dropbox
def download_image_from_dropbox(dbx, milky_leak_instance, image_name):
    subfolder = get_subfolder_by_counter(milky_leak_instance.image_counter)
    dropbox_path = f'/MilkyLeak/{subfolder}/{image_name}'
    local_buffer = BytesIO()

    try:
        metadata, res = dbx.files_download(dropbox_path)
        local_buffer.write(res.content)
        return local_buffer
    except Exception as e:
        logger.error(f"Error al descargar la imagen desde Dropbox: {e}")
        return None

# Obtener la imagen desde el servicio configurado
def get_image(milky_leak_instance):
    """
    Descarga una imagen desde el servicio configurado (Mega o Dropbox) en `milky_leak_instance`.
    """
    image_name = f"{milky_leak_instance.image_prefix}{milky_leak_instance.image_counter}.jpg"

    if milky_leak_instance.storage_service == 'mega':
        m = authenticate_mega(milky_leak_instance)
        if m:
            return download_image_from_mega(m, milky_leak_instance, milky_leak_instance.folder_location, image_name)
    elif milky_leak_instance.storage_service == 'dropbox':
        dbx = authenticate_dropbox(milky_leak_instance)
        if dbx:
            return download_image_from_dropbox(dbx, milky_leak_instance, image_name)

    return None

# Función para postear imagen en Twitter
def post_image(milky_leak_instance, image_buffer, message):
    api = authenticate_twitter(milky_leak_instance)
    if not api:
        return

    try:
        # Guardar el buffer en un archivo temporal para poder subirlo a Twitter
        temp_path = "/tmp/temp_image.jpg"
        with open(temp_path, 'wb') as f:
            f.write(image_buffer.getbuffer())

        # Subir la imagen a Twitter
        media = api.media_upload(temp_path)
        api.update_status(status=message, media_ids=[media.media_id])
    except Exception as e:
        logger.error(f"Error posteando imagen en Twitter: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# Obtener los 25 principales followers
def get_top_followers(milky_leak_instance, limit=25):
    api = authenticate_twitter(milky_leak_instance)
    followers = api.get_followers(count=limit)  # Cambiado a `get_followers`
    top_followers = [
        {
            'name': follower.name,
            'screen_name': follower.screen_name,
            'followers_count': follower.followers_count
        }
        for follower in followers
    ]
    return sorted(top_followers, key=lambda x: x['followers_count'], reverse=True)

# Obtener las 25 principales cuentas que sigo con más seguidores
def get_top_following(milky_leak_instance, limit=25):
    api = authenticate_twitter(milky_leak_instance)
    following = api.get_friends(count=limit)  # Cambiado a `get_friends`
    top_following = [
        {
            'name': friend.name,
            'screen_name': friend.screen_name,
            'followers_count': friend.followers_count
        }
        for friend in following
    ]
    return sorted(top_following, key=lambda x: x['followers_count'], reverse=True)

# Obtener menciones recientes
def get_top_mentions(milky_leak_instance, limit=25):
    api = authenticate_twitter(milky_leak_instance)
    mentions = api.mentions_timeline(count=limit)
    top_mentions = [
        {
            'name': mention.user.name,
            'screen_name': mention.user.screen_name,
            'followers_count': mention.user.followers_count,
            'interaction_type': 'mention'
        }
        for mention in mentions
    ]
    return sorted(top_mentions, key=lambda x: x['followers_count'], reverse=True)

# Obtener retweets recientes
def get_top_retweets(milky_leak_instance, limit=25):
    api = authenticate_twitter(milky_leak_instance)
    retweets = api.retweets_of_me(count=limit)
    top_retweets = [
        {
            'name': retweet.user.name,
            'screen_name': retweet.user.screen_name,
            'followers_count': retweet.user.followers_count,
            'interaction_type': 'retweet'
        }
        for retweet in retweets
    ]
    return sorted(top_retweets, key=lambda x: x['followers_count'], reverse=True)

# Vista para la página principal de pruebas y el ejecutor de post
def milkyleak_view(request):
    milky_leak_instance = get_object_or_404(MilkyLeak, id=1)

    # Configurar la conexión de almacenamiento según el servicio seleccionado
    storage_connected = False

    if milky_leak_instance.storage_service == 'dropbox':
        storage_connected = check_dropbox_connection(milky_leak_instance)
    elif milky_leak_instance.storage_service == 'mega':
        storage_connected = check_mega_connection(milky_leak_instance)
    
    # Verificar conexión con Twitter
    twitter_connected = check_twitter_connection(milky_leak_instance)

    # Contexto base para pasar a la plantilla
    context = {
        'milky_leak': milky_leak_instance,
        'mega_connected': storage_connected if milky_leak_instance.storage_service == 'mega' else False,
        'dropbox_connected': storage_connected if milky_leak_instance.storage_service == 'dropbox' else False,
        'twitter_connected': twitter_connected,
        #'top_followers': get_top_followers(milky_leak_instance),
        #'top_following': get_top_following(milky_leak_instance),
        'success': False,  # Valor predeterminado para GET
        'message': '',     # Mensaje predeterminado
    }

    # Procesar el formulario si es una solicitud POST
    if request.method == 'POST':
        post_text = request.POST.get('post_text')
        
        # Ejecutar la tarea asincrónica para publicar la imagen (usando Celery si está configurado)
        post_image_task.delay(milky_leak_instance.id, post_text)  # Enviar texto como argumento adicional si se necesita

        # Actualizar el contexto para mostrar el mensaje de éxito
        context.update({
            'success': True,
            'message': f"Post enviado con el texto: {post_text}",
        })

    return render(request, 'milkyleak.html', context)
