<template>
  <nav class="bg-[#001a4d] py-6 px-4 shadow-xl sticky top-0 z-50">
    <div class="container mx-auto flex justify-between items-center">
        
        <!-- Logo y Título -->
        <div class="flex items-center space-x-4">
            <div class="bg-white p-1 rounded-full shadow-lg border border-gray-200">
                <img src="/imagenes/logo.png" alt="Logo LDP Conocoto" class="h-16 w-16 md:h-20 md:w-20 rounded-full object-cover">
            </div>
            <h1 class="text-2xl md:text-3xl font-black text-white tracking-tighter">
                L.D.P. <span class="text-[#FFD700]">CONOCOTO</span>
            </h1>
        </div>

        <!-- Enlaces -->
        <div class="hidden md:flex space-x-8 text-white text-lg font-medium">
            <!-- Cambiamos la etiqueta 'a' por 'router-link' para que sea instantáneo -->
            <router-link to="/" class="hover:text-[#FFD700] transition">Inicio</router-link>
            <a href="#" class="hover:text-[#FFD700] transition">Equipos</a>
            <a href="#" class="hover:text-[#FFD700] transition">Estadísticas</a>
        </div>

        <!-- Botón de Login -->
        <!-- Cambiamos el href="login.html" por to="/login" -->
        <router-link to="/login" class="bg-[#FFD700] text-[#001a4d] px-6 py-3 rounded-full font-bold hover:bg-yellow-500 transition shadow-md inline-block">
            Iniciar Sesión
        </router-link>
    </div>
  </nav>
</template>