import streamlit as st
import os
import pytz

from datetime import datetime
import time
from langchain.chat_models import ChatOpenAI
from langchain import PromptTemplate
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
import openai
import requests
from dotenv import load_dotenv

load_dotenv()

## CONSTANTES ##
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY_L")
NOMBRE_COMPLETO = "Siro Bayón"
NOMBRE = NOMBRE_COMPLETO.split()[0]
EDAD = 39
ZONA = pytz.timezone("Europe/Madrid")
FECHA_CUMPLEAÑOS = datetime(2023,11,4)
TEMA = """El viaje a Zaragoza para ver nuestro primer concierto de Metallica en el coche de Laorden. Fueron Laorden, Sergio y Siro. A la vuelta, \
    de madrugada, se oía un ruido muy fuerte y extraño en el coche. Resultaron ser unos auriculares que pegaban contra la carrocería."""

## INSTANCIAMOS LLM ##
chat = ChatOpenAI(
    temperature=1,
    openai_api_key=OPENAI_API_KEY,
)

## TEMPLATES ##
TEMPLATE = '''
Eres un poeta experto en escribir sonetos. Tu dominio de la lengua castellana es total.
Tu misión es dedicar un soneto a {cumpleañero} por su cumpleaños.
El soneto debe seguir el siguiente esquema de rima: ABBA ABBA CDC DCD
La rima del soneto debe de ser consonante.
La temática del soneto debe girar en torno a: {tema}.
{cumpleañero} cumple hoy {edad} años.
'''

prompt=PromptTemplate(
    template=TEMPLATE,
    input_variables=["cumpleañero","edad","tema"]
)
system_message_prompt = SystemMessagePromptTemplate(prompt=prompt)
human_template="{text}"
human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

## FUNCIONES ##
def print_HTML(texto:str) -> None:
    """Recoge el código HTML en la función markdown

    Parameters
    ----------
    texto : str
        _description_
    """
    st.markdown(
            f"""            
            <div style="background-color: #1a1a1a; display: flex; justify-content: center; align-items: center; font-family: 'Arial', sans-serif; margin-top: 20px;">
                <div style="background-color: #ffeb3b; border: 2px solid #fdd835; padding: 20px 30px; border-radius: 10px; box-shadow: 0 0 15px rgba(0, 0, 0, 0.5);">            
                    <h2 style="color: #333; font-size: 1.8em; text-align: center; border-bottom: 2px solid #fbc02d; padding-bottom: 10px;"></h2>                
                    <p style="color: #333; font-size: 1.2em; text-align: center; line-height: 1.6;">
                    {texto}
                    </p>                    
                </div>                
            </div>
            """,
            unsafe_allow_html=True
            )


def stream_response_assistant(texto:str,cadencia:float=0.03)->None:
    """Streamea la respuesta del LLM como chat message con una cadencia determinada

    Parameters
    ----------
    texto : str
        El texto a streamear
    cadencia : float, optional
        en segundos cuanto espera antes de mostrar la siguiente cadena de texto, by default 0.03
    """
    frase = ""
    output = st.empty()
    for char in texto:
        frase += char
        with output:
            print_HTML(frase)
        
        time.sleep(cadencia)
        output.empty()
    print_HTML(frase)


def cuenta_atras(fecha_evento:datetime,nombre:str,edad:int,tematica:str)->None:
    """Función que imprimirá una cuenta atrás hasta el evento pasado como argumento.
    Si el día del evento es el día presente, mostrará un mensaje de la IA y unos globos.
    Si ha pasado un día o más mostrará una cuenta atrás hasta el evento del año siguiente.
    Función pensada para los cumpleaños.

    Parameters
    ----------
    fecha_evento : datetime
        fecha del cumpleaños
    nombre : str
        nombre de la persona que cumple años
    edad : int
        años que va a cumplir
    tematica : str
        Temática para el soneto del LLM
    """
    while True:
        # Obtenemos el tiempo actual
        ahora = datetime.now()

        # Calculamos la diferencia entre el evento y ahora
        diferencia = fecha_evento - ahora

        # Obtenemos los días, horas, minutos y segundos restantes
        dias = diferencia.days
        horas = diferencia.seconds // 3600
        minutos = (diferencia.seconds // 60) % 60
        segundos = diferencia.seconds % 60

        if dias < 0:
            if dias < -1:
                fecha_evento = datetime(fecha_evento.year+1,fecha_evento.month,fecha_evento.day)
                continue
            chat_prompt_with_values = chat_prompt.format_prompt(cumpleañero=nombre, \
                                                              edad=edad,
                                                              tema=tematica,
                                            text="Hoy es mi cumpleaños")
            st.balloons()
            st.markdown(f"""
            <div style="background-color: #1a1a1a; display: flex; justify-content: center; align-items: center; height: 30vh; font-family: 'Arial', sans-serif;">
                <div style="background-color: #4caf50; border: 2px solid #388e3c; padding: 20px 30px; border-radius: 10px; box-shadow: 0 0 15px rgba(0, 0, 0, 0.5);">            
                    <h1 style="color: #ffffff; font-size: 2em; text-align: center;">¡Feliz Cumpleaños, <b>{NOMBRE}!</b></h1>                
                    <p style="color: #f0f0f0; font-size: 1.4em; text-align: center;">Esperemos que disfrutes de tu día.</p>                
                </div>            
            </div>
            """,
            unsafe_allow_html=True,
            )
            with st.spinner(f"¡¡¡ Ha llegado el gran día !!! Sé paciente mientras cargamos tu regalo, {NOMBRE}..."):
                try:
                    response = chat(chat_prompt_with_values.to_messages()).content

                # Quitamos saltos de linea sustituyendolos por <br>
                    response = response.replace("\n", "<br>") # Para que el HTML se visualice correctamente
                except openai.Error as oe:
                    st.error(oe)
                except requests.exceptions.RequestException as re:
                    st.error(f"Error de conexión: {re}")
                except TypeError as te:
                    st.error(f"Error de tipo de datos al interactuar con la API de OpenAI.")
                except ValueError as ve:
                    st.error(f"Error de valor al interactuar con la API de OpenAI.")

            st.balloons()
            stream_response_assistant(response)
            while True:
                st.balloons()
                time.sleep(3)

        container_cumple = st.empty()
        
        with container_cumple:
            #st.title(f"Quedan :red[{dias}] días, :red[{horas}] horas, :red[{minutos}] minutos y :red[{segundos}] segundos para el cumpleaños de :green[{nombre}].")
            st.markdown(f"""
                        <div style="text-align: center; padding: 20px; background: linear-gradient(45deg, #800080, #000080); border-radius: 8px;">
                        <h1 style="color: #FFFFFF;">¡Falta poco para el cumpleaños de {NOMBRE_COMPLETO}!</h1>
                        <h2 style="color: #333333; background-color: #FFFDD0; padding: 10px; border-radius: 8px;">Quedan {dias} días, {horas} horas, {minutos} minutos y {segundos} segundos</h2>
                        </div>
                        """,
                        unsafe_allow_html=True)


        # Esperamos un segundo antes de actualizar
        time.sleep(1)
        container_cumple.empty()

if __name__ == '__main__':
    # Configuración de la app
    st.set_page_config(
        page_title=f"EFEMÉRIDE {NOMBRE_COMPLETO} ✨🎈",
        page_icon="🎁",
        layout="centered",
        initial_sidebar_state="collapsed",
)
        
    cuenta_atras(FECHA_CUMPLEAÑOS, NOMBRE_COMPLETO, EDAD, TEMA)