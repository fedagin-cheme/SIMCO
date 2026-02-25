import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('simco', {
  engine: {
    getStatus: () => ipcRenderer.invoke('engine:status'),
    getUrl: () => ipcRenderer.invoke('engine:url'),
    restart: () => ipcRenderer.invoke('engine:restart'),
    onReady: (callback) => { ipcRenderer.on('engine:ready', callback) },
    onOffline: (callback) => { ipcRenderer.on('engine:offline', callback) },
  },
  window: {
    minimize: () => ipcRenderer.send('window:minimize'),
    maximize: () => ipcRenderer.send('window:maximize'),
    close: () => ipcRenderer.send('window:close'),
  },
  shell: {
    openExternal: (url) => ipcRenderer.send('shell:open', url),
  },
})
