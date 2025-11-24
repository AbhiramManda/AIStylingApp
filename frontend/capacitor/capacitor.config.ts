import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.abhiram.ai_styling',
  appName: 'AI Personal Styling App',
  webDir: 'dist',       // React build output folder
  bundledWebRuntime: false, //
  server: {
    androidScheme: 'https',   // Required if calling backend APIs over HTTPS
  }
};

export default config;



