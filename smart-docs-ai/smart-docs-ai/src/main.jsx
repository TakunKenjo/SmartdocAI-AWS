// Polyfill cho biến global của Node.js trong môi trường trình duyệt của Vite
if (typeof global === "undefined") {
  window.global = window;
}

import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { BrowserRouter } from "react-router";
import { Provider } from "react-redux";
import { store } from "@/store/index.js";

createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <Provider store={store}>
      <App />
    </Provider>
  </BrowserRouter>
)
