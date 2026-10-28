#la lista global(contendra la informacion de los estudiantes)
estud_beca = [
    # Declaracion de diccionarios de estudiantes modelo
    {
        "Nombre": "Luis",
        "Edad": 18,
        "carnet": 5647097,
        "carrera": "Ingenieria electronica",
        "correo": "luis@example.com",
    },
    {
        "Nombre": "Elena",
        "Edad": 21,
        "carnet": 150408,
        "carrera": "Ingenieria civil",
        "correo": "elena@example.com",
    },
    {
        "Nombre": "Martin",
        "Edad": 25,
        "carnet": 9876542,
        "carrera": "Ingenieria en sistemas",
        "correo": "mar@example.com",
    },
    {
        "Nombre": "Andres",
        "Edad": 22,
        "carnet": 1234567,
        "carrera": "Ingenieria industrial",
        "correo": "andres@example.com",
    },
    {
        "Nombre": "Valeria",
        "Edad": 24,
        "carnet": 1987450,
        "carrera": "Ingenieria Computacion",
        "correo": "valeria@example.com",
    },
]

def agregar_estudiante(nombre, edad, carnet, carrera, correo):
    #funcion para agregar estudiantes a la lista global
    estudiante = {
        "Nombre": nombre,
        "Edad": edad,
        "carnet": carnet,
        "carrera": carrera,
        "correo": correo
    }
    estud_beca.append(estudiante)

#practicamente, esto es para crear el formulario que agregue estudiantes y que esto pueda entrar en la lista global

import streamlit as st

with st.form(key="agregar_estudiante_form"):
    nombre = st.text_input("Nombre")
    edad = st.number_input("Edad", min_value=0)
    carnet = st.number_input("Carnet", min_value=0)
    carrera = st.text_input("Carrera")
    correo = st.text_input("Correo")

    if st.form_submit_button("Agregar Estudiante"):
        agregar_estudiante(nombre, edad, carnet, carrera, correo)