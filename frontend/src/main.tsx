import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { Layout } from './components/Layout'
import { AuthProvider } from './context/AuthContext'
import { ApprovalDetailPage, ApprovalsPage } from './pages/ApprovalPage'
import { DashboardPage } from './pages/DashboardPage'
import { NewIssuePage } from './pages/NewIssuePage'
import { PetitionDetailPage } from './pages/PetitionDetailPage'
import { ProfilePage } from './pages/ProfilePage'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<DashboardPage />} />
            <Route path="new" element={<NewIssuePage />} />
            <Route path="petitions/:id" element={<PetitionDetailPage />} />
            <Route path="approvals" element={<ApprovalsPage />} />
            <Route path="approvals/:id" element={<ApprovalDetailPage />} />
            <Route path="profile" element={<ProfilePage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
