import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useModel = defineStore('counter', () => {
  const running = ref(false)
  
  function run() {
    running.value = true
  }
  function stop() {
    running.value = false
  }

  return { running, run, stop }
})
