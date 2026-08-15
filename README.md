# Taller OS 3.0 ULTRA

Sistema operativo integral para un taller de chapa y pintura.

## Cómo abrirlo

1. Descomprimí todos los archivos dentro de **una única carpeta**.
2. Hacé doble clic en `INSTALAR_Y_ABRIR.bat`.
3. La aplicación se abre en el navegador.
4. En usos posteriores podés abrir `ABRIR_TALLER_OS.bat`.

## Importante

- No usa Supabase.
- No usa SQL.
- No tiene datos demo: arranca operativamente vacía.
- Todos los archivos del proyecto están en el mismo nivel, sin subcarpetas.
- Hasta integrar Google Sheets, la app guarda la operación en `taller_os_data.json`, un archivo JSON plano que se crea automáticamente junto a `app.py`.
- El Centro de datos permite descargar un respaldo JSON completo y un Excel de control.
- La arquitectura separa las pantallas de `store.py`, por lo que Google Sheets puede reemplazar la persistencia local sin rehacer la aplicación.

## Flujo central

LEAD → COTIZACIÓN → APROBADO → TURNO → INGRESO → PRODUCCIÓN → CONTROL → ENTREGA → COBRO → RENTABILIDAD

## Módulos

- HOY ejecutivo
- Captación & CRM
- Cotizador PRO por piezas e ítems
- Agenda & capacidad
- Órdenes de trabajo
- Producción / Kanban / WIP
- Control de calidad y retrabajos
- Materiales, compras, stock y consumo por OT
- Caja & finanzas
- Objetivos y reparto
- Seguros y capital inmovilizado
- Proveedores y cuenta corriente
- Reportes y rentabilidad
- Auditoría
- Configuración
- Centro de datos / backups

## Primer paso recomendado

Entrá a **Configuración** y cargá tus costos reales por hora, estructura fija, capacidad semanal y márgenes. Luego comenzá por **Captación & CRM** o cargá una **OT directa**.
