<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const cedula = ref('')
const correo = ref('')
const password = ref('')
const confirmarPassword = ref('')

const cargando = ref(false)
const mensajeError = ref('')
const mensajeExito = ref('')

const validarPasswordSegura = (valor) => {
    const texto = (valor || '').trim()
    if (texto.length < 8) return 'La contraseña debe tener al menos 8 caracteres.'
    if (!/[A-Z]/.test(texto)) return 'La contraseña debe incluir al menos una mayúscula.'
    if (!/[a-z]/.test(texto)) return 'La contraseña debe incluir al menos una minúscula.'
    if (!/\d/.test(texto)) return 'La contraseña debe incluir al menos un número.'
    if (!/[^A-Za-z0-9]/.test(texto)) return 'La contraseña debe incluir al menos un carácter especial.'
    return ''
}

const registrarse = async () => {
    mensajeError.value = ''
    mensajeExito.value = ''

    const validacionPassword = validarPasswordSegura(password.value)
    if (validacionPassword) {
        mensajeError.value = validacionPassword
        return
    }

    if (password.value !== confirmarPassword.value) {
        mensajeError.value = "Las contraseñas no coinciden. Intenta de nuevo."
        return
    }

    cargando.value = true

    try {
        const payload = {
            cedula: cedula.value.trim(),
            correo: correo.value.trim().toLowerCase(),
            password: password.value
        }

        const res = await fetch('http://127.0.0.1:8000/registro', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })

        const data = await res.json()

        if (res.ok) {
            mensajeExito.value = data.mensaje
            cedula.value = ''
            correo.value = ''
            password.value = ''
            confirmarPassword.value = ''
            
            setTimeout(() => {
                router.push('/login')
            }, 3000)
        } else {
            mensajeError.value = data.detail || 'No se pudo completar el registro.'
        }
    } catch (error) {
        mensajeError.value = "Error de red. No se pudo contactar con el servidor."
    } finally {
        cargando.value = false
    }
}
</script>

<template>
    <div class="min-h-screen bg-gray-100 flex flex-col justify-center items-center p-4 font-sans">
        
        <div class="max-w-md w-full bg-white rounded-3xl shadow-xl overflow-hidden border border-gray-200">
            <div class="bg-[#001a4d] p-6 text-center">
                <div class="bg-white inline-flex p-3 rounded-full shadow-lg mb-3">
                    <span class="text-3xl">⚽</span>
                </div>
                <h1 class="text-2xl font-black text-white tracking-wide">Crea tu Cuenta</h1>
                <p class="text-blue-200 text-sm mt-1">Liga Deportiva Parroquial de Conocoto</p>
            </div>

            <div class="p-8">
                <div v-if="mensajeError" class="bg-red-50 border border-red-200 text-red-600 p-3 rounded-xl text-sm font-bold mb-4 flex items-center">
                    ⚠️ {{ mensajeError }}
                </div>
                
                <div v-if="mensajeExito" class="bg-green-50 border border-green-200 text-green-700 p-3 rounded-xl text-sm font-bold mb-4 flex items-center">
                    ✅ {{ mensajeExito }}
                </div>

                <form @submit.prevent="registrarse" class="space-y-4">
                    
                    <div>
                        <label class="block text-sm font-bold text-gray-700 mb-1">Cédula de Identidad</label>
                        <input v-model="cedula" type="text" required placeholder="Tu número de cédula..." autocomplete="nope"
                               class="w-full p-3 bg-gray-50 border border-gray-300 rounded-xl outline-none focus:border-[#001a4d] focus:bg-white transition" />
                        <p class="text-[10px] text-gray-400 mt-1">* Debes estar inscrito previamente por tu equipo.</p>
                    </div>

                    <div>
                        <label class="block text-sm font-bold text-gray-700 mb-1">Correo Electrónico</label>
                        <input v-model="correo" type="email" required placeholder="nombre.apellido@ligaconocoto.com"
                               autocomplete="nope"
                               style="text-transform: lowercase;"
                               class="w-full p-3 bg-gray-50 border border-gray-300 rounded-xl outline-none focus:border-[#001a4d] focus:bg-white transition" />
                    </div>

                    <div>
                        <label class="block text-sm font-bold text-gray-700 mb-1">Contraseña</label>
                        <input v-model="password" type="password" required placeholder="Crea una contraseña segura"
                               autocomplete="new-password"
                               class="w-full p-3 bg-gray-50 border border-gray-300 rounded-xl outline-none focus:border-[#001a4d] focus:bg-white transition" />
                        <p class="text-[11px] text-gray-500 mt-2 leading-5">
                            Usa al menos 8 caracteres, una mayúscula, una minúscula, un número y un símbolo.
                        </p>
                    </div>

                    <div>
                        <label class="block text-sm font-bold text-gray-700 mb-1">Confirmar Contraseña</label>
                        <input v-model="confirmarPassword" type="password" required placeholder="Repite tu contraseña"
                               autocomplete="new-password"
                               class="w-full p-3 bg-gray-50 border border-gray-300 rounded-xl outline-none focus:border-[#001a4d] focus:bg-white transition" />
                    </div>

                    <div class="pt-2">
                        <button type="submit" :disabled="cargando" 
                                class="w-full bg-yellow-400 hover:bg-yellow-500 text-[#001a4d] font-black py-3.5 rounded-xl shadow-md transition flex justify-center items-center disabled:opacity-70 disabled:cursor-not-allowed">
                            <span v-if="cargando" class="inline-block animate-spin rounded-full h-5 w-5 border-2 border-[#001a4d] border-t-transparent mr-2"></span>
                            REGISTRARME COMO JUGADOR
                        </button>
                    </div>
                </form>
                
                <div class="mt-6 text-center text-sm font-bold text-gray-500">
                    ¿Ya tienes una cuenta? 
                    <router-link to="/login" class="text-blue-600 hover:underline">Inicia Sesión aquí</router-link>
                </div>
            </div>
        </div>
    </div>
</template>