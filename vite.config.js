import { defineConfig } from 'vite';
export default defineConfig({build:{target:'esnext'},server:{proxy:{'/api':'http://127.0.0.1:8000','/runtime':'http://127.0.0.1:8000','/data':'http://127.0.0.1:8000'}}});
