<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Datos del usuario logeado
const usuarioAutenticado = ref(null)
const miIdJugador = ref(null)
const miIdEquipo = ref(null)

// Datos principales
const partidos = ref([])
const cargando = ref(true)

// Modales y estados
const mostrarCamerino = ref(false)
const camerinoData = ref([])
const partidoCamerino = ref(null)

const mostrarCalificacion = ref(false)
const partidoA_Calificar = ref(null)
const puntajeAsignado = ref(0)
const msjCalificacion = ref('')

const cargarMisDatosYPartidos = async () => {
    cargando.value = true
    try {
        // 1. Obtener mi ID de equipo desde la lista de jugadores (para el camerino)
        const resJugadores = await fetch('http://127.0.0.1:8000/jugadores')
        if (resJugadores.ok) {
            const lista = await resJugadores.json()
            const misDatos = lista.find(j => j.id_jugador === miIdJugador.value)
            if (misDatos) {
                miIdEquipo.value = misDatos.id_equipo
            }
        }

        // 2. Obtener mis partidos
        const res = await fetch(`http://127.0.0.1:8000/jugador/${miIdJugador.value}/partidos`)
        if (res.ok) {
            partidos.value = await res.json()
        }
    } catch (error) {
        console.error("Error al cargar el dashboard del jugador", error)
    } finally {
        cargando.value = false
    }
}

onMounted(() => {
    const usuarioSesion = JSON.parse(localStorage.getItem('usuario'))
    // Verificación de seguridad
    if (!usuarioSesion || usuarioSesion.rol !== 'Jugador' || !usuarioSesion.id_jugador) {
        localStorage.removeItem('usuario')
        router.push('/login')
        return
    }
    
    usuarioAutenticado.value = usuarioSesion
    miIdJugador.value = usuarioSesion.id_jugador
    
    cargarMisDatosYPartidos()
})

const cerrarSesion = () => {
    localStorage.removeItem('usuario')
    router.push('/login')
}

// Computadas para separar partidos por jugar y ya jugados
const partidosProximos = computed(() => partidos.value.filter(p => p.estado === 'Pendiente'))
const partidosJugados = computed(() => partidos.value.filter(p => p.estado === 'Finalizado'))

// ACCIÓN: Registrar Asistencia
const marcarAsistencia = async (partido, estado) => {
    // Si el jugador está suspendido, no puede marcar asistencia
    if (partido.estoy_suspendido) {
        alert("No puedes confirmar asistencia porque estás suspendido para este encuentro.")
        return
    }

    try {
        const payload = {
            id_partido: partido.id_partido,
            id_jugador: miIdJugador.value,
            estado: estado // 'Asistiré' o 'No asistiré'
        }
        const res = await fetch('http://127.0.0.1:8000/jugador/asistencia', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })

        if (res.ok) {
            // Actualizamos la vista sin recargar la página entera
            partido.mi_asistencia = estado
        }
    } catch (error) {
        alert("Error de conexión al marcar asistencia.")
    }
}

// ACCIÓN: Ver Camerino Virtual
const abrirCamerino = async (partido) => {
    partidoCamerino.value = partido
    camerinoData.value = []
    
    try {
        const res = await fetch(`http://127.0.0.1:8000/partido/${partido.id_partido}/equipo/${miIdEquipo.value}/asistencias`)
        if (res.ok) {
            camerinoData.value = await res.json()
            mostrarCamerino.value = true
        }
    } catch (error) {
        alert("Error al conectar con el camerino.")
    }
}

// ACCIÓN: Calificar Árbitro
const prepararCalificacion = (partido) => {
    if (!partido.id_arbitro) {
        alert("Este partido no tuvo árbitro central asignado.")
        return
    }
    partidoA_Calificar.value = partido
    puntajeAsignado.value = 0
    msjCalificacion.value = ''
    mostrarCalificacion.value = true
}

const asignarEstrella = (estrella) => {
    puntajeAsignado.value = estrella
}

const enviarCalificacion = async () => {
    if (puntajeAsignado.value === 0) {
        msjCalificacion.value = "Selecciona al menos una estrella."
        return
    }
    
    try {
        const payload = {
            id_arbitro: partidoA_Calificar.value.id_arbitro,
            id_jugador: miIdJugador.value,
            id_partido: partidoA_Calificar.value.id_partido,
            puntaje: puntajeAsignado.value
        }
        
        const res = await fetch('http://127.0.0.1:8000/jugador/calificar_arbitro', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        
        const d = await res.json()
        if (res.ok) {
            alert(d.mensaje)
            mostrarCalificacion.value = false
        } else {
            msjCalificacion.value = d.detail // Ej: Ya lo calificaste
        }
    } catch (error) {
        msjCalificacion.value = "Error de red."
    }
}
</script>

<template>
    <div class="bg-gray-100 font-sans min-h-screen pb-20">
        
        <!-- NAVBAR -->
        <nav class="bg-[#001a4d] p-4 shadow-md text-white flex justify-between items-center sticky top-0 z-50">
            <div class="flex items-center space-x-3">
                <span class="text-2xl">🏃‍♂️</span>
                <h1 class="text-xl font-black tracking-wide">Mi Portal</h1>
            </div>
            <button @click="cerrarSesion" class="text-blue-200 hover:text-white font-bold text-sm transition">Cerrar Sesión</button>
        </nav>

        <main class="container mx-auto mt-6 px-4 max-w-4xl">
            
            <!-- BIENVENIDA -->
            <div class="bg-white rounded-3xl shadow-sm border border-gray-200 p-6 mb-8 text-center">
                <h2 class="text-2xl font-black text-[#001a4d]">Bienvenido a la Cancha</h2>
                <p class="text-gray-500 text-sm mt-1">Aquí tienes el control de tus asistencias y resultados.</p>
            </div>

            <div v-if="cargando" class="text-center py-20 text-gray-400 font-bold animate-pulse">
                Cargando tu calendario...
            </div>

            <div v-else class="space-y-12">
                
                <!-- SECCIÓN: PRÓXIMOS PARTIDOS -->
                <section>
                    <h3 class="text-lg font-black text-gray-800 mb-4 flex items-center border-b pb-2">
                        <span class="mr-2">🔥</span> Próximos Encuentros
                    </h3>
                    
                    <div class="space-y-5">
                        <div v-for="partido in partidosProximos" :key="partido.id_partido" 
                             class="bg-white rounded-3xl shadow-lg border-2 overflow-hidden transition-all"
                             :class="partido.estoy_suspendido ? 'border-red-400' : 'border-blue-100'">
                            
                            <!-- Banner Suspensión -->
                            <div v-if="partido.estoy_suspendido" class="bg-red-500 text-white text-center py-1.5 font-black text-xs uppercase tracking-widest">
                                ⚠️ Estás suspendido para este encuentro
                            </div>

                            <div class="p-5">
                                <!-- Fecha y Hora -->
                                <div class="flex justify-between items-center mb-4">
                                    <span class="bg-gray-100 text-gray-600 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">📅 {{ partido.fecha }}</span>
                                    <span class="bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-xs font-black">⏰ {{ partido.hora }}</span>
                                </div>
                                
                                <!-- Equipos -->
                                <div class="flex items-center justify-between mt-2">
                                    <div class="flex flex-col items-center w-[40%] text-center">
                                        <img v-if="partido.logo_local" :src="partido.logo_local" class="h-12 w-12 object-contain mb-2 drop-shadow-sm" />
                                        <div v-else class="h-12 w-12 rounded-full bg-gray-100 flex items-center justify-center text-xl mb-2">🛡️</div>
                                        <span class="font-black text-sm text-[#001a4d] leading-tight">{{ partido.local }}</span>
                                    </div>
                                    <span class="text-xs bg-[#001a4d] text-yellow-400 font-black px-3 py-1 rounded-xl shadow-inner">VS</span>
                                    <div class="flex flex-col items-center w-[40%] text-center">
                                        <img v-if="partido.logo_visitante" :src="partido.logo_visitante" class="h-12 w-12 object-contain mb-2 drop-shadow-sm" />
                                        <div v-else class="h-12 w-12 rounded-full bg-gray-100 flex items-center justify-center text-xl mb-2">🛡️</div>
                                        <span class="font-black text-sm text-[#001a4d] leading-tight">{{ partido.visitante }}</span>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Acciones Jugador -->
                            <div class="bg-gray-50 border-t p-4">
                                <p class="text-center text-xs font-bold text-gray-500 mb-3 uppercase">¿Asistirás a este partido?</p>
                                
                                <div class="flex space-x-3 mb-4">
                                    <!-- Botón SÍ -->
                                    <button @click="marcarAsistencia(partido, 'Asistiré')" :disabled="partido.estoy_suspendido"
                                            :class="partido.mi_asistencia === 'Asistiré' ? 'bg-green-500 text-white shadow-inner scale-95 border-green-600' : 'bg-white text-gray-600 border-gray-300 hover:bg-green-50 hover:border-green-400 hover:text-green-700'"
                                            class="w-1/2 py-3 rounded-xl font-black text-sm border-2 transition-all disabled:opacity-50">
                                        👍 SÍ VOY
                                    </button>
                                    
                                    <!-- Botón NO -->
                                    <button @click="marcarAsistencia(partido, 'No asistiré')" :disabled="partido.estoy_suspendido"
                                            :class="partido.mi_asistencia === 'No asistiré' ? 'bg-red-500 text-white shadow-inner scale-95 border-red-600' : 'bg-white text-gray-600 border-gray-300 hover:bg-red-50 hover:border-red-400 hover:text-red-700'"
                                            class="w-1/2 py-3 rounded-xl font-black text-sm border-2 transition-all disabled:opacity-50">
                                        👎 NO VOY
                                    </button>
                                </div>

                                <button @click="abrirCamerino(partido)" class="w-full bg-[#001a4d] text-yellow-400 font-black py-3 rounded-xl shadow-md transition flex justify-center items-center text-sm">
                                    <span class="mr-2">👥</span> VER CAMERINO (Compañeros)
                                </button>
                            </div>
                        </div>

                        <div v-if="partidosProximos.length === 0" class="text-center py-10 bg-white rounded-2xl border text-gray-400 text-sm font-bold">
                            No tienes partidos programados próximamente.
                        </div>
                    </div>
                </section>

                <!-- SECCIÓN: HISTORIAL Y CALIFICACIONES -->
                <section>
                    <h3 class="text-lg font-black text-gray-800 mb-4 flex items-center border-b pb-2">
                        <span class="mr-2">🏆</span> Historial de Resultados
                    </h3>

                    <div class="space-y-4">
                        <div v-for="partido in partidosJugados" :key="partido.id_partido" 
                             class="bg-white rounded-2xl shadow-sm border p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
                            
                            <!-- Info Básica -->
                            <div class="flex flex-col items-center sm:items-start w-full sm:w-auto">
                                <span class="text-xs font-bold text-gray-400 mb-1">📅 {{ partido.fecha }}</span>
                                <div class="flex items-center space-x-3 bg-gray-50 px-4 py-2 rounded-xl border">
                                    <span class="font-black text-[#001a4d]">{{ partido.local }}</span>
                                    <span class="bg-[#001a4d] text-white px-2 py-0.5 rounded text-sm font-black">{{ partido.goles_local }} - {{ partido.goles_visitante }}</span>
                                    <span class="font-black text-[#001a4d]">{{ partido.visitante }}</span>
                                </div>
                                <span class="text-[10px] text-gray-400 mt-2 font-bold uppercase">Juez: {{ partido.arbitro }}</span>
                            </div>

                            <!-- Botón Calificar Árbitro -->
                            <div class="w-full sm:w-auto">
                                <button @click="prepararCalificacion(partido)" class="w-full sm:w-auto bg-yellow-400 hover:bg-yellow-500 text-[#001a4d] font-black px-5 py-2.5 rounded-xl shadow-sm text-xs transition uppercase flex justify-center items-center">
                                    <span class="mr-1.5 text-base">⭐</span> Calificar Árbitro
                                </button>
                            </div>
                        </div>

                        <div v-if="partidosJugados.length === 0" class="text-center py-10 bg-white rounded-2xl border text-gray-400 text-sm font-bold">
                            Aún no has jugado ningún partido oficial.
                        </div>
                    </div>
                </section>

            </div>
        </main>

        <!-- ========================================== -->
        <!-- MODAL: CAMERINO VIRTUAL (ASISTENCIAS)      -->
        <!-- ========================================== -->
        <div v-if="mostrarCamerino" class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div class="bg-white rounded-3xl shadow-2xl max-w-md w-full overflow-hidden flex flex-col border border-gray-200">
                <div class="bg-[#001a4d] p-5 text-white flex justify-between items-center">
                    <h3 class="font-black uppercase text-base flex items-center"><span class="mr-2">👥</span> Camerino Virtual</h3>
                    <button @click="mostrarCamerino = false" class="text-white hover:text-gray-300 font-bold text-xl">✕</button>
                </div>
                
                <div class="bg-blue-50 px-5 py-3 border-b border-blue-100 flex justify-between items-center text-xs font-black text-[#001a4d]">
                    <span>Lista de Convocados</span>
                    <span>Total: {{ camerinoData.length }}</span>
                </div>

                <div class="overflow-y-auto max-h-[60vh] p-5 space-y-3 bg-gray-50">
                    <div v-for="jugador in camerinoData" :key="jugador.id_jugador" 
                         class="bg-white border rounded-2xl p-3 flex items-center justify-between shadow-sm">
                        
                        <div class="flex items-center space-x-3 w-[70%]">
                            <img v-if="jugador.url_foto" :src="jugador.url_foto" class="h-10 w-10 object-cover rounded-full border border-gray-200" />
                            <div v-else class="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center text-xs">👤</div>
                            
                            <div class="truncate">
                                <p class="font-bold text-gray-800 text-sm truncate" :class="{'line-through text-gray-400': jugador.suspendido}">
                                    {{ jugador.nombre }}
                                </p>
                                <span class="bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded text-[10px] font-black">#{{ jugador.numero_camiseta }}</span>
                            </div>
                        </div>

                        <!-- Badge de Estado -->
                        <div class="text-right">
                            <span v-if="jugador.suspendido" class="bg-red-100 text-red-700 border border-red-200 px-2 py-1 rounded-lg text-[10px] font-black uppercase shadow-sm">
                                ❌ Sancionado
                            </span>
                            <span v-else-if="jugador.estado_asistencia === 'Asistiré'" class="bg-green-100 text-green-700 border border-green-200 px-2 py-1 rounded-lg text-[10px] font-black uppercase shadow-sm">
                                🟢 Sí Va
                            </span>
                            <span v-else-if="jugador.estado_asistencia === 'No asistiré'" class="bg-red-50 text-red-600 border border-red-200 px-2 py-1 rounded-lg text-[10px] font-black uppercase shadow-sm">
                                🔴 No Va
                            </span>
                            <span v-else class="bg-gray-100 text-gray-500 border border-gray-200 px-2 py-1 rounded-lg text-[10px] font-black uppercase shadow-sm">
                                ⚪ Pendiente
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- ========================================== -->
        <!-- MODAL: CALIFICAR ÁRBITRO                   -->
        <!-- ========================================== -->
        <div v-if="mostrarCalificacion" class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div class="bg-white rounded-3xl shadow-2xl max-w-sm w-full overflow-hidden flex flex-col border border-gray-200">
                <div class="bg-[#001a4d] p-5 text-white flex justify-between items-center text-center relative">
                    <h3 class="font-black uppercase text-base w-full">⚖️ Calificar Desempeño</h3>
                    <button @click="mostrarCalificacion = false" class="text-white hover:text-gray-300 font-bold text-xl absolute right-5">✕</button>
                </div>
                
                <div class="p-8 text-center space-y-6">
                    <div>
                        <p class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Árbitro Central</p>
                        <p class="text-xl font-black text-[#001a4d]">{{ partidoA_Calificar.arbitro }}</p>
                    </div>

                    <div v-if="msjCalificacion" class="bg-blue-50 text-blue-800 p-2 rounded-lg text-xs font-bold border border-blue-200">
                        {{ msjCalificacion }}
                    </div>

                    <div>
                        <p class="text-sm font-bold text-gray-700 mb-4">¿Cómo fue su arbitraje en el encuentro?</p>
                        <div class="flex justify-center space-x-2">
                            <!-- Sistema de 5 Estrellas Interactivo -->
                            <button v-for="star in 5" :key="star" @click="asignarEstrella(star)"
                                    class="text-4xl transition-transform hover:scale-125 focus:outline-none"
                                    :class="star <= puntajeAsignado ? 'text-yellow-400 drop-shadow-md' : 'text-gray-200 hover:text-yellow-200'">
                                ★
                            </button>
                        </div>
                        <p class="text-[10px] text-gray-400 mt-3 font-bold uppercase">
                            {{ puntajeAsignado === 0 ? 'Selecciona una puntuación' : puntajeAsignado + ' de 5 Estrellas' }}
                        </p>
                    </div>

                    <button @click="enviarCalificacion" class="w-full bg-green-600 hover:bg-green-700 text-white font-black py-3 rounded-xl shadow-md transition text-sm">
                        ENVIAR REPORTE A LA LIGA
                    </button>
                </div>
            </div>
        </div>

    </div>
</template>