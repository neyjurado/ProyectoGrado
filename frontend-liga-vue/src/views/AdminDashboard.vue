<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const vistaActual = ref('jugadores') 

const calcularFechaMaxima = () => {
    const hoy = new Date(); hoy.setFullYear(hoy.getFullYear() - 15); return hoy.toISOString().split('T')[0];
}
const fechaMaximaPermitida = ref(calcularFechaMaxima())

// VARIABLES JUGADORES
const equipos = ref([])
const jugadoresRegistrados = ref([]) 
const cargando = ref(false)
const mensajeError = ref('')
const mensajeExito = ref('')
const mostrarCarnet = ref(false)

const cedula = ref('')
const id_equipo = ref('')
const nombre = ref('')
const apellido = ref('')
const fecha_nacimiento = ref('')
const numero_camiseta = ref('')
const acepta_terminos = ref(false) 

const editandoJugador = ref(false)
const idJugadorEditando = ref(null)
const filtroBusqueda = ref('') 
const filtroEquipoSelect = ref('') 

const videoRef = ref(null)
const canvasRef = ref(null)
const camaraAbierta = ref(false)
const fotoTomada = ref(false)
const fotoBase64 = ref('')

const docPreview = ref('')
const docSeleccionado = ref(null)

const datosCarnet = ref({ nombre: '', apellido: '', equipo: '', categoria: '', cedula: '', numero_camiseta: '', fotoBase64: '', logoEquipo: '' })
const jugadoresSuspendidos = ref([])
const fotoVocaliaArchivo = ref(null)
const fotoVocaliaPreview = ref('')

const seleccionarDocumento = (event) => {
    const archivo = event.target.files[0]
    if (!archivo) return
    if (!archivo.type.startsWith('image/')) {
        mensajeError.value = "Selecciona una imagen válida (PNG, JPG) para el documento."
        window.scrollTo({ top: 0, behavior: 'smooth' });
        return
    }
    docSeleccionado.value = archivo
    docPreview.value = URL.createObjectURL(archivo)
}
const removerDocumento = () => { docPreview.value = ''; docSeleccionado.value = null; }

const equipoSeleccionado = computed(() => {
    const eq = equipos.value.find(e => e.id === id_equipo.value)
    return eq ? { nombre: eq.nombre, categoria: eq.categoria } : { nombre: 'EQUIPO', categoria: 'CATEGORÍA' }
})

// VARIABLES EQUIPOS Y ÁRBITROS
const cargandoEquipo = ref(false)
const msjErrorEquipo = ref('')
const msjExitoEquipo = ref('')
const editandoEquipo = ref(false)
const idEquipoEditando = ref(null)
const nuevoEquipo = ref({ nombre: '', fecha_fundacion: '', categoria: '', url_logo: '' })
const logoPreview = ref('')
const archivoSeleccionado = ref(null)

const formatearTextoMayusculas = (valor) => (valor || '').toUpperCase()
const fechaMaximaFundacion = new Date().toISOString().split('T')[0]
const fechaMinimaFundacion = new Date(Date.now() - 1000 * 60 * 60 * 24 * 365 * 50).toISOString().split('T')[0]

const normalizarEntero = (valor, minimo, maximo) => {
    const numero = Number.parseInt(valor, 10)
    if (Number.isNaN(numero)) return minimo
    return Math.min(Math.max(numero, minimo), maximo)
}

const mostrarModalPlantilla = ref(false)
const equipoSeleccionadoPlantilla = ref('')
const jugadoresFiltradosPlantilla = ref([])

const arbitros = ref([])
const cargandoArbitro = ref(false)
const msjErrorArbitro = ref('')
const msjExitoArbitro = ref('')
const nuevoArbitro = ref({ nombre: '', apellido: '', cedula: '', experiencia_anios: '' })
const arbitroFotoPreview = ref('')
const archivoArbitroSeleccionado = ref(null)

// VARIABLES CALENDARIO Y RESULTADOS
const partidos = ref([])
const cargandoCalendario = ref(false)
const formCalendario = ref({ fecha_inicio: '' })

const mostrarModalEditarPartido = ref(false)
const idPartidoEditando = ref(null)
const formEditarPartido = ref({ fecha: '', hora: '', id_arbitro: '' })

const mostrarModalVocalia = ref(false)
const partidoSeleccionadoVocalia = ref(null)
const plantillaLocalVocalia = ref([])
const plantillaVisitanteVocalia = ref([])
const golesLocalForm = ref(0)
const golesVisitanteForm = ref(0)
const novedadesForm = ref('') // NUEVO: Campo de novedades en vocalía

const mostrarModalActaFinalizada = ref(false)
const actaFinalizadaData = ref(null)
const detallesActa = ref({ novedades: '', incidencias_local: [], incidencias_visitante: [] }) // NUEVO: Para guardar detalle del acta
const cargandoActa = ref(false)

// VARIABLES ESTADÍSTICAS Y GESTIÓN DE TORNEO
const categoriaEstadisticas = ref('Máxima')
const tablaPosiciones = ref([])
const maxGoleadores = ref([])

const filtroTraspasoBusqueda = ref('') 
const filtroTraspasoDestino = ref('') // NUEVO: Filtro para equipo destino
const formTraspaso = ref({ id_jugador: '', id_nuevo_equipo: '', nuevo_numero_camiseta: '' })
const msjTraspasoError = ref('')
const msjTraspasoExito = ref('')

// CARGA DE DATOS
const cargarEquipos = async () => { try { const res = await fetch('http://127.0.0.1:8000/equipos'); equipos.value = await res.json(); } catch (err) {} }
const cargarJugadores = async () => { try { const res = await fetch('http://127.0.0.1:8000/jugadores'); if(res.ok) jugadoresRegistrados.value = await res.json(); } catch (err) {} }
const cargarArbitros = async () => { try { const res = await fetch('http://127.0.0.1:8000/arbitros'); if(res.ok) arbitros.value = await res.json(); } catch (err) {} }
const cargarPartidos = async () => { try { const res = await fetch('http://127.0.0.1:8000/partidos'); if(res.ok) partidos.value = await res.json(); } catch (err) {} }
const cargarJugadoresSuspendidos = async () => { try { const res = await fetch('http://127.0.0.1:8000/jugadores/suspendidos'); if(res.ok) jugadoresSuspendidos.value = await res.json(); } catch (err) {} }

const cargarEstadisticas = async () => {
    try {
        const resPos = await fetch(`http://127.0.0.1:8000/estadisticas/posiciones/${categoriaEstadisticas.value}`)
        if (resPos.ok) tablaPosiciones.value = await resPos.json()
        const resGol = await fetch(`http://127.0.0.1:8000/goleadores/${categoriaEstadisticas.value}`)
        if (resGol.ok) maxGoleadores.value = await resGol.json()
    } catch (err) {}
}

onMounted(async () => {
    const usuarioSesion = JSON.parse(localStorage.getItem('usuario'))
    if (!usuarioSesion) { router.push('/login'); return; }
    await cargarEquipos(); await cargarJugadores(); await cargarArbitros(); await cargarPartidos(); await cargarEstadisticas(); await cargarJugadoresSuspendidos();
})
const cerrarSesion = () => { localStorage.removeItem('usuario'); router.push('/login'); }

// COMPUTADAS
const jugadoresFiltrados = computed(() => {
    return jugadoresRegistrados.value.filter(j => {
        const texto = filtroBusqueda.value.toLowerCase();
        const match = j.nombre.toLowerCase().includes(texto) || j.apellido.toLowerCase().includes(texto) || j.cedula.toLowerCase().includes(texto);
        const matchEq = filtroEquipoSelect.value === '' || j.id_equipo === parseInt(filtroEquipoSelect.value);
        return match && matchEq;
    });
})

const jugadoresParaTraspaso = computed(() => {
    const txt = filtroTraspasoBusqueda.value.toLowerCase();
    if(!txt) return jugadoresRegistrados.value;
    return jugadoresRegistrados.value.filter(j => 
        j.nombre.toLowerCase().includes(txt) || 
        j.apellido.toLowerCase().includes(txt) || 
        j.cedula.includes(txt)
    );
})

// NUEVO: Filtro para equipo destino
const equiposDestinoParaTraspaso = computed(() => {
    const txt = filtroTraspasoDestino.value.toLowerCase();
    if(!txt) return equipos.value;
    return equipos.value.filter(eq => eq.nombre.toLowerCase().includes(txt));
})

const partidosPendientes = computed(() => partidos.value.filter(p => p.estado === 'Pendiente'))
const hayPartidosPendientes = computed(() => partidosPendientes.value.length > 0)
const contarJugadores = (id) => jugadoresRegistrados.value.filter(j => j.id_equipo === id).length
const obtenerLogoEquipo = (nombre) => { const eq = equipos.value.find(e => e.nombre === nombre); return eq ? eq.url_logo : null; }

// HELPERS MULTIMEDIA
const abrirCamara = async () => { try { const stream = await navigator.mediaDevices.getUserMedia({ video: true }); videoRef.value.srcObject = stream; camaraAbierta.value = true; fotoTomada.value = false; fotoBase64.value = ''; } catch (err) { mensajeError.value = "No se pudo acceder a la cámara."; } }
const capturarFoto = () => { const context = canvasRef.value.getContext('2d'); context.drawImage(videoRef.value, 0, 0, 320, 240); fotoBase64.value = canvasRef.value.toDataURL('image/png'); fotoTomada.value = true; camaraAbierta.value = false; const stream = videoRef.value.srcObject; if (stream) stream.getTracks().forEach(track => track.stop()); }
const imprimirCarnet = () => window.print()

const base64ToFile = async (base64String, filename) => { const res = await fetch(base64String); const blob = await res.blob(); return new File([blob], filename, { type: 'image/png' }); }
const uploadToFirebase = async (file, folder) => { const formData = new FormData(); formData.append('file', file); formData.append('folder', folder); const res = await fetch('http://127.0.0.1:8000/upload-image', { method: 'POST', body: formData }); const data = await res.json(); if (!res.ok) throw new Error(data.detail); return data.url; }

const limpiarFormularioJugador = () => { editandoJugador.value = false; idJugadorEditando.value = null; cedula.value = ''; id_equipo.value = ''; nombre.value = ''; apellido.value = ''; fecha_nacimiento.value = ''; numero_camiseta.value = ''; acepta_terminos.value = false; fotoBase64.value = ''; fotoTomada.value = false; camaraAbierta.value = false; removerDocumento(); mensajeError.value = ''; mensajeExito.value = ''; }
const validarCedula = (event) => { const valor = (event?.target?.value ?? cedula.value).replace(/\D/g, '').slice(0, 10); cedula.value = valor }
const validarJugadorFormulario = () => {
    const textoCedula = cedula.value.trim()
    if (!/^[0-9]{1,10}$/.test(textoCedula)) return 'La cédula debe tener solo números y máximo 10 dígitos.'
    if (!nombre.value.trim() || !apellido.value.trim()) return 'Ingresa nombres y apellidos del jugador.'
    if (!fecha_nacimiento.value) return 'Selecciona la fecha de nacimiento.'
    const edad = new Date().getFullYear() - new Date(fecha_nacimiento.value).getFullYear()
    if (edad < 15) return 'El jugador debe ser mayor de 15 años para registrarse.'
    if (!id_equipo.value) return 'Selecciona un equipo para el jugador.'
    const camiseta = Number(numero_camiseta.value)
    if (!Number.isInteger(camiseta) || camiseta < 1 || camiseta > 99) return 'El número de camiseta debe estar entre 1 y 99.'
    if (!fotoBase64.value) return 'Toma o sube una foto del jugador antes de guardar.'
    if (!editandoJugador.value && !docSeleccionado.value) return 'Adjunta una imagen del documento del jugador.'
    if (!acepta_terminos.value) return 'Debes aceptar los términos y condiciones.'
    return ''
}

// ACCIONES JUGADORES
const prepararReimpresion = (j) => { datosCarnet.value = { nombre: j.nombre, apellido: j.apellido, equipo: j.nombre_equipo, categoria: j.categoria_equipo, cedula: j.cedula, numero_camiseta: j.numero_camiseta, fotoBase64: j.url_foto, logoEquipo: obtenerLogoEquipo(j.nombre_equipo) }; mostrarCarnet.value = true; window.scrollTo({ top: 0, behavior: 'smooth' }); }
const prepararEdicionJugador = (j) => { editandoJugador.value = true; idJugadorEditando.value = j.id_jugador; cedula.value = j.cedula; nombre.value = j.nombre; apellido.value = j.apellido; fecha_nacimiento.value = j.fecha_nacimiento; numero_camiseta.value = j.numero_camiseta; id_equipo.value = j.id_equipo; fotoBase64.value = j.url_foto || ''; fotoTomada.value = !!j.url_foto; docPreview.value = j.url_documento || ''; acepta_terminos.value = true; window.scrollTo({ top: 0, behavior: 'smooth' }); }
const eliminarJugador = async (id, n) => { if (!confirm(`¿Dar de baja a ${n}?`)) return; try { const res = await fetch(`http://127.0.0.1:8000/jugadores/${id}`, { method: 'DELETE' }); if (res.ok) { alert("Dado de baja."); await cargarJugadores(); } } catch (err) {} }
const manejarSuspensionJugador = async (jugador) => {
    if (jugador.suspendido_hasta) {
        if (!confirm(`¿Quitar la suspensión de ${jugador.nombre} ${jugador.apellido}?`)) return
        try {
            const res = await fetch(`http://127.0.0.1:8000/jugadores/${jugador.id_jugador}/suspender`, { method: 'DELETE' })
            if (res.ok) { await cargarJugadores(); await cargarJugadoresSuspendidos(); mensajeExito.value = 'Suspensión removida.'; setTimeout(() => { mensajeExito.value = '' }, 3000) }
        } catch (err) {}
        return
    }
    const motivo = window.prompt('Motivo de la suspensión por un año', 'Conducta reiterada')
    if (!motivo || !motivo.trim()) return
    try {
        const res = await fetch(`http://127.0.0.1:8000/jugadores/${jugador.id_jugador}/suspender`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ motivo: motivo.trim() }) })
        if (res.ok) { await cargarJugadores(); await cargarJugadoresSuspendidos(); mensajeExito.value = 'Jugador suspendido por un año.'; setTimeout(() => { mensajeExito.value = '' }, 3000) }
        else { const d = await res.json(); mensajeError.value = d.detail || 'No se pudo suspender.' }
    } catch (err) { mensajeError.value = 'No se pudo registrar la suspensión.' }
}

const registrarJugador = async () => {
    const validacion = validarJugadorFormulario()
    if (validacion) { mensajeError.value = validacion; window.scrollTo({ top: 0, behavior: 'smooth' }); return; }
    mensajeError.value = ''
    cargando.value = true; mensajeError.value = ''; mensajeExito.value = '';
    try {
        let rf = fotoBase64.value, df = docPreview.value;
        if (fotoBase64.value.startsWith('data:image')) rf = await uploadToFirebase(await base64ToFile(fotoBase64.value, `r_${cedula.value}.png`), 'jugadores_rostros');
        if (docSeleccionado.value) df = await uploadToFirebase(docSeleccionado.value, 'jugadores_documentos');
        const payload = { cedula: cedula.value, id_equipo: parseInt(id_equipo.value), nombre: nombre.value, apellido: apellido.value, fecha_nacimiento: fecha_nacimiento.value, url_foto: rf, numero_camiseta: parseInt(numero_camiseta.value), url_documento: df, acepta_terminos: acepta_terminos.value }
        const res = await fetch(editandoJugador.value ? `http://127.0.0.1:8000/jugadores/${idJugadorEditando.value}` : 'http://127.0.0.1:8000/jugadores', { method: editandoJugador.value ? 'PUT' : 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
        if (res.ok) { datosCarnet.value = { nombre: nombre.value, apellido: apellido.value, equipo: equipoSeleccionado.value.nombre, categoria: equipoSeleccionado.value.categoria, cedula: cedula.value, numero_camiseta: numero_camiseta.value, fotoBase64: rf, logoEquipo: obtenerLogoEquipo(equipoSeleccionado.value.nombre) }; mostrarCarnet.value = true; await cargarJugadores(); limpiarFormularioJugador(); mensajeExito.value = "Guardado con éxito."; setTimeout(() => { mensajeExito.value = '' }, 4000); }
        else { const d = await res.json(); mensajeError.value = d.detail; window.scrollTo({ top: 0, behavior: 'smooth' }); }
    } catch (err) { mensajeError.value = "Error de conexión."; window.scrollTo({ top: 0, behavior: 'smooth' }); } finally { cargando.value = false; }
}

// ACCIONES EQUIPOS
const seleccionarEscudo = (event) => { const archivo = event.target.files[0]; if (!archivo) return; archivoSeleccionado.value = archivo; logoPreview.value = URL.createObjectURL(archivo); }
const removerEscudo = () => { logoPreview.value = ''; archivoSeleccionado.value = null; }
const prepararEdicionEquipo = (equipo) => { editandoEquipo.value = true; idEquipoEditando.value = equipo.id; nuevoEquipo.value.nombre = formatearTextoMayusculas(equipo.nombre); nuevoEquipo.value.categoria = equipo.categoria; logoPreview.value = equipo.url_logo || ''; window.scrollTo({ top: 0, behavior: 'smooth' }); }
const eliminarEquipo = async (id, n) => { 
    if (contarJugadores(id) > 0) { alert("⚠️ No se puede eliminar: El equipo contiene jugadores registrados."); return; } 
    if (!confirm(`¿Dar de baja al equipo ${n}?`)) return; 
    try { 
        const res = await fetch(`http://127.0.0.1:8000/equipos/${id}`, { method: 'DELETE' }); 
        if (res.ok) { alert("🏆 Equipo eliminado."); await cargarEquipos(); await cargarEstadisticas(); } 
        else { const d = await res.json(); alert(`⚠️ Restricción SQL:\n${d.detail}\n💡 Nota: Partidos vinculados impiden el borrado.`); } 
    } catch (e) { alert("❌ Error de red."); } 
}
const verPlantilla = (equipo) => { equipoSeleccionadoPlantilla.value = equipo.nombre; jugadoresFiltradosPlantilla.value = jugadoresRegistrados.value.filter(j => j.id_equipo === equipo.id); mostrarModalPlantilla.value = true; }

const registrarEquipo = async () => { cargandoEquipo.value = true; msjErrorEquipo.value = ''; msjExitoEquipo.value = ''; let logo = logoPreview.value; try { const nombreEquipo = formatearTextoMayusculas(nuevoEquipo.value.nombre); nuevoEquipo.value.nombre = nombreEquipo; if (archivoSeleccionado.value) logo = await uploadToFirebase(archivoSeleccionado.value, 'equipos'); const res = await fetch(editandoEquipo.value ? `http://127.0.0.1:8000/equipos/${idEquipoEditando.value}` : 'http://127.0.0.1:8000/equipos', { method: editandoEquipo.value ? 'PUT' : 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ nombre_equipo: nombreEquipo, categoria: nuevoEquipo.value.categoria, fecha_fundacion: nuevoEquipo.value.fecha_fundacion || null, url_logo: logo }) }); if (res.ok) { nuevoEquipo.value = { nombre: '', fecha_fundacion: '', categoria: '', url_logo: '' }; editandoEquipo.value = false; removerEscudo(); await cargarEquipos(); await cargarEstadisticas(); msjExitoEquipo.value="Éxito"; setTimeout(()=>msjExitoEquipo.value='', 3000); } else { const d = await res.json(); msjErrorEquipo.value = d.detail; } } catch (e) {} finally { cargandoEquipo.value = false; } }
const cancelarEdicionEquipo = () => { editandoEquipo.value = false; nuevoEquipo.value = { nombre: '', fecha_fundacion: '', categoria: '', url_logo: '' }; removerEscudo(); }

// ACCIONES ÁRBITROS
const seleccionarArbitroFoto = (event) => { const archivo = event.target.files[0]; if (!archivo) return; archivoArbitroSeleccionado.value = archivo; arbitroFotoPreview.value = URL.createObjectURL(archivo); }
const removerArbitroFoto = () => { arbitroFotoPreview.value = ''; archivoArbitroSeleccionado.value = null; }
const registrarArbitro = async () => { cargandoArbitro.value = true; msjErrorArbitro.value = ''; let f = null; try { if (archivoArbitroSeleccionado.value) f = await uploadToFirebase(archivoArbitroSeleccionado.value, 'arbitros'); const res = await fetch('http://127.0.0.1:8000/arbitros', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ nombre: nuevoArbitro.value.nombre.trim(), apellido: nuevoArbitro.value.apellido.trim(), cedula: nuevoArbitro.value.cedula ? nuevoArbitro.value.cedula.trim() : null, experiencia_anios: nuevoArbitro.value.experiencia_anios ? parseInt(nuevoArbitro.value.experiencia_anios) : null, url_foto: f }) }); if (res.ok) { nuevoArbitro.value = { nombre: '', apellido: '', cedula: '', experiencia_anios: '' }; removerArbitroFoto(); await cargarArbitros(); msjExitoArbitro.value="Registrado"; setTimeout(()=>msjExitoArbitro.value='', 3000); } else { const d = await res.json(); msjErrorArbitro.value = d.detail || 'No se pudo registrar el árbitro.'; } } catch (e) { msjErrorArbitro.value = 'Error de red.'; } finally { cargandoArbitro.value = false; } }

// CALENDARIO Y VOCALÍA
const obtenerPasswordFixture = async () => {
    const passwordIngresado = window.prompt('Ingresa la contraseña para generar el fixture', '')
    if (!passwordIngresado || !passwordIngresado.trim()) return null
    return passwordIngresado.trim()
}

const generarFixtureConPassword = async (password) => {
    const res = await fetch('http://127.0.0.1:8000/generar-calendario', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...formCalendario.value, password })
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) throw new Error(data.detail || 'No se pudo generar el fixture.')
    return data.mensaje || 'Fixture generado correctamente.'
}

const textoErrorApi = (detalle, fallback) => {
    if (!detalle) return fallback
    if (typeof detalle === 'string') return detalle
    if (Array.isArray(detalle)) {
        return detalle
            .map((item) => item?.msg || item?.detail || JSON.stringify(item))
            .join(' | ')
    }
    if (typeof detalle === 'object') {
        return detalle.detail || JSON.stringify(detalle)
    }
    return String(detalle)
}

const borrarFixtureConPassword = async (password) => {
    const res = await fetch('http://127.0.0.1:8000/partidos/fixture', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) throw new Error(textoErrorApi(data.detail, 'No se pudo borrar el fixture.'))
    return data.mensaje || 'Fixture eliminado correctamente.'
}

const dispararGeneracionCalendario = async () => {
    if (!confirm('¿Generar el fixture con la fecha seleccionada?')) return
    const password = await obtenerPasswordFixture()
    if (!password) return
    cargandoCalendario.value = true
    try {
        const mensaje = await generarFixtureConPassword(password)
        await cargarPartidos()
        await cargarEstadisticas()
        alert(mensaje)
    } catch (e) {
        alert(textoErrorApi(e?.message, 'Error de red'))
    } finally {
        cargandoCalendario.value = false
    }
}

const recrearFixtureCalendario = async () => {
    if (!confirm('¿Eliminar el fixture actual y crear uno nuevo?')) return
    const password = await obtenerPasswordFixture()
    if (!password) return
    cargandoCalendario.value = true
    try {
        await borrarFixtureConPassword(password)
        const mensaje = await generarFixtureConPassword(password)
        await cargarPartidos()
        await cargarEstadisticas()
        alert(mensaje)
    } catch (e) {
        alert(textoErrorApi(e?.message, 'Error de red'))
    } finally {
        cargandoCalendario.value = false
    }
}

const borrarFixtureActual = async () => {
    if (!confirm('¿Eliminar solo el fixture actual?')) return
    const password = await obtenerPasswordFixture()
    if (!password) return
    cargandoCalendario.value = true
    try {
        const mensaje = await borrarFixtureConPassword(password)
        await cargarPartidos()
        await cargarEstadisticas()
        alert(mensaje)
    } catch (e) {
        alert(textoErrorApi(e?.message, 'Error de red'))
    } finally {
        cargandoCalendario.value = false
    }
}
const abrirModalEditarPartido = (partido) => { idPartidoEditando.value = partido.id_partido; formEditarPartido.value = { fecha: partido.fecha, hora: partido.hora, id_arbitro: partido.id_arbitro || '', id_arbitro_2: partido.id_arbitro_2 || '', id_arbitro_3: partido.id_arbitro_3 || '' }; mostrarModalEditarPartido.value = true; }
const guardarEdicionPartido = async () => { try { const res = await fetch(`http://127.0.0.1:8000/partidos/${idPartidoEditando.value}`, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ fecha: formEditarPartido.value.fecha, hora: formEditarPartido.value.hora, id_arbitro: formEditarPartido.value.id_arbitro ? parseInt(formEditarPartido.value.id_arbitro) : null, id_arbitro_2: formEditarPartido.value.id_arbitro_2 ? parseInt(formEditarPartido.value.id_arbitro_2) : null, id_arbitro_3: formEditarPartido.value.id_arbitro_3 ? parseInt(formEditarPartido.value.id_arbitro_3) : null }) }); if (res.ok) { mostrarModalEditarPartido.value = false; await cargarPartidos(); alert("Partido actualizado."); } else { const d = await res.json(); alert(d.detail); } } catch (e) {} }

// NUEVO: Ver Acta Extrae la información detallada desde la base de datos
const verActaFinalizada = async (p) => { 
    actaFinalizadaData.value = p; 
    mostrarModalActaFinalizada.value = true; 
    cargandoActa.value = true;
    try {
        const res = await fetch(`http://127.0.0.1:8000/partidos/${p.id_partido}/acta_detalles`)
        if(res.ok) {
            detallesActa.value = await res.json()
        }
    } catch (err) {
        console.error("Error al cargar detalles")
    } finally {
        cargandoActa.value = false;
    }
}

const seleccionarFotoVocalia = (event) => {
    const archivo = event.target.files[0]
    if (!archivo) return
    fotoVocaliaArchivo.value = archivo
    fotoVocaliaPreview.value = URL.createObjectURL(archivo)
}
const removerFotoVocalia = () => {
    fotoVocaliaPreview.value = ''
    fotoVocaliaArchivo.value = null
}
const abrirMesaVocalia = async (partido) => {
    partidoSeleccionadoVocalia.value = partido; golesLocalForm.value = 0; golesVisitanteForm.value = 0; novedadesForm.value = ''; removerFotoVocalia();
    try {
        const res = await fetch(`http://127.0.0.1:8000/partidos/${partido.id_partido}/vocalia`)
        if (res.ok) {
            const d = await res.json();
            plantillaLocalVocalia.value = d.jugadores_local.map(j => ({ ...j, goles: 0, amarillas: 0, rojas: 0 }))
            plantillaVisitanteVocalia.value = d.jugadores_visitante.map(j => ({ ...j, goles: 0, amarillas: 0, rojas: 0 }))
            mostrarModalVocalia.value = true
        }
    } catch (err) {}
}

const enviarActaVocalia = async () => {
    plantillaLocalVocalia.value.forEach(j => {
        j.goles = normalizarEntero(j.goles, 0, 99)
        j.amarillas = normalizarEntero(j.amarillas, 0, 2)
        j.rojas = normalizarEntero(j.rojas, 0, 1)
    })
    plantillaVisitanteVocalia.value.forEach(j => {
        j.goles = normalizarEntero(j.goles, 0, 99)
        j.amarillas = normalizarEntero(j.amarillas, 0, 2)
        j.rojas = normalizarEntero(j.rojas, 0, 1)
    })
    golesLocalForm.value = normalizarEntero(golesLocalForm.value, 0, 99)
    golesVisitanteForm.value = normalizarEntero(golesVisitanteForm.value, 0, 99)

    const sl = plantillaLocalVocalia.value.reduce((a, j) => a + Number(j.goles), 0);
    const sv = plantillaVisitanteVocalia.value.reduce((a, j) => a + Number(j.goles), 0);
    
    if (sl !== parseInt(golesLocalForm.value)) { alert(`Error: Goles individuales del Local suman ${sl}, marcador global dice ${golesLocalForm.value}.`); return; }
    if (sv !== parseInt(golesVisitanteForm.value)) { alert(`Error: Goles individuales del Visitante suman ${sv}, marcador global dice ${golesVisitanteForm.value}.`); return; }
    if (!confirm("¿Confirmas los datos? Se cerrará el partido.")) return;
    
    const incL = plantillaLocalVocalia.value.filter(j => j.goles > 0 || j.amarillas > 0 || j.rojas > 0).map(j => ({ id_jugador: j.id_jugador, goles: j.goles, amarillas: j.amarillas, rojas: j.rojas }))
    const incV = plantillaVisitanteVocalia.value.filter(j => j.goles > 0 || j.amarillas > 0 || j.rojas > 0).map(j => ({ id_jugador: j.id_jugador, goles: j.goles, amarillas: j.amarillas, rojas: j.rojas }))
    
    try {
        let fotoVocaliaUrl = ''
        if (fotoVocaliaArchivo.value) fotoVocaliaUrl = await uploadToFirebase(fotoVocaliaArchivo.value, 'vocalia')
        const payload = { 
            goles_local: parseInt(golesLocalForm.value), 
            goles_visitante: parseInt(golesVisitanteForm.value), 
            novedades: novedadesForm.value,
            foto_vocalia_url: fotoVocaliaUrl || undefined,
            incidencias: [...incL, ...incV] 
        }
        const res = await fetch(`http://127.0.0.1:8000/partidos/${partidoSeleccionadoVocalia.value.id_partido}/finalizar`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
        if (res.ok) { mostrarModalVocalia.value = false; await cargarPartidos(); await cargarEstadisticas(); alert("Acta finalizada y estadísticas actualizadas."); }
    } catch (e) { alert("Error de red"); }
}

// MÉTODOS GESTIÓN DE TORNEO
const ejecutarTraspasoOficial = async () => {
    msjTraspasoError.value = ''; msjTraspasoExito.value = '';
    try {
        const res = await fetch(`http://127.0.0.1:8000/jugadores/${formTraspaso.value.id_jugador}/traspaso`, {
            method: 'PUT', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ id_nuevo_equipo: parseInt(formTraspaso.value.id_nuevo_equipo), nuevo_numero_camiseta: parseInt(formTraspaso.value.nuevo_numero_camiseta) })
        });
        const d = await res.json()
        if (res.ok) {
            msjTraspasoExito.value = d.mensaje; formTraspaso.value = { id_jugador: '', id_nuevo_equipo: '', nuevo_numero_camiseta: '' }; filtroTraspasoBusqueda.value = ''; filtroTraspasoDestino.value = '';
            await cargarJugadores();
        } else { msjTraspasoError.value = d.detail; }
    } catch (e) { msjTraspasoError.value = "Error de red."; }
}

const alterarCategoriaClub = async (id, catActual) => {
    const nuevaCat = catActual === 'Máxima' ? 'Primera' : 'Máxima';
    if (!confirm(`¿Confirmas cambiar al equipo a la serie de ${nuevaCat}?`)) return;
    try {
        const res = await fetch(`http://127.0.0.1:8000/equipos/${id}/categoria`, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ nueva_categoria: nuevaCat }) });
        if (res.ok) { await cargarEquipos(); await cargarEstadisticas(); alert("Categoría actualizada con éxito."); }
    } catch (e) {}
}
</script>

<template>
    <div class="bg-gray-100 font-sans min-h-screen pb-20">
        
        <nav class="bg-[#001a4d] p-4 shadow-md text-white flex justify-between items-center no-imprimir sticky top-0 z-50">
            <div class="flex items-center space-x-3"><span class="text-2xl">🛡️</span><h1 class="text-xl font-bold">Panel de Administración - LDP Conocoto</h1></div>
            <button @click="cerrarSesion" class="bg-red-600 hover:bg-red-700 transition px-4 py-2 rounded-lg text-sm font-bold shadow-md">Cerrar Sesión</button>
        </nav>

        <main class="container mx-auto mt-8 px-4">
            
            <div class="flex flex-wrap gap-3 mb-8 no-imprimir justify-center border-b border-gray-300 pb-6">
                <button @click="vistaActual = 'jugadores'" :class="vistaActual === 'jugadores' ? 'bg-[#001a4d] text-white shadow-lg scale-105' : 'bg-white text-gray-600 hover:bg-gray-50 border'" class="px-5 py-3 rounded-xl font-bold transition flex items-center">📝 Jugadores</button>
                <button @click="vistaActual = 'equipos'" :class="vistaActual === 'equipos' ? 'bg-[#001a4d] text-white shadow-lg scale-105' : 'bg-white text-gray-600 hover:bg-gray-50 border'" class="px-5 py-3 rounded-xl font-bold transition flex items-center">🛡️ Equipos</button>
                <button @click="vistaActual = 'arbitros'" :class="vistaActual === 'arbitros' ? 'bg-[#001a4d] text-white shadow-lg scale-105' : 'bg-white text-gray-600 hover:bg-gray-50 border'" class="px-5 py-3 rounded-xl font-bold transition flex items-center">🏁 Árbitros</button>
                <button @click="vistaActual = 'calendario'" :class="vistaActual === 'calendario' ? 'bg-[#001a4d] text-white shadow-lg scale-105' : 'bg-white text-gray-600 hover:bg-gray-50 border'" class="px-5 py-3 rounded-xl font-bold transition flex items-center">📅 Calendario</button>
                <button @click="vistaActual = 'resultados'" :class="vistaActual === 'resultados' ? 'bg-[#001a4d] text-white shadow-lg scale-105' : 'bg-white text-gray-600 hover:bg-gray-50 border'" class="px-5 py-3 rounded-xl font-bold transition flex items-center">⚽ Resultados</button>
                <button @click="vistaActual = 'estadisticas'" :class="vistaActual === 'estadisticas' ? 'bg-[#001a4d] text-white shadow-lg scale-105' : 'bg-white text-gray-600 hover:bg-gray-50 border'" class="px-5 py-3 rounded-xl font-bold transition flex items-center">📊 Estadísticas</button>
                <button @click="vistaActual = 'torneo'" :class="vistaActual === 'torneo' ? 'bg-[#001a4d] text-white shadow-lg scale-105' : 'bg-white text-gray-600 hover:bg-gray-50 border'" class="px-5 py-3 rounded-xl font-bold transition flex items-center">🔄 Gestión Torneo</button>
            </div>

            <!-- VISTA 1: JUGADORES -->
            <div v-show="vistaActual === 'jugadores'" class="space-y-8">
                <div class="bg-white p-8 rounded-2xl shadow-lg border border-gray-200 no-imprimir">
                    <h2 class="text-2xl font-black text-gray-800 mb-6 flex items-center"><span class="mr-2 text-blue-600">📝</span> {{ editandoJugador ? 'EDITAR JUGADOR' : 'REGISTRO DE JUGADOR' }}</h2>
                    <div v-if="mensajeError" class="bg-red-50 text-red-600 p-4 rounded-lg font-medium mb-6 border flex items-center">⚠️ {{ mensajeError }}</div>
                    <div v-if="mensajeExito" class="bg-green-50 text-green-700 p-4 rounded-lg font-medium mb-6 border flex items-center">✅ {{ mensajeExito }}</div>
                    <form @submit.prevent="registrarJugador" class="space-y-6">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div class="flex flex-col items-center space-y-4 bg-gray-50 p-6 rounded-xl border-2 border-dashed border-gray-300">
                                <video ref="videoRef" width="320" height="240" autoplay class="rounded-lg bg-black" v-show="camaraAbierta" style="transform: scaleX(-1);"></video>
                                <canvas ref="canvasRef" width="320" height="240" class="hidden"></canvas>
                                <img :src="fotoBase64" class="rounded-lg shadow-md max-h-48 object-cover" width="200" v-show="fotoTomada" />
                                <div class="flex space-x-4">
                                    <button v-if="!camaraAbierta && !fotoTomada" @click="abrirCamara" type="button" class="bg-blue-600 text-white px-4 py-2 rounded-lg font-bold text-sm">📸 Abrir Cámara</button>
                                    <button v-if="camaraAbierta" @click="capturarFoto" type="button" class="bg-green-600 text-white px-6 py-2 rounded-lg font-bold text-sm">🎯 Capturar</button>
                                    <button v-if="fotoTomada" @click="abrirCamara" type="button" class="bg-gray-600 text-white px-4 py-2 rounded-lg font-bold text-sm">🔄 Retomar</button>
                                </div>
                            </div>
                            <div class="flex flex-col items-center justify-center space-y-4 bg-gray-50 p-6 rounded-xl border-2 border-dashed border-gray-300">
                                <p class="text-sm font-bold text-gray-600">Foto Cédula / Pasaporte</p>
                                <div v-if="!docPreview" class="text-gray-400 text-5xl">🪪</div>
                                <div v-else class="relative"><img :src="docPreview" class="h-32 object-contain bg-white rounded-lg" /><button @click="removerDocumento" type="button" class="absolute -top-2 -right-2 bg-red-600 text-white rounded-full w-6 h-6">✕</button></div>
                                <label class="cursor-pointer bg-white rounded-md font-bold text-blue-700 text-sm"><span>Seleccionar archivo</span><input @change="seleccionarDocumento" type="file" accept="image/*" class="sr-only" /></label>
                            </div>
                        </div>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4 border-t">
                            <div><label class="block text-sm font-bold text-gray-700 mb-1">Documento ID</label><input v-model="cedula" @input="validarCedula" type="text" required maxlength="10" inputmode="numeric" class="w-full p-3 border rounded-lg uppercase outline-none" /><p class="text-xs text-gray-500 mt-1">Máximo 10 dígitos.</p></div>
                            <div class="md:col-span-2">
                                <label class="block text-sm font-bold text-gray-700 mb-1">Equipo <span v-if="editandoJugador" class="text-xs text-red-500 font-normal">(Usa 'Gestión Torneo' para transferencias)</span></label>
                                <select v-model="id_equipo" :disabled="editandoJugador" required :class="{'bg-gray-100 cursor-not-allowed': editandoJugador}" class="w-full p-3 border rounded-lg bg-white outline-none"><option v-for="eq in equipos" :key="eq.id" :value="eq.id">{{ eq.nombre }} ({{ eq.categoria }})</option></select>
                            </div>
                            <div><label class="block text-sm font-bold text-gray-700 mb-1">Nombres</label><input v-model="nombre" type="text" required class="w-full p-3 border rounded-lg outline-none" /></div>
                            <div><label class="block text-sm font-bold text-gray-700 mb-1">Apellidos</label><input v-model="apellido" type="text" required class="w-full p-3 border rounded-lg outline-none" /></div>
                            <div><label class="block text-sm font-bold text-gray-700 mb-1">F. Nacimiento</label><input v-model="fecha_nacimiento" :max="fechaMaximaPermitida" type="date" required class="w-full p-3 border rounded-lg outline-none" /></div>
                            <div><label class="block text-sm font-bold text-gray-700 mb-1">Nº Camiseta</label><input v-model="numero_camiseta" type="number" required min="1" max="99" class="w-full p-3 border rounded-lg outline-none" /></div>
                        </div>
                        <div class="pt-6 border-t">
                            <label class="flex items-start space-x-3 cursor-pointer p-4 bg-blue-50 rounded-xl"><input v-model="acepta_terminos" type="checkbox" required class="mt-1 h-5 w-5" /><span class="text-sm text-gray-700">Acepto los Términos y Condiciones de la LDP Conocoto.</span></label>
                            <div class="flex space-x-4 mt-4"><button v-if="editandoJugador" @click="limpiarFormularioJugador" type="button" class="w-1/3 bg-gray-500 text-white font-bold py-4 rounded-xl shadow transition">CANCELAR EDICIÓN</button><button type="submit" :disabled="!acepta_terminos || cargando" class="w-full bg-[#001a4d] text-white font-bold py-4 rounded-xl shadow flex justify-center items-center">{{ editandoJugador ? 'ACTUALIZAR JUGADOR' : 'GUARDAR JUGADOR' }}</button></div>
                            <div v-if="mensajeError" class="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-700">⚠️ {{ mensajeError }}</div>
                            <div v-if="mensajeExito" class="mt-4 rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm font-semibold text-green-700">✅ {{ mensajeExito }}</div>
                        </div>
                    </form>
                </div>

                <!-- CARNET IMPRIMIBLE MEJORADO CON ESCUDO -->
                <div class="seccion-carnet" v-show="mostrarCarnet">
                    <div class="carnet-imprimible bg-[#001a4d] w-[350px] h-[500px] rounded-2xl shadow-2xl relative overflow-hidden text-white mx-auto border-4 border-yellow-400">
                        <div class="bg-white text-center py-4 text-blue-900 font-black text-xl flex justify-center relative">
                            <span>L.D.P. CONOCOTO</span>
                            <img v-if="datosCarnet.logoEquipo" :src="datosCarnet.logoEquipo" class="w-12 h-12 object-contain absolute top-1 right-3 bg-white rounded-full p-1 drop-shadow-sm border border-gray-200" />
                        </div>
                        <div class="flex justify-center mt-6"><img :src="datosCarnet.fotoBase64" class="w-40 h-40 object-cover border-4 border-white rounded-lg bg-gray-200" /></div>
                        <div class="p-6 text-center space-y-1">
                            <h3 class="text-2xl font-bold uppercase tracking-tighter">{{ datosCarnet.nombre }} {{ datosCarnet.apellido }}</h3>
                            <p class="text-yellow-400 font-bold text-lg">{{ datosCarnet.equipo }}</p>
                            <p class="text-blue-200 font-semibold text-sm uppercase tracking-widest">{{ datosCarnet.categoria }}</p>
                            <div class="flex justify-around pt-4 border-t border-blue-400 mt-2">
                                <div><p class="text-[10px] text-blue-200">DOCUMENTO ID</p><p class="font-mono text-sm font-bold uppercase">{{ datosCarnet.cedula }}</p></div>
                                <div><p class="text-[10px] text-blue-200">Nº CAMISETA</p><p class="font-mono text-sm font-bold text-yellow-400">#{{ datosCarnet.numero_camiseta }}</p></div>
                            </div>
                        </div>
                        <div class="absolute bottom-0 w-full bg-yellow-400 text-blue-900 text-center py-2 font-black text-[11px] italic uppercase tracking-wider">Liga Deportiva Parroquial de Conocoto</div>
                    </div>
                    <div class="flex space-x-4 max-w-sm mx-auto mt-6 no-imprimir">
                        <button @click="imprimirCarnet" class="w-full bg-gray-800 hover:bg-black transition text-white py-3 rounded-lg font-bold shadow-lg">🖨️ Imprimir</button>
                        <button @click="mostrarCarnet = false" class="w-full bg-red-600 hover:bg-red-700 transition text-white py-3 rounded-lg font-bold shadow-lg">Cerrar Visualización</button>
                    </div>
                </div>

                <div class="bg-white p-8 rounded-2xl shadow-lg border no-imprimir">
                    <h2 class="text-2xl font-black text-gray-800 mb-6 flex items-center justify-between"><div>📋 JUGADORES REGISTRADOS</div><div class="text-sm font-bold bg-blue-50 text-blue-700 px-3 py-1 rounded-full">Total: {{ jugadoresFiltrados.length }}</div></h2>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                        <div class="md:col-span-2 relative"><span class="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">🔍</span><input v-model="filtroBusqueda" type="text" placeholder="Buscar..." class="w-full pl-10 p-3 border rounded-xl outline-none" /></div>
                        <div><select v-model="filtroEquipoSelect" class="w-full p-3 border rounded-xl bg-gray-50 outline-none"><option value="">-- Todos --</option><option v-for="eq in equipos" :key="eq.id" :value="eq.id">{{ eq.nombre }}</option></select></div>
                    </div>
                    <div class="overflow-x-auto">
                        <table class="w-full text-left border-collapse">
                            <thead><tr class="bg-gray-100 text-sm"><th class="p-3 border-b-2">Foto</th><th class="p-3 border-b-2">Identidad</th><th class="p-3 border-b-2">Equipo</th><th class="p-3 border-b-2 text-center">Camiseta</th><th class="p-3 border-b-2 text-center">Acciones</th></tr></thead>
                            <tbody>
                                <tr v-for="jug in jugadoresFiltrados" :key="jug.id_jugador" class="border-b hover:bg-gray-50 transition">
                                    <td class="p-3"><img v-if="jug.url_foto" :src="jug.url_foto" class="h-10 w-10 object-cover rounded-md" /><div v-else class="h-10 w-10 bg-gray-200 rounded flex items-center justify-center">👤</div></td>
                                    <td class="p-3"><p class="font-bold text-[#001a4d]">{{ jug.nombre }} {{ jug.apellido }}</p><p class="text-xs font-mono uppercase text-gray-500">{{ jug.cedula }}</p></td>
                                    <td class="p-3"><div class="flex items-center space-x-2"><img v-if="obtenerLogoEquipo(jug.nombre_equipo)" :src="obtenerLogoEquipo(jug.nombre_equipo)" class="h-6 w-6 object-contain" /><span class="font-medium text-gray-700">{{ jug.nombre_equipo }}</span></div></td>
                                    <td class="p-3 text-center"><span class="px-2 py-0.5 bg-yellow-100 font-black rounded border text-yellow-800">#{{ jug.numero_camiseta }}</span></td>
                                    <td class="p-3 text-center"><div class="flex justify-center space-x-2"><button @click="prepararReimpresion(jug)" class="bg-blue-100 text-blue-700 p-2 rounded hover:bg-blue-200">🖨️</button><button @click="prepararEdicionJugador(jug)" class="bg-gray-100 text-gray-700 p-2 rounded hover:bg-gray-200">✏️</button><button @click="manejarSuspensionJugador(jug)" :class="jug.suspendido_hasta ? 'bg-orange-100 text-orange-700 hover:bg-orange-200' : 'bg-red-50 text-red-600 hover:bg-red-100'" class="p-2 rounded">⏸️</button><button @click="eliminarJugador(jug.id_jugador, `${jug.nombre} ${jug.apellido}`)" class="bg-red-50 text-red-600 p-2 rounded hover:bg-red-100">🗑️</button></div></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div class="mt-8 border-t pt-6">
                        <h3 class="text-lg font-black text-gray-800 mb-3">🛑 Gestión de suspensiones activas</h3>
                        <div v-if="jugadoresSuspendidos.length" class="space-y-2">
                            <div v-for="s in jugadoresSuspendidos" :key="s.id_jugador" class="flex items-center justify-between rounded-xl border border-orange-200 bg-orange-50 px-4 py-3 text-sm">
                                <div>
                                    <p class="font-bold text-gray-800">{{ s.nombre }} {{ s.apellido }}</p>
                                    <p class="text-xs text-gray-600">{{ s.equipo }} · Hasta {{ s.fecha_fin }}</p>
                                    <p v-if="s.motivo" class="text-xs text-orange-700">Motivo: {{ s.motivo }}</p>
                                </div>
                                <button @click="manejarSuspensionJugador({ id_jugador: s.id_jugador, nombre: s.nombre, apellido: s.apellido, suspendido_hasta: true })" class="rounded-lg bg-orange-600 px-3 py-2 text-xs font-bold text-white">Quitar</button>
                            </div>
                        </div>
                        <p v-else class="text-sm text-gray-500">No hay jugadores con suspensión activa.</p>
                    </div>
                </div>
            </div>

            <!-- VISTA 2: EQUIPOS -->
            <div v-show="vistaActual === 'equipos'" class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div class="bg-white p-8 rounded-2xl border shadow-lg h-fit">
                    <h2 class="text-2xl font-black text-[#001a4d] mb-6">🛡️ {{ editandoEquipo ? 'EDITAR EQUIPO' : 'Nuevo Equipo' }}</h2>
                    <div v-if="msjErrorEquipo" class="bg-red-50 text-red-600 p-3 rounded-lg text-sm mb-4 border">⚠️ {{ msjErrorEquipo }}</div>
                    <div v-if="msjExitoEquipo" class="bg-green-50 text-green-700 p-3 rounded-lg text-sm mb-4 border">✅ {{ msjExitoEquipo }}</div>
                    <form @submit.prevent="registrarEquipo" class="space-y-5">
                        <div><label class="block text-sm font-bold text-gray-700 mb-1">Nombre</label><input v-model="nuevoEquipo.nombre" @input="nuevoEquipo.nombre = formatearTextoMayusculas($event.target.value)" type="text" required class="w-full p-3 border rounded-lg outline-none uppercase" /></div>
                        <div><label class="block text-sm font-bold text-gray-700 mb-1">Categoría</label><select v-model="nuevoEquipo.categoria" required class="w-full p-3 border rounded-lg bg-white outline-none"><option value="Máxima">Máxima</option><option value="Primera">Primera</option></select></div>
                        <div><label class="block text-sm font-bold text-gray-700 mb-1">Fecha Fundación</label><input v-model="nuevoEquipo.fecha_fundacion" type="date" :max="fechaMaximaFundacion" :min="fechaMinimaFundacion" class="w-full p-3 border rounded-lg outline-none" /></div>
                        <div>
                            <label class="block text-sm font-bold text-gray-700 mb-1">Escudo Oficial</label>
                            <div class="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-xl bg-gray-50 relative group">
                                <div class="space-y-2 text-center flex flex-col items-center">
                                    <div v-if="!logoPreview" class="text-gray-400 text-5xl">🛡️</div>
                                    <div v-else class="relative"><img :src="logoPreview" class="h-24 w-24 object-contain" /><button @click="removerEscudo" type="button" class="absolute -top-2 -right-2 bg-red-600 text-white rounded-full w-6 h-6">✕</button></div>
                                    <label class="cursor-pointer font-bold text-blue-700 text-sm hover:underline"><span>Seleccionar archivo</span><input @change="seleccionarEscudo" type="file" accept="image/*" class="sr-only" /></label>
                                </div>
                            </div>
                        </div>
                        <div class="flex space-x-3"><button v-if="editandoEquipo" @click="cancelarEdicionEquipo" type="button" class="w-1/3 bg-gray-500 text-white font-bold py-3 rounded-xl transition">Cancelar</button><button type="submit" class="w-full bg-yellow-400 text-blue-900 font-bold py-3 rounded-xl shadow transition">{{ editandoEquipo ? 'Actualizar' : 'Guardar' }}</button></div>
                    </form>
                </div>
                <div class="bg-white p-8 rounded-2xl border shadow-lg">
                    <h2 class="text-2xl font-black text-gray-800 mb-6">📋 Equipos Registrados</h2>
                    <div class="overflow-x-auto">
                        <table class="w-full text-left border-collapse">
                            <thead><tr class="bg-gray-100 text-sm"><th>Escudo</th><th>Nombre</th><th>Categoría</th><th class="text-center">Plantilla</th><th class="text-center">Acciones</th></tr></thead>
                            <tbody>
                                <tr v-for="eq in equipos" :key="eq.id" class="border-b hover:bg-gray-50 transition">
                                    <td class="p-3"><img v-if="eq.url_logo" :src="eq.url_logo" class="h-10 w-10 object-contain rounded-full border bg-white" /><div v-else class="h-10 w-10 rounded-full bg-gray-100 flex items-center justify-center text-xl">🛡️</div></td>
                                    <td class="p-3 font-bold text-[#001a4d]">{{ formatearTextoMayusculas(eq.nombre) }}</td>
                                    <td class="p-3"><span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-bold">{{ eq.categoria }}</span></td>
                                    <td class="p-3 text-center font-bold text-gray-600">{{ contarJugadores(eq.id) }} / 25</td>
                                    <td class="p-3 text-center"><div class="flex justify-center space-x-2"><button @click="prepararEdicionEquipo(eq)" class="bg-gray-100 hover:bg-gray-200 p-2 rounded">✏️</button><button @click="verPlantilla(eq)" class="bg-blue-50 hover:bg-blue-100 text-blue-600 p-2 rounded">👥</button><button @click="eliminarEquipo(eq.id, eq.nombre)" class="bg-red-50 hover:bg-red-100 text-red-600 p-2 rounded">🗑️</button></div></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- VISTA 3: ÁRBITROS -->
            <div v-show="vistaActual === 'arbitros'" class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <!-- (Sin cambios de observaciones acá, la dejo tal cual) -->
                <div class="bg-white p-8 rounded-2xl border shadow-lg h-fit">
                    <h2 class="text-2xl font-black text-[#001a4d] mb-6">🏁 Nuevo Árbitro Oficial</h2>
                    <div v-if="msjErrorArbitro" class="bg-red-50 text-red-600 p-3 rounded-lg text-sm mb-4 border">⚠️ {{ msjErrorArbitro }}</div>
                    <div v-if="msjExitoArbitro" class="bg-green-50 text-green-700 p-3 rounded-lg text-sm mb-4 border">✅ {{ msjExitoArbitro }}</div>
                    <form @submit.prevent="registrarArbitro" class="space-y-5">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div><label class="block text-sm font-bold text-gray-700 mb-1">Nombres</label><input v-model="nuevoArbitro.nombre" type="text" required class="w-full p-3 border rounded-lg outline-none" /></div>
                            <div><label class="block text-sm font-bold text-gray-700 mb-1">Apellidos</label><input v-model="nuevoArbitro.apellido" type="text" required class="w-full p-3 border rounded-lg outline-none" /></div>
                        </div>
                        <div><label class="block text-sm font-bold text-gray-700 mb-1">Cédula</label><input v-model="nuevoArbitro.cedula" type="text" maxlength="10" inputmode="numeric" class="w-full p-3 border rounded-lg outline-none" /></div>
                        <div><label class="block text-sm font-bold text-gray-700 mb-1">Años de Experiencia</label><input v-model="nuevoArbitro.experiencia_anios" type="number" min="0" class="w-full p-3 border rounded-lg outline-none" /></div>
                        <div>
                            <label class="block text-sm font-bold text-gray-700 mb-1">Fotografía de Perfil</label>
                            <div class="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-xl bg-gray-50 relative group">
                                <div class="space-y-2 text-center flex flex-col items-center">
                                    <div v-if="!arbitroFotoPreview" class="text-gray-400 text-5xl">👤</div>
                                    <div v-else class="relative"><img :src="arbitroFotoPreview" class="h-24 w-24 object-cover rounded-full border" /><button @click="removerArbitroFoto" type="button" class="absolute -top-1 -right-1 bg-red-600 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs">✕</button></div>
                                    <label class="cursor-pointer font-bold text-blue-700 text-sm hover:underline"><span>Seleccionar foto</span><input @change="seleccionarArbitroFoto" type="file" accept="image/*" class="sr-only" /></label>
                                </div>
                            </div>
                        </div>
                        <button type="submit" :disabled="cargandoArbitro" class="w-full bg-[#001a4d] hover:bg-blue-900 text-white font-bold py-3 rounded-xl shadow transition">REGISTRAR ÁRBITRO CENTRAL</button>
                    </form>
                </div>
                <div class="bg-white p-8 rounded-2xl border shadow-lg">
                    <h2 class="text-2xl font-black text-gray-800 mb-6">📋 Cuerpo Arbitral Registrado</h2>
                    <table class="w-full text-left border-collapse">
                        <thead><tr class="bg-gray-100 text-sm"><th class="p-3 border-b-2 text-center">Foto</th><th class="p-3 border-b-2">Nombre Completo</th><th class="p-3 border-b-2">Cédula</th><th class="p-3 border-b-2 text-center">Experiencia</th></tr></thead>
                        <tbody>
                            <tr v-for="arb in arbitros" :key="arb.id_arbitro" class="border-b hover:bg-gray-50 transition">
                                <td class="p-3 flex justify-center"><img v-if="arb.url_foto" :src="arb.url_foto" class="h-10 w-10 object-cover rounded-full border" /><div v-else class="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">🏁</div></td>
                                <td class="p-3 font-bold text-[#001a4d]">{{ arb.nombre }} {{ arb.apellido }}</td>
                                <td class="p-3 text-sm text-gray-700">{{ arb.cedula || 'Sin cédula' }}</td>
                                <td class="p-3 text-center"><span class="px-2 py-1 bg-green-50 text-green-800 font-bold rounded-md border border-green-200 text-xs">{{ arb.experiencia_anios || 0 }} años</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- VISTA 4: CALENDARIO -->
            <div v-show="vistaActual === 'calendario'" class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div class="lg:col-span-1 bg-white p-6 rounded-2xl border shadow-lg h-fit">
                    <div class="flex items-start justify-between gap-3 mb-4">
                        <div>
                            <h2 class="text-xl font-black text-[#001a4d]">⚙️ Fixture Oficial</h2>
                            <p class="text-xs text-gray-500 mt-1">Genera, limpia o reconstruye el calendario del torneo.</p>
                        </div>
                        <span class="bg-blue-50 text-blue-700 text-[10px] font-black px-3 py-1 rounded-full border border-blue-200 uppercase tracking-wider">{{ partidos.length }} partidos</span>
                    </div>
                    <form @submit.prevent="dispararGeneracionCalendario" class="space-y-4">
                        <div>
                            <label class="block text-xs font-black text-gray-700 mb-1 uppercase tracking-wide">Sábado de Inicio</label>
                            <input v-model="formCalendario.fecha_inicio" type="date" required class="w-full p-3 border rounded-xl text-sm outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100" />
                        </div>
                        <button type="submit" class="w-full bg-[#001a4d] hover:bg-blue-900 text-white font-black py-3 rounded-xl text-sm shadow transition">Generar Fixture</button>
                        <button type="button" @click="recrearFixtureCalendario" class="w-full bg-yellow-400 hover:bg-yellow-500 text-[#001a4d] font-black py-3 rounded-xl text-sm shadow transition">Borrar y recrear fixture</button>
                        <button type="button" @click="borrarFixtureActual" class="w-full bg-red-600 hover:bg-red-700 text-white font-black py-3 rounded-xl text-sm shadow transition">Borrar fixture actual</button>
                    </form>
                </div>
                <div class="lg:col-span-2 bg-white p-8 rounded-2xl shadow-xl border border-gray-200">
                    <h2 class="text-2xl font-black text-gray-800 mb-6 flex items-center justify-between"><div><span class="mr-2 text-blue-600">📋</span> CRONOGRAMA OFICIAL</div><div class="text-sm font-bold bg-blue-50 text-blue-700 px-4 py-1.5 rounded-full border border-blue-200">Total: {{ partidos.length }}</div></h2>
                    <div class="overflow-y-auto max-h-[72vh] space-y-4 pr-3">
                        <div v-for="partido in partidos" :key="partido.id_partido" class="border-2 border-gray-200/80 rounded-2xl p-5 bg-gray-50 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm hover:shadow-md hover:bg-white hover:border-blue-900/30 transition-all duration-200">
                            <div class="flex flex-col border-b md:border-b-0 md:border-r pr-5 min-w-[140px]">
                                <span class="text-sm font-black text-[#001a4d]">📅 {{ partido.fecha }}</span>
                                <span class="text-base font-mono font-black text-blue-600 mt-1">⏰ {{ partido.hora }}</span>
                            </div>
                            <div class="flex items-center justify-center flex-1 space-x-4 min-w-[320px]">
                                <div class="flex items-center space-x-3 justify-end w-[44%] text-right">
                                    <span class="font-black text-sm md:text-base text-[#001a4d] truncate">{{ partido.local }}</span>
                                    <img v-if="obtenerLogoEquipo(partido.local)" :src="obtenerLogoEquipo(partido.local)" class="h-10 w-10 object-contain rounded-full border-2 border-gray-200 bg-white p-0.5 shadow-sm" />
                                </div>
                                <span class="text-xs bg-[#001a4d] text-yellow-400 font-black px-3 py-1 rounded-xl shadow-inner tracking-wider">VS</span>
                                <div class="flex items-center space-x-3 justify-start w-[44%] text-left">
                                    <img v-if="obtenerLogoEquipo(partido.visitante)" :src="obtenerLogoEquipo(partido.visitante)" class="h-10 w-10 object-contain rounded-full border-2 border-gray-200 bg-white p-0.5 shadow-sm" />
                                    <span class="font-black text-sm md:text-base text-[#001a4d] truncate">{{ partido.visitante }}</span>
                                </div>
                            </div>
                            <div class="flex items-center space-x-4 justify-between md:justify-end min-w-[190px]">
                                <div class="flex flex-col items-end">
                                    <span :class="partido.estado === 'Finalizado' ? 'bg-green-100 text-green-800 border-green-300' : 'bg-yellow-100 text-yellow-800 border-yellow-300'" class="text-xs font-black px-3 py-1 rounded-full border-2 uppercase tracking-widest shadow-sm">{{ partido.estado }}</span>
                                    <span class="text-xs font-semibold text-gray-500 mt-2 truncate max-w-[140px] italic">🏁 {{ partido.arbitro }}</span>
                                </div>
                                <button v-if="partido.estado === 'Pendiente'" @click="abrirModalEditarPartido(partido)" class="bg-gray-200 hover:bg-[#001a4d] hover:text-white text-gray-700 p-3 rounded-xl transition font-bold shadow-sm">✏️</button>
                                <button v-else @click="verActaFinalizada(partido)" class="bg-green-600 hover:bg-green-700 text-white p-3 rounded-xl transition text-sm font-bold shadow-sm flex items-center">🔍 Acta</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- VISTA 5: RESULTADOS -->
            <div v-show="vistaActual === 'resultados'" class="grid grid-cols-1 gap-8">
                <div class="bg-white p-8 rounded-2xl shadow-lg border border-gray-200">
                    <h2 class="text-2xl font-black text-gray-800 mb-6 flex items-center">⚽ MESA DE CONTROL: REGISTRO DE ACTAS</h2>
                    <div class="flex space-x-4 mb-6 border-b pb-4"><p class="text-base font-black text-[#001a4d] border-b-4 border-blue-900 pb-2">🎯 Partidos por Jugar ({{ partidosPendientes.length }})</p></div>
                    <div class="space-y-4">
                        <div v-for="partido in partidosPendientes" :key="partido.id_partido" class="border-2 rounded-2xl p-6 bg-gray-50 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-sm">
                            <div class="flex flex-col min-w-[130px]">
                                <span class="text-sm font-black text-gray-500 uppercase">📅 {{ partido.fecha }}</span>
                                <span class="text-base font-mono font-black text-blue-600 mt-0.5">⏰ {{ partido.hora }}</span>
                            </div>
                            <div class="flex items-center justify-center flex-1 space-x-4">
                                <div class="flex items-center space-x-2 justify-end w-[40%] text-right">
                                    <span class="font-black text-base text-[#001a4d] truncate">{{ partido.local }}</span>
                                    <img v-if="obtenerLogoEquipo(partido.local)" :src="obtenerLogoEquipo(partido.local)" class="h-9 w-9 object-contain" />
                                </div>
                                <span class="text-xs bg-[#001a4d] text-yellow-400 font-black px-3 py-1 rounded-xl">VS</span>
                                <div class="flex items-center space-x-2 justify-start w-[40%] text-left">
                                    <img v-if="obtenerLogoEquipo(partido.visitante)" :src="obtenerLogoEquipo(partido.visitante)" class="h-9 w-9 object-contain" />
                                    <span class="font-black text-base text-[#001a4d] truncate">{{ partido.visitante }}</span>
                                </div>
                            </div>
                            <div class="min-w-[160px] text-right"><button @click="abrirMesaVocalia(partido)" class="bg-green-600 hover:bg-green-700 text-white font-black px-5 py-2.5 rounded-xl text-sm shadow transition">📝 Llenar Vocalía</button></div>
                        </div>
                        <div v-if="partidosPendientes.length === 0" class="text-center py-16 text-gray-400 italic">No hay partidos pendientes por jugar.</div>
                    </div>
                </div>
            </div>

            <!-- VISTA 6: ESTADÍSTICAS -->
            <div v-show="vistaActual === 'estadisticas'" class="space-y-8">
                <!-- (Sin cambios de observaciones acá, se mantiene tal cual) -->
                <div class="bg-white p-6 rounded-2xl shadow-lg border flex flex-col md:flex-row items-center justify-between gap-4">
                    <h2 class="text-2xl font-black text-[#001a4d]">📊 RENDIMIENTO Y TABLAS DEL CAMPEONATO</h2>
                    <select v-model="categoriaEstadisticas" @change="cargarEstadisticas" class="p-3 border rounded-xl bg-gray-50 font-bold text-[#001a4d] outline-none"><option value="Máxima">Serie Máxima (Domingos)</option><option value="Primera">Serie Primera (Sábados)</option></select>
                </div>
                <div class="grid grid-cols-1 xl:grid-cols-3 gap-8">
                    <div class="xl:col-span-2 bg-white p-6 rounded-2xl border shadow-lg overflow-x-auto">
                        <h3 class="text-xl font-black text-gray-800 mb-4 flex items-center">🏆 Tabla de Posiciones Oficial</h3>
                        <table class="w-full text-left border-collapse text-sm">
                            <thead><tr class="bg-gray-100 text-gray-700 font-black"><th class="p-3 text-center">Pos</th><th class="p-3">Club</th><th class="p-3 text-center">PJ</th><th class="p-3 text-center">PG</th><th class="p-3 text-center">PE</th><th class="p-3 text-center">PP</th><th class="p-3 text-center">GF</th><th class="p-3 text-center">GC</th><th class="p-3 text-center">GD</th><th class="p-3 text-center bg-blue-50 text-blue-900 font-black">PTS</th></tr></thead>
                            <tbody>
                                <tr v-for="(pos, idx) in tablaPosiciones" :key="pos.id_equipo" class="border-b hover:bg-gray-50 transition">
                                    <td class="p-3 text-center font-bold text-gray-500">{{ idx + 1 }}</td>
                                    <td class="p-3 font-black text-[#001a4d] flex items-center space-x-2"><img v-if="pos.url_logo" :src="pos.url_logo" class="h-6 w-6 object-contain rounded-full" /><span>{{ pos.nombre }}</span></td>
                                    <td class="p-3 text-center font-mono">{{ pos.pj }}</td>
                                    <td class="p-3 text-center text-green-600 font-bold font-mono">{{ pos.pg }}</td>
                                    <td class="p-3 text-center text-gray-500 font-mono">{{ pos.pe }}</td>
                                    <td class="p-3 text-center text-red-500 font-mono">{{ pos.pp }}</td>
                                    <td class="p-3 text-center font-mono">{{ pos.gf }}</td>
                                    <td class="p-3 text-center font-mono">{{ pos.gc }}</td>
                                    <td class="p-3 text-center font-bold font-mono" :class="pos.gd >= 0 ? 'text-blue-600' : 'text-red-500'">{{ pos.gd }}</td>
                                    <td class="p-3 text-center font-black bg-blue-50 text-blue-900 font-mono text-base">{{ pos.pts }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div class="xl:col-span-1 bg-white p-6 rounded-2xl border shadow-lg">
                        <h3 class="text-xl font-black text-gray-800 mb-4 flex items-center">⚽ Goleadores Destacados</h3>
                        <div class="space-y-3">
                            <div v-for="(gol, idx) in maxGoleadores" :key="idx" class="flex items-center justify-between p-3 border rounded-xl bg-gray-50">
                                <div class="flex items-center space-x-3 w-[70%]">
                                    <span class="font-black text-gray-400 text-sm">#{{ idx + 1 }}</span>
                                    <div class="truncate"><p class="font-black text-sm text-[#001a4d] truncate">{{ gol.jugador }}</p><p class="text-xs text-gray-500 truncate font-semibold">{{ gol.equipo }}</p></div>
                                </div>
                                <div class="text-right"><span class="bg-blue-900 text-white font-black px-3 py-1 rounded-lg text-sm font-mono">⚽ {{ gol.goles }}</span></div>
                            </div>
                            <div v-if="maxGoleadores.length === 0" class="text-center py-10 text-gray-400 italic">Ningún gol registrado en la serie todavía.</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- VISTA 7: GESTIÓN DE TORNEO (MERCADO DE PASES) -->
            <div v-show="vistaActual === 'torneo'" class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <!-- Formulario de Traspaso -->
                <div class="lg:col-span-1 bg-white p-6 rounded-2xl border shadow-lg h-fit">
                    <div class="flex items-start justify-between gap-3 mb-4">
                        <div>
                            <h3 class="text-xl font-black text-[#001a4d] flex items-center">🔄 Traspaso Oficial</h3>
                            <p class="text-xs text-gray-500 mt-1">Filtra por jugador y destino antes de confirmar el cambio.</p>
                        </div>
                        <span class="bg-gray-100 text-gray-600 text-[10px] font-black px-3 py-1 rounded-full border uppercase tracking-wider">Mercado</span>
                    </div>
                    <div v-if="hayPartidosPendientes" class="mb-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs font-semibold text-amber-800 shadow-sm">⚠️ Los traspasos quedan bloqueados hasta que se jueguen todos los partidos pendientes.</div>
                    <div v-if="msjTraspasoError" class="bg-red-50 text-red-700 p-3 rounded-2xl text-xs mb-3 border border-red-200">⚠️ {{ msjTraspasoError }}</div>
                    <div v-if="msjTraspasoExito" class="bg-green-50 text-green-700 p-3 rounded-2xl text-xs mb-3 border border-green-200">✅ {{ msjTraspasoExito }}</div>
                    <form @submit.prevent="ejecutarTraspasoOficial" class="space-y-4">
                        <div class="bg-gradient-to-br from-gray-50 to-white p-4 rounded-2xl border border-gray-200 shadow-sm space-y-3">
                            <div>
                                <label class="block text-[11px] font-black text-gray-700 mb-2 uppercase tracking-wider">🔍 Buscar jugador</label>
                                <input v-model="filtroTraspasoBusqueda" type="text" placeholder="Nombre, apellido o cédula" class="w-full p-3 border border-gray-300 rounded-xl text-sm outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100 bg-white" />
                            </div>
                            <div>
                                <label class="block text-[11px] font-black text-gray-700 mb-2 uppercase tracking-wider">Seleccionar jugador</label>
                                <select v-model="formTraspaso.id_jugador" required class="w-full p-3 border border-gray-300 rounded-xl bg-white text-sm font-medium outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100">
                                <option value="" disabled>-- Seleccione Jugador --</option>
                                <option v-for="j in jugadoresParaTraspaso" :key="j.id_jugador" :value="j.id_jugador">{{ j.apellido }} {{ j.nombre }} ({{ j.nombre_equipo }})</option>
                                </select>
                            </div>
                        </div>
                        <div class="bg-blue-50 p-4 rounded-2xl border border-blue-100 shadow-sm space-y-3">
                            <div>
                                <label class="block text-[11px] font-black text-gray-700 mb-2 uppercase tracking-wider">🔍 Buscar equipo destino</label>
                                <input v-model="filtroTraspasoDestino" type="text" placeholder="Nombre del club" class="w-full p-3 border border-blue-200 rounded-xl text-sm outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100 bg-white" />
                            </div>
                            <div>
                                <label class="block text-[11px] font-black text-gray-700 mb-2 uppercase tracking-wider">Nuevo equipo destino</label>
                                <select v-model="formTraspaso.id_nuevo_equipo" required class="w-full p-3 border border-blue-200 rounded-xl bg-white text-sm font-medium outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100">
                                <option value="" disabled>-- Seleccione Destino --</option>
                                <option v-for="eq in equiposDestinoParaTraspaso" :key="eq.id" :value="eq.id">{{ eq.nombre }} ({{ eq.categoria }})</option>
                                </select>
                            </div>
                        </div>
                        <div>
                            <label class="block text-[11px] font-black text-gray-700 mb-2 uppercase tracking-wider">Nuevo número de dorsal</label>
                            <input v-model="formTraspaso.nuevo_numero_camiseta" type="number" required min="1" max="99" class="w-full p-3 border rounded-xl text-sm font-bold outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100" placeholder="Ej. 10" />
                        </div>
                        <button type="submit" :disabled="hayPartidosPendientes" class="w-full bg-[#001a4d] hover:bg-blue-900 text-white font-black py-3 rounded-xl text-xs shadow transition disabled:cursor-not-allowed disabled:bg-gray-400">FIRMAR TRASPASO EN LA LIGA</button>
                    </form>
                </div>
                <div class="lg:col-span-2 bg-white p-6 rounded-2xl border shadow-lg">
                    <h3 class="text-xl font-black text-gray-800 mb-2">🛡️ Control de Ascensos y Descensos de Categoría</h3>
                    <p class="text-xs text-gray-400 mb-4">Modifica directamente las series de los clubes al terminar la temporada anual.</p>
                    <div v-if="hayPartidosPendientes" class="mb-4 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-700">⚠️ Los ascensos y descensos quedan bloqueados hasta que se completen todos los partidos pendientes.</div>
                    <table class="w-full text-left border-collapse text-xs">
                        <thead><tr class="bg-gray-100 font-bold"> <th class="p-3">Escudo</th> <th class="p-3">Nombre Club</th> <th class="p-3">Serie Actual</th> <th class="p-3 text-center">Modificación</th> </tr></thead>
                        <tbody>
                            <tr v-for="eq in equipos" :key="eq.id" class="border-b hover:bg-gray-50 transition">
                                <td class="p-3"><img v-if="eq.url_logo" :src="eq.url_logo" class="h-8 w-8 object-contain rounded-full bg-white" /></td>
                                <td class="p-3 font-black text-sm text-[#001a4d]">{{ eq.nombre }}</td>
                                <td class="p-3"><span :class="eq.categoria === 'Máxima' ? 'bg-yellow-100 text-yellow-800 font-black border-yellow-300' : 'bg-blue-100 text-blue-800 border-blue-300'" class="px-2.5 py-1 rounded-full border font-bold">{{ eq.categoria }}</span></td>
                                <td class="p-3 text-center"><button @click="alterarCategoriaClub(eq.id, eq.categoria)" :disabled="hayPartidosPendientes" :class="eq.categoria === 'Máxima' ? 'bg-orange-500 hover:bg-orange-600' : 'bg-green-600 hover:bg-green-700'" class="text-white font-bold px-3 py-1.5 rounded-lg transition-all text-[11px] disabled:cursor-not-allowed disabled:bg-gray-400">{{ eq.categoria === 'Máxima' ? 'Descender a Primera' : 'Ascender a Máxima' }}</button></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

        </main>

        <!-- MODAL: EDITAR / ASIGNAR ÁRBITRO -->
        <div v-if="mostrarModalEditarPartido" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div class="bg-white rounded-2xl shadow-xl max-w-md w-full overflow-hidden flex flex-col border">
                <div class="bg-[#001a4d] p-4 text-white flex justify-between items-center"><h3 class="text-lg font-black uppercase">⚙️ CONFIGURACIÓN DEL PARTIDO</h3><button @click="mostrarModalEditarPartido = false" class="text-white text-xl font-bold hover:text-gray-300">✕</button></div>
                <div class="p-6">
                    <form @submit.prevent="guardarEdicionPartido" class="space-y-4">
                        <div><label class="block text-sm font-bold text-gray-700 mb-1">Fecha del Encuentro</label><input v-model="formEditarPartido.fecha" type="date" required class="w-full p-3 border rounded-xl outline-none" /></div>
                        <div><label class="block text-sm font-bold text-gray-700 mb-1">Hora de Juego</label><select v-model="formEditarPartido.hora" required class="w-full p-3 border rounded-xl bg-white outline-none"><option value="08:00">08:00 AM</option><option value="10:00">10:00 AM</option><option value="12:00">12:00 PM</option><option value="14:00">14:00 PM</option><option value="16:00">16:00 PM</option></select></div>
                        <div><label class="block text-sm font-bold text-gray-700 mb-1">Árbitro 1</label><select v-model="formEditarPartido.id_arbitro" class="w-full p-3 border rounded-xl bg-white outline-none"><option value="">-- Sin asignar --</option><option v-for="arb in arbitros" :key="arb.id_arbitro" :value="arb.id_arbitro">{{ arb.nombre }} {{ arb.apellido }} ({{ arb.experiencia_anios }} años exp.)</option></select></div>
                        <div><label class="block text-sm font-bold text-gray-700 mb-1">Árbitro 2</label><select v-model="formEditarPartido.id_arbitro_2" class="w-full p-3 border rounded-xl bg-white outline-none"><option value="">-- Sin asignar --</option><option v-for="arb in arbitros" :key="arb.id_arbitro + '-2'" :value="arb.id_arbitro">{{ arb.nombre }} {{ arb.apellido }} ({{ arb.experiencia_anios }} años exp.)</option></select></div>
                        <div><label class="block text-sm font-bold text-gray-700 mb-1">Árbitro 3</label><select v-model="formEditarPartido.id_arbitro_3" class="w-full p-3 border rounded-xl bg-white outline-none"><option value="">-- Sin asignar --</option><option v-for="arb in arbitros" :key="arb.id_arbitro + '-3'" :value="arb.id_arbitro">{{ arb.nombre }} {{ arb.apellido }} ({{ arb.experiencia_anios }} años exp.)</option></select></div>
                        <div class="flex space-x-3 pt-4"><button type="button" @click="mostrarModalEditarPartido = false" class="w-1/2 bg-gray-500 hover:bg-gray-600 text-white font-bold py-3 rounded-xl transition">Cancelar</button><button type="submit" class="w-1/2 bg-[#001a4d] hover:bg-blue-900 text-white font-bold py-3 rounded-xl shadow transition">Guardar Cambios</button></div>
                    </form>
                </div>
            </div>
        </div>

        <!-- MODAL: HOJA DE VOCALÍA DIGITAL (CON CAMPO NOVEDADES) -->
        <div v-if="mostrarModalVocalia" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div class="bg-white rounded-3xl shadow-2xl max-w-6xl w-full max-h-[95vh] overflow-hidden flex flex-col border border-gray-200">
                <div class="bg-[#001a4d] p-5 text-white flex justify-between items-center"><div><h3 class="text-xl font-black uppercase tracking-wider">Acta de Vocalía Oficial</h3><p class="text-yellow-400 text-xs font-bold font-mono">Estadio La Moya - LDP Conocoto</p></div><button @click="mostrarModalVocalia = false" class="text-white hover:text-gray-300 text-xl font-bold">✕</button></div>
                <div class="p-6 overflow-y-auto flex-1 space-y-6 bg-gray-100">
                    <div class="bg-white p-6 rounded-2xl shadow-sm border flex items-center justify-around max-w-xl mx-auto text-center">
                        <div class="w-[40%] truncate"><p class="font-black text-[#001a4d] text-base mb-1">{{ partidoSeleccionadoVocalia.local }}</p><input v-model="golesLocalForm" type="number" min="0" class="w-20 p-2 border-2 text-center text-xl font-black rounded-xl focus:border-blue-900 outline-none" /></div>
                        <div class="text-xl font-black text-gray-400">:</div>
                        <div class="w-[40%] truncate"><p class="font-black text-[#001a4d] text-base mb-1">{{ partidoSeleccionadoVocalia.visitante }}</p><input v-model="golesVisitanteForm" type="number" min="0" class="w-20 p-2 border-2 text-center text-xl font-black rounded-xl focus:border-blue-900 outline-none" /></div>
                    </div>
                    
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div class="bg-white p-5 rounded-2xl shadow-sm border space-y-3">
                            <h4 class="font-black text-sm text-[#001a4d] border-b pb-2 uppercase flex items-center justify-between"><span>🛡️ Incidencias: {{ partidoSeleccionadoVocalia.local }}</span><span class="text-xs text-gray-400 font-normal">Goles / 🟨 / 🟥</span></h4>
                            <div class="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                                <div v-for="jug in plantillaLocalVocalia" :key="jug.id_jugador" :class="{'bg-red-50 border-red-200 opacity-60': jug.suspendido, 'bg-gray-50 border-gray-200': !jug.suspendido}" class="flex items-center justify-between p-2 border rounded-xl text-xs hover:bg-gray-100 transition">
                                    <div class="flex items-center space-x-2 truncate w-[45%]"><span class="font-mono font-black text-blue-700 bg-blue-100 px-1.5 py-0.5 rounded">#{{ jug.numero_camiseta }}</span><p class="font-bold text-gray-800 truncate">{{ jug.nombre }} {{ jug.apellido }}</p><span v-if="jug.suspendido" class="ml-1 text-[9px] font-black text-red-600 bg-red-100 px-1.5 py-0.5 rounded uppercase">❌ Suspendido</span></div>
                                    <div class="flex items-center space-x-2">
                                        <span title="Goles">⚽</span><input v-model="jug.goles" :disabled="jug.suspendido" type="number" min="0" class="w-10 p-1 border text-center font-bold rounded outline-none focus:border-blue-600 disabled:bg-gray-200 disabled:cursor-not-allowed" />
                                        <span title="Amarillas">🟨</span><input v-model="jug.amarillas" :disabled="jug.suspendido" type="number" min="0" max="2" class="w-10 p-1 border border-yellow-300 text-center font-bold rounded bg-yellow-50 outline-none focus:border-yellow-600 disabled:bg-gray-200 disabled:cursor-not-allowed" />
                                        <span title="Rojas">🟥</span><input v-model="jug.rojas" :disabled="jug.suspendido" type="number" min="0" max="1" class="w-10 p-1 border border-red-300 text-center font-bold rounded bg-red-50 outline-none focus:border-red-600 disabled:bg-gray-200 disabled:cursor-not-allowed" />
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="bg-white p-5 rounded-2xl shadow-sm border space-y-3">
                            <h4 class="font-black text-sm text-[#001a4d] border-b pb-2 uppercase flex items-center justify-between"><span>🛡️ Incidencias: {{ partidoSeleccionadoVocalia.visitante }}</span><span class="text-xs text-gray-400 font-normal">Goles / 🟨 / 🟥</span></h4>
                            <div class="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                                <div v-for="jug in plantillaVisitanteVocalia" :key="jug.id_jugador" :class="{'bg-red-50 border-red-200 opacity-60': jug.suspendido, 'bg-gray-50 border-gray-200': !jug.suspendido}" class="flex items-center justify-between p-2 border rounded-xl text-xs hover:bg-gray-100 transition">
                                    <div class="flex items-center space-x-2 truncate w-[45%]"><span class="font-mono font-black text-blue-700 bg-blue-100 px-1.5 py-0.5 rounded">#{{ jug.numero_camiseta }}</span><p class="font-bold text-gray-800 truncate">{{ jug.nombre }} {{ jug.apellido }}</p><span v-if="jug.suspendido" class="ml-1 text-[9px] font-black text-red-600 bg-red-100 px-1.5 py-0.5 rounded uppercase">❌ Suspendido</span></div>
                                    <div class="flex items-center space-x-2">
                                        <span title="Goles">⚽</span><input v-model="jug.goles" :disabled="jug.suspendido" type="number" min="0" class="w-10 p-1 border text-center font-bold rounded outline-none focus:border-blue-600 disabled:bg-gray-200 disabled:cursor-not-allowed" />
                                        <span title="Amarillas">🟨</span><input v-model="jug.amarillas" :disabled="jug.suspendido" type="number" min="0" max="2" class="w-10 p-1 border border-yellow-300 text-center font-bold rounded bg-yellow-50 outline-none focus:border-yellow-600 disabled:bg-gray-200 disabled:cursor-not-allowed" />
                                        <span title="Rojas">🟥</span><input v-model="jug.rojas" :disabled="jug.suspendido" type="number" min="0" max="1" class="w-10 p-1 border border-red-300 text-center font-bold rounded bg-red-50 outline-none focus:border-red-600 disabled:bg-gray-200 disabled:cursor-not-allowed" />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- CAMPO NOVEDADES -->
                    <div class="bg-white p-5 rounded-2xl shadow-sm border">
                        <h4 class="font-black text-sm text-[#001a4d] border-b pb-2 mb-3 uppercase">� Foto de Vocalía</h4>
                        <div v-if="!fotoVocaliaPreview" class="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-300 bg-gray-50 px-4 py-6">
                            <p class="text-sm font-semibold text-gray-600">Sube una imagen de la vocalía original.</p>
                            <label class="mt-3 cursor-pointer rounded-lg bg-blue-900 px-4 py-2 text-sm font-bold text-white">Seleccionar foto<input @change="seleccionarFotoVocalia" type="file" accept="image/*" class="sr-only" /></label>
                        </div>
                        <div v-else class="space-y-3">
                            <img :src="fotoVocaliaPreview" class="mx-auto h-40 rounded-xl object-cover" />
                            <button @click="removerFotoVocalia" type="button" class="rounded-lg bg-red-600 px-3 py-2 text-sm font-bold text-white">Quitar foto</button>
                        </div>
                    </div>
                    <div class="bg-white p-5 rounded-2xl shadow-sm border">
                        <h4 class="font-black text-sm text-[#001a4d] border-b pb-2 mb-3 uppercase">�📝 Novedades del Partido (Opcional)</h4>
                        <textarea v-model="novedadesForm" placeholder="Registra cualquier eventualidad, reclamo, observaciones sobre los jugadores o hinchada..." class="w-full p-3 border rounded-xl outline-none focus:border-blue-900 min-h-[80px] text-sm"></textarea>
                    </div>

                </div>
                <div class="bg-gray-100 p-4 text-right border-t flex justify-end space-x-3"><button @click="mostrarModalVocalia = false" class="bg-gray-400 hover:bg-gray-500 text-white font-bold px-6 py-2 rounded-xl text-sm transition">Cancelar Acta</button><button @click="enviarActaVocalia" class="bg-blue-900 hover:bg-blue-950 text-white font-black px-8 py-2 rounded-xl text-sm shadow transition">💾 Registrar y Finalizar Partido</button></div>
            </div>
        </div>

        <!-- MODAL: VER ACTA FINALIZADA (REPORTE OFICIAL CON DETALLES) -->
        <div v-if="mostrarModalActaFinalizada" class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div class="bg-white rounded-3xl shadow-2xl max-w-2xl w-full overflow-hidden flex flex-col border border-gray-200">
                <div class="bg-[#001a4d] p-5 text-white flex justify-between items-center">
                    <h3 class="font-black uppercase text-lg flex items-center">🔍 Resultado Oficial</h3>
                    <button @click="mostrarModalActaFinalizada = false" class="text-white hover:text-gray-300 font-bold text-xl">✕</button>
                </div>
                <div class="p-8 text-center bg-gray-50/50 space-y-6">
                    <div class="inline-block bg-blue-100 text-blue-800 px-4 py-1.5 rounded-full font-bold text-xs uppercase tracking-widest mb-2 shadow-sm">
                        📅 {{ actaFinalizadaData.fecha }} - ⏰ {{ actaFinalizadaData.hora }}
                    </div>
                    <div v-if="detallesActa.foto_vocalia_url" class="flex justify-center">
                        <img :src="detallesActa.foto_vocalia_url" class="h-40 rounded-2xl object-cover border" />
                    </div>
                    
                    <div class="flex items-center justify-center space-x-6">
                        <div class="flex flex-col items-center w-1/3">
                            <img v-if="obtenerLogoEquipo(actaFinalizadaData.local)" :src="obtenerLogoEquipo(actaFinalizadaData.local)" class="h-20 w-20 object-contain mb-3 drop-shadow-md" />
                            <div v-else class="h-20 w-20 rounded-full bg-gray-200 flex items-center justify-center text-3xl mb-3 shadow-inner">🛡️</div>
                            <p class="font-black text-[#001a4d] text-base leading-tight">{{ actaFinalizadaData.local }}</p>
                        </div>
                        
                        <div class="flex flex-col items-center justify-center">
                            <div class="bg-white border-2 border-gray-100 shadow-xl rounded-2xl px-6 py-4 flex items-center space-x-4">
                                <span class="text-5xl font-black text-gray-800">{{ actaFinalizadaData.goles_local }}</span>
                                <span class="text-2xl font-black text-gray-300">-</span>
                                <span class="text-5xl font-black text-gray-800">{{ actaFinalizadaData.goles_visitante }}</span>
                            </div>
                            <span class="mt-4 text-xs font-bold text-gray-400 bg-gray-100 px-3 py-1 rounded-lg uppercase">Finalizado</span>
                        </div>
                        
                        <div class="flex flex-col items-center w-1/3">
                            <img v-if="obtenerLogoEquipo(actaFinalizadaData.visitante)" :src="obtenerLogoEquipo(actaFinalizadaData.visitante)" class="h-20 w-20 object-contain mb-3 drop-shadow-md" />
                            <div v-else class="h-20 w-20 rounded-full bg-gray-200 flex items-center justify-center text-3xl mb-3 shadow-inner">🛡️</div>
                            <p class="font-black text-[#001a4d] text-base leading-tight">{{ actaFinalizadaData.visitante }}</p>
                        </div>
                    </div>
                    
                    <div class="pt-4 flex justify-center">
                        <p class="text-sm font-bold text-gray-500 bg-white px-6 py-2 rounded-xl shadow-sm border border-gray-100">
                            <span class="mr-2">🏁</span> Juez Central: <span class="text-[#001a4d]">{{ actaFinalizadaData.arbitro }}</span>
                        </p>
                    </div>

                    <!-- NUEVA SECCIÓN DE DETALLES DEL ACTA -->
                    <div v-if="!cargandoActa" class="mt-4 text-left border-t border-gray-200 pt-4 max-h-[250px] overflow-y-auto pr-2">
                        <div class="grid grid-cols-2 gap-6 mb-4">
                            <div>
                                <h5 class="font-black text-xs text-[#001a4d] uppercase border-b pb-1 mb-2">{{ actaFinalizadaData.local }}</h5>
                                <ul class="text-xs space-y-1">
                                    <li v-for="inc in detallesActa.incidencias_local" :key="inc.jugador" class="flex justify-between items-center border-b border-gray-100 pb-1">
                                        <span class="truncate pr-1 text-gray-700 font-bold">{{inc.jugador}}</span>
                                        <span class="whitespace-nowrap">
                                            <span v-if="inc.goles > 0">⚽ {{inc.goles}}</span>
                                            <span v-if="inc.amarillas > 0" class="ml-1">🟨 {{inc.amarillas}}</span>
                                            <span v-if="inc.rojas > 0" class="ml-1">🟥 {{inc.rojas}}</span>
                                        </span>
                                    </li>
                                    <li v-if="detallesActa.incidencias_local.length === 0" class="text-gray-400 italic">Sin incidencias registradas.</li>
                                </ul>
                            </div>
                            <div>
                                <h5 class="font-black text-xs text-[#001a4d] uppercase border-b pb-1 mb-2">{{ actaFinalizadaData.visitante }}</h5>
                                <ul class="text-xs space-y-1">
                                    <li v-for="inc in detallesActa.incidencias_visitante" :key="inc.jugador" class="flex justify-between items-center border-b border-gray-100 pb-1">
                                        <span class="truncate pr-1 text-gray-700 font-bold">{{inc.jugador}}</span>
                                        <span class="whitespace-nowrap">
                                            <span v-if="inc.goles > 0">⚽ {{inc.goles}}</span>
                                            <span v-if="inc.amarillas > 0" class="ml-1">🟨 {{inc.amarillas}}</span>
                                            <span v-if="inc.rojas > 0" class="ml-1">🟥 {{inc.rojas}}</span>
                                        </span>
                                    </li>
                                    <li v-if="detallesActa.incidencias_visitante.length === 0" class="text-gray-400 italic">Sin incidencias registradas.</li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="bg-yellow-50 p-4 rounded-xl border border-yellow-200 mt-4">
                            <h5 class="font-black text-[11px] text-yellow-800 uppercase mb-2 flex items-center">📝 Novedades Registradas en Vocalía</h5>
                            <p class="text-xs text-gray-700 whitespace-pre-wrap font-medium">{{ detallesActa.novedades }}</p>
                        </div>
                    </div>
                    <div v-else class="mt-4 text-center text-sm text-gray-500 py-4 font-bold animate-pulse">Cargando incidencias del encuentro...</div>

                </div>
            </div>
        </div>

        <!-- MODAL FLOTANTE: VER PLANTILLA -->
        <div v-if="mostrarModalPlantilla" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <!-- (Se mantiene tal cual) -->
            <div class="bg-white rounded-2xl max-w-2xl w-full max-h-[85vh] overflow-hidden flex flex-col border">
                <div class="bg-[#001a4d] p-5 text-white flex justify-between items-center"><div><h3 class="text-xl font-black uppercase">Plantilla Oficial</h3><p class="text-yellow-400 text-sm font-bold">{{ equipoSeleccionadoPlantilla }}</p></div><button @click="mostrarModalPlantilla = false" class="text-white w-8 h-8 rounded-full">✕</button></div>
                <div class="p-6 overflow-y-auto flex-1 space-y-4">
                    <div v-for="jug in jugadoresFiltradosPlantilla" :key="jug.id_jugador" class="flex items-center justify-between border p-3 rounded-xl bg-gray-50">
                        <div class="flex items-center space-x-4"><img v-if="jug.url_foto" :src="jug.url_foto" class="h-12 w-12 object-cover rounded-full border" /><div v-else class="h-12 w-12 bg-gray-200 rounded-full flex items-center justify-center">👤</div><div><p class="font-bold text-[#001a4d]">{{ jug.nombre }} {{ jug.apellido }}</p></div></div>
                        <div class="text-right"><span class="px-3 py-1 bg-yellow-100 rounded font-black text-lg">#{{ jug.numero_camiseta }}</span></div>
                    </div>
                </div>
            </div>
        </div>

    </div>
</template>

<style>
@media print {
    body { background-color: white !important; margin: 0; padding: 0; }
    .no-imprimir { display: none !important; }
    .seccion-carnet { display: block !important; position: absolute; top: 0; left: 0; width: 100%; margin-top: 2cm; }
    .carnet-imprimible { margin: 0 auto; box-shadow: none !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
}
</style>