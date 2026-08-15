from __future__ import annotations

import streamlit as st
from theme import page_title
from permissions import ROLE_PERMISSIONS


def render(repo, user, settings):
    page_title("Configuración", "Objetivos, estructura de costos, cupos y arquitectura de permisos.")
    tabs = st.tabs(["Negocio y cotizador", "Usuarios y permisos"])

    with tabs[0]:
        with st.form("settings_form"):
            a, b, c = st.columns(3)
            target = a.number_input("Utilidad distribuible objetivo / mes", min_value=0.0, value=float(settings.get("distributable_target", 6666667)), step=100000.0)
            fixed = b.number_input("Estructura fija mensual", min_value=0.0, value=float(settings.get("monthly_fixed_costs", 2000000)), step=100000.0)
            reserve = c.number_input("Reserva %", min_value=0.0, max_value=50.0, value=float(settings.get("reserve_rate", .05)) * 100, step=1.0)

            a, b, c = st.columns(3)
            tech = a.number_input("Socio técnico %", min_value=0.0, max_value=100.0, value=float(settings.get("technical_share", .60)) * 100, step=1.0)
            owner = b.number_input("Socio empresario %", min_value=0.0, max_value=100.0, value=float(settings.get("owner_share", .40)) * 100, step=1.0)
            ins = c.number_input("Cupo capital seguros", min_value=0.0, value=float(settings.get("insurance_capital_limit", 3000000)), step=100000.0)

            st.markdown("#### Motor interno del cotizador")
            a, b, c = st.columns(3)
            labor = a.number_input("Costo interno hora productiva", min_value=0.0, value=float(settings.get("labor_cost_per_hour", 18000)), step=1000.0)
            paint = b.number_input("Costo pintura por paño", min_value=0.0, value=float(settings.get("paint_cost_per_panel", 55000)), step=1000.0)
            hours = c.number_input("Horas productivas por día", min_value=1.0, value=float(settings.get("productive_hours_per_day", 7)), step=.5)

            a, b, c = st.columns(3)
            floor = a.number_input("Margen mínimo / piso %", min_value=0.0, max_value=90.0, value=float(settings.get("floor_margin", .25)) * 100, step=1.0)
            target_margin = b.number_input("Margen objetivo %", min_value=0.0, max_value=90.0, value=float(settings.get("target_margin", .40)) * 100, step=1.0)
            capacity = c.number_input("Capacidad semanal de autos", min_value=1, value=int(settings.get("weekly_capacity_cars", 8)), step=1)
            ok = st.form_submit_button("Aplicar cambios en esta vista", type="primary", use_container_width=True)

        if ok:
            if abs((tech + owner) - 100) > 0.01:
                st.error("La distribución entre socios debe sumar 100%.")
            else:
                payload = {
                    "distributable_target": target,
                    "monthly_fixed_costs": fixed,
                    "reserve_rate": reserve / 100,
                    "technical_share": tech / 100,
                    "owner_share": owner / 100,
                    "insurance_capital_limit": ins,
                    "labor_cost_per_hour": labor,
                    "paint_cost_per_panel": paint,
                    "productive_hours_per_day": hours,
                    "floor_margin": floor / 100,
                    "target_margin": target_margin / 100,
                    "weekly_capacity_cars": capacity,
                }
                if settings.get("id"):
                    repo.update("settings", settings["id"], payload, user, "Actualizó configuración económica del taller")
                else:
                    payload["id"] = "main"
                    repo.insert("settings", payload, user, "Creó configuración económica del taller")
                st.success("Configuración aplicada para esta sesión de demostración.")
                st.rerun()

    with tabs[1]:
        st.info(
            "Por ahora no hay login ni almacenamiento de usuarios. Esta pantalla muestra la arquitectura "
            "de permisos que tendrá Taller OS cuando conectemos la persistencia con Google Sheets."
        )
        rows = []
        for role, permissions in ROLE_PERMISSIONS.items():
            rows.append({
                "Rol": role,
                "Acceso": ", ".join(sorted(permissions)) if permissions else "—",
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)
