import { defineConfig } from 'vite';
export default defineConfig({server:{port:5175,strictPort:true,allowedHosts:["terminal.local"],proxy:{'/api':'http://127.0.0.1:8005'}}});
