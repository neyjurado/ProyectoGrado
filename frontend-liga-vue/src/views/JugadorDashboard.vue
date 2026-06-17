<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Variables de Estado
const nombreJugador = ref('Jugador')
const cargando = ref(false)
const mensajeExito = ref('')
const mensajeError = ref('')

// Variables del Formulario
const id_arbitro = ref('')
const id_partido = ref('')
const id_jugador = ref('')
const puntaje = ref('')

// Verificación de Seguridad y Saludo Dinámico
onMounted(() => {
    const usuarioSesion = JSON.parse(localStorage.getItem('usuario'))
    
    // Si no está logueado o no es Jugador, lo pateamos al login
    if (!usuarioSesion || usuarioSesion.rol !== 'Jugador') {
        router.push('/login')
        return
    }
    
    // Extraemos el nombre antes del '@' del correo para saludarlo
    nombreJugador.value = usuarioSesion.correo.split('@')[0]
})

const cerrarSesion = () => {
    localStorage.removeItem('usuario')
    router.push('/login')
}

const enviarCalificacion = async () => {
    // Validar que haya seleccionado una estrella
    if (!puntaje.value) {
        mensajeError.value = "Por favor, selecciona una calificación de estrellas."
        return
    }

    cargando.value = true
    mensajeError.value = ''
    mensajeExito.value = ''

    const payload = {
        id_arbitro: parseInt(id_arbitro.value),
        id_jugador: parseInt(id_jugador.value),
        id_partido: parseInt(id_partido.value),
        puntaje: parseInt(puntaje.value)
    }

    try {
        const res = await fetch('http://127.0.0.1:8000/calificar-arbitro', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        })

        const datos = await res.json()

        if (res.ok) {
            mensajeExito.value = datos.mensaje
            
            // Limpiar el formulario tras el éxito
            id_arbitro.value = ''
            id_partido.value = ''
            id_jugador.value = ''
            puntaje.value = ''
        } else {
            mensajeError.value = datos.detail || "Error al enviar la calificación."
        }
    } catch (err) {
        mensajeError.value = "Error de conexión con el servidor."
    } finally {
        cargando.value = false
    }
}
</script>

<template>
    <div class="bg-gray-50 font-sans min-h-screen">
        
        <nav class="bg-[#001a4d] p-4 shadow-md text-white flex justify-between items-center sticky top-0 z-50">
            <div class="flex items-center space-x-2">
                <span class="text-xl">🏃‍♂️</span>
                <h1 class="text-lg font-bold">Mi Portal</h1>
            </div>
            <button @click="cerrarSesion" class="text-sm font-semibold text-red-300 hover:text-red-100 transition">
                Cerrar Sesión
            </button>
        </nav>

        <main class="container mx-auto mt-6 px-4 max-w-md">
            
            <div class="bg-white p-5 rounded-xl shadow-sm border border-gray-100 mb-6 text-center">
                <h2 class="text-xl font-extrabold text-gray-800 capitalize">Hola, {{ nombreJugador }}</h2>
                <p class="text-sm text-gray-500 mt-1">Tu opinión ayuda a mejorar la liga.</p>
            </div>

            <div class="bg-white p-6 rounded-xl shadow-md border-t-4 border-[#001a4d]">
                <h3 class="text-lg font-bold text-gray-900 mb-4 flex items-center justify-center">
                    <span>⚖️ Calificar Árbitro</span>
                </h3>

                <div v-if="mensajeError" class="bg-red-50 text-red-600 p-3 rounded-lg text-sm mb-4 border border-red-200 text-center font-medium">
                    ❌ {{ mensajeError }}
                </div>
                <div v-if="mensajeExito" class="bg-green-50 text-green-700 p-3 rounded-lg text-sm mb-4 border border-green-200 text-center font-medium">
                    ✅ {{ mensajeExito }}
                </div>
                
                <form @submit.prevent="enviarCalificacion" class="space-y-5">
                    
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-xs font-bold text-gray-700 mb-1">ID Árbitro</label>
                            <input v-model="id_arbitro" type="number" required class="w-full p-2 border border-gray-300 rounded-lg bg-gray-50 text-center focus:ring-2 focus:ring-[#001a4d] outline-none" placeholder="Ej. 1" />
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-gray-700 mb-1">ID Partido</label>
                            <input v-model="id_partido" type="number" required class="w-full p-2 border border-gray-300 rounded-lg bg-gray-50 text-center focus:ring-2 focus:ring-[#001a4d] outline-none" placeholder="Ej. 10" />
                        </div>
                    </div>

                    <div>
                        <label class="block text-xs font-bold text-gray-700 mb-1">Mi ID de Jugador</label>
                        <input v-model="id_jugador" type="number" required class="w-full p-2 border border-gray-300 rounded-lg bg-gray-50 text-center focus:ring-2 focus:ring-[#001a4d] outline-none" placeholder="Tu ID en la tabla" />
                    </div>

                    <div class="pt-4 border-t border-gray-100">
                        <label class="block text-sm font-bold text-center text-gray-700 mb-2">Puntaje del Desempeño</label>
                        <div class="rating-container">
                            <input v-model="puntaje" type="radio" id="star5" value="5" class="star-radio" />
                            <label for="star5" class="star-label">★</label>
                            
                            <input v-model="puntaje" type="radio" id="star4" value="4" class="star-radio" />
                            <label for="star4" class="star-label">★</label>
                            
                            <input v-model="puntaje" type="radio" id="star3" value="3" class="star-radio" />
                            <label for="star3" class="star-label">★</label>
                            
                            <input v-model="puntaje" type="radio" id="star2" value="2" class="star-radio" />
                            <label for="star2" class="star-label">★</label>
                            
                            <input v-model="puntaje" type="radio" id="star1" value="1" class="star-radio" />
                            <label for="star1" class="star-label">★</label>
                        </div>
                    </div>

                    <button type="submit" :disabled="cargando" class="w-full bg-yellow-400 hover:bg-yellow-500 text-blue-900 font-bold py-3 rounded-lg shadow transition mt-4 disabled:opacity-70 flex justify-center items-center">
                        <span v-if="cargando" class="inline-block animate-spin rounded-full h-5 w-5 border-2 border-blue-900 border-t-transparent mr-2"></span>
                        {{ cargando ? 'Enviando...' : 'Enviar Calificación' }}
                    </button>
                </form>
            </div>
        </main>
    </div>
</template>

<style scoped>
/* Estilos para las estrellas de calificación */
.star-radio { display: none; }
.star-label { font-size: 2.5rem; color: #d1d5db; cursor: pointer; transition: color 0.2s; }
.star-radio:checked ~ .star-label { color: #d1d5db; }
.star-label:hover, 
.star-label:hover ~ .star-label, 
.star-radio:checked + .star-label, 
.star-radio:checked + .star-label ~ .star-label { 
    color: #FFD700; 
}
.rating-container { 
    display: flex; 
    flex-direction: row-reverse; 
    justify-content: center; 
}
</style>