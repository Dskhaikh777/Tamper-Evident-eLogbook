import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Provider } from 'react-redux'
import { store } from './store'
import '@fontsource/national-park/400.css'
import '@fontsource/national-park/500.css'
import '@fontsource/national-park/700.css'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(

  <Provider store={store}>
    <App />
  </Provider>

)
