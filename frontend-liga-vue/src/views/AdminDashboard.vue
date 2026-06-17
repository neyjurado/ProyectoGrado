<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Menú de Navegación Interna
const vistaActual = ref('jugadores') // 'jugadores' o 'equipos'

// ==========================================
// VARIABLES - MÓDULO JUGADORES
// ==========================================
const equipos = ref([])
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

const videoRef = ref(null)
const canvasRef = ref(null)
const camaraAbierta = ref(false)
const fotoTomada = ref(false)
const fotoBase64 = ref('')

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

const nuevoEquipo = ref({
    nombre: '',
    fecha_fundacion: '',
    categoria: '',
    url_logo: ''
})

// Variables para el manejo visual del archivo local
const logoPreview = ref('')
const archivoSeleccionado = ref(null)

// Función para previsualizar el escudo en pantalla
const seleccionarEscudo = (event) => {
    const archivo = event.target.files[0]
    if (!archivo) return

    if (!archivo.type.startsWith('image/')) {
        msjErrorEquipo.value = "Por favor, selecciona un archivo de imagen válido (PNG, JPG)."
        return
    }

    archivoSeleccionado.value = archivo
    logoPreview.value = URL.createObjectURL(archivo)
}

// Función para remover el escudo seleccionado
const removerEscudo = () => {
    logoPreview.value = ''
    archivoSeleccionado.value = null
}

// ==========================================
// LÓGICA PRINCIPAL
// ==========================================
const cargarEquipos = async () => {
    try {
        const res = await fetch('http://127.0.0.1:8000/equipos')
        equipos.value = await res.json()
    } catch (err) {
        console.error("No se pudieron cargar los equipos.")
    }
}

onMounted(async () => {
    const usuarioSesion = JSON.parse(localStorage.getItem('usuario'))
    if (!usuarioSesion || usuarioSesion.rol !== 'Administrador') {
        router.push('/login')
        return
    }
    await cargarEquipos()
})

const cerrarSesion = () => {
    localStorage.removeItem('usuario')
    router.push('/login')
}

// Lógica Cámara
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

// Lógica Registrar Jugador
const imprimirCarnet = () => window.print()

const registrarJugador = async () => {
    if (!fotoBase64.value) { mensajeError.value = "¡Debes tomar la foto primero!"; return }
    cargando.value = true; mensajeError.value = ''; mensajeExito.value = ''
    
    const payload = {
        cedula: cedula.value, id_equipo: parseInt(id_equipo.value),
        nombre: nombre.value, apellido: apellido.value,
        fecha_nacimiento: fecha_nacimiento.value, url_foto: fotoBase64.value,
        numero_camiseta: parseInt(numero_camiseta.value)
    }

    try {
        const res = await fetch('http://127.0.0.1:8000/jugadores', {
            method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
        })
        const datos = await res.json()
        if (res.ok) { mensajeExito.value = datos.mensaje; mostrarCarnet.value = true } 
        else { mensajeError.value = datos.detail }
    } catch (err) { mensajeError.value = "Error de conexión." } 
    finally { cargando.value = false }
}

// Lógica Registrar Equipo (AHORA HACE LA DOBLE FUNCIÓN)
const registrarEquipo = async () => {
    cargandoEquipo.value = true; 
    msjErrorEquipo.value = ''; 
    msjExitoEquipo.value = '';
    
    let urlDescargaFinal = null;

    try {
        // PASO 1: Si seleccionó un escudo, subirlo a Firebase a través del Backend
        if (archivoSeleccionado.value) {
            const formData = new FormData();
            formData.append('file', archivoSeleccionado.value);
            formData.append('folder', 'equipos');

            const uploadRes = await fetch('http://127.0.0.1:8000/upload-image', {
                method: 'POST',
                body: formData // No enviamos 'Content-Type', el navegador lo pone automáticamente con el Boundary para archivos
            });
            
            const uploadData = await uploadRes.json();
            
            if (!uploadRes.ok) throw new Error(uploadData.detail || "Error al subir la imagen");
            
            urlDescargaFinal = uploadData.url; // Guardamos la URL pública
        }

        // PASO 2: Guardar el equipo en la base de datos SQL
        const payload = {
            nombre_equipo: nuevoEquipo.value.nombre,
            categoria: nuevoEquipo.value.categoria,
            fecha_fundacion: nuevoEquipo.value.fecha_fundacion ? nuevoEquipo.value.fecha_fundacion : null,
            url_logo: urlDescargaFinal // Enviamos la URL si existe, si no, va en null
        }

        const res = await fetch('http://127.0.0.1:8000/equipos', {
            method: 'POST', 
            headers: {'Content-Type': 'application/json'}, 
            body: JSON.stringify(payload)
        })
        
        const datos = await res.json()
        
        if (res.ok) { 
            msjExitoEquipo.value = "¡Equipo y escudo registrados exitosamente!" 
            nuevoEquipo.value = { nombre: '', fecha_fundacion: '', categoria: '', url_logo: '' }
            removerEscudo() // Limpiamos la foto de previsualización
            await cargarEquipos() // Actualizamos la tabla
        } else { 
            msjErrorEquipo.value = datos.detail 
        }
    } catch (err) { 
        msjErrorEquipo.value = err.message || "Error al conectar con el servidor.";
    } finally { 
        cargandoEquipo.value = false 
    }
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
            
            <div class="flex flex-wrap gap-4 mb-8 no-imprimir justify-center border-b pb-6">
                <button @click="vistaActual = 'jugadores'" :class="vistaActual === 'jugadores' ? 'bg-[#001a4d] text-white shadow-lg scale-105' : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'" class="px-6 py-3 rounded-xl font-bold transition duration-200 flex items-center">
                    <span class="mr-2">📝</span> Registro de Jugadores
                </button>
                <button @click="vistaActual = 'equipos'" :class="vistaActual === 'equipos' ? 'bg-[#001a4d] text-white shadow-lg scale-105' : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'" class="px-6 py-3 rounded-xl font-bold transition duration-200 flex items-center">
                    <span class="mr-2">🛡️</span> Gestión de Equipos
                </button>
            </div>

            <div v-show="vistaActual === 'jugadores'" class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div class="lg:col-span-2 bg-white p-8 rounded-2xl shadow-lg border border-gray-200 no-imprimir">
                    <h2 class="text-2xl font-black text-gray-800 mb-6 flex items-center">
                        <span class="mr-2">📝</span> REGISTRO DE JUGADOR
                    </h2>

                    <div v-if="mensajeError" class="bg-red-50 text-red-600 p-4 rounded-lg font-medium mb-6 border border-red-200">⚠️ {{ mensajeError }}</div>
                    <div v-if="mensajeExito" class="bg-green-50 text-green-700 p-4 rounded-lg font-medium mb-6 border border-green-200">✅ {{ mensajeExito }}</div>
                    
                    <form @submit.prevent="registrarJugador" class="space-y-6">
                        <div class="flex flex-col items-center space-y-4 bg-gray-50 p-6 rounded-xl border-2 border-dashed border-gray-300">
                            <video ref="videoRef" width="320" height="240" autoplay class="rounded-lg bg-black shadow-inner" v-show="camaraAbierta" style="transform: scaleX(-1);"></video>
                            <canvas ref="canvasRef" width="320" height="240" class="hidden"></canvas>
                            <img :src="fotoBase64" class="rounded-lg shadow-md" width="200" v-show="fotoTomada" />
                            
                            <div class="flex space-x-4">
                                <button v-if="!camaraAbierta && !fotoTomada" @click="abrirCamara" type="button" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-bold text-sm transition">📸 Abrir Cámara</button>
                                <button v-if="camaraAbierta" @click="capturarFoto" type="button" class="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg font-bold text-sm shadow-md animate-pulse">🎯 Capturar Foto</button>
                                <button v-if="fotoTomada" @click="abrirCamara" type="button" class="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg font-bold text-sm transition">🔄 Retomar Foto</button>
                            </div>
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label class="block text-sm font-bold text-gray-700 mb-1">Cédula</label>
                                <input v-model="cedula" type="text" required maxlength="10" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#001a4d] outline-none" />
                            </div>
                            <div>
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
                                <label class="block text-sm font-bold text-gray-700 mb-1">Fecha de Nacimiento</label>
                                <input v-model="fecha_nacimiento" type="date" required class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#001a4d] outline-none" />
                            </div>
                            <div>
                                <label class="block text-sm font-bold text-gray-700 mb-1">Nº Camiseta</label>
                                <input v-model="numero_camiseta" type="number" required min="1" max="99" placeholder="Ej. 10" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#001a4d] outline-none" />
                            </div>
                        </div>

                        <button type="submit" :disabled="cargando" class="w-full bg-[#001a4d] hover:bg-blue-900 text-white font-bold py-4 rounded-xl shadow-lg transition flex justify-center items-center">
                            <span v-if="cargando" class="inline-block animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent mr-2"></span>
                            FINALIZAR E IMPRIMIR CARNET
                        </button>
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
                                <div><p class="text-[10px] text-blue-200">CÉDULA</p><p class="font-mono text-sm font-bold">{{ cedula }}</p></div>
                                <div><p class="text-[10px] text-blue-200">Nº CAMISETA</p><p class="font-mono text-sm font-bold text-yellow-400">#{{ numero_camiseta }}</p></div>
                            </div>
                        </div>
                        <div class="absolute bottom-0 w-full bg-yellow-400 text-blue-900 text-center py-2 font-black text-[11px] italic uppercase tracking-wider">Liga Deportiva Parroquial de Conocoto</div>
                    </div>
                    <button @click="imprimirCarnet" class="w-full mt-6 bg-gray-800 hover:bg-black transition text-white py-3 rounded-lg font-bold shadow-lg no-imprimir">🖨️ Imprimir Carnet</button>
                </div>
            </div>

            <div v-show="vistaActual === 'equipos'" class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                
                <div class="bg-white p-8 rounded-2xl shadow-lg border border-gray-200 h-fit">
                    <h2 class="text-2xl font-black text-[#001a4d] mb-6 flex items-center">
                        <span class="mr-2">🛡️</span> Nuevo Equipo
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
                                <option value="Serie A">Serie A</option>
                                <option value="Serie B">Serie B</option>
                                <option value="Maxima">Máxima</option>
                                <option value="Femenino">Femenino</option>
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

                        <button type="submit" :disabled="cargandoEquipo" class="w-full bg-yellow-400 hover:bg-yellow-500 text-blue-900 font-bold py-3 rounded-xl shadow transition flex justify-center items-center mt-2">
                            <span v-if="cargandoEquipo" class="inline-block animate-spin rounded-full h-5 w-5 border-2 border-blue-900 border-t-transparent mr-2"></span>
                            Guardar Equipo
                        </button>
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
                                </tr>
                                <tr v-if="equipos.length === 0">
                                    <td colspan="4" class="p-6 text-center text-gray-500 italic">No hay equipos registrados aún.</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

            </div>

        </main>
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