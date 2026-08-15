from __future__ import annotations

from datetime import date, timedelta, datetime


def demo_seed() -> dict[str, list[dict]]:
    today = date.today()
    now = datetime.now().isoformat(timespec="seconds")
    return {
        "leads": [
            {"id":"L1","created_at":now,"name":"Martín López","whatsapp":"3875551200","car":"Toyota Corolla 2020","plate":"AE123BC","damage":"Golpe puerta trasera derecha","source":"Instagram","need_visit":False,"status":"Cotizado","lost_reason":"","notes":"Quiere resolver antes del viernes."},
            {"id":"L2","created_at":now,"name":"Lucía Fernández","whatsapp":"3875554411","car":"VW Amarok 2019","plate":"AD778QW","damage":"Paragolpes delantero rayado y fisura","source":"Referido","need_visit":True,"status":"Contactado","lost_reason":"","notes":"Enviar visita."},
            {"id":"L3","created_at":now,"name":"Gonzalo Díaz","whatsapp":"3875559982","car":"Peugeot 208 2022","plate":"AF331KL","damage":"Guardabarros + óptica","source":"Google","need_visit":False,"status":"Nuevo","lost_reason":"","notes":""},
            {"id":"L4","created_at":now,"name":"Carla Ríos","whatsapp":"3875558884","car":"Fiat Cronos 2021","plate":"AE910ZZ","damage":"Rayón lateral completo","source":"Tarjeta / QR","need_visit":False,"status":"Seguimiento","lost_reason":"","notes":"Presupuesto enviado ayer."},
            {"id":"L5","created_at":now,"name":"Nicolás Vega","whatsapp":"3875551150","car":"Ford Ka 2018","plate":"AC221PP","damage":"Portón trasero hundido","source":"Instagram","need_visit":False,"status":"Perdido","lost_reason":"Precio","notes":"Eligió una opción más barata."},
        ],
        "quotes": [
            {"id":"Q1","number":41,"created_at":now,"lead_id":"L1","customer_name":"Martín López","car":"Toyota Corolla 2020","plate":"AE123BC","status":"Enviada","estimated_cost":310000,"floor_price":415000,"target_price":525000,"offered_price":510000,"estimated_days":3,"items":[],"notes":"Incluye desarme y armado."},
            {"id":"Q2","number":42,"created_at":now,"lead_id":"L4","customer_name":"Carla Ríos","car":"Fiat Cronos 2021","plate":"AE910ZZ","status":"Seguimiento","estimated_cost":390000,"floor_price":520000,"target_price":650000,"offered_price":630000,"estimated_days":4,"items":[],"notes":""},
        ],
        "work_orders": [
            {"id":"OT1","number":43,"created_at":now,"customer_name":"Sofía Méndez","whatsapp":"3875554000","car":"Renault Sandero 2020","plate":"AE444MN","km":63000,"fuel":"1/2","stage":"Chapa","appointment_date":(today-timedelta(days=3)).isoformat(),"promised_date":(today+timedelta(days=1)).isoformat(),"delivery_date":None,"agreed_amount":780000,"advance":250000,"paid_amount":250000,"actual_material_cost":185000,"parts_cost":0,"outsourcing_cost":0,"scope":"Puerta trasera + zócalo","excluded_scope":"Óptica rayada no incluida","preexisting_damage":"Rayas paragolpes trasero","photos":[],"notes":"Prioridad alta","archived":False},
            {"id":"OT2","number":44,"created_at":now,"customer_name":"Diego Martínez","whatsapp":"3875554011","car":"Chevrolet Cruze 2018","plate":"AC778TT","km":90500,"fuel":"1/4","stage":"Preparación","appointment_date":(today-timedelta(days=2)).isoformat(),"promised_date":today.isoformat(),"delivery_date":None,"agreed_amount":620000,"advance":200000,"paid_amount":200000,"actual_material_cost":142000,"parts_cost":35000,"outsourcing_cost":0,"scope":"Guardabarros delantero + puerta","excluded_scope":"","preexisting_damage":"","photos":[],"notes":"Entrega hoy 18hs","archived":False},
            {"id":"OT3","number":45,"created_at":now,"customer_name":"Mariana Soto","whatsapp":"3875554022","car":"VW Gol Trend 2017","plate":"AB131XY","km":112000,"fuel":"3/4","stage":"Pintura","appointment_date":(today-timedelta(days=4)).isoformat(),"promised_date":(today-timedelta(days=1)).isoformat(),"delivery_date":None,"agreed_amount":590000,"advance":300000,"paid_amount":300000,"actual_material_cost":170000,"parts_cost":0,"outsourcing_cost":0,"scope":"Capot y paragolpes","excluded_scope":"","preexisting_damage":"Parabrisas picado","photos":[],"notes":"ATRASADO","archived":False},
            {"id":"OT4","number":46,"created_at":now,"customer_name":"Pablo Arias","whatsapp":"3875554033","car":"Toyota Hilux 2021","plate":"AF990HK","km":48200,"fuel":"1/2","stage":"Armado","appointment_date":(today-timedelta(days=5)).isoformat(),"promised_date":(today+timedelta(days=2)).isoformat(),"delivery_date":None,"agreed_amount":1250000,"advance":500000,"paid_amount":500000,"actual_material_cost":290000,"parts_cost":85000,"outsourcing_cost":30000,"scope":"Caja lateral derecha + faro","excluded_scope":"","preexisting_damage":"","photos":[],"notes":"","archived":False},
            {"id":"OT5","number":47,"created_at":now,"customer_name":"Ana Correa","whatsapp":"3875554044","car":"Honda HR-V 2020","plate":"AE555RX","km":57500,"fuel":"1/2","stage":"Control de calidad","appointment_date":(today-timedelta(days=6)).isoformat(),"promised_date":today.isoformat(),"delivery_date":None,"agreed_amount":910000,"advance":400000,"paid_amount":400000,"actual_material_cost":205000,"parts_cost":60000,"outsourcing_cost":0,"scope":"Lateral izquierdo","excluded_scope":"","preexisting_damage":"","photos":[],"notes":"Revisar tono bajo sol","archived":False},
        ],
        "material_movements": [
            {"id":"MM1","created_at":now,"movement_date":(today-timedelta(days=3)).isoformat(),"type":"Compra","material":"Primer 2K","supplier":"Pinturería Norte","quantity":4,"unit":"L","amount":118000,"work_order_id":"","estimated_consumption":0,"actual_consumption":0,"notes":"Cuenta corriente"},
            {"id":"MM2","created_at":now,"movement_date":(today-timedelta(days=2)).isoformat(),"type":"Consumo","material":"Masilla poliéster","supplier":"","quantity":1.5,"unit":"kg","amount":31000,"work_order_id":"OT1","estimated_consumption":28000,"actual_consumption":31000,"notes":""},
            {"id":"MM3","created_at":now,"movement_date":(today-timedelta(days=1)).isoformat(),"type":"Consumo","material":"Base color","supplier":"","quantity":0.8,"unit":"L","amount":52000,"work_order_id":"OT3","estimated_consumption":47000,"actual_consumption":52000,"notes":""},
        ],
        "materials": [
            {"id":"M1","name":"Primer 2K","stock":7.2,"unit":"L","min_stock":3,"avg_unit_cost":29500,"supplier":"Pinturería Norte"},
            {"id":"M2","name":"Masilla poliéster","stock":5.5,"unit":"kg","min_stock":2,"avg_unit_cost":20600,"supplier":"Pinturería Norte"},
            {"id":"M3","name":"Thinner","stock":12,"unit":"L","min_stock":5,"avg_unit_cost":8000,"supplier":"Color Center"},
            {"id":"M4","name":"Lija P400","stock":18,"unit":"u","min_stock":10,"avg_unit_cost":1200,"supplier":"Color Center"},
        ],
        "financial_movements": [
            {"id":"F1","created_at":now,"movement_date":(today-timedelta(days=5)).isoformat(),"direction":"Ingreso","type":"Anticipo cliente","account":"Caja","category":"Cobros","amount":500000,"status":"Pagado","due_date":None,"paid_date":(today-timedelta(days=5)).isoformat(),"counterparty":"Pablo Arias","work_order_id":"OT4","notes":""},
            {"id":"F2","created_at":now,"movement_date":(today-timedelta(days=4)).isoformat(),"direction":"Egreso","type":"Compra","account":"Caja","category":"Pinturería","amount":118000,"status":"Pendiente","due_date":(today+timedelta(days=10)).isoformat(),"paid_date":None,"counterparty":"Pinturería Norte","work_order_id":"","notes":"Cuenta corriente"},
            {"id":"F3","created_at":now,"movement_date":(today-timedelta(days=3)).isoformat(),"direction":"Ingreso","type":"Anticipo cliente","account":"Banco","category":"Cobros","amount":300000,"status":"Pagado","due_date":None,"paid_date":(today-timedelta(days=3)).isoformat(),"counterparty":"Mariana Soto","work_order_id":"OT3","notes":""},
            {"id":"F4","created_at":now,"movement_date":today.isoformat(),"direction":"Ingreso","type":"Saldo cliente","account":"Caja","category":"Cobros","amount":420000,"status":"Pendiente","due_date":today.isoformat(),"paid_date":None,"counterparty":"Diego Martínez","work_order_id":"OT2","notes":"Cobrar al entregar"},
            {"id":"F5","created_at":now,"movement_date":(today-timedelta(days=7)).isoformat(),"direction":"Egreso","type":"Gasto fijo","account":"Banco","category":"Estructura","amount":310000,"status":"Pagado","due_date":None,"paid_date":(today-timedelta(days=7)).isoformat(),"counterparty":"Servicios / alquiler","work_order_id":"","notes":""},
        ],
        "insurance_jobs": [
            {"id":"S1","created_at":now,"work_order_id":"OT4","insurer":"Aseguradora Demo","authorization_date":(today-timedelta(days=7)).isoformat(),"approved_amount":1250000,"material_cost":290000,"capital_financed":930000,"delivery_date":None,"invoice_date":None,"estimated_collection_date":(today+timedelta(days=35)).isoformat(),"actual_collection_date":None,"collection_status":"Pendiente","margin":330000,"notes":"Pago 30/45 días"},
            {"id":"S2","created_at":now,"work_order_id":"OTX","insurer":"Compañía Federal","authorization_date":(today-timedelta(days=20)).isoformat(),"approved_amount":850000,"material_cost":210000,"capital_financed":720000,"delivery_date":(today-timedelta(days=8)).isoformat(),"invoice_date":(today-timedelta(days=8)).isoformat(),"estimated_collection_date":(today+timedelta(days=20)).isoformat(),"actual_collection_date":None,"collection_status":"Facturado","margin":280000,"notes":""},
        ],
        "audit_log": [
            {"id":"A1","created_at":now,"actor_name":"Demo Dueño","action":"CREÓ","entity":"OT","entity_id":"OT5","description":"Creó OT #00047 · Honda HR-V"},
            {"id":"A2","created_at":now,"actor_name":"Demo Socio Técnico","action":"MODIFICÓ","entity":"OT","entity_id":"OT3","description":"Movió OT #00045 a Pintura"},
            {"id":"A3","created_at":now,"actor_name":"Demo Dueño","action":"CARGÓ","entity":"FINANZAS","entity_id":"F4","description":"Cargó cuenta a cobrar $420.000"},
        ],
        "settings": [
            {"id":"main","distributable_target":6666667,"technical_share":0.60,"owner_share":0.40,"reserve_rate":0.05,"monthly_fixed_costs":2000000,"insurance_capital_limit":3000000,"weekly_capacity_cars":8,"labor_cost_per_hour":18000,"paint_cost_per_panel":55000,"floor_margin":0.25,"target_margin":0.40,"productive_hours_per_day":7}
        ],
        "app_users": [],
    }
