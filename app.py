from flask import Flask, render_template_string, request, jsonify, session
from supabase import create_client
import csv
import io
from datetime import datetime, timedelta
import hashlib

app = Flask(__name__)
app.secret_key = 'mersha_secret_key_2026'

SUPABASE_URL = 'https://zhqklrymzzecaiinlscj.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpocWtscnltenplY2FpaW5sc2NqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc2NjU5MzgsImV4cCI6MjEwMzI0MTkzOH0.gPuYPrOl8-dejnNC7XNWrbp0lkCoVTDB8CPh1wmFoWY'

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Conexion exitosa a Supabase")
except Exception as e:
    print(f"Error de conexion: {e}")
    supabase = None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verificar_usuario(usuario, password):
    if supabase:
        try:
            response = supabase.table('usuarios').select('*').eq('usuario', usuario).eq('activo', True).execute()
            if response.data:
                user = response.data[0]
                if user['password'] == hash_password(password):
                    return user
        except Exception as e:
            print(f"Error leyendo usuarios: {e}")
    usuarios_fijos = {
        'admin': {'password': hash_password('mersha2026'), 'nombre': 'Administrador', 'rol': 'admin'},
        'juan': {'password': hash_password('juan123'), 'nombre': 'Juan Perez', 'rol': 'asesor'},
        'maria': {'password': hash_password('maria123'), 'nombre': 'Maria Lopez', 'rol': 'asesor'},
        'carlos': {'password': hash_password('carlos123'), 'nombre': 'Carlos Rodriguez', 'rol': 'asesor'}
    }
    if usuario in usuarios_fijos and usuarios_fijos[usuario]['password'] == hash_password(password):
        return {'usuario': usuario, **usuarios_fijos[usuario]}
    return None

COMISIONES_POR_PLAN = {
    'Tradicional': 15,
    'Tradicional con Cremacion': 12,
    'Cremacion Directa': 10,
    'Cremacion con Despedida': 12,
    'Plan Familiar': 15,
    'Plan Corporativo': 8,
    'Otro': 10
}
BONO_POR_CUOTAS = {1: 0, 2: 2, 3: 5, 4: 8, 5: 10}
METAS_MENSUALES = {'Juan Perez': 10, 'Maria Lopez': 8, 'Carlos Rodriguez': 6}
META_DEFAULT = 5

CANTONES_DISTRITOS = {
    'San Jose': {
        'San Jose': ['Carmen', 'Merced', 'Hospital', 'Catedral', 'Zapote', 'San Francisco de Dos Rios', 'Uruca', 'Mata Redonda', 'Pavas', 'Hatillo', 'San Sebastian'],
        'Escazu': ['Escazu', 'San Antonio', 'San Rafael'],
        'Desamparados': ['Desamparados', 'San Miguel', 'San Juan de Dios', 'San Rafael Arriba', 'San Antonio', 'Frailes', 'Patarra'],
        'Goicoechea': ['Guadalupe', 'San Francisco', 'Calle Blancos', 'Mata de Platano', 'Ipis', 'Rancho Redondo', 'Purral'],
        'Curridabat': ['Curridabat', 'Granadilla', 'Sanchez', 'Tirrases'],
        'Montes de Oca': ['San Pedro', 'Sabanilla', 'Mercedes', 'San Rafael'],
        'Tibas': ['San Juan', 'Cinco Esquinas', 'Anselmo Llorente', 'Leon XIII', 'Colima']
    },
    'Heredia': {
        'Heredia': ['Heredia', 'Mercedes', 'San Francisco', 'Ulloa', 'Varablanca'],
        'Barva': ['Barva', 'San Pedro', 'San Pablo', 'San Roque', 'Santa Lucia'],
        'Santo Domingo': ['Santo Domingo', 'San Vicente', 'San Miguel', 'Paracito', 'Santo Tomas'],
        'Santa Barbara': ['Santa Barbara', 'San Pedro', 'San Juan', 'Jesus', 'Santo Domingo'],
        'San Rafael': ['San Rafael', 'San Josecito', 'Santiago', 'Angeles', 'Concepcion'],
        'Belen': ['San Antonio', 'La Ribera', 'La Asuncion']
    },
    'Cartago': {
        'Cartago': ['Oriental', 'Occidental', 'Carmen', 'San Nicolas', 'Aguacaliente', 'Guadalupe'],
        'Paraiso': ['Paraiso', 'Santiago', 'Orosi', 'Cachi', 'Llanos de Santa Lucia'],
        'La Union': ['Tres Rios', 'San Diego', 'San Juan', 'San Rafael', 'Concepcion'],
        'Turrialba': ['Turrialba', 'La Suiza', 'Peralta', 'Santa Cruz', 'Santa Teresita'],
        'Oreamuno': ['San Rafael', 'Cot', 'Potrero Cerrado', 'Cipreses', 'Santa Rosa']
    },
    'Limon': {
        'Pococi': ['Guapiles', 'Jimenez', 'Rita', 'Roxana', 'Cariari', 'Colorado', 'La Colonia', 'Las Palmas', 'El Molino', 'La Perla'],
        'Limon': ['Limon', 'Valle La Estrella', 'Rio Blanco', 'Matama'],
        'Siquirres': ['Siquirres', 'Pacuarito', 'Florida', 'Germania', 'El Cairo'],
        'Matina': ['Matina', 'Batan', 'Carrandi'],
        'Guacimo': ['Guacimo', 'Mercedes', 'Pocora', 'Rio Jimenez', 'Duacari']
    }
}

def calcular_comision_completa(venta):
    resultado = venta.get('resultado', '')
    monto = float(venta.get('monto', 0) or 0)
    cuotas = int(venta.get('cuotas', 1) or 1)
    tipo_plan = venta.get('tipo_plan', 'Otro')
    if resultado != 'Venta Concretada' or monto <= 0:
        return 0
    porcentaje_base = COMISIONES_POR_PLAN.get(tipo_plan, 10)
    bono_cuotas = BONO_POR_CUOTAS.get(cuotas, 10) if cuotas >= 5 else BONO_POR_CUOTAS.get(cuotas, 0)
    return monto * ((porcentaje_base + bono_cuotas) / 100)

def registrar_auditoria(usuario, accion, detalle=''):
    try:
        datos = {'usuario': usuario, 'accion': accion, 'detalle': detalle, 'fecha': datetime.now().isoformat()}
        supabase.table('auditoria').insert(datos).execute()
    except Exception as e:
        print(f"Error al registrar auditoria: {e}")

# ====== FUNCIONES DE CONTRATOS ======
def crear_contrato_db(venta_id, numero_contrato, estado='borrador'):
    if not supabase:
        return False, "Sin conexión"
    try:
        supabase.table('contratos').insert({
            'venta_id': venta_id,
            'numero_contrato': numero_contrato,
            'estado': estado
        }).execute()
        return True, "Contrato creado"
    except Exception as e:
        return False, str(e)

def listar_contratos_db():
    if not supabase:
        return []
    try:
        response = supabase.table('contratos').select('*, ventas(contacto, tipo_plan, monto)').order('fecha_creacion', desc=True).execute()
        return response.data
    except:
        return []

def actualizar_estado_contrato(contrato_id, estado):
    if not supabase:
        return False, "Sin conexión"
    try:
        supabase.table('contratos').update({'estado': estado}).eq('id', contrato_id).execute()
        return True, "Estado actualizado"
    except Exception as e:
        return False, str(e)

def adjuntar_pdf_contrato(contrato_id, pdf_nombre, pdf_base64):
    if not supabase:
        return False, "Sin conexión"
    try:
        supabase.table('contratos').update({
            'pdf_nombre': pdf_nombre,
            'pdf_base64': pdf_base64
        }).eq('id', contrato_id).execute()
        return True, "PDF adjuntado"
    except Exception as e:
        return False, str(e)

HTML = '''
<!DOCTYPE html>
<html lang="es-CR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Funerarias Mersha - Control de Ventas</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #f4f7f6; padding: 20px; }
        .container { max-width: 1400px; margin: auto; background: white; padding: 25px; border-radius: 10px; }
        h1 { text-align: center; color: #2c3e50; margin-bottom: 20px; }
        h2 { color: #34495e; margin: 20px 0 10px; }
        .login-container {
            max-width: 400px; margin: 100px auto; background: white;
            padding: 30px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .login-container h2 { text-align: center; margin-bottom: 20px; }
        .login-container input { width: 100%; padding: 12px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 5px; }
        .login-container button { width: 100%; padding: 12px; background: #27ae60; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        .user-info { display: flex; justify-content: space-between; align-items: center; padding: 10px; background: #f8f9fa; border-radius: 8px; margin-bottom: 15px; }
        .user-info button { background: #e74c3c; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; }
        .menu { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; background: #f8f9fa; padding: 15px; border-radius: 10px; }
        .menu button { padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        .menu button:hover { background: #219a52; }
        .menu button.active { background: #1e8449; }
        .seccion { display: none; }
        .seccion.active { display: block; }
        form { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-bottom: 20px; padding: 20px; background: #f8f9fa; border-radius: 8px; }
        .campo { display: flex; flex-direction: column; }
        label { font-weight: bold; margin-bottom: 5px; font-size: 14px; }
        input, select, textarea { padding: 10px; border: 1px solid #ccc; border-radius: 5px; font-size: 14px; }
        button[type="submit"] { padding: 12px; background: #27ae60; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .search-bar { display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap; padding: 15px; background: #f8f9fa; border-radius: 8px; }
        .search-bar input, .search-bar select { padding: 10px; border: 1px solid #ccc; border-radius: 5px; }
        .search-bar input { flex: 1; min-width: 200px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 10px; border-bottom: 1px solid #ddd; text-align: left; font-size: 14px; }
        th { background: #f8f9fa; font-weight: bold; }
        tr:hover { background: #f1f1f1; }
        .btn-eliminar { background: #e74c3c; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; font-size: 12px; }
        .btn-editar { background: #f39c12; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; margin-right: 5px; font-size: 12px; }
        .btn-ver { background: #3498db; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; margin-right: 5px; font-size: 12px; }
        .btn-contrato { background: #1abc9c; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; margin-right: 5px; font-size: 12px; }
        .btn-exportar { background: #3498db; color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer; }
        .btn-whatsapp { background: #25D366; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; margin-right: 5px; font-size: 12px; }
        .btn-correo { background: #6c757d; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; margin-right: 5px; font-size: 12px; }
        .tarjetas { display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }
        .tarjeta { flex: 1; min-width: 150px; background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }
        .tarjeta h3 { font-size: 24px; color: #27ae60; }
        .alerta { background: #fff3cd; border: 1px solid #ffc107; color: #856404; padding: 10px; border-radius: 5px; margin-bottom: 10px; }
        .alerta-roja { background: #f8d7da; border: 1px solid #e74c3c; color: #721c24; padding: 10px; border-radius: 5px; margin-bottom: 10px; }
        .alerta-verde { background: #d4edda; border: 1px solid #27ae60; color: #155724; padding: 10px; border-radius: 5px; margin-bottom: 10px; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; justify-content: center; align-items: center; }
        .modal.show { display: flex; }
        .modal-content { background: white; padding: 20px; border-radius: 10px; max-width: 700px; width: 90%; max-height: 80vh; overflow-y: auto; }
        .modal-close { float: right; cursor: pointer; font-size: 24px; }
        .reporte-opciones { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px; }
        .reporte-opciones button { padding: 10px 15px; background: #3498db; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .reporte-opciones button.active { background: #1e8449; }
        .dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .dashboard-box { background: #f9f9f9; padding: 15px; border-radius: 8px; }
        @media print {
            .menu, .user-info, .btn-eliminar, .btn-editar, .btn-ver, .btn-contrato, .btn-exportar, .btn-whatsapp, .btn-correo, form, .search-bar {
                display: none !important;
            }
        }
    </style>
</head>
<body>
    <div id="loginScreen" class="login-container">
        <h2>Funerarias Mersha</h2>
        <form id="loginForm">
            <input type="text" id="loginUsuario" placeholder="Usuario" required>
            <input type="password" id="loginPassword" placeholder="Contraseña" required>
            <button type="submit">Ingresar</button>
        </form>
        <div id="loginError" style="color:red; margin-top:10px; text-align:center;"></div>
    </div>
    <div id="appContainer" class="container" style="display:none;">
        <div class="user-info">
            <div><strong>Usuario:</strong> <span id="nombreUsuario"></span> | <span id="rolUsuario"></span></div>
            <button onclick="logout()">Cerrar Sesion</button>
        </div>
        <h1>Funerarias Mersha - Control de Ventas</h1>
        <div class="menu">
            <button class="active" onclick="mostrarSeccion('dashboard', this)">Dashboard</button>
            <button onclick="mostrarSeccion('registro', this)">Registro</button>
            <button onclick="mostrarSeccion('reportes', this)">Reportes</button>
            <button onclick="mostrarSeccion('seguimiento', this)">Seguimiento</button>
            <button onclick="mostrarSeccion('clientes', this)">Clientes</button>
            <button onclick="mostrarSeccion('metas', this)">Metas</button>
            <button onclick="mostrarSeccion('contratos', this)">Contratos</button>
            <button onclick="mostrarSeccion('notificaciones', this)">Notificaciones</button>
            <button onclick="mostrarSeccion('auditoria', this)">Auditoria</button>
            <button onclick="mostrarSeccion('usuarios', this)" id="btnUsuarios">Usuarios</button>
        </div>
        <div id="dashboard" class="seccion active">
            <div class="tarjetas">
                <div class="tarjeta"><h3 id="dashVentas">0</h3><p>Ventas Mes</p></div>
                <div class="tarjeta"><h3 id="dashMonto">0</h3><p>Monto Mes</p></div>
                <div class="tarjeta"><h3 id="dashComisiones">0</h3><p>Comisiones</p></div>
                <div class="tarjeta"><h3 id="dashPendientes">0</h3><p>Seguimientos Hoy</p></div>
            </div>
        </div>
        <div id="registro" class="seccion">
            <form id="formVenta">
                <input type="hidden" id="ventaId">
                <div class="campo"><label>Fecha *</label><input type="date" id="fecha" required></div>
                <div class="campo"><label>Nombre *</label><input type="text" id="contacto" required></div>
                <div class="campo"><label>Cedula</label><input type="text" id="cedula"></div>
                <div class="campo"><label>Telefono</label><input type="tel" id="telefono"></div>
                <div class="campo"><label>Correo</label><input type="email" id="email"></div>
                <div class="campo"><label>Provincia</label><select id="provincia" onchange="cargarCantones()"><option value="">Selecciona...</option></select></div>
                <div class="campo"><label>Canton</label><select id="canton" onchange="cargarDistritos()"><option value="">Selecciona...</option></select></div>
                <div class="campo"><label>Distrito</label><select id="distrito"><option value="">Selecciona...</option></select></div>
                <div class="campo"><label>Tipo Plan *</label><select id="tipoPlan" required><option value="">Selecciona...</option><option value="Tradicional">Tradicional</option><option value="Tradicional con Cremacion">Tradicional con Cremacion</option><option value="Cremacion Directa">Cremacion Directa</option><option value="Cremacion con Despedida">Cremacion con Despedida</option><option value="Plan Familiar">Plan Familiar</option><option value="Plan Corporativo">Plan Corporativo</option></select></div>
                <div class="campo"><label>Resultado *</label><select id="resultado" required><option value="">Selecciona...</option><option value="Cita Agendada">Cita Agendada</option><option value="Venta Concretada">Venta Concretada</option><option value="No Interesado">No Interesado</option><option value="Llamar Despues">Llamar Despues</option><option value="Seguimiento">Seguimiento</option></select></div>
                <div class="campo"><label>Monto (CRC)</label><input type="number" id="monto"></div>
                <div class="campo"><label>Cuotas</label><input type="number" id="cuotas" value="1"></div>
                <div class="campo"><label>Asesor *</label><input type="text" id="asesor" required></div>
                <div class="campo"><label>Fecha Seguimiento</label><input type="date" id="fechaSeguimiento"></div>
                <div class="campo" style="grid-column: span 2;"><label>Notas</label><textarea id="notas"></textarea></div>
                <div style="grid-column: span 2;"><button type="submit" id="btnSubmit">Agregar Venta</button><button type="button" id="btnCancelar" style="display:none; background:#95a5a6;" onclick="cancelarEdicion()">Cancelar</button></div>
            </form>
            <h2>Ventas Registradas</h2>
            <div class="search-bar">
                <input type="text" id="busqueda" placeholder="Buscar..." onkeyup="filtrarTabla()">
                <select id="filtroAsesor" onchange="filtrarTabla()"><option value="">Todos</option></select>
                <button class="btn-exportar" onclick="exportarCSV()">Exportar CSV</button>
            </div>
            <table><thead><tr><th>Fecha</th><th>Nombre</th><th>Telefono</th><th>Ubicacion</th><th>Plan</th><th>Resultado</th><th>Monto</th><th>Comision</th><th>Asesor</th><th>Acciones</th></tr></thead><tbody id="tablaVentasBody"></tbody></table>
        </div>
        <div id="reportes" class="seccion">
            <h2>Reportes</h2>
            <div class="reporte-opciones">
                <button class="active" onclick="cambiarReporte('general', this)">Resumen</button>
                <button onclick="cambiarReporte('asesor', this)">Por Asesor</button>
                <button onclick="cambiarReporte('plan', this)">Por Plan</button>
                <button onclick="cambiarReporte('fechas', this)">Por Fechas</button>
                <button onclick="cambiarReporte('provincia', this)">Por Provincia</button>
                <button onclick="cambiarReporte('canton', this)">Por Canton</button>
                <button onclick="cambiarReporte('distrito', this)">Por Distrito</button>
            </div>
            <button class="btn-exportar" onclick="exportarReporteActual()">Exportar Excel</button>
            <div id="reporte-general" class="reporte-contenido">
                <div class="tarjetas">
                    <div class="tarjeta"><h3 id="rgVentas">0</h3><p>Ventas</p></div>
                    <div class="tarjeta"><h3 id="rgMonto">0</h3><p>Monto</p></div>
                    <div class="tarjeta"><h3 id="rgComisiones">0</h3><p>Comisiones</p></div>
                </div>
            </div>
            <div id="reporte-asesor" class="reporte-contenido" style="display:none;">
                <table><thead><tr><th>Asesor</th><th>Ventas</th><th>Monto</th><th>Comision</th></tr></thead><tbody id="repAsesor"></tbody></table>
            </div>
            <div id="reporte-plan" class="reporte-contenido" style="display:none;">
                <table><thead><tr><th>Plan</th><th>Ventas</th><th>Monto</th><th>Comision</th></tr></thead><tbody id="repPlan"></tbody></table>
            </div>
            <div id="reporte-fechas" class="reporte-contenido" style="display:none;">
                <div class="search-bar"><label>Desde:</label><input type="date" id="fechaDesde"><label>Hasta:</label><input type="date" id="fechaHasta"><button onclick="generarReporteFechas()">Generar</button></div>
                <div id="resultadoFechas"></div>
            </div>
            <div id="reporte-provincia" class="reporte-contenido" style="display:none;">
                <table><thead><tr><th>Provincia</th><th>Ventas</th><th>Monto</th><th>Comision</th></tr></thead><tbody id="repProvincia"></tbody></table>
            </div>
            <div id="reporte-canton" class="reporte-contenido" style="display:none;">
                <table><thead><tr><th>Canton</th><th>Provincia</th><th>Ventas</th><th>Monto</th><th>Comision</th></tr></thead><tbody id="repCanton"></tbody></table>
            </div>
            <div id="reporte-distrito" class="reporte-contenido" style="display:none;">
                <table><thead><tr><th>Distrito</th><th>Canton</th><th>Ventas</th><th>Monto</th><th>Comision</th></tr></thead><tbody id="repDistrito"></tbody></table>
            </div>
        </div>
        <div id="seguimiento" class="seccion">
            <h2>Seguimientos Pendientes</h2>
            <div class="search-bar">
                <button onclick="cargarSeguimiento('hoy')">Hoy</button>
                <button onclick="cargarSeguimiento('7dias')">Proximos 7 dias</button>
                <button onclick="cargarSeguimiento('todos')">Todos</button>
            </div>
            <div id="listaSeguimiento"></div>
        </div>
        <div id="clientes" class="seccion">
            <h2>Clientes</h2>
            <div class="search-bar"><input type="text" id="busquedaCliente" placeholder="Buscar cliente..." onkeyup="filtrarClientes()"></div>
            <table><thead><tr><th>Nombre</th><th>Cedula</th><th>Telefono</th><th>Ubicacion</th><th>Estado</th><th>Acciones</th></tr></thead><tbody id="tablaClientes"></tbody></table>
        </div>
        <div id="metas" class="seccion">
            <h2>Metas por Asesor</h2>
            <div id="contenidoMetas"></div>
        </div>
        <div id="contratos" class="seccion">
            <h2>Gestión de Contratos</h2>
            <div class="search-bar"><button onclick="cargarContratos()">Actualizar lista</button></div>
            <table><thead><tr><th>Número</th><th>Cliente</th><th>Plan</th><th>Monto</th><th>Estado</th><th>PDF</th><th>Acciones</th></tr></thead><tbody id="tablaContratos"></tbody></table>
        </div>
        <div id="notificaciones" class="seccion">
            <h2>Notificaciones y Recordatorios</h2>
            <div id="listaNotificaciones"></div>
        </div>
        <div id="auditoria" class="seccion">
            <h2>Registro de Actividad</h2>
            <div id="listaAuditoria"></div>
        </div>
        <div id="usuarios" class="seccion">
            <h2>Gestion de Usuarios</h2>
            <form id="formUsuario">
                <input type="hidden" id="usuarioId">
                <div class="campo"><label>Usuario *</label><input type="text" id="usuarioNombre" required></div>
                <div class="campo"><label>Contraseña *</label><input type="password" id="usuarioPassword"></div>
                <div class="campo"><label>Nombre completo *</label><input type="text" id="usuarioNombreCompleto" required></div>
                <div class="campo"><label>Rol *</label><select id="usuarioRol"><option value="asesor">Asesor</option><option value="admin">Administrador</option></select></div>
                <div class="campo"><label>Activo</label><select id="usuarioActivo"><option value="true">Si</option><option value="false">No</option></select></div>
                <div style="grid-column: span 2;"><button type="submit" id="btnUsuarioSubmit">Agregar Usuario</button></div>
            </form>
            <h3>Usuarios Registrados</h3>
            <table><thead><tr><th>Usuario</th><th>Nombre</th><th>Rol</th><th>Activo</th><th>Acciones</th></tr></thead><tbody id="tablaUsuarios"></tbody></table>
        </div>
    </div>
    <div class="modal" id="modalContrato">
        <div class="modal-content">
            <span class="modal-close" onclick="cerrarModalContrato()">&times;</span>
            <h2>Contrato de Servicio</h2>
            <div id="contenidoContrato"></div>
            <button onclick="window.print()">Imprimir Contrato</button>
        </div>
    </div>
    <div class="modal" id="modalHistorial">
        <div class="modal-content">
            <span class="modal-close" onclick="cerrarModalHistorial()">&times;</span>
            <h2>Historial del Cliente</h2>
            <div id="contenidoHistorial"></div>
        </div>
    </div>

    <script>
        let todasLasVentas = [];
        let reporteActual = 'general';
        const cantonesDistritos = ''' + str(CANTONES_DISTRITOS) + ''';

        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const usuario = document.getElementById('loginUsuario').value;
            const password = document.getElementById('loginPassword').value;
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({usuario, password})
            });
            const data = await res.json();
            if (data.success) {
                document.getElementById('loginScreen').style.display = 'none';
                document.getElementById('appContainer').style.display = 'block';
                document.getElementById('nombreUsuario').textContent = data.nombre;
                document.getElementById('rolUsuario').textContent = data.rol;
                if (data.rol !== 'admin') {
                    document.getElementById('btnUsuarios').style.display = 'none';
                }
                cargarTodo();
            } else {
                document.getElementById('loginError').textContent = data.error;
            }
        });

        async function logout() {
            await fetch('/api/logout');
            document.getElementById('appContainer').style.display = 'none';
            document.getElementById('loginScreen').style.display = 'block';
        }

        function cargarTodo() {
            cargarProvincias();
            cargarVentas();
            cargarDashboard();
            cargarSeguimiento('todos');
            cargarNotificaciones();
            cargarAuditoria();
            cargarContratos();
            if (document.getElementById('rolUsuario').textContent === 'admin') {
                cargarUsuarios();
            }
        }

        function cargarProvincias() {
            const select = document.getElementById('provincia');
            select.innerHTML = '<option value="">Selecciona...</option>';
            Object.keys(cantonesDistritos).forEach(p => select.innerHTML += `<option value="${p}">${p}</option>`);
        }

        function cargarCantones() {
            const provincia = document.getElementById('provincia').value;
            const select = document.getElementById('canton');
            select.innerHTML = '<option value="">Selecciona...</option>';
            if (provincia && cantonesDistritos[provincia]) {
                Object.keys(cantonesDistritos[provincia]).forEach(c => select.innerHTML += `<option value="${c}">${c}</option>`);
            }
            document.getElementById('distrito').innerHTML = '<option value="">Selecciona...</option>';
        }

        function cargarDistritos() {
            const provincia = document.getElementById('provincia').value;
            const canton = document.getElementById('canton').value;
            const select = document.getElementById('distrito');
            select.innerHTML = '<option value="">Selecciona...</option>';
            if (provincia && canton && cantonesDistritos[provincia] && cantonesDistritos[provincia][canton]) {
                cantonesDistritos[provincia][canton].forEach(d => select.innerHTML += `<option value="${d}">${d}</option>`);
            }
        }

        function mostrarSeccion(nombre, boton) {
            document.querySelectorAll('.seccion').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.menu button').forEach(b => b.classList.remove('active'));
            document.getElementById(nombre).classList.add('active');
            boton.classList.add('active');
            if (nombre === 'dashboard') cargarDashboard();
            if (nombre === 'reportes') cargarTodosLosReportes();
            if (nombre === 'seguimiento') cargarSeguimiento('todos');
            if (nombre === 'clientes') cargarClientes();
            if (nombre === 'metas') cargarMetas();
            if (nombre === 'contratos') cargarContratos();
            if (nombre === 'notificaciones') cargarNotificaciones();
            if (nombre === 'auditoria') cargarAuditoria();
            if (nombre === 'usuarios') cargarUsuarios();
        }

        async function cargarDashboard() {
            const res = await fetch('/api/dashboard');
            const data = await res.json();
            if (data.success) {
                document.getElementById('dashVentas').textContent = data.data.ventas_mes;
                document.getElementById('dashMonto').textContent = data.data.monto_mes.toLocaleString();
                document.getElementById('dashComisiones').textContent = data.data.comisiones_mes.toLocaleString();
                document.getElementById('dashPendientes').textContent = data.data.seguimientos_hoy;
            }
        }

        async function cargarVentas() {
            const res = await fetch('/api/ventas');
            const data = await res.json();
            if (data.success) {
                todasLasVentas = data.data;
                renderizarTabla(data.data);
                cargarFiltros();
            }
        }

        function renderizarTabla(ventas) {
            const tbody = document.getElementById('tablaVentasBody');
            tbody.innerHTML = '';
            if (!ventas.length) {
                tbody.innerHTML = '<tr><td colspan="10">No hay registros</td></tr>';
                return;
            }
            ventas.forEach(v => {
                const comision = v.comision || 0;
                const ubicacion = [v.distrito, v.canton, v.provincia].filter(Boolean).join(', ');
                tbody.innerHTML += `<tr>
                    <td>${v.fecha}</td><td>${v.contacto}</td><td>${v.telefono || '-'}</td>
                    <td>${ubicacion || '-'}</td><td>${v.tipo_plan}</td><td>${v.resultado}</td>
                    <td>${v.monto ? Number(v.monto).toLocaleString() : '-'}</td>
                    <td>${comision ? Number(comision).toLocaleString() : '-'}</td>
                    <td>${v.asesor}</td>
                    <td>
                        <button class="btn-editar" onclick="editarVenta('${v.id}')">Editar</button>
                        <button class="btn-contrato" onclick="generarContrato('${v.id}')">Contrato</button>
                        <button class="btn-eliminar" onclick="eliminarVenta('${v.id}')">Eliminar</button>
                    </td>
                </tr>`;
            });
        }

        function cargarFiltros() {
            const asesores = [...new Set(todasLasVentas.map(v => v.asesor).filter(Boolean))];
            const select = document.getElementById('filtroAsesor');
            select.innerHTML = '<option value="">Todos</option>';
            asesores.forEach(a => select.innerHTML += `<option value="${a}">${a}</option>`);
        }

        function filtrarTabla() {
            const busqueda = document.getElementById('busqueda').value.toLowerCase();
            const asesor = document.getElementById('filtroAsesor').value;
            const filtradas = todasLasVentas.filter(v => {
                const matchBusqueda = !busqueda || v.contacto.toLowerCase().includes(busqueda) || (v.cedula && v.cedula.includes(busqueda));
                const matchAsesor = !asesor || v.asesor === asesor;
                return matchBusqueda && matchAsesor;
            });
            renderizarTabla(filtradas);
        }

        document.getElementById('formVenta').addEventListener('submit', async function(e) {
            e.preventDefault();
            const ventaId = document.getElementById('ventaId').value;
            const datos = {
                fecha: document.getElementById('fecha').value,
                contacto: document.getElementById('contacto').value,
                cedula: document.getElementById('cedula').value,
                telefono: document.getElementById('telefono').value,
                email: document.getElementById('email').value,
                provincia: document.getElementById('provincia').value,
                canton: document.getElementById('canton').value,
                distrito: document.getElementById('distrito').value,
                zona: [document.getElementById('distrito').value, document.getElementById('canton').value, document.getElementById('provincia').value].filter(Boolean).join(', '),
                tipo_plan: document.getElementById('tipoPlan').value,
                resultado: document.getElementById('resultado').value,
                monto: document.getElementById('monto').value || null,
                cuotas: document.getElementById('cuotas').value || 1,
                asesor: document.getElementById('asesor').value,
                fecha_seguimiento: document.getElementById('fechaSeguimiento').value || null,
                notas: document.getElementById('notas').value
            };
            if (!datos.fecha || !datos.contacto || !datos.tipo_plan || !datos.resultado || !datos.asesor) {
                alert('Complete los campos obligatorios');
                return;
            }
            const url = ventaId ? '/api/ventas/' + ventaId : '/api/ventas';
            const method = ventaId ? 'PUT' : 'POST';
            const res = await fetch(url, {
                method: method,
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(datos)
            });
            const resultado = await res.json();
            if (resultado.success) {
                alert(ventaId ? 'Venta actualizada' : 'Venta guardada');
                cancelarEdicion();
                cargarVentas();
                cargarSeguimiento('todos');
            }
        });

        function editarVenta(id) {
            const venta = todasLasVentas.find(v => v.id === id);
            if (!venta) return;
            document.getElementById('ventaId').value = venta.id;
            document.getElementById('fecha').value = venta.fecha;
            document.getElementById('contacto').value = venta.contacto;
            document.getElementById('cedula').value = venta.cedula || '';
            document.getElementById('telefono').value = venta.telefono || '';
            document.getElementById('email').value = venta.email || '';
            if (venta.provincia) {
                document.getElementById('provincia').value = venta.provincia;
                cargarCantones();
                if (venta.canton) {
                    document.getElementById('canton').value = venta.canton;
                    cargarDistritos();
                    if (venta.distrito) document.getElementById('distrito').value = venta.distrito;
                }
            }
            document.getElementById('tipoPlan').value = venta.tipo_plan;
            document.getElementById('resultado').value = venta.resultado;
            document.getElementById('monto').value = venta.monto || '';
            document.getElementById('cuotas').value = venta.cuotas || 1;
            document.getElementById('asesor').value = venta.asesor;
            document.getElementById('fechaSeguimiento').value = venta.fecha_seguimiento || '';
            document.getElementById('notas').value = venta.notas || '';
            document.getElementById('btnSubmit').textContent = 'Actualizar Venta';
            document.getElementById('btnCancelar').style.display = 'inline-block';
            window.scrollTo(0, 0);
        }

        function cancelarEdicion() {
            document.getElementById('ventaId').value = '';
            document.getElementById('formVenta').reset();
            document.getElementById('cuotas').value = 1;
            document.getElementById('btnSubmit').textContent = 'Agregar Venta';
            document.getElementById('btnCancelar').style.display = 'none';
        }

        async function eliminarVenta(id) {
            if (confirm('Eliminar?')) {
                await fetch('/api/ventas/' + id, { method: 'DELETE' });
                cargarVentas();
            }
        }

        async function cargarSeguimiento(filtro) {
            const res = await fetch('/api/ventas');
            const data = await res.json();
            const contenedor = document.getElementById('listaSeguimiento');
            if (!data.success) return;
            const hoy = new Date().toISOString().split('T')[0];
            let seguimientos = data.data.filter(v => v.fecha_seguimiento);
            if (filtro === 'hoy') seguimientos = seguimientos.filter(s => s.fecha_seguimiento === hoy);
            if (filtro === '7dias') {
                const limite = new Date();
                limite.setDate(limite.getDate() + 7);
                const limiteISO = limite.toISOString().split('T')[0];
                seguimientos = seguimientos.filter(s => s.fecha_seguimiento >= hoy && s.fecha_seguimiento <= limiteISO);
            }
            if (!seguimientos.length) {
                contenedor.innerHTML = '<div class="alerta">No hay seguimientos programados</div>';
                return;
            }
            let html = '<table><thead><tr><th>Fecha Seguimiento</th><th>Nombre</th><th>Telefono</th><th>Resultado</th><th>Asesor</th><th>Recordatorio</th></tr></thead><tbody>';
            seguimientos.forEach(s => {
                const telefono = s.telefono ? s.telefono.replace(/[^0-9]/g, '') : '';
                const waLink = telefono ? `https://wa.me/506${telefono}?text=${encodeURIComponent('Hola ' + s.contacto + ', le recordamos su seguimiento programado para hoy.')}` : '#';
                const mailLink = s.email ? `mailto:${s.email}?subject=${encodeURIComponent('Recordatorio de seguimiento')}&body=${encodeURIComponent('Hola ' + s.contacto + ', le recordamos su seguimiento programado.')}` : '#';
                html += `<tr>
                    <td>${s.fecha_seguimiento}</td>
                    <td>${s.contacto}</td>
                    <td>${s.telefono || '-'}</td>
                    <td>${s.resultado}</td>
                    <td>${s.asesor}</td>
                    <td>
                        <button class="btn-whatsapp" onclick="window.open('${waLink}', '_blank')">WhatsApp</button>
                        <button class="btn-correo" onclick="window.location.href='${mailLink}'">Correo</button>
                    </td>
                </tr>`;
            });
            html += '</tbody></table>';
            contenedor.innerHTML = html;
        }

        async function cargarClientes() {
            const res = await fetch('/api/clientes');
            const data = await res.json();
            if (data.success) {
                const tbody = document.getElementById('tablaClientes');
                tbody.innerHTML = '';
                data.data.forEach(c => {
                    const ubicacion = [c.distrito, c.canton, c.provincia].filter(Boolean).join(', ');
                    tbody.innerHTML += `<tr><td>${c.nombre}</td><td>${c.cedula || '-'}</td><td>${c.telefono || '-'}</td><td>${ubicacion || '-'}</td><td>${c.estado || '-'}</td><td><button class="btn-ver" onclick="verHistorial('${c.cedula || c.nombre}')">Ver</button></td></tr>`;
                });
            }
        }

        function filtrarClientes() {
            const busqueda = document.getElementById('busquedaCliente').value.toLowerCase();
            document.querySelectorAll('#tablaClientes tr').forEach(f => {
                f.style.display = f.textContent.toLowerCase().includes(busqueda) ? '' : 'none';
            });
        }

        async function verHistorial(identificador) {
            const res = await fetch('/api/historial?identificador=' + encodeURIComponent(identificador));
            const data = await res.json();
            if (data.success && data.data.length > 0) {
                let html = '<table><thead><tr><th>Fecha</th><th>Plan</th><th>Resultado</th><th>Monto</th><th>Asesor</th><th>Notas</th></tr></thead><tbody>';
                data.data.forEach(v => {
                    html += `<tr><td>${v.fecha}</td><td>${v.tipo_plan}</td><td>${v.resultado}</td><td>${v.monto ? Number(v.monto).toLocaleString() : '-'}</td><td>${v.asesor}</td><td>${v.notas || '-'}</td></tr>`;
                });
                html += '</tbody></table>';
                document.getElementById('contenidoHistorial').innerHTML = html;
                document.getElementById('modalHistorial').classList.add('show');
            } else {
                alert('No hay historial para este cliente');
            }
        }

        function cerrarModalHistorial() {
            document.getElementById('modalHistorial').classList.remove('show');
        }

        async function cargarMetas() {
            const res = await fetch('/api/metas');
            const data = await res.json();
            if (data.success) {
                let html = '<table><thead><tr><th>Asesor</th><th>Meta</th><th>Ventas</th></tr></thead><tbody>';
                data.data.forEach(m => {
                    html += `<tr><td>${m.asesor}</td><td>${m.meta}</td><td>${m.ventas}</td></tr>`;
                });
                html += '</tbody></table>';
                document.getElementById('contenidoMetas').innerHTML = html;
            }
        }

        async function cargarContratos() {
            const res = await fetch('/api/contratos');
            const data = await res.json();
            const tbody = document.getElementById('tablaContratos');
            if (data.success && data.data.length > 0) {
                let html = '';
                data.data.forEach(c => {
                    const cliente = c.ventas ? c.ventas.contacto : 'Sin cliente';
                    const plan = c.ventas ? c.ventas.tipo_plan : '-';
                    const monto = c.ventas ? Number(c.ventas.monto).toLocaleString() : '-';
                    const pdf = c.pdf_nombre ? `<a href="data:application/pdf;base64,${c.pdf_base64}" download="${c.pdf_nombre}">Descargar</a>` : 'No adjunto';
                    html += `<tr>
                        <td>${c.numero_contrato}</td>
                        <td>${cliente}</td>
                        <td>${plan}</td>
                        <td>${monto}</td>
                        <td>${c.estado}</td>
                        <td>${pdf}</td>
                        <td>
                            <button class="btn-editar" onclick="cambiarEstadoContrato('${c.id}', 'firmado')">Firmar</button>
                            <button class="btn-editar" onclick="cambiarEstadoContrato('${c.id}', 'anulado')">Anular</button>
                            <button class="btn-ver" onclick="subirPDF('${c.id}')">Subir PDF</button>
                        </td>
                    </tr>`;
                });
                tbody.innerHTML = html;
            } else {
                tbody.innerHTML = '<tr><td colspan="7">No hay contratos</td></tr>';
            }
        }

        async function cambiarEstadoContrato(id, estado) {
            const res = await fetch('/api/contratos/' + id + '/estado', {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({estado: estado})
            });
            const data = await res.json();
            if (data.success) cargarContratos();
            else alert('Error: ' + data.message);
        }

        function subirPDF(id) {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.pdf';
            input.onchange = async function(e) {
                const file = e.target.files[0];
                if (!file) return;
                const reader = new FileReader();
                reader.onload = async function(ev) {
                    const base64 = ev.target.result.split(',')[1];
                    const res = await fetch('/api/contratos/' + id + '/pdf', {
                        method: 'PUT',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({pdf_nombre: file.name, pdf_base64: base64})
                    });
                    const data = await res.json();
                    if (data.success) cargarContratos();
                    else alert('Error: ' + data.message);
                };
                reader.readAsDataURL(file);
            };
            input.click();
        }

        async function cargarNotificaciones() {
            const res = await fetch('/api/notificaciones');
            const data = await res.json();
            if (data.success) {
                const contenedor = document.getElementById('listaNotificaciones');
                if (!data.data.length) {
                    contenedor.innerHTML = '<div class="alerta-verde">No hay notificaciones pendientes</div>';
                    return;
                }
                let html = '';
                data.data.forEach(n => {
                    html += `<div class="${n.tipo === 'urgente' ? 'alerta-roja' : 'alerta'}"><strong>${n.titulo}</strong><br>${n.mensaje}</div>`;
                });
                contenedor.innerHTML = html;
            }
        }

        async function cargarAuditoria() {
            const res = await fetch('/api/auditoria');
            const data = await res.json();
            const contenedor = document.getElementById('listaAuditoria');
            if (data.success && data.data.length > 0) {
                let html = '<table><thead><tr><th>Fecha</th><th>Usuario</th><th>Accion</th><th>Detalle</th></tr></thead><tbody>';
                data.data.forEach(a => {
                    html += `<tr><td>${a.fecha}</td><td>${a.usuario}</td><td>${a.accion}</td><td>${a.detalle}</td></tr>`;
                });
                html += '</tbody></table>';
                contenedor.innerHTML = html;
            } else {
                contenedor.innerHTML = '<div class="alerta">No hay registros de auditoría</div>';
            }
        }

        async function cargarUsuarios() {
            const res = await fetch('/api/usuarios');
            const data = await res.json();
            if (data.success) {
                const tbody = document.getElementById('tablaUsuarios');
                tbody.innerHTML = '';
                data.data.forEach(u => {
                    tbody.innerHTML += `<tr><td>${u.usuario}</td><td>${u.nombre}</td><td>${u.rol}</td><td>${u.activo ? 'Si' : 'No'}</td><td><button class="btn-editar" onclick="editarUsuario('${u.id}')">Editar</button><button class="btn-eliminar" onclick="eliminarUsuario('${u.id}')">Eliminar</button></td></tr>`;
                });
            }
        }

        async function editarUsuario(id) {
            const res = await fetch('/api/usuarios');
            const data = await res.json();
            const usuario = data.data.find(u => u.id === id);
            if (usuario) {
                document.getElementById('usuarioId').value = usuario.id;
                document.getElementById('usuarioNombre').value = usuario.usuario;
                document.getElementById('usuarioPassword').value = '';
                document.getElementById('usuarioNombreCompleto').value = usuario.nombre;
                document.getElementById('usuarioRol').value = usuario.rol;
                document.getElementById('usuarioActivo').value = usuario.activo ? 'true' : 'false';
                document.getElementById('btnUsuarioSubmit').textContent = 'Actualizar Usuario';
                window.scrollTo(0, 0);
            }
        }

        async function eliminarUsuario(id) {
            if (confirm('Eliminar usuario?')) {
                await fetch('/api/usuarios/' + id, { method: 'DELETE' });
                cargarUsuarios();
            }
        }

        document.getElementById('formUsuario').addEventListener('submit', async function(e) {
            e.preventDefault();
            const id = document.getElementById('usuarioId').value;
            const datos = {
                usuario: document.getElementById('usuarioNombre').value,
                nombre: document.getElementById('usuarioNombreCompleto').value,
                rol: document.getElementById('usuarioRol').value,
                activo: document.getElementById('usuarioActivo').value === 'true'
            };
            if (document.getElementById('usuarioPassword').value) {
                datos.password = document.getElementById('usuarioPassword').value;
            }
            const url = id ? '/api/usuarios/' + id : '/api/usuarios';
            const method = id ? 'PUT' : 'POST';
            const res = await fetch(url, {
                method: method,
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(datos)
            });
            const resultado = await res.json();
            if (resultado.success) {
                alert(id ? 'Usuario actualizado' : 'Usuario creado');
                document.getElementById('formUsuario').reset();
                document.getElementById('btnUsuarioSubmit').textContent = 'Agregar Usuario';
                cargarUsuarios();
            } else {
                alert('Error: ' + resultado.message);
            }
        });

        async function generarContrato(id) {
            const venta = todasLasVentas.find(v => v.id === id);
            if (!venta) return;
            const numeroContrato = 'FM-' + new Date().getFullYear() + '-' + String(Math.floor(Math.random() * 10000)).padStart(4, '0');
            const res = await fetch('/api/contratos', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({venta_id: venta.id, numero_contrato: numeroContrato, estado: 'borrador'})
            });
            const data = await res.json();
            if (!data.success) {
                alert('Error al crear contrato: ' + data.message);
                return;
            }
            const contratoHTML = `<h3>CONTRATO DE SERVICIO FUNERARIO</h3><p><strong>Numero:</strong> ${numeroContrato}</p><p><strong>Fecha:</strong> ${new Date().toLocaleDateString('es-CR')}</p><hr><p><strong>Cliente:</strong> ${venta.contacto}</p><p><strong>Cedula:</strong> ${venta.cedula || 'No registrada'}</p><p><strong>Telefono:</strong> ${venta.telefono || 'No registrado'}</p><p><strong>Direccion:</strong> ${[venta.distrito, venta.canton, venta.provincia].filter(Boolean).join(', ')}</p><hr><p><strong>Plan:</strong> ${venta.tipo_plan}</p><p><strong>Monto:</strong> ₡${Number(venta.monto || 0).toLocaleString()}</p><p><strong>Cuotas:</strong> ${venta.cuotas || 1}</p><p><strong>Asesor:</strong> ${venta.asesor}</p><hr><p>El cliente acepta los terminos y condiciones del servicio funerario contratado.</p><p>_________________________</p><p>Firma del Cliente</p>`;
            document.getElementById('contenidoContrato').innerHTML = contratoHTML;
            document.getElementById('modalContrato').classList.add('show');
            await fetch('/api/auditoria', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({accion: 'Generar contrato', detalle: 'Contrato ' + numeroContrato + ' para ' + venta.contacto})});
        }

        function cerrarModalContrato() { document.getElementById('modalContrato').classList.remove('show'); }

        function cambiarReporte(tipo, boton) {
            reporteActual = tipo;
            document.querySelectorAll('.reporte-opciones button').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.reporte-contenido').forEach(c => c.style.display = 'none');
            boton.classList.add('active');
            document.getElementById('reporte-' + tipo).style.display = 'block';
            cargarTodosLosReportes();
        }

        async function cargarTodosLosReportes() {
            const res = await fetch('/api/reportes_completos');
            const data = await res.json();
            if (data.success) {
                const r = data.data;
                document.getElementById('rgVentas').textContent = r.total_ventas;
                document.getElementById('rgMonto').textContent = r.monto_total.toLocaleString();
                document.getElementById('rgComisiones').textContent = r.comisiones_totales.toLocaleString();
                let htmlAsesor = '';
                Object.keys(r.por_asesor).forEach(a => { const info = r.por_asesor[a]; htmlAsesor += `<tr><td>${a}</td><td>${info.ventas}</td><td>${info.monto.toLocaleString()}</td><td>${info.comision.toLocaleString()}</td></tr>`; });
                document.getElementById('repAsesor').innerHTML = htmlAsesor;
                let htmlPlan = '';
                Object.keys(r.por_plan).forEach(p => { const info = r.por_plan[p]; htmlPlan += `<tr><td>${p}</td><td>${info.ventas}</td><td>${info.monto.toLocaleString()}</td><td>${info.comision.toLocaleString()}</td></tr>`; });
                document.getElementById('repPlan').innerHTML = htmlPlan;
                let htmlProvincia = '';
                Object.keys(r.por_provincia).forEach(p => { const info = r.por_provincia[p]; htmlProvincia += `<tr><td>${p}</td><td>${info.ventas}</td><td>${info.monto.toLocaleString()}</td><td>${info.comision.toLocaleString()}</td></tr>`; });
                document.getElementById('repProvincia').innerHTML = htmlProvincia;
                let htmlCanton = '';
                Object.keys(r.por_canton).forEach(c => { const info = r.por_canton[c]; htmlCanton += `<tr><td>${c}</td><td>${info.provincia}</td><td>${info.ventas}</td><td>${info.monto.toLocaleString()}</td><td>${info.comision.toLocaleString()}</td></tr>`; });
                document.getElementById('repCanton').innerHTML = htmlCanton;
                let htmlDistrito = '';
                Object.keys(r.por_distrito).forEach(d => { const info = r.por_distrito[d]; htmlDistrito += `<tr><td>${d}</td><td>${info.canton}</td><td>${info.provincia}</td><td>${info.ventas}</td><td>${info.monto.toLocaleString()}</td><td>${info.comision.toLocaleString()}</td></tr>`; });
                document.getElementById('repDistrito').innerHTML = htmlDistrito;
            }
        }

        function exportarReporteActual() { window.location.href = '/api/exportar_reporte?tipo=' + reporteActual; }
        function exportarCSV() { window.location.href = '/api/exportar_csv'; }
    </script>
</body>
</html>
'''

# ====== RUTAS ======
@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    usuario = data.get('usuario', '')
    password = data.get('password', '')
    user = verificar_usuario(usuario, password)
    if user:
        session['usuario'] = user['usuario']
        session['rol'] = user['rol']
        session['nombre'] = user['nombre']
        registrar_auditoria(user['usuario'], 'Inicio de sesion')
        return jsonify({'success': True, 'nombre': user['nombre'], 'rol': user['rol']})
    return jsonify({'success': False, 'error': 'Credenciales invalidas'})

@app.route('/api/logout')
def logout():
    usuario = session.get('usuario', 'Desconocido')
    registrar_auditoria(usuario, 'Cierre de sesion')
    session.clear()
    return jsonify({'success': True})

@app.route('/api/auditoria', methods=['GET'])
def get_auditoria():
    if not supabase:
        return jsonify({'success': False, 'data': []})
    try:
        accion = request.args.get('accion', '')
        query = supabase.table('auditoria').select('*').order('fecha', desc=True)
        if accion:
            query = query.eq('accion', accion)
        response = query.execute()
        return jsonify({'success': True, 'data': response.data})
    except:
        return jsonify({'success': False, 'data': []})

@app.route('/api/auditoria', methods=['POST'])
def crear_auditoria():
    data = request.json
    usuario = session.get('usuario', 'Desconocido')
    registrar_auditoria(usuario, data.get('accion', ''), data.get('detalle', ''))
    return jsonify({'success': True})

@app.route('/api/notificaciones')
def get_notificaciones():
    if not supabase:
        return jsonify({'success': False, 'data': []})
    try:
        hoy = datetime.now().strftime('%Y-%m-%d')
        response = supabase.table('ventas').select('*').execute()
        ventas = response.data
        notificaciones = []
        seguimientos_hoy = [v for v in ventas if v.get('fecha_seguimiento') == hoy]
        if seguimientos_hoy:
            notificaciones.append({'tipo': 'urgente', 'titulo': 'Seguimientos para hoy', 'mensaje': f'Tienes {len(seguimientos_hoy)} seguimientos programados para hoy'})
        seguimientos_vencidos = [v for v in ventas if v.get('fecha_seguimiento') and v.get('fecha_seguimiento') < hoy and v.get('resultado') != 'Venta Concretada']
        if seguimientos_vencidos:
            notificaciones.append({'tipo': 'urgente', 'titulo': 'Seguimientos vencidos', 'mensaje': f'Tienes {len(seguimientos_vencidos)} seguimientos vencidos'})
        return jsonify({'success': True, 'data': notificaciones})
    except:
        return jsonify({'success': False, 'data': []})

@app.route('/api/dashboard')
def get_dashboard():
    if not supabase:
        return jsonify({'success': False})
    try:
        response = supabase.table('ventas').select('*').execute()
        ventas = response.data
        mes_actual = datetime.now().strftime('%Y-%m')
        hoy = datetime.now().strftime('%Y-%m-%d')
        ventas_mes = [v for v in ventas if v.get('fecha', '').startswith(mes_actual) and v.get('resultado') == 'Venta Concretada']
        monto_mes = sum(float(v.get('monto', 0)) for v in ventas_mes if v.get('monto'))
        comisiones_mes = sum(calcular_comision_completa(v) for v in ventas_mes)
        seguimientos_hoy = [v for v in ventas if v.get('fecha_seguimiento') == hoy]
        return jsonify({'success': True, 'data': {'ventas_mes': len(ventas_mes), 'monto_mes': monto_mes, 'comisiones_mes': comisiones_mes, 'seguimientos_hoy': len(seguimientos_hoy)}})
    except:
        return jsonify({'success': False})

@app.route('/api/ventas', methods=['GET'])
def get_ventas():
    if not supabase:
        return jsonify({'success': False, 'data': []})
    try:
        response = supabase.table('ventas').select('*').order('fecha', desc=True).execute()
        ventas = response.data
        for venta in ventas:
            venta['comision'] = calcular_comision_completa(venta)
        return jsonify({'success': True, 'data': ventas})
    except:
        return jsonify({'success': False, 'data': []})

@app.route('/api/ventas', methods=['POST'])
def crear_venta():
    if not supabase:
        return jsonify({'success': False, 'error': 'Sin conexion'})
    try:
        data = request.json
        supabase.table('ventas').insert(data).execute()
        usuario = session.get('usuario', 'Desconocido')
        registrar_auditoria(usuario, 'Crear venta', f"Venta para {data.get('contacto')}")
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ventas/<venta_id>', methods=['PUT'])
def actualizar_venta(venta_id):
    if not supabase:
        return jsonify({'success': False})
    try:
        data = request.json
        supabase.table('ventas').update(data).eq('id', venta_id).execute()
        usuario = session.get('usuario', 'Desconocido')
        registrar_auditoria(usuario, 'Actualizar venta', f"Venta ID: {venta_id}")
        return jsonify({'success': True})
    except:
        return jsonify({'success': False})

@app.route('/api/ventas/<venta_id>', methods=['DELETE'])
def eliminar_venta(venta_id):
    if not supabase:
        return jsonify({'success': False})
    try:
        supabase.table('ventas').delete().eq('id', venta_id).execute()
        usuario = session.get('usuario', 'Desconocido')
        registrar_auditoria(usuario, 'Eliminar venta', f"Venta ID: {venta_id}")
        return jsonify({'success': True})
    except:
        return jsonify({'success': False})

@app.route('/api/clientes')
def get_clientes():
    if not supabase:
        return jsonify({'success': False, 'data': []})
    try:
        response = supabase.table('ventas').select('*').order('fecha', desc=True).execute()
        ventas = response.data
        clientes = {}
        for v in ventas:
            cedula = v.get('cedula', '') or v.get('contacto', 'sin_cedula')
            if cedula not in clientes:
                clientes[cedula] = {
                    'nombre': v.get('contacto'), 'cedula': v.get('cedula', ''),
                    'telefono': v.get('telefono', ''), 'provincia': v.get('provincia', ''),
                    'canton': v.get('canton', ''), 'distrito': v.get('distrito', ''),
                    'estado': v.get('resultado', '')
                }
        return jsonify({'success': True, 'data': list(clientes.values())})
    except:
        return jsonify({'success': False, 'data': []})

@app.route('/api/historial')
def get_historial():
    if not supabase:
        return jsonify({'success': False, 'data': []})
    try:
        identificador = request.args.get('identificador', '')
        response = supabase.table('ventas').select('*').execute()
        ventas = [v for v in response.data if v.get('cedula') == identificador or v.get('contacto') == identificador]
        ventas.sort(key=lambda x: x.get('fecha', ''), reverse=True)
        return jsonify({'success': True, 'data': ventas})
    except:
        return jsonify({'success': False, 'data': []})

@app.route('/api/metas')
def get_metas():
    if not supabase:
        return jsonify({'success': False, 'data': []})
    try:
        mes_actual = datetime.now().strftime('%Y-%m')
        response = supabase.table('ventas').select('*').execute()
        ventas = response.data
        asesores_ventas = {}
        for v in ventas:
            if v.get('fecha', '').startswith(mes_actual) and v.get('resultado') == 'Venta Concretada':
                asesor = v.get('asesor', 'Sin asignar')
                asesores_ventas[asesor] = asesores_ventas.get(asesor, 0) + 1
        datos_metas = []
        for asesor, ventas_count in asesores_ventas.items():
            meta = METAS_MENSUALES.get(asesor, META_DEFAULT)
            datos_metas.append({'asesor': asesor, 'meta': meta, 'ventas': ventas_count})
        return jsonify({'success': True, 'data': datos_metas})
    except:
        return jsonify({'success': False, 'data': []})

@app.route('/api/reportes_completos')
def get_reportes_completos():
    if not supabase:
        return jsonify({'success': False})
    try:
        response = supabase.table('ventas').select('*').execute()
        ventas = response.data
        concretadas = [v for v in ventas if v.get('resultado') == 'Venta Concretada']
        por_asesor = {}
        por_plan = {}
        por_provincia = {}
        por_canton = {}
        por_distrito = {}
        monto_total = 0
        comisiones_totales = 0
        for v in ventas:
            if v.get('resultado') == 'Venta Concretada' and v.get('monto'):
                monto = float(v.get('monto', 0))
                comision = calcular_comision_completa(v)
                monto_total += monto
                comisiones_totales += comision
                asesor = v.get('asesor', 'Sin asignar')
                if asesor not in por_asesor:
                    por_asesor[asesor] = {'ventas': 0, 'monto': 0, 'comision': 0}
                por_asesor[asesor]['ventas'] += 1
                por_asesor[asesor]['monto'] += monto
                por_asesor[asesor]['comision'] += comision
                plan = v.get('tipo_plan', 'Sin plan')
                if plan not in por_plan:
                    por_plan[plan] = {'ventas': 0, 'monto': 0, 'comision': 0}
                por_plan[plan]['ventas'] += 1
                por_plan[plan]['monto'] += monto
                por_plan[plan]['comision'] += comision
                provincia = v.get('provincia', 'Sin provincia')
                if provincia not in por_provincia:
                    por_provincia[provincia] = {'ventas': 0, 'monto': 0, 'comision': 0}
                por_provincia[provincia]['ventas'] += 1
                por_provincia[provincia]['monto'] += monto
                por_provincia[provincia]['comision'] += comision
                canton = v.get('canton', 'Sin canton')
                if canton not in por_canton:
                    por_canton[canton] = {'provincia': provincia, 'ventas': 0, 'monto': 0, 'comision': 0}
                por_canton[canton]['ventas'] += 1
                por_canton[canton]['monto'] += monto
                por_canton[canton]['comision'] += comision
                distrito = v.get('distrito', 'Sin distrito')
                if distrito not in por_distrito:
                    por_distrito[distrito] = {'canton': canton, 'provincia': provincia, 'ventas': 0, 'monto': 0, 'comision': 0}
                por_distrito[distrito]['ventas'] += 1
                por_distrito[distrito]['monto'] += monto
                por_distrito[distrito]['comision'] += comision
        return jsonify({'success': True, 'data': {
            'total_ventas': len(concretadas),
            'monto_total': monto_total,
            'comisiones_totales': comisiones_totales,
            'por_asesor': por_asesor,
            'por_plan': por_plan,
            'por_provincia': por_provincia,
            'por_canton': por_canton,
            'por_distrito': por_distrito
        }})
    except:
        return jsonify({'success': False})

@app.route('/api/exportar_reporte')
def exportar_reporte():
    if not supabase:
        return "Sin conexion", 500
    try:
        tipo = request.args.get('tipo', 'general')
        response = supabase.table('ventas').select('*').execute()
        ventas = response.data
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Fecha', 'Nombre', 'Telefono', 'Provincia', 'Canton', 'Distrito', 'Plan', 'Resultado', 'Monto', 'Comision', 'Asesor'])
        for v in ventas:
            writer.writerow([v.get('fecha',''), v.get('contacto',''), v.get('telefono',''), v.get('provincia',''), v.get('canton',''), v.get('distrito',''), v.get('tipo_plan',''), v.get('resultado',''), v.get('monto',''), round(calcular_comision_completa(v),2), v.get('asesor','')])
        output.seek(0)
        return output.getvalue(), 200, {'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename=reporte.csv'}
    except Exception as e:
        return str(e), 500

@app.route('/api/exportar_csv')
def exportar_csv():
    if not supabase:
        return "Sin conexion", 500
    try:
        response = supabase.table('ventas').select('*').order('fecha', desc=True).execute()
        ventas = response.data
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Fecha', 'Nombre', 'Cedula', 'Telefono', 'Provincia', 'Canton', 'Distrito', 'Plan', 'Resultado', 'Monto', 'Comision', 'Asesor'])
        for v in ventas:
            writer.writerow([v.get('fecha',''), v.get('contacto',''), v.get('cedula',''), v.get('telefono',''), v.get('provincia',''), v.get('canton',''), v.get('distrito',''), v.get('tipo_plan',''), v.get('resultado',''), v.get('monto',''), round(calcular_comision_completa(v),2), v.get('asesor','')])
        output.seek(0)
        return output.getvalue(), 200, {'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename=ventas_mersha.csv'}
    except Exception as e:
        return str(e), 500

# ====== RUTAS DE CONTRATOS ======
@app.route('/api/contratos', methods=['GET'])
def get_contratos():
    contratos = listar_contratos_db()
    return jsonify({'success': True, 'data': contratos})

@app.route('/api/contratos', methods=['POST'])
def crear_contrato_route():
    data = request.json
    venta_id = data.get('venta_id')
    numero_contrato = data.get('numero_contrato')
    estado = data.get('estado', 'borrador')
    exito, mensaje = crear_contrato_db(venta_id, numero_contrato, estado)
    if exito:
        registrar_auditoria(session.get('usuario', 'admin'), 'Crear contrato', f"Contrato {numero_contrato}")
    return jsonify({'success': exito, 'message': mensaje})

@app.route('/api/contratos/<contrato_id>/estado', methods=['PUT'])
def actualizar_estado_contrato_route(contrato_id):
    data = request.json
    estado = data.get('estado', '')
    exito, mensaje = actualizar_estado_contrato(contrato_id, estado)
    if exito:
        registrar_auditoria(session.get('usuario', 'admin'), 'Actualizar contrato', f"Contrato ID: {contrato_id} -> {estado}")
    return jsonify({'success': exito, 'message': mensaje})

@app.route('/api/contratos/<contrato_id>/pdf', methods=['PUT'])
def adjuntar_pdf_route(contrato_id):
    data = request.json
    pdf_nombre = data.get('pdf_nombre', 'contrato.pdf')
    pdf_base64 = data.get('pdf_base64', '')
    exito, mensaje = adjuntar_pdf_contrato(contrato_id, pdf_nombre, pdf_base64)
    if exito:
        registrar_auditoria(session.get('usuario', 'admin'), 'Adjuntar PDF', f"Contrato ID: {contrato_id}")
    return jsonify({'success': exito, 'message': mensaje})

# ====== RUTAS DE USUARIOS ======
@app.route('/api/usuarios', methods=['GET'])
def get_usuarios():
    if not supabase:
        return jsonify({'success': False, 'data': []})
    try:
        response = supabase.table('usuarios').select('*').order('creado_en', desc=False).execute()
        usuarios = []
        for u in response.data:
            usuarios.append({'id': u.get('id'), 'usuario': u.get('usuario'), 'nombre': u.get('nombre'), 'rol': u.get('rol'), 'activo': u.get('activo', True)})
        return jsonify({'success': True, 'data': usuarios})
    except:
        return jsonify({'success': False, 'data': []})

@app.route('/api/usuarios', methods=['POST'])
def crear_usuario_route():
    data = request.json
    usuario = data.get('usuario', '')
    password = data.get('password', '')
    nombre = data.get('nombre', '')
    rol = data.get('rol', 'asesor')
    if not usuario or not password or not nombre:
        return jsonify({'success': False, 'message': 'Todos los campos son obligatorios'})
    exito, mensaje = crear_usuario_db(usuario, password, nombre, rol)
    if exito:
        registrar_auditoria(session.get('usuario', 'admin'), 'Crear usuario', f"Usuario {usuario}")
    return jsonify({'success': exito, 'message': mensaje})

@app.route('/api/usuarios/<usuario_id>', methods=['PUT'])
def actualizar_usuario_route(usuario_id):
    data = request.json
    nombre = data.get('nombre', '')
    rol = data.get('rol', 'asesor')
    activo = data.get('activo', True)
    password = data.get('password', '')
    exito, mensaje = actualizar_usuario_db(usuario_id, nombre, rol, activo, password if password else None)
    if exito:
        registrar_auditoria(session.get('usuario', 'admin'), 'Actualizar usuario', f"ID: {usuario_id}")
    return jsonify({'success': exito, 'message': mensaje})

@app.route('/api/usuarios/<usuario_id>', methods=['DELETE'])
def eliminar_usuario_route(usuario_id):
    if not supabase:
        return jsonify({'success': False, 'error': 'Sin conexión'})
    try:
        supabase.table('usuarios').delete().eq('id', usuario_id).execute()
        registrar_auditoria(session.get('usuario', 'admin'), 'Eliminar usuario', f"ID: {usuario_id}")
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("Servidor iniciado en http://localhost:5000")
    app.run(debug=True, port=5000)
flask==3.0.0
supabase==2.0.0
python-dotenv==1.0.0
