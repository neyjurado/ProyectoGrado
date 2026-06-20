<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const vistaActual = ref('jugadores') 

// ==========================================
// VALIDACIONES DE FECHA (Mínimo 15 años)
// ==========================================
const calcularFechaMaxima = () => {
    const hoy = new Date();
    hoy.setFullYear(hoy.getFullYear() - 15);
    return hoy.toISOString().split('T')[0];
}
const fechaMaximaPermitida = ref(calcularFechaMaxima())

// ==========================================
// VARIABLES - MÓDULO JUGADORES
// ==========================================
const equipos = ref([])
const jugadoresRegistrados = ref([]) 
const cargando = ref(false)
const mensajeError = ref('')
const mensajeExito = ref('')
const mostrarCarnet = ref(false)

// Variables del Formulario de Jugadores
const cedula = ref('')
const id_equipo = ref('')
const nombre = ref('')
const apellido = ref('')
const fecha_nacimiento = ref('')
const numero_camiseta = ref('')
const acepta_terminos = ref(false)

// Control de Edición y Búsqueda
const editandoJugador = ref(false)
const idJugadorEditando = ref(null)
const filtroBusqueda = ref('') // Para la barra de búsqueda
const filtroEquipoSelect = ref('') // Para el select de filtro

const videoRef = ref(null)
const canvasRef = ref(null)
const camaraAbierta = ref(false)
const fotoTomada = ref(false)
const fotoBase64 = ref('')

const docPreview = ref('')
const docSeleccionado = ref(null)

const seleccionarDocumento = (event) => {
    const archivo = event.target.files[0]
    if (!archivo) return
    if (!archivo.type.startsWith('image/')) {
        mensajeError.value = "Selecciona una imagen válida (PNG, JPG) para el documento."
        return
    }
    docSeleccionado.value = archivo
    docPreview.value = URL.createObjectURL(archivo)
}

const removerDocumento = () => {
    docPreview.value = ''
    docSeleccionado.value = null
}

const equipoSeleccionado = computed(() => {
    const eq = equipos.value.find(e => e.id === id_equipo.value)
    return eq ? { nombre: eq.nombre, categoria: eq.categoria } : { nombre: 'EQUIPO', categoria: 'CATEGORÍA' }
})

// ==========================================
// VARIABLES - MÓDULO EQUIPOS
// ==========================================
const cargandoEquipo = ref(false)
const msjErrorEquipo = ref('')
const msjExitoEquipo = ref('')

// Control de Edición de Equipos
const editandoEquipo = ref(false)
const idEquipoEditando = ref(null)

const nuevoEquipo = ref({
    nombre: '',
    fecha_fundacion: '',
    categoria: '',
    url_logo: ''
})

const logoPreview = ref('')
const archivoSeleccionado = ref(null)

// Variables para el Modal de Ver Plantilla
const mostrarModalPlantilla = ref(false)
const equipoSeleccionadoPlantilla = ref('')
const jugadoresFiltradosPlantilla = ref([])

const seleccionarEscudo = (event) => {
    const archivo = event.target.files[0]
    if (!archivo) return
    if (!archivo.type.startsWith('image/')) {
        msjErrorEquipo.value = "Selecciona una imagen válida (PNG, JPG)."
        return
    }
    archivoSeleccionado.value = archivo
    logoPreview.value = URL.createObjectURL(archivo)
}

const removerEscudo = () => {
    logoPreview.value = ''
    archivoSeleccionado.value = null
}

// ==========================================
// LÓGICA DE CARGA DE DATOS
// ==========================================
const cargarEquipos = async () => {
    try {
        const res = await fetch('http://127.0.0.1:8000/equipos')
        equipos.value = await res.json()
    } catch (err) {
        console.error("No se pudieron cargar los equipos.")
    }
}

const cargarJugadores = async () => {
    try {
        const res = await fetch('http://127.0.0.1:8000/jugadores')
        if(res.ok) {
            jugadoresRegistrados.value = await res.json()
        }
    } catch (err) {
        console.error("No se pudieron cargar los jugadores.")
    }
}

onMounted(async () => {
    const usuarioSesion = JSON.parse(localStorage.getItem('usuario'))
    if (!usuarioSesion || usuarioSesion.rol !== 'Administrador') {
        router.push('/login')
        return
    }
    await cargarEquipos()
    await cargarJugadores()
})

const cerrarSesion = () => {
    localStorage.removeItem('usuario')
    router.push('/login')
}

// ==========================================
// PROPIEDADES COMPUTADAS (BUSCADOR MÁGICO)
// ==========================================
const jugadoresFiltrados = computed(() => {
    return jugadoresRegistrados.value.filter(jugador => {
        const texto = filtroBusqueda.value.toLowerCase();
        const coincideTexto = 
            jugador.nombre.toLowerCase().includes(texto) ||
            jugador.apellido.toLowerCase().includes(texto) ||
            jugador.cedula.toLowerCase().includes(texto);
            
        const coincideEquipo = filtroEquipoSelect.value === '' || jugador.id_equipo === parseInt(filtroEquipoSelect.value);
        
        return coincideTexto && coincideEquipo;
    });
})

// Cuenta cuántos jugadores tiene un equipo
const contarJugadores = (id_equipo) => {
    return jugadoresRegistrados.value.filter(j => j.id_equipo === id_equipo).length;
}

// ==========================================
// LÓGICA CÁMARA
// ==========================================
const abrirCamara = async () => {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true })
        videoRef.value.srcObject = stream
        camaraAbierta.value = true; fotoTomada.value = false; fotoBase64.value = ''
    } catch (err) {
        mensajeError.value = "No se pudo acceder a la cámara."
    }
}

const capturarFoto = () => {
    const context = canvasRef.value.getContext('2d')
    context.drawImage(videoRef.value, 0, 0, 320, 240)
    fotoBase64.value = canvasRef.value.toDataURL('image/png')
    fotoTomada.value = true; camaraAbierta.value = false
    const stream = videoRef.value.srcObject
    if (stream) stream.getTracks().forEach(track => track.stop())
}

const imprimirCarnet = () => window.print()

const prepararReimpresion = (jugador) => {
    cedula.value = jugador.cedula;
    nombre.value = jugador.nombre;
    apellido.value = jugador.apellido;
    numero_camiseta.value = jugador.numero_camiseta;
    id_equipo.value = jugador.id_equipo;
    fotoBase64.value = jugador.url_foto;
    mostrarCarnet.value = true;
    window.scrollTo(0, 0);
}

// HELPERS DE CONVERSIÓN Y SUBIDA
const base64ToFile = async (base64String, filename) => {
    const res = await fetch(base64String);
    const blob = await res.blob();
    return new File([blob], filename, { type: 'image/png' });
}

const uploadToFirebase = async (file, folder) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('folder', folder);
    const res = await fetch('http://127.0.0.1:8000/upload-image', { method: 'POST', body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail);
    return data.url;
}

const cerrarCarnetYLimpiar = () => {
    mostrarCarnet.value = false;
    editandoJugador.value = false;
    idJugadorEditando.value = null;
    cedula.value = '';
    id_equipo.value = '';
    nombre.value = '';
    apellido.value = '';
    fecha_nacimiento.value = '';
    numero_camiseta.value = '';
    acepta_terminos.value = false;
    fotoBase64.value = '';
    fotoTomada.value = false;
    camaraAbierta.value = false;
    removerDocumento();
    mensajeExito.value = '';
    mensajeError.value = '';
}

// ==========================================
// ACCIONES: ACCIONES DE JUGADORES (CRUD)
// ==========================================
const prepararEdicionJugador = (jugador) => {
    editandoJugador.value = true;
    idJugadorEditando.value = jugador.id_jugador;
    
    cedula.value = jugador.cedula;
    nombre.value = jugador.nombre;
    apellido.value = jugador.apellido;
    fecha_nacimiento.value = jugador.fecha_nacimiento;
    numero_camiseta.value = jugador.numero_camiseta;
    id_equipo.value = jugador.id_equipo;
    
    fotoBase64.value = jugador.url_foto || '';
    fotoTomada.value = !!jugador.url_foto;
    docPreview.value = jugador.url_documento || ''; 
    acepta_terminos.value = true;
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

const eliminarJugador = async (id_jugador, nombreCompleto) => {
    if (!confirm(`¿Estás seguro de que deseas dar de baja al jugador ${nombreCompleto}?`)) return;
    
    try {
        const res = await fetch(`http://127.0.0.1:8000/jugadores/${id_jugador}`, { method: 'DELETE' });
        const data = await res.json();
        if (res.ok) {
            alert(data.mensaje);
            await cargarJugadores();
        } else {
            alert(`Error: ${data.detail}`);
        }
    } catch (err) {
        alert("Error de conexión al dar de baja al jugador.");
    }
}

const registrarJugador = async () => {
    if (!fotoBase64.value) { mensajeError.value = "¡Debes tomar la foto del rostro primero!"; return }
    if (!editandoJugador.value && !docSeleccionado.value) { mensajeError.value = "¡Debes adjuntar la foto del documento de identidad!"; return }
    if (!acepta_terminos.value) { mensajeError.value = "Debes aceptar los términos y condiciones."; return }

    cargando.value = true; mensajeError.value = ''; mensajeExito.value = ''
    
    try {
        let urlRostroFinal = fotoBase64.value;
        let urlDocumentoFinal = docPreview.value;

        if (fotoBase64.value.startsWith('data:image')) {
            const fotoFile = await base64ToFile(fotoBase64.value, `rostro_${cedula.value}.png`);
            urlRostroFinal = await uploadToFirebase(fotoFile, 'jugadores_rostros');
        }
        if (docSeleccionado.value) {
            urlDocumentoFinal = await uploadToFirebase(docSeleccionado.value, 'jugadores_documentos');
        }

        const payload = {
            cedula: cedula.value, 
            id_equipo: parseInt(id_equipo.value),
            nombre: nombre.value, 
            apellido: apellido.value,
            fecha_nacimiento: fecha_nacimiento.value, 
            url_foto: urlRostroFinal,            
            numero_camiseta: parseInt(numero_camiseta.value),
            url_documento: urlDocumentoFinal,
            acepta_terminos: acepta_terminos.value
        }

        const urlEndpoint = editandoJugador.value 
            ? `http://127.0.0.1:8000/jugadores/${idJugadorEditando.value}`
            : 'http://127.0.0.1:8000/jugadores';
            
        const metodo = editandoJugador.value ? 'PUT' : 'POST';

        const res = await fetch(urlEndpoint, {
            method: metodo, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
        })
        const datos = await res.json()

        if (res.ok) { 
            mensajeExito.value = editandoJugador.value ? "¡Jugador actualizado exitosamente!" : datos.mensaje; 
            mostrarCarnet.value = true;
            await cargarJugadores();
        } else { 
            mensajeError.value = datos.detail 
        }
    } catch (err) { 
        mensajeError.value = err.message || "Error al procesar el registro." 
    } finally { 
        cargando.value = false 
    }
}

// ==========================================
// ACCIONES: ACCIONES DE EQUIPOS (CRUD)
// ==========================================
const prepararEdicionEquipo = (equipo) => {
    editandoEquipo.value = true;
    idEquipoEditando.value = equipo.id;
    
    nuevoEquipo.value.nombre = equipo.nombre;
    nuevoEquipo.value.categoria = equipo.categoria;
    logoPreview.value = equipo.url_logo || '';
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

const eliminarEquipo = async (id_equipo, nombreEquipo) => {
    // Validamos en Frontend antes de preguntar al backend
    const cantidad = contarJugadores(id_equipo);
    if (cantidad > 0) {
        alert(`No puedes dar de baja a "${nombreEquipo}" porque tiene ${cantidad} jugadores registrados. Da de baja o transfiere a los jugadores primero.`);
        return;
    }

    if (!confirm(`¿Estás seguro de que deseas dar de baja al equipo ${nombreEquipo}?`)) return;
    
    try {
        const res = await fetch(`http://127.0.0.1:8000/equipos/${id_equipo}`, { method: 'DELETE' });
        const data = await res.json();
        if (res.ok) {
            alert(data.mensaje);
            await cargarEquipos();
        } else {
            alert(`Error: ${data.detail}`);
        }
    } catch (err) {
        alert("Error de conexión al dar de baja al equipo.");
    }
}

const verPlantilla = (equipo) => {
    equipoSeleccionadoPlantilla.value = equipo.nombre;
    jugadoresFiltradosPlantilla.value = jugadoresRegistrados.value.filter(j => j.id_equipo === equipo.id);
    mostrarModalPlantilla.value = true;
}

const registrarEquipo = async () => {
    cargandoEquipo.value = true; msjErrorEquipo.value = ''; msjExitoEquipo.value = '';
    let urlDescargaFinal = logoPreview.value;

    try {
        if (archivoSeleccionado.value) {
            urlDescargaFinal = await uploadToFirebase(archivoSeleccionado.value, 'equipos');
        }

        const payload = {
            nombre_equipo: nuevoEquipo.value.nombre,
            categoria: nuevoEquipo.value.categoria,
            fecha_fundacion: nuevoEquipo.value.fecha_fundacion ? nuevoEquipo.value.fecha_fundacion : null,
            url_logo: urlDescargaFinal 
        }

        const urlEndpoint = editandoEquipo.value 
            ? `http://127.0.0.1:8000/equipos/${idEquipoEditando.value}`
            : 'http://127.0.0.1:8000/equipos';
            
        const metodo = editandoEquipo.value ? 'PUT' : 'POST';

        const res = await fetch(urlEndpoint, {
            method: metodo, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
        })
        const datos = await res.json()
        
        if (res.ok) { 
            msjExitoEquipo.value = editandoEquipo.value ? "¡Equipo actualizado correctamente!" : "¡Equipo registrado exitosamente!";
            nuevoEquipo.value = { nombre: '', fecha_fundacion: '', categoria: '', url_logo: '' }
            editandoEquipo.value = false;
            idEquipoEditando.value = null;
            removerEscudo() 
            await cargarEquipos() 
        } else { 
            msjErrorEquipo.value = datos.detail 
        }
    } catch (err) { 
        msjErrorEquipo.value = err.message || "Error al conectar con el servidor.";
    } finally { 
        cargandoEquipo.value = false 
    }
}

const cancelarEdicionEquipo = () => {
    editandoEquipo.value = false;
    idEquipoEditando.value = null;
    nuevoEquipo.value = { nombre: '', fecha_fundacion: '', categoria: '', url_logo: '' };
    removerEscudo();
}
</script>

<template>
    <div class="bg-gray-100 font-sans min-h-screen pb-20">
        
        <nav class="bg-[#001a4d] p-4 shadow-md text-white flex justify-between items-center no-imprimir sticky top-0 z-50">
            <div class="flex items-center space-x-3">
                <span class="text-2xl">🛡️</span>
                <h1 class="text-xl font-bold">Panel de Administración</h1>
            </div>
            <button @click="cerrarSesion" class="bg-red-600 hover:bg-red-700 transition px-4 py-2 rounded-lg text-sm font-bold shadow-md">
                Cerrar Sesión
            </button>
        </nav>

        <main class="container mx-auto mt-8 px-4">
            
            <div class="flex flex-wrap gap-3 mb-8 no-imprimir justify-center border-b border-gray-300 pb-6">
                <button @click="vistaActual = 'jugadores'" :class="vistaActual === 'jugadores' ? 'bg-[#001a4d] text-white shadow-lg scale-105' : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'" class="px-5 py-3 rounded-xl font-bold transition duration-200 flex items-center">
                    <span class="mr-2">📝</span> Jugadores
                </button>
                <button @click="vistaActual = 'equipos'" :class="vistaActual === 'equipos' ? 'bg-[#001a4d] text-white shadow-lg scale-105' : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'" class="px-5 py-3 rounded-xl font-bold transition duration-200 flex items-center">
                    <span class="mr-2">🛡️</span> Equipos
                </button>
                
                <button @click="vistaActual = 'calendario'" :class="vistaActual === 'calendario' ? 'bg-[#001a4d] text-white shadow-lg scale-105' : 'bg-white text-gray-400 border border-gray-200 hover:bg-gray-200'" class="px-5 py-3 rounded-xl font-bold transition duration-200 flex items-center relative">
                    <span class="mr-2">📅</span> Calendario
                    <span class="absolute -top-2 -right-2 bg-yellow-400 text-[#001a4d] text-[9px] px-2 rounded-full">Pronto</span>
                </button>
                <button @click="vistaActual = 'resultados'" :class="vistaActual === 'resultados' ? 'bg-[#001a4d] text-white shadow-lg scale-105' : 'bg-white text-gray-400 border border-gray-200 hover:bg-gray-200'" class="px-5 py-3 rounded-xl font-bold transition duration-200 flex items-center relative">
                    <span class="mr-2">⚽</span> Resultados
                    <span class="absolute -top-2 -right-2 bg-yellow-400 text-[#001a4d] text-[9px] px-2 rounded-full">Pronto</span>
                </button>
            </div>

            <div v-show="vistaActual === 'jugadores'" class="space-y-8">
                
                <div class="bg-white p-8 rounded-2xl shadow-lg border border-gray-200 no-imprimir">
                    <h2 class="text-2xl font-black text-gray-800 mb-6 flex items-center">
                        <span class="mr-2 text-blue-600">📝</span> {{ editandoJugador ? 'EDITAR JUGADOR SELECCIONADO' : 'REGISTRO DE JUGADOR' }}
                    </h2>

                    <div v-if="mensajeError" class="bg-red-50 text-red-600 p-4 rounded-lg font-medium mb-6 border border-red-200 flex items-center"><span class="mr-2">⚠️</span> {{ mensajeError }}</div>
                    <div v-if="mensajeExito" class="bg-green-50 text-green-700 p-4 rounded-lg font-medium mb-6 border border-green-200 flex items-center"><span class="mr-2">✅</span> {{ mensajeExito }}</div>
                    
                    <form @submit.prevent="registrarJugador" class="space-y-6">
                        
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div class="flex flex-col items-center space-y-4 bg-gray-50 p-6 rounded-xl border-2 border-dashed border-gray-300">
                                <p class="text-sm font-bold text-gray-600">Foto del Rostro</p>
                                <video ref="videoRef" width="320" height="240" autoplay class="rounded-lg bg-black shadow-inner" v-show="camaraAbierta" style="transform: scaleX(-1);"></video>
                                <canvas ref="canvasRef" width="320" height="240" class="hidden"></canvas>
                                <img :src="fotoBase64" class="rounded-lg shadow-md max-h-48 object-cover" width="200" v-show="fotoTomada" />
                                
                                <div class="flex space-x-4">
                                    <button v-if="!camaraAbierta && !fotoTomada" @click="abrirCamara" type="button" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-bold text-sm transition">📸 Abrir Cámara</button>
                                    <button v-if="camaraAbierta" @click="capturarFoto" type="button" class="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg font-bold text-sm shadow-md animate-pulse">🎯 Capturar Foto</button>
                                    <button v-if="fotoTomada" @click="abrirCamara" type="button" class="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg font-bold text-sm transition">🔄 Retomar Foto</button>
                                </div>
                            </div>

                            <div class="flex flex-col items-center justify-center space-y-4 bg-gray-50 p-6 rounded-xl border-2 border-dashed border-gray-300">
                                <p class="text-sm font-bold text-gray-600">Foto Cédula / Pasaporte</p>
                                
                                <div v-if="!docPreview" class="text-gray-400 mb-1 text-5xl">🪪</div>
                                <div v-else class="relative mb-2">
                                    <img :src="docPreview" class="h-32 object-contain rounded-lg shadow-md border bg-white" alt="Doc preview" />
                                    <button @click="removerDocumento" type="button" class="absolute -top-2 -right-2 bg-red-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold shadow-md hover:bg-red-700 transition">✕</button>
                                </div>

                                <div class="flex text-sm text-gray-600">
                                    <label class="relative cursor-pointer bg-white rounded-md font-bold text-blue-700 hover:text-blue-800 focus-within:outline-none">
                                        <span>{{ docPreview ? 'Cambiar archivo' : 'Seleccionar archivo' }}</span>
                                        <input @change="seleccionarDocumento" type="file" accept="image/*" class="sr-only" />
                                    </label>
                                </div>
                            </div>
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4 border-t border-gray-200">
                            <div class="md:col-span-1">
                                <label class="block text-sm font-bold text-gray-700 mb-1">Cédula / Pasaporte</label>
                                <input v-model="cedula" type="text" placeholder="Ej. 1723456789 o AB12345" required class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#001a4d] outline-none uppercase" />
                            </div>
                            
                            <div class="md:col-span-2">
                                <label class="block text-sm font-bold text-gray-700 mb-1">Seleccionar Equipo</label>
                                <select v-model="id_equipo" required class="w-full p-3 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-[#001a4d] outline-none">
                                    <option value="" disabled>-- Seleccione un Equipo --</option>
                                    <option v-for="eq in equipos" :key="eq.id" :value="eq.id">{{ eq.nombre }} ({{ eq.categoria }})</option>
                                </select>
                            </div>
                            
                            <div>
                                <label class="block text-sm font-bold text-gray-700 mb-1">Nombres</label>
                                <input v-model="nombre" type="text" required class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#001a4d] outline-none" />
                            </div>
                            
                            <div>
                                <label class="block text-sm font-bold text-gray-700 mb-1">Apellidos</label>
                                <input v-model="apellido" type="text" required class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#001a4d] outline-none" />
                            </div>
                            
                            <div>
                                <label class="block text-sm font-bold text-gray-700 mb-1 flex justify-between">
                                    Fecha de Nacimiento <span class="text-xs text-red-500 font-normal">Mín. 15 años</span>
                                </label>
                                <input v-model="fecha_nacimiento" :max="fechaMaximaPermitida" type="date" required class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#001a4d] outline-none" />
                            </div>
                            
                            <div>
                                <label class="block text-sm font-bold text-gray-700 mb-1">Nº Camiseta</label>
                                <input v-model="numero_camiseta" type="number" required min="1" max="99" placeholder="Ej. 10" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#001a4d] outline-none" />
                            </div>
                        </div>

                        <div class="pt-6 border-t border-gray-200">
                            <label class="flex items-start space-x-3 cursor-pointer p-4 bg-blue-50 rounded-xl border border-blue-100 hover:bg-blue-100 transition">
                                <input v-model="acepta_terminos" type="checkbox" required class="mt-1 h-5 w-5 text-blue-600 rounded border-gray-300 focus:ring-blue-500" />
                                <span class="text-sm text-gray-700 font-medium">
                                    Confirmo que los datos ingresados son verídicos y acepto los <span class="text-blue-700 font-bold hover:underline">Términos y Condiciones</span> para el tratamiento de datos personales e imagen por parte de la L.D.P. Conocoto.
                                </span>
                            </label>
                            
                            <div class="flex space-x-4 mt-4">
                                <button v-if="editandoJugador" @click="cerrarCarnetYLimpiar" type="button" class="w-1/3 bg-gray-500 hover:bg-gray-600 text-white font-bold py-4 rounded-xl transition shadow-lg">
                                    CANCELAR EDICIÓN
                                </button>
                                <button type="submit" :disabled="!acepta_terminos || cargando" :class="acepta_terminos && !cargando ? 'bg-[#001a4d] hover:bg-blue-900' : 'bg-gray-400 cursor-not-allowed'" class="w-full text-white font-bold py-4 rounded-xl shadow-lg transition flex justify-center items-center">
                                    <span v-if="cargando" class="inline-block animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent mr-2"></span>
                                    {{ editandoJugador ? 'ACTUALIZAR DATOS JUGADOR' : 'GUARDAR JUGADOR E IMPRIMIR CARNET' }}
                                </button>
                            </div>
                        </div>

                    </form>
                </div>

                <div class="seccion-carnet" v-show="mostrarCarnet">
                    <div class="carnet-imprimible bg-[#001a4d] w-[350px] h-[500px] rounded-2xl shadow-2xl relative overflow-hidden text-white mx-auto border-4 border-yellow-400">
                        <div class="bg-white text-center py-4 text-blue-900 font-black text-xl">L.D.P. CONOCOTO</div>
                        <div class="flex justify-center mt-6"><img :src="fotoBase64" class="w-40 h-40 object-cover border-4 border-white rounded-lg bg-gray-200" /></div>
                        <div class="p-6 text-center space-y-1">
                            <h3 class="text-2xl font-bold uppercase tracking-tighter">{{ nombre }} {{ apellido }}</h3>
                            <p class="text-yellow-400 font-bold text-lg">{{ equipoSeleccionado.nombre }}</p>
                            <p class="text-blue-200 font-semibold text-sm uppercase tracking-widest">{{ equipoSeleccionado.categoria }}</p>
                            <div class="flex justify-around pt-4 border-t border-blue-400 mt-2">
                                <div><p class="text-[10px] text-blue-200">DOCUMENTO ID</p><p class="font-mono text-sm font-bold uppercase">{{ cedula }}</p></div>
                                <div><p class="text-[10px] text-blue-200">Nº CAMISETA</p><p class="font-mono text-sm font-bold text-yellow-400">#{{ numero_camiseta }}</p></div>
                            </div>
                        </div>
                        <div class="absolute bottom-0 w-full bg-yellow-400 text-blue-900 text-center py-2 font-black text-[11px] italic uppercase tracking-wider">Liga Deportiva Parroquial de Conocoto</div>
                    </div>
                    <div class="flex space-x-4 max-w-sm mx-auto mt-6 no-imprimir">
                        <button @click="imprimirCarnet" class="w-full bg-gray-800 hover:bg-black transition text-white py-3 rounded-lg font-bold shadow-lg">🖨️ Imprimir</button>
                        <button @click="cerrarCarnetYLimpiar" class="w-full bg-red-600 hover:bg-red-700 transition text-white py-3 rounded-lg font-bold shadow-lg">Cerrar y Nuevo Registro</button>
                    </div>
                </div>

                <div class="bg-white p-8 rounded-2xl shadow-lg border border-gray-200 no-imprimir">
                    <h2 class="text-2xl font-black text-gray-800 mb-6 flex items-center justify-between">
                        <div class="flex items-center"><span class="mr-2 text-blue-600">📋</span> JUGADORES REGISTRADOS</div>
                        <div class="text-sm font-medium bg-blue-50 text-blue-700 px-3 py-1 rounded-full border border-blue-200">Total: {{ jugadoresFiltrados.length }}</div>
                    </h2>
                    
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                        <div class="md:col-span-2 relative">
                            <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">🔍</span>
                            <input v-model="filtroBusqueda" type="text" placeholder="Buscar por nombre, apellido o documento..." class="w-full pl-10 p-3 border border-gray-300 rounded-xl outline-none focus:ring-2 focus:ring-[#001a4d] bg-gray-50 text-sm font-medium" />
                        </div>
                        <div>
                            <select v-model="filtroEquipoSelect" class="w-full p-3 border border-gray-300 rounded-xl bg-gray-50 outline-none focus:ring-2 focus:ring-[#001a4d] text-sm font-medium">
                                <option value="">-- Todos los Equipos --</option>
                                <option v-for="eq in equipos" :key="eq.id" :value="eq.id">{{ eq.nombre }}</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="overflow-x-auto">
                        <table class="w-full text-left border-collapse">
                            <thead>
                                <tr class="bg-gray-100 text-gray-700 text-sm">
                                    <th class="p-3 border-b-2 text-center">Foto</th>
                                    <th class="p-3 border-b-2">Identidad</th>
                                    <th class="p-3 border-b-2">Equipo</th>
                                    <th class="p-3 border-b-2 text-center">Camiseta</th>
                                    <th class="p-3 border-b-2 text-center">Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="jug in jugadoresFiltrados" :key="jug.id_jugador" class="border-b hover:bg-gray-50 transition">
                                    <td class="p-3 flex justify-center">
                                        <img v-if="jug.url_foto" :src="jug.url_foto" class="h-10 w-10 object-cover rounded-md border border-gray-300 shadow-sm" alt="Foto Jugador" />
                                        <div v-else class="h-10 w-10 rounded-md bg-gray-200 flex items-center justify-center text-xs">👤</div>
                                    </td>
                                    <td class="p-3">
                                        <p class="font-bold text-[#001a4d]">{{ jug.nombre }} {{ jug.apellido }}</p>
                                        <p class="text-xs text-gray-500 font-mono uppercase">{{ jug.cedula }}</p>
                                    </td>
                                    <td class="p-3 font-medium text-gray-700">{{ jug.nombre_equipo || 'Sin asignar' }}</td>
                                    <td class="p-3 text-center">
                                        <span class="px-2 py-1 bg-yellow-100 text-yellow-800 rounded font-black border border-yellow-200">#{{ jug.numero_camiseta }}</span>
                                    </td>
                                    <td class="p-3">
                                        <div class="flex justify-center space-x-2">
                                            <button @click="prepararReimpresion(jug)" title="Reimprimir Carnet" class="bg-blue-100 hover:bg-blue-200 text-blue-700 p-2 rounded transition">🖨️</button>
                                            <button @click="prepararEdicionJugador(jug)" title="Editar Jugador" class="bg-gray-100 hover:bg-gray-200 text-gray-700 p-2 rounded transition">✏️</button>
                                            <button @click="eliminarJugador(jug.id_jugador, `${jug.nombre} ${jug.apellido}`)" title="Dar de Baja" class="bg-red-50 hover:bg-red-100 text-red-600 p-2 rounded transition">🗑️</button>
                                        </div>
                                    </td>
                                </tr>
                                <tr v-if="jugadoresFiltrados.length === 0">
                                    <td colspan="5" class="p-6 text-center text-gray-500 italic">No se encontraron jugadores que coincidan con la búsqueda.</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

            </div>

            <div v-show="vistaActual === 'equipos'" class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                
                <div class="bg-white p-8 rounded-2xl shadow-lg border border-gray-200 h-fit">
                    <h2 class="text-2xl font-black text-[#001a4d] mb-6 flex items-center">
                        <span class="mr-2">🛡️</span> {{ editandoEquipo ? 'EDITAR EQUIPO SELECCIONADO' : 'Nuevo Equipo' }}
                    </h2>

                    <div v-if="msjErrorEquipo" class="bg-red-50 text-red-600 p-3 rounded-lg text-sm mb-4 border border-red-200">⚠️ {{ msjErrorEquipo }}</div>
                    <div v-if="msjExitoEquipo" class="bg-green-50 text-green-700 p-3 rounded-lg text-sm mb-4 border border-green-200">✅ {{ msjExitoEquipo }}</div>
                    
                    <form @submit.prevent="registrarEquipo" class="space-y-5">
                        <div>
                            <label class="block text-sm font-bold text-gray-700 mb-1">Nombre del Equipo</label>
                            <input v-model="nuevoEquipo.nombre" type="text" required class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#001a4d] outline-none" placeholder="Ej. LDU Conocoto" />
                        </div>
                        
                        <div>
                            <label class="block text-sm font-bold text-gray-700 mb-1">Categoría</label>
                            <select v-model="nuevoEquipo.categoria" required class="w-full p-3 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-[#001a4d] outline-none">
                                <option value="" disabled>-- Seleccione Categoría --</option>
                                <option value="Máxima">Máxima</option>
                                <option value="Primera">Primera</option>
                            </select>
                        </div>

                        <div>
                            <label class="block text-sm font-bold text-gray-700 mb-1">Fecha de Fundación <span class="text-gray-400 font-normal">(Opcional)</span></label>
                            <input v-model="nuevoEquipo.fecha_fundacion" type="date" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#001a4d] outline-none" />
                        </div>

                        <div>
                            <label class="block text-sm font-bold text-gray-700 mb-1">Escudo del Equipo <span class="text-gray-400 font-normal">(Opcional)</span></label>
                            <div class="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-xl bg-gray-50 hover:border-[#001a4d] transition relative group">
                                <div class="space-y-2 text-center flex flex-col items-center">
                                    
                                    <div v-if="!logoPreview" class="text-gray-400 group-hover:text-[#001a4d] transition mb-1">
                                        <span class="text-5xl">🛡️</span>
                                    </div>
                                    
                                    <div v-else class="relative mb-2">
                                        <img :src="logoPreview" class="h-24 w-24 object-contain rounded-lg shadow-md border bg-white" alt="Escudo preview" />
                                        <button @click="removerEscudo" type="button" class="absolute -top-2 -right-2 bg-red-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold shadow-md hover:bg-red-700 transition">✕</button>
                                    </div>

                                    <div class="flex text-sm text-gray-600">
                                        <label class="relative cursor-pointer bg-white rounded-md font-bold text-blue-700 hover:text-blue-800 focus-within:outline-none">
                                            <span>{{ logoPreview ? 'Cambiar escudo' : 'Seleccionar archivo' }}</span>
                                            <input @change="seleccionarEscudo" type="file" accept="image/*" class="sr-only" />
                                        </label>
                                    </div>
                                    <p class="text-xs text-gray-400">PNG o JPG de hasta 5MB</p>
                                </div>
                            </div>
                        </div>

                        <div class="flex space-x-3">
                            <button v-if="editandoEquipo" @click="cancelarEdicionEquipo" type="button" class="w-1/3 bg-gray-500 hover:bg-gray-600 text-white font-bold py-3 rounded-xl transition shadow">
                                Cancelar
                            </button>
                            <button type="submit" :disabled="cargandoEquipo" class="w-full bg-yellow-400 hover:bg-yellow-500 text-blue-900 font-bold py-3 rounded-xl shadow transition flex justify-center items-center">
                                <span v-if="cargandoEquipo" class="inline-block animate-spin rounded-full h-5 w-5 border-2 border-blue-900 border-t-transparent mr-2"></span>
                                {{ editandoEquipo ? 'Actualizar Equipo' : 'Guardar Equipo' }}
                            </button>
                        </div>
                    </form>
                </div>

                <div class="bg-white p-8 rounded-2xl shadow-lg border border-gray-200">
                    <h2 class="text-2xl font-black text-gray-800 mb-6 flex items-center">
                        <span class="mr-2">📋</span> Equipos Registrados
                    </h2>
                    
                    <div class="overflow-x-auto">
                        <table class="w-full text-left border-collapse">
                            <thead>
                                <tr class="bg-gray-100 text-gray-700 text-sm">
                                    <th class="p-3 border-b-2">ID</th>
                                    <th class="p-3 border-b-2 text-center">Escudo</th>
                                    <th class="p-3 border-b-2">Nombre</th>
                                    <th class="p-3 border-b-2">Categoría</th>
                                    <th class="p-3 border-b-2 text-center">Plantilla</th>
                                    <th class="p-3 border-b-2 text-center">Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="eq in equipos" :key="eq.id" class="border-b hover:bg-gray-50 transition">
                                    <td class="p-3 font-mono text-gray-500 text-sm">{{ eq.id }}</td>
                                    
                                    <td class="p-3 flex justify-center">
                                        <img v-if="eq.url_logo" :src="eq.url_logo" class="h-10 w-10 object-contain rounded-full bg-white p-1 border shadow-sm" alt="Logo" />
                                        <div v-else class="h-10 w-10 rounded-full bg-gray-100 flex items-center justify-center text-xl border shadow-inner">🛡️</div>
                                    </td>

                                    <td class="p-3 font-bold text-[#001a4d]">{{ eq.nombre }}</td>
                                    <td class="p-3">
                                        <span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-bold">
                                            {{ eq.categoria }}
                                        </span>
                                    </td>
                                    <td class="p-3 text-center">
                                        <span class="font-bold text-gray-600">{{ contarJugadores(eq.id) }} <span class="text-xs font-normal">/ 25</span></span>
                                    </td>
                                    <td class="p-3">
                                        <div class="flex justify-center space-x-2">
                                            <button @click="prepararEdicionEquipo(eq)" title="Editar Equipo" class="bg-gray-100 hover:bg-gray-200 text-gray-700 p-2 rounded transition">✏️</button>
                                            <button @click="verPlantilla(eq)" title="Ver Plantilla" class="bg-blue-50 hover:bg-blue-100 text-blue-600 p-2 rounded transition">👥</button>
                                            <button @click="eliminarEquipo(eq.id, eq.nombre)" title="Dar de Baja" class="bg-red-50 hover:bg-red-100 text-red-600 p-2 rounded transition">🗑️</button>
                                        </div>
                                    </td>
                                </tr>
                                <tr v-if="equipos.length === 0">
                                    <td colspan="6" class="p-6 text-center text-gray-500 italic">No hay equipos registrados aún.</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

            </div>

        </main>

        <div v-if="mostrarModalPlantilla" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div class="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[85vh] overflow-hidden flex flex-col border border-gray-200">
                <div class="bg-[#001a4d] p-5 text-white flex justify-between items-center">
                    <div>
                        <h3 class="text-xl font-black uppercase">Plantilla Oficial</h3>
                        <p class="text-yellow-400 text-sm font-bold">{{ equipoSeleccionadoPlantilla }}</p>
                    </div>
                    <button @click="mostrarModalPlantilla = false" class="bg-white/10 hover:bg-white/20 w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm transition">✕</button>
                </div>
                
                <div class="p-6 overflow-y-auto flex-1 space-y-4">
                    <div v-for="jug in jugadoresFiltradosPlantilla" :key="jug.id_jugador" class="flex items-center justify-between border p-3 rounded-xl bg-gray-50 hover:bg-gray-100 transition shadow-sm">
                        <div class="flex items-center space-x-4">
                            <img v-if="jug.url_foto" :src="jug.url_foto" class="h-12 w-12 object-cover rounded-full border bg-white shadow-sm" />
                            <div v-else class="h-12 w-12 rounded-full bg-gray-200 flex items-center justify-center text-lg shadow-inner">👤</div>
                            <div>
                                <p class="font-bold text-[#001a4d] text-base leading-tight">{{ jug.nombre }} {{ jug.apellido }}</p>
                                <p class="text-xs text-gray-400 font-mono mt-0.5">ID: {{ jug.cedula }}</p>
                            </div>
                        </div>
                        <div class="text-right">
                            <span class="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-lg font-black border border-yellow-300 shadow-sm text-lg">#{{ jug.numero_camiseta }}</span>
                        </div>
                    </div>
                    
                    <div v-if="jugadoresFiltradosPlantilla.length === 0" class="text-center py-12 text-gray-400 italic">
                        No hay jugadores inscritos en este equipo todavía.
                    </div>
                </div>
                
                <div class="bg-gray-100 p-4 text-right border-t">
                    <button @click="mostrarModalPlantilla = false" class="bg-[#001a4d] hover:bg-blue-900 text-white font-bold px-5 py-2 rounded-lg text-sm transition shadow">Cerrar Plantilla</button>
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