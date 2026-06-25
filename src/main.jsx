import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import PhoneFrame from './Components/PhoneFrame'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <PhoneFrame>
      <App />
    </PhoneFrame>
  </StrictMode>,
)
