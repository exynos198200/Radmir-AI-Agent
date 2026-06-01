const { app, BrowserWindow, globalShortcut, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false, // For simpler IPC in this architecture
    },
    titleBarStyle: 'hidden', // Modern modern, frameless look
    vibrancy: 'ultradark', // MacOS Glassmorphism
    backgroundMaterial: 'acrylic', // Windows 11 Glassmorphism
    autoHideMenuBar: true
  });

  // Load the React app
  const startUrl = process.env.ELECTRON_START_URL || `file://${path.join(__dirname, '../dist/index.html')}`;
  mainWindow.loadURL(startUrl);

  // Register Voice Hotkey (Q+E is tricky for global shortcuts natively without modifiers, using a combination or listening via keyhook. Using CommandOrControl+E as robust fallback)
  globalShortcut.register('CommandOrControl+Shift+E', () => {
    mainWindow.webContents.send('trigger-voice-recording');
    if (!mainWindow.isFocused()) {
        mainWindow.focus();
    }
  });

  mainWindow.on('closed', function () {
    mainWindow = null;
  });
}

function startPythonBackend() {
  const isPackaged = app.isPackaged;
  
  if (isPackaged) {
    // In production, run the bundled executable
    const executablePath = path.join(process.resourcesPath, 'backend-server.exe');
    pythonProcess = spawn(executablePath, [], {
        cwd: path.dirname(executablePath)
    });
  } else {
    // In development, assume python is in PATH
    pythonProcess = spawn('python', ['-m', 'backend.main'], {
        cwd: path.join(__dirname, '..')
    });
  }

  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python: ${data}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python Error: ${data}`);
  });
}

app.on('ready', () => {
    startPythonBackend();
    createWindow();
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
  if (pythonProcess) {
      pythonProcess.kill();
  }
});

app.on('activate', function () {
  if (mainWindow === null) createWindow();
});
