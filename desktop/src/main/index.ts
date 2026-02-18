import { app, BrowserWindow, ipcMain, shell } from 'electron'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'
import { spawn, ChildProcess } from 'child_process'

const __dirname = dirname(fileURLToPath(import.meta.url))

// ─── Config ───────────────────────────────────────────────────────────────────
const ENGINE_PORT = 8742
const ENGINE_HOST = '127.0.0.1'
const DEV_URL = `http://localhost:5173`

// ─── State ────────────────────────────────────────────────────────────────────
let mainWindow: BrowserWindow | null = null
let engineProcess: ChildProcess | null = null
let engineReady = false

// ─── Window ───────────────────────────────────────────────────────────────────
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    backgroundColor: '#0f1117',
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'hidden',
    frame: false,
    webPreferences: {
      preload: join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  })

  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL(DEV_URL)
    mainWindow.webContents.openDevTools({ mode: 'detach' })
  } else {
    mainWindow.loadFile(join(__dirname, '../dist/index.html'))
  }

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

// ─── Python Engine ────────────────────────────────────────────────────────────
function startEngine() {
  // In development: assumes uvicorn is already running (started manually)
  // In production: spawns the bundled Python executable
  if (process.env.NODE_ENV === 'development') {
    console.log('[Engine] Dev mode — expecting engine on port', ENGINE_PORT)
    engineReady = true
    return
  }

  const enginePath = join(process.resourcesPath, 'engine', 'simco-engine')
  console.log('[Engine] Starting:', enginePath)

  engineProcess = spawn(enginePath, ['--port', String(ENGINE_PORT)], {
    stdio: ['ignore', 'pipe', 'pipe'],
  })

  engineProcess.stdout?.on('data', (data: Buffer) => {
    const msg = data.toString()
    console.log('[Engine]', msg)
    if (msg.includes('Application startup complete')) {
      engineReady = true
      mainWindow?.webContents.send('engine:ready')
    }
  })

  engineProcess.stderr?.on('data', (data: Buffer) => {
    console.error('[Engine ERROR]', data.toString())
  })

  engineProcess.on('exit', (code) => {
    console.log('[Engine] Exited with code', code)
    engineReady = false
    mainWindow?.webContents.send('engine:offline')
  })
}

function stopEngine() {
  if (engineProcess) {
    engineProcess.kill()
    engineProcess = null
  }
}

// ─── IPC Handlers ─────────────────────────────────────────────────────────────
ipcMain.handle('engine:status', () => ({
  ready: engineReady,
  url: `http://${ENGINE_HOST}:${ENGINE_PORT}`,
}))

ipcMain.handle('engine:url', () => `http://${ENGINE_HOST}:${ENGINE_PORT}`)

// Window controls
ipcMain.on('window:minimize', () => mainWindow?.minimize())
ipcMain.on('window:maximize', () => {
  if (mainWindow?.isMaximized()) {
    mainWindow.unmaximize()
  } else {
    mainWindow?.maximize()
  }
})
ipcMain.on('window:close', () => mainWindow?.close())

// Open external links in browser, not Electron
ipcMain.on('shell:open', (_event, url: string) => {
  shell.openExternal(url)
})

// ─── App Lifecycle ─────────────────────────────────────────────────────────────
app.whenReady().then(() => {
  createWindow()
  startEngine()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  stopEngine()
  if (process.platform !== 'darwin') app.quit()
})

app.on('before-quit', () => {
  stopEngine()
})
