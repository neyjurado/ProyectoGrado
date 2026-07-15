<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Variables globales
const equipos = ref([])
const partidos = ref([])
const totalJugadores = ref(0)
const cargando = ref(true)

// Variables de estadísticas y categorías
const categorias = [
    { id: 1, nombre: 'Máxima', icono: '🏆' },
    { id: 2, nombre: 'Primera', icono: '⚽' }
]
const categoriaSeleccionada = ref('Máxima')
const filtroCalendario = ref('Todas')
const tablaPosiciones = ref([])
const goleadores = ref([])

// Funciones de carga
const cargarDatosGenerales = async () => {
    try {
        const [resEq, resPart, resJug] = await Promise.all([
            fetch('http://127.0.0.1:8000/equipos'),
            fetch('http://127.0.0.1:8000/partidos'),
            fetch('http://127.0.0.1:8000/jugadores')
        ])
        
        if (resEq.ok) equipos.value = await resEq.json()
        if (resPart.ok) partidos.value = await resPart.json()
        if (resJug.ok) {
            const j = await resJug.json()
            totalJugadores.value = j.length
        }
    } catch (error) {
        console.error("Error cargando los datos:", error)
    } finally {
        cargando.value = false
    }
}

const verCategoria = async (categoria) => {
    categoriaSeleccionada.value = categoria
    try {
        const [resPos, resGol] = await Promise.all([
            fetch(`http://127.0.0.1:8000/estadisticas/posiciones/${categoria}`),
            fetch(`http://127.0.0.1:8000/goleadores/${categoria}`)
        ])
        
        if (resPos.ok) tablaPosiciones.value = await resPos.json()
        if (resGol.ok) goleadores.value = await resGol.json()
    } catch (error) {
        console.error("Error cargando estadísticas:", error)
    }
}

onMounted(async () => {
    await cargarDatosGenerales()
    await verCategoria('Máxima') // Carga por defecto la serie Máxima
})

// Computadas
const partidosCalendario = computed(() => {
    if (filtroCalendario.value === 'Todas') return partidos.value
    return partidos.value.filter(p => p.categoria_local === filtroCalendario.value || p.categoria_visitante === filtroCalendario.value)
})

const partidosCalendarioPendientes = computed(() => partidosCalendario.value.filter(p => p.estado === 'Pendiente'))
const partidosCalendarioFinalizados = computed(() => partidosCalendario.value.filter(p => p.estado === 'Finalizado'))

const filtrosCalendario = computed(() => [
    { nombre: 'Todas', icono: '📅' },
    ...categorias
])

const totalEquipos = computed(() => equipos.value.length)

// Helpers
const obtenerLogo = (nombreEquipo) => {
    const eq = equipos.value.find(e => e.nombre === nombreEquipo)
    return eq ? eq.url_logo : null
}

const irARegistro = () => router.push('/registro-jugador')
const irALogin = () => router.push('/login')
</script>

<template>
    <div class="bg-gray-100 font-sans min-h-screen pb-12">
        
        <nav class="bg-[#001a4d] px-6 py-4 shadow-lg flex justify-between items-center sticky top-0 z-50">
            <div class="flex items-center space-x-4 cursor-pointer">
                <div class="bg-white p-1 rounded-full w-14 h-14 flex items-center justify-center shadow-md">
                    <img src="/imagenes/logo.png" alt="Logo LDP Conocoto" class="h-12 w-12 object-cover rounded-full" />
                </div>
                <h1 class="text-2xl md:text-3xl font-black tracking-wider text-white m-0 leading-tight">L.D.P. CONOCOTO</h1>
            </div>
            
            <div class="flex space-x-4">
                <button @click="irARegistro" class="bg-transparent border border-gray-300 text-gray-200 hover:border-white hover:text-white transition px-4 py-2 rounded-lg font-semibold text-sm md:text-base">
                    Registro Jugadores
                </button>
                <button @click="irALogin" class="bg-yellow-400 hover:bg-yellow-500 text-[#001a4d] transition px-6 py-2 rounded-lg font-black shadow-md text-sm md:text-base">
                    Iniciar Sesión
                </button>
            </div>
        </nav>

        <div class="relative w-full h-[400px] bg-cover bg-center shadow-md" style="background-image: url('/imagenes/fondo.png');">
        </div>

        <main class="container mx-auto px-4 mt-8 relative z-20">
            
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-10">
                
                <div class="lg:col-span-2 space-y-10">
                    
                    <div class="bg-white rounded-2xl shadow-md border border-gray-100 overflow-hidden">
                        <div class="bg-[#001a4d] text-white p-4">
                            <h3 class="text-lg font-black uppercase flex items-center"><span class="mr-2 text-yellow-400">📊</span> Tablas de Posiciones</h3>
                        </div>
                        
                        <!-- Selectores de Categoría de tu diseño -->
                        <div class="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div v-for="cat in categorias" :key="cat.id" @click="verCategoria(cat.nombre)" 
                                 :class="categoriaSeleccionada === cat.nombre ? 'border-[#001a4d] bg-blue-50 shadow-md ring-2 ring-[#001a4d] ring-opacity-20' : 'border-gray-200 bg-gray-50 hover:shadow-md'"
                                 class="border rounded-xl p-6 cursor-pointer transition flex items-center group">
                                <div class="text-4xl mr-4 group-hover:scale-110 transition">{{ cat.icono }}</div>
                                <div>
                                    <h4 class="text-2xl font-black text-[#001a4d]">{{ cat.nombre }}</h4>
                                    <p class="text-blue-600 font-bold text-sm mt-1 group-hover:underline">Ver clasificación →</p>
                                </div>
                            </div>
                        </div>

                        <!-- TABLA DE POSICIONES MOSTRADA DEBAJO -->
                        <div class="px-6 pb-6 overflow-x-auto">
                            <h4 class="font-bold text-[#001a4d] mb-3 text-lg border-b pb-2">Clasificación Serie {{ categoriaSeleccionada }}</h4>
                            <table class="w-full text-left text-sm border-collapse">
                                <thead>
                                    <tr class="bg-gray-100 text-gray-700 font-black">
                                        <th class="p-2 text-center border-b">Pos</th>
                                        <th class="p-2 border-b">Club</th>
                                        <th class="p-2 text-center border-b">PJ</th>
                                        <th class="p-2 text-center border-b text-green-600">PG</th>
                                        <th class="p-2 text-center border-b text-gray-500">PE</th>
                                        <th class="p-2 text-center border-b text-red-500">PP</th>
                                        <th class="p-2 text-center border-b">GD</th>
                                        <th class="p-2 text-center border-b bg-blue-50 text-blue-900">PTS</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr v-for="(pos, idx) in tablaPosiciones" :key="pos.id_equipo" class="border-b hover:bg-gray-50">
                                        <td class="p-2 text-center font-bold text-gray-500">{{ idx + 1 }}</td>
                                        <td class="p-2 font-black text-[#001a4d] flex items-center space-x-2">
                                            <img v-if="pos.url_logo" :src="pos.url_logo" class="h-5 w-5 object-contain rounded-full" />
                                            <div v-else class="h-5 w-5 bg-gray-200 rounded-full flex items-center justify-center text-[8px]">🛡️</div>
                                            <span class="truncate">{{ pos.nombre }}</span>
                                        </td>
                                        <td class="p-2 text-center font-mono">{{ pos.pj }}</td>
                                        <td class="p-2 text-center font-mono text-green-600 font-bold">{{ pos.pg }}</td>
                                        <td class="p-2 text-center font-mono text-gray-500">{{ pos.pe }}</td>
                                        <td class="p-2 text-center font-mono text-red-500">{{ pos.pp }}</td>
                                        <td class="p-2 text-center font-mono font-bold" :class="pos.gd >= 0 ? 'text-blue-600' : 'text-red-500'">{{ pos.gd }}</td>
                                        <td class="p-2 text-center font-mono font-black bg-blue-50 text-blue-900">{{ pos.pts }}</td>
                                    </tr>
                                    <tr v-if="tablaPosiciones.length === 0">
                                        <td colspan="8" class="p-6 text-center text-gray-400 italic">No hay datos registrados aún.</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div class="bg-white rounded-2xl shadow-md border border-gray-100 overflow-hidden">
                        <div class="bg-[#001a4d] text-white p-4">
                            <h3 class="text-lg font-black uppercase flex items-center"><span class="mr-2 text-yellow-400">🔥</span> Máximos Goleadores</h3>
                        </div>
                        <div class="p-0 overflow-x-auto">
                            <table class="w-full text-left">
                                <thead>
                                    <tr class="bg-gray-100 text-gray-600 text-xs uppercase border-b border-gray-200">
                                        <th class="p-4 font-bold">Jugador</th>
                                        <th class="p-4 font-bold">Equipo</th>
                                        <th class="p-4 font-bold">Categoría</th>
                                        <th class="p-4 font-bold text-center">Goles</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr v-for="(gol, index) in goleadores" :key="index" class="border-b hover:bg-gray-50 transition">
                                        <td class="p-4 flex items-center">
                                            <span class="font-black text-gray-400 w-6">{{ index + 1 }}.</span>
                                            <span class="font-bold text-[#001a4d]">{{ gol.jugador }}</span>
                                        </td>
                                        <td class="p-4 text-sm text-gray-600 font-medium">{{ gol.equipo }}</td>
                                        <td class="p-4">
                                            <span class="bg-blue-50 text-[#001a4d] border border-blue-200 text-[10px] font-bold px-2 py-1 rounded-full uppercase">{{ categoriaSeleccionada }}</span>
                                        </td>
                                        <td class="p-4 text-center font-black text-xl text-yellow-500">{{ gol.goles }}</td>
                                    </tr>
                                    <tr v-if="goleadores.length === 0">
                                        <td colspan="4" class="p-8 text-center text-gray-400 italic font-medium">No hay goles registrados en el torneo actual.</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div class="bg-white rounded-2xl shadow-md border border-gray-100 overflow-hidden">
                        <div class="bg-[#001a4d] border-b p-4 flex flex-col md:flex-row md:items-center justify-between gap-3 text-white">
                            <div>
                                <h3 class="text-lg font-black uppercase flex items-center"><span class="mr-2 text-yellow-400">🏟️</span> Calendario Oficial</h3>
                                <p class="text-[11px] text-blue-100 mt-1">Filtra por categoría y revisa resultados de partidos ya disputados.</p>
                            </div>
                            <span class="bg-white text-[#001a4d] text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-wider shadow-sm">Total: {{ partidosCalendario.length }}</span>
                        </div>

                        <div class="p-4 border-b bg-gray-50 flex flex-wrap gap-2">
                            <button v-for="filtro in filtrosCalendario" :key="filtro.nombre" @click="filtroCalendario = filtro.nombre"
                                    :class="filtroCalendario === filtro.nombre ? 'bg-[#001a4d] text-white shadow-md' : 'bg-white text-gray-600 border border-gray-200 hover:border-[#001a4d] hover:text-[#001a4d]'"
                                    class="px-4 py-2 rounded-full text-xs font-black transition flex items-center gap-2">
                                <span>{{ filtro.icono }}</span>
                                <span>{{ filtro.nombre }}</span>
                            </button>
                        </div>
                        
                        <div class="p-4 grid grid-cols-1 md:grid-cols-2 gap-4 max-h-[440px] overflow-y-auto">
                            <article v-for="partido in partidosCalendario" :key="partido.id_partido" class="bg-gray-50 border border-gray-200 rounded-2xl p-4 hover:shadow-md hover:border-[#001a4d] hover:bg-white transition flex flex-col justify-between">
                                <div class="text-center mb-3 border-b border-gray-200 pb-2 flex items-center justify-between gap-2">
                                    <p class="text-xs text-gray-500 font-black uppercase tracking-wider">📅 {{ partido.fecha }} • ⏰ {{ partido.hora }}</p>
                                    <span :class="partido.estado === 'Finalizado' ? 'bg-green-100 text-green-700 border-green-200' : 'bg-yellow-100 text-yellow-800 border-yellow-200'" class="px-2 py-1 rounded-full border text-[10px] font-black uppercase tracking-widest">{{ partido.estado }}</span>
                                </div>
                                <div class="flex justify-between items-center">
                                    <div class="flex flex-col items-center justify-center w-[40%] text-center">
                                        <img v-if="obtenerLogo(partido.local)" :src="obtenerLogo(partido.local)" class="h-10 w-10 object-contain mb-1 drop-shadow-sm rounded-full bg-white border border-gray-100" />
                                        <div v-else class="h-10 w-10 bg-gray-200 rounded-full flex items-center justify-center text-[10px] mb-1">🛡️</div>
                                        <p class="text-sm font-bold text-[#001a4d] leading-tight">{{ partido.local }}</p>
                                    </div>
                                    <div class="w-[20%] text-center">
                                        <span class="text-[10px] font-black bg-[#001a4d] text-yellow-400 px-2 py-1 rounded shadow-inner">VS</span>
                                    </div>
                                    <div class="flex flex-col items-center justify-center w-[40%] text-center">
                                        <img v-if="obtenerLogo(partido.visitante)" :src="obtenerLogo(partido.visitante)" class="h-10 w-10 object-contain mb-1 drop-shadow-sm rounded-full bg-white border border-gray-100" />
                                        <div v-else class="h-10 w-10 bg-gray-200 rounded-full flex items-center justify-center text-[10px] mb-1">🛡️</div>
                                        <p class="text-sm font-bold text-[#001a4d] leading-tight">{{ partido.visitante }}</p>
                                    </div>
                                </div>
                                <div class="mt-4 flex items-center justify-between gap-3">
                                    <span class="text-[10px] font-black uppercase tracking-wider text-gray-500">{{ partido.categoria_local || partido.categoria_visitante || 'Sin categoría' }}</span>
                                    <span v-if="partido.estado === 'Finalizado'" class="bg-green-600 text-white font-black px-3 py-1 rounded-xl text-xs shadow-sm">{{ partido.goles_local }} - {{ partido.goles_visitante }}</span>
                                    <span v-else class="bg-[#001a4d] text-yellow-400 font-black px-3 py-1 rounded-xl text-xs shadow-sm">Pendiente</span>
                                </div>
                            </article>
                            <div v-if="partidosCalendario.length === 0" class="col-span-full py-8 text-center text-gray-400 italic font-medium">No hay partidos para mostrar con este filtro.</div>
                        </div>

                        <div class="px-4 pb-4 grid grid-cols-1 md:grid-cols-2 gap-3">
                            <div class="rounded-2xl bg-blue-50 border border-blue-100 p-4 flex items-center justify-between">
                                <span class="text-xs font-black uppercase tracking-wider text-blue-700">Pendientes</span>
                                <span class="text-xl font-black text-[#001a4d]">{{ partidosCalendarioPendientes.length }}</span>
                            </div>
                            <div class="rounded-2xl bg-green-50 border border-green-100 p-4 flex items-center justify-between">
                                <span class="text-xs font-black uppercase tracking-wider text-green-700">Finalizados</span>
                                <span class="text-xl font-black text-[#001a4d]">{{ partidosCalendarioFinalizados.length }}</span>
                            </div>
                        </div>
                    </div>

                </div>

                <div class="space-y-10">
                    
                    <div class="bg-white rounded-2xl shadow-md border border-gray-100 overflow-hidden flex flex-col">
                        <div class="bg-[#001a4d] text-white p-3 text-center">
                            <h3 class="text-sm font-black uppercase tracking-widest flex justify-center items-center">
                                <span class="mr-2 text-yellow-400">📈</span> Estadísticas
                            </h3>
                        </div>
                        <div class="p-6 flex flex-col space-y-4">
                            <div class="flex justify-between items-center border-b border-gray-100 pb-2">
                                <span class="text-gray-500 font-bold text-xs uppercase">Categorías</span>
                                <span class="text-2xl font-black text-[#001a4d]">2</span>
                            </div>
                            <div class="flex justify-between items-center border-b border-gray-100 pb-2">
                                <span class="text-gray-500 font-bold text-xs uppercase">Equipos</span>
                                <span class="text-2xl font-black text-[#001a4d]">
                                    <span v-if="cargando" class="animate-pulse text-gray-300">...</span>
                                    <span v-else>{{ totalEquipos }}</span>
                                </span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-gray-500 font-bold text-xs uppercase">Jugadores</span>
                                <span class="text-2xl font-black text-[#001a4d]">
                                    <span v-if="cargando" class="animate-pulse text-gray-300">...</span>
                                    <span v-else>{{ totalJugadores }}</span>
                                </span>
                            </div>
                        </div>
                    </div>

                    <div class="bg-white rounded-2xl shadow-md border border-gray-100 overflow-hidden">
                        <div class="bg-gray-100 text-[#001a4d] p-4 border-b">
                            <h3 class="text-sm font-black uppercase flex items-center"><span class="mr-2">📄</span> Documentos</h3>
                        </div>
                        <div class="p-4 space-y-3">
                            <a href="/reglamento.pdf" target="_blank" class="flex items-center p-3 rounded-lg border border-gray-200 hover:border-[#001a4d] hover:bg-blue-50 transition group">
                                <span class="text-xl mr-3 grayscale group-hover:grayscale-0 transition">📑</span>
                                <span class="font-bold text-xs text-gray-600 group-hover:text-[#001a4d]">Reglamento General 2026</span>
                            </a>
                        </div>
                    </div>

                </div>
            </div>
        </main>

        <footer class="bg-[#001a4d] text-white mt-16 pt-12 pb-6 border-t-4 border-yellow-400">
            <div class="container mx-auto px-4">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-12 mb-8">
                    <div>
                        <h3 class="text-2xl font-black mb-6 text-yellow-400 uppercase tracking-widest">L.D.P. Conocoto</h3>
                        <div class="space-y-4 text-gray-300 font-medium text-sm">
                            <p class="flex items-start">
                                <span class="mr-3 text-xl text-yellow-400">📍</span> 
                                <span>Estadio Parroquial "La Moya"<br>Calle Julio Moreno, Conocoto.</span>
                            </p>
                            <p class="flex items-center">
                                <span class="mr-3 text-xl text-yellow-400">📧</span> info@ligaconocoto.com
                            </p>
                            <p class="flex items-center">
                                <span class="mr-3 text-xl text-yellow-400">📱</span> +593 99 999 9999
                            </p>
                        </div>
                    </div>

                    <div class="rounded-xl overflow-hidden shadow-2xl border-2 border-blue-800 h-64 relative">
                        <iframe 
                            src="https://www.google.com/maps/embed?pb=!1m14!1m8!1m3!1d8582.148055188447!2d-78.472603!3d-0.299682!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x91d5bd1babd9739b%3A0xd2388fc698e5aec9!2sEstadio%20Parroquial%20%22La%20Moya%22!5e1!3m2!1ses-419!2sus!4v1778878562895!5m2!1ses-419!2sus" 
                            width="100%" 
                            height="100%" 
                            style="border:0; position: absolute; top: 0; left: 0;" 
                            allowfullscreen="" 
                            loading="lazy" 
                            referrerpolicy="no-referrer-when-downgrade">
                        </iframe>
                    </div>
                </div>
                <div class="border-t border-blue-900 pt-6 text-center text-xs text-gray-400 font-medium uppercase tracking-wider">
                    © 2026 Liga Deportiva Parroquial Conocoto. Desarrollado para el proyecto de grado.
                </div>
            </div>
        </footer>

    </div>
</template>