<template>
  <div class="min-h-screen bg-gray-100">
    <!-- Sidebar -->
    <Sidebar />
    
    <!-- Main Content -->
    <div class="lg:pl-64">
      <!-- Top Navbar -->
      <Navbar />
      
      <!-- Page Content -->
      <main class="py-6 px-4 sm:px-6 lg:px-8">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import Sidebar from './components/Sidebar.vue'
import Navbar from './components/Navbar.vue'
</script>
