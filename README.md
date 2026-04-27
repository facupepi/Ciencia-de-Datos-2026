# Ciencia de Datos 2026

Este repositorio contiene los proyectos y trabajos prácticos para la materia Ciencia de Datos 2026.

## Configuración del Entorno

Para ejecutar los proyectos en este repositorio, necesitarás tener Python 3 instalado. Se recomienda encarecidamente utilizar un entorno virtual para gestionar las dependencias del proyecto y evitar conflictos entre paquetes.

### Pasos para la configuración

1.  **Clonar el repositorio:**
    Primero, clona este repositorio en tu máquina local usando el siguiente comando:
    ```bash
    git clone https://github.com/facupepi/Ciencia-de-Datos-2026.git
    cd Ciencia-de-Datos-2026
    ```

2.  **Crear un Entorno Virtual:**
    Una vez dentro del directorio del proyecto, crea un entorno virtual. El siguiente comando creará una carpeta `venv` dentro de tu proyecto que contendrá una instalación de Python y pip específica para este proyecto.
    ```bash
    python -m venv venv
    ```

3.  **Activar el Entorno Virtual:**
    Antes de instalar las dependencias, debes activar el entorno virtual.

    *   **En Windows:**
        ```powershell
        .\venv\Scripts\Activate.ps1
        ```
        Si encuentras un error de ejecución de scripts, puede que necesites cambiar la política de ejecución para el proceso actual con:
        ```powershell
        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
        ```
        Luego intenta activar el entorno de nuevo.

    *   **En macOS y Linux:**
        ```bash
        source venv/bin/activate
        ```
    Una vez activado, verás `(venv)` al principio de la línea de comandos de tu terminal.

4.  **Instalar las Dependencias:**
    Con el entorno virtual activado, instala todas las librerías necesarias ejecutando el siguiente comando. Este comando lee el archivo `requirements.txt` y descarga las versiones correctas de los paquetes.
    ```bash
    pip install -r requirements.txt
    ```

¡Y eso es todo! Ahora tienes un entorno aislado con todas las dependencias necesarias para trabajar en los proyectos de este repositorio.
