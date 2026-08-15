# Taller OS — versión sin subcarpetas

Esta versión está preparada para que puedas abrir y recorrer la aplicación sin configurar ninguna base de datos.

## Importante

- NO usa Supabase.
- NO usa SQL.
- NO usa Google Sheets todavía.
- NO requiere secrets ni credenciales.
- NO tiene subcarpetas dentro del proyecto.
- Todos los archivos están en la misma carpeta.
- Los datos son de demostración y viven solamente mientras la sesión de Streamlit está abierta.
- Cuando conectemos Google Sheets, reemplazaremos únicamente la capa de datos sin rehacer la interfaz.

## Abrir por primera vez

1. Descomprimí el ZIP.
2. Entrá en la carpeta `Taller_OS_SIN_SUBCARPETAS`.
3. Hacé doble clic en `INSTALAR_Y_ABRIR.bat`.
4. Esperá a que se instalen las dependencias.
5. Taller OS se abrirá en el navegador.

## Abrir las siguientes veces

Hacé doble clic en `ABRIR_TALLER_OS.bat`.

## Archivo principal

`app.py`

## Módulos

Los módulos están aplanados en la misma carpeta:

- `view_hoy.py`
- `view_captacion.py`
- `view_cotizador.py`
- `view_ordenes.py`
- `view_produccion.py`
- `view_materiales.py`
- `view_finanzas.py`
- `view_objetivos.py`
- `view_seguros.py`
- `view_auditoria.py`
- `view_configuracion.py`

Los motores auxiliares (`repository.py`, `metrics.py`, `utils.py`, etc.) también están en esa misma carpeta.

## Datos

La app arranca con datos demo. Podés crear y modificar registros para probar la experiencia. Al reiniciar completamente la sesión, esos cambios se pierden. Esto es intencional en esta etapa: primero evaluamos la aplicación y después conectamos Google Sheets.
