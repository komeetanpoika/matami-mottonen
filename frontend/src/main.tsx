import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import './index.css'
import { LangProvider } from './lang'
import LandingPage from './pages/LandingPage'

const Todo = ({ name }: { name: string }) => <div style={{ padding: '2rem' }}>{name}</div>

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <LangProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/events" element={<Todo name="events" />} />
          <Route path="/events/thanks" element={<Todo name="thanks" />} />
          <Route path="/events/:slug" element={<Todo name="event" />} />
          <Route path="/admin/login" element={<Todo name="admin login" />} />
          <Route path="/admin" element={<Todo name="admin" />} />
          <Route path="/admin/events/new" element={<Todo name="new" />} />
          <Route path="/admin/events/:id" element={<Todo name="edit" />} />
          <Route path="/admin/events/:id/attendees" element={<Todo name="attendees" />} />
        </Routes>
      </BrowserRouter>
    </LangProvider>
  </StrictMode>,
)
