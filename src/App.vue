<template>
  <div id="app">
    <h1>FL-Sen Demographics</h1>
    <FloridaMap />
  </div>
</template>

<script setup lang="ts">
import FloridaMap from './components/FloridaMap.vue'
</script>

<style>
body {
  margin: 0;
  padding: 0;
  background-color: #f4f4f9;
}
#app {
  padding: 1rem;
  text-align: center;
}
h1 {
  margin-top: 0;
  font-family: sans-serif;
  color: #333;
}
</style>
