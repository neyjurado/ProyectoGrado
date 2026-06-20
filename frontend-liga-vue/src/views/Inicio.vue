<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// ==========================================
// 1. VARIABLES REACTIVAS REALES
// ==========================================
const equipos = ref([])
const cargando = ref(true)

// Datos que empiezan limpios desde cero
const estadisticasExtra = ref({
    jugadores: 0,    // Sincronizado a 0 por limpieza de BD
    categorias: 2   // Máxima y Primera
})

const categorias = ref([
    { id: 1, nombre: 'Máxima', icono: '🏆' },
    { id: 2, nombre: 'Primera', icono: '⚽' }
])

// Arreglos vacíos reales listos para recibir datos de tu base de datos
const goleadores = ref([])
const partidos = ref([])

// ==========================================
// 2. LÓGICA DE BASE DE DATOS
// ==========================================
const cargarEquipos = async () => {
    try {
        const res = await fetch('http://127.0.0.1:8000/equipos');
        if (!res.ok) throw new Error("Error en la red");
        equipos.value = await res.json();
    } catch (err) {
        console.error("Error cargando equipos", err);
    } finally {
        cargando.value = false;
    }
}

const totalEquipos = computed(() => equipos.value.length)

// ==========================================
// 3. FUNCIONES DE NAVEGACIÓN
// ==========================================
const irARegistro = () => router.push('/registro-jugador')
const irALogin = () => router.push('/login')
const verCategoria = (nombreCategoria) => console.log("Navegando a posiciones de:", nombreCategoria)

const abrirDetallePartido = (idPartido) => {
    console.log("Abriendo detalles del partido para el ID:", idPartido)
}

onMounted(() => {
    cargarEquipos()
})
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
                        <div class="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div v-for="cat in categorias" :key="cat.id" @click="verCategoria(cat.nombre)" class="border border-gray-200 hover:border-[#001a4d] bg-gray-50 rounded-xl p-6 cursor-pointer transition flex items-center group shadow-sm hover:shadow-md">
                                <div class="text-4xl mr-4 group-hover:scale-110 transition">{{ cat.icono }}</div>
                                <div>
                                    <h4 class="text-2xl font-black text-[#001a4d]">{{ cat.nombre }}</h4>
                                    <p class="text-blue-600 font-bold text-sm mt-1 group-hover:underline">Ver clasificación →</p>
                                </div>
                            </div>
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
                                    <tr v-for="(gol, index) in goleadores" :key="gol.id" class="border-b hover:bg-gray-50 transition">
                                        <td class="p-4 flex items-center">
                                            <span class="font-black text-gray-400 w-6">{{ index + 1 }}.</span>
                                            <span class="font-bold text-[#001a4d]">{{ gol.nombre }}</span>
                                        </td>
                                        <td class="p-4 text-sm text-gray-600 font-medium">{{ gol.equipo }}</td>
                                        <td class="p-4">
                                            <span class="bg-blue-50 text-[#001a4d] border border-blue-200 text-[10px] font-bold px-2 py-1 rounded-full uppercase">{{ gol.categoria }}</span>
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
                        <div class="bg-[#001a4d] border-b p-4 flex justify-between items-center text-white">
                            <h3 class="text-lg font-black uppercase flex items-center"><span class="mr-2 text-yellow-400">🏟️</span> Próxima Fecha</h3>
                            <span class="bg-white text-[#001a4d] text-[10px] font-black px-2 py-1 rounded uppercase tracking-wider shadow-sm">Jornada Activa</span>
                        </div>
                        
                        <div class="p-4 grid grid-cols-1 md:grid-cols-2 gap-4 max-h-[400px] overflow-y-auto">
                            <div v-for="partido in partidos" :key="partido.id" @click="abrirDetallePartido(partido.id)" class="bg-gray-50 border border-gray-200 rounded-lg p-4 cursor-pointer hover:shadow-md hover:border-[#001a4d] hover:bg-white transition flex flex-col justify-between">
                                <div class="text-center mb-3 border-b border-gray-200 pb-2">
                                    <p class="text-xs text-gray-500 font-bold uppercase tracking-wider">{{ partido.fecha }} • {{ partido.hora }}</p>
                                </div>
                                <div class="flex justify-between items-center">
                                    <div class="text-center w-[40%]">
                                        <p class="text-sm font-bold text-[#001a4d] leading-tight">{{ partido.local }}</p>
                                    </div>
                                    <div class="w-[20%] text-center">
                                        <span class="text-[10px] font-black bg-gray-200 text-gray-500 px-2 py-1 rounded">VS</span>
                                    </div>
                                    <div class="text-center w-[40%]">
                                        <p class="text-sm font-bold text-[#001a4d] leading-tight">{{ partido.visitante }}</p>
                                    </div>
                                </div>
                                <p class="text-[10px] text-center text-blue-500 font-semibold mt-3">Ver detalles del partido →</p>
                            </div>
                            <div v-if="partidos.length === 0" class="col-span-full py-8 text-center text-gray-400 italic font-medium">No hay partidos programados para este fin de semana.</div>
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
                                <span class="text-2xl font-black text-[#001a4d]">{{ estadisticasExtra.categorias }}</span>
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
                                <span class="text-2xl font-black text-[#001a4d]">{{ estadisticasExtra.jugadores }}</span>
                            </div>
                        </div>
                    </div>

                    <div class="bg-white rounded-2xl shadow-md border border-gray-100 overflow-hidden">
                        <div class="bg-gray-100 text-[#001a4d] p-4 border-b">
                            <h3 class="text-sm font-black uppercase flex items-center"><span class="mr-2">📄</span> Documentos</h3>
                        </div>
                        <div class="p-4 space-y-3">
                            <a href="#" class="flex items-center p-3 rounded-lg border border-gray-200 hover:border-[#001a4d] hover:bg-blue-50 transition group">
                                <span class="text-xl mr-3 grayscale group-hover:grayscale-0 transition">📑</span>
                                <span class="font-bold text-xs text-gray-600 group-hover:text-[#001a4d]">Reglamento General 2026</span>
                            </a>
                            <a href="#" class="flex items-center p-3 rounded-lg border border-gray-200 hover:border-[#001a4d] hover:bg-blue-50 transition group">
                                <span class="text-xl mr-3 grayscale group-hover:grayscale-0 transition">📑</span>
                                <span class="font-bold text-xs text-gray-600 group-hover:text-[#001a4d]">Cronograma de Vocalías</span>
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

<style scoped>
::-webkit-scrollbar {
    width: 6px;
}
::-webkit-scrollbar-track {
    background: transparent; 
}
::-webkit-scrollbar-thumb {
    background: #cbd5e1; 
    border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
    background: #001a4d; 
}
</style>