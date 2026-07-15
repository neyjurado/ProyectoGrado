<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const correo = ref('')
const password = ref('')
const cargando = ref(false)
const mensajeError = ref('')
const mostrarPassword = ref(false)

const procesarLogin = async () => {
    if (!correo.value || !password.value) return;

    cargando.value = true;
    mensajeError.value = '';

    try {
        const respuesta = await fetch('http://127.0.0.1:8000/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ correo: correo.value, password: password.value })
        });

        const datos = await respuesta.json();

        if (respuesta.ok) {
            localStorage.setItem('usuario', JSON.stringify(datos.usuario));
            
            // Redirección silenciosa y directa
            if (datos.usuario.rol === 'Administrador') {
                router.push('/admin'); 
            } else if (datos.usuario.rol === 'Jugador') {
                router.push('/jugador');
            } else {
                router.push('/'); 
            }
        } else {
            mensajeError.value = datos.detail || "Error al iniciar sesión.";
        }
    } catch (error) {
        mensajeError.value = "Error de conexión con el servidor.";
    } finally {
        cargando.value = false;
    }
}
</script>

<template>
    <div class="bg-gray-100 font-sans min-h-screen flex flex-col">
        
        <nav class="bg-[#001a4d] p-4 shadow-md">
            <div class="container mx-auto flex justify-between items-center">
                <div class="flex items-center space-x-3">
                    <span class="text-2xl bg-white p-1 rounded-full">⚽</span>
                    <h1 class="text-xl font-black text-white tracking-tighter">
                        L.D.P. <span class="text-[#FFD700]">CONOCOTO</span>
                    </h1>
                </div>
                <router-link to="/" class="text-white hover:text-yellow-400 font-semibold text-sm transition flex items-center">
                    <span class="mr-1">←</span> Volver al Inicio
                </router-link>
            </div>
        </nav>

        <main class="flex-grow flex items-center justify-center p-4">
            <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden border-t-8 border-[#001a4d]">
                
                <div class="p-8">
                    <div class="text-center mb-8">
                        <h2 class="text-3xl font-extrabold text-gray-900">Bienvenido</h2>
                        <p class="text-gray-500 mt-2 text-sm">Ingresa tus credenciales para acceder al sistema</p>
                    </div>

                    <div v-if="mensajeError" class="bg-red-50 text-red-600 p-3 rounded-lg text-sm mb-4 border border-red-200 text-center font-medium">
                        {{ mensajeError }}
                    </div>

                    <form @submit.prevent="procesarLogin" class="space-y-6">
                        <div>
                            <label for="correo" class="block text-sm font-semibold text-gray-700 mb-1">Correo Electrónico</label>
                            <input 
                                v-model="correo"
                                type="email" 
                                id="correo" 
                                autocomplete="nope"
                                class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-[#001a4d] focus:border-transparent outline-none transition"
                                placeholder="ejemplo@correo.com"
                                required
                            >
                        </div>

                        <div>
                            <label for="password" class="block text-sm font-semibold text-gray-700 mb-1">Contraseña</label>
                            <div class="relative">
                                <input 
                                    v-model="password"
                                    :type="mostrarPassword ? 'text' : 'password'" 
                                    id="password" 
                                    autocomplete="new-password"
                                    class="w-full px-4 py-3 pr-12 rounded-lg border border-gray-300 focus:ring-2 focus:ring-[#001a4d] focus:border-transparent outline-none transition"
                                    placeholder="••••••••"
                                    required
                                >
                                <button type="button" @click="mostrarPassword = !mostrarPassword" class="absolute inset-y-0 right-0 px-4 text-gray-500 hover:text-[#001a4d]" :aria-label="mostrarPassword ? 'Ocultar contraseña' : 'Ver contraseña'">
                                    {{ mostrarPassword ? '🙈' : '👁️' }}
                                </button>
                            </div>
                        </div>

                        <button 
                            type="submit" 
                            :disabled="cargando"
                            class="w-full bg-[#001a4d] hover:bg-blue-900 text-white font-bold py-3 px-4 rounded-lg shadow-lg hover:shadow-xl transition duration-200 disabled:opacity-70 flex justify-center items-center"
                        >
                            <span v-if="cargando" class="inline-block animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent mr-2"></span>
                            {{ cargando ? 'Verificando...' : 'Ingresar al Sistema' }}
                        </button>
                    </form>

                    <div class="mt-6 text-center">
                        <p class="text-sm text-gray-600">
                            ¿Problemas para ingresar? <a href="#" class="text-blue-700 hover:underline font-semibold">Contacta al administrador</a>
                        </p>
                    </div>
                </div>
            </div>
        </main>
    </div>
</template>