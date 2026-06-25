import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { createPetition, uploadPhoto } from '../api/client'
import { FormLabel, FormSection, PhotoUploadZone, useFormReveal } from '../components/form/FormFields'
import { LoginPrompt } from '../components/LoginPrompt'
import { MapPicker } from '../components/MapPicker'
import { useAuth } from '../context/AuthContext'

const DEFAULT_LAT = 12.9716
const DEFAULT_LNG = 77.5946

export function NewIssuePage() {
  const navigate = useNavigate()
  const { user, loading: authLoading, googleEnabled } = useAuth()
  const formVisible = useFormReveal()
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [description, setDescription] = useState('')
  const [address, setAddress] = useState('')
  const [lat, setLat] = useState(DEFAULT_LAT)
  const [lng, setLng] = useState(DEFAULT_LNG)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [descFocused, setDescFocused] = useState(false)

  const handleFileSelect = (f: File) => {
    if (preview) URL.revokeObjectURL(preview)
    setFile(f)
    setPreview(URL.createObjectURL(f))
  }

  const handleRemovePhoto = () => {
    if (preview) URL.revokeObjectURL(preview)
    setFile(null)
    setPreview(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) {
      setError('Please upload a photo of the issue')
      return
    }
    setSubmitting(true)
    setError('')
    try {
      const photo_url = await uploadPhoto(file)
      const { petition } = await createPetition({
        photo_url,
        location: { address, lat, lng },
        description,
      })
      navigate(`/approvals/${petition.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit')
    } finally {
      setSubmitting(false)
    }
  }

  if (!authLoading && googleEnabled && !user) {
    return (
      <LoginPrompt
        title="Sign in to report an issue"
        description="Use your Google account so complaints are sent from your Gmail to the municipal authority."
      />
    )
  }

  return (
    <div className="report-form-page max-w-2xl mx-auto">
      <header className="mb-[clamp(1.25rem,3.5vw,2rem)] text-center sm:text-left">
        <h2 className="text-[clamp(1.5rem,4vw,1.75rem)] font-semibold text-civic-900 tracking-tight mb-2">
          Report a Civic Issue
        </h2>
        <p className="text-slate-600 text-[clamp(0.875rem,2vw,1rem)] leading-relaxed">
          Photograph the problem, pin the location, and Urbis will route your complaint to the right department.
        </p>
      </header>

      <form
        onSubmit={handleSubmit}
        className="report-form-card bg-white rounded-[1.5rem] sm:rounded-[1.75rem] border border-stone-200/70 shadow-[0_4px_28px_-10px_rgba(12,74,110,0.1)] p-[clamp(1.25rem,3.5vw,2rem)] space-y-[clamp(1.5rem,4vw,2.25rem)]"
      >
        <FormSection visible={formVisible} delay={0}>
          <FormLabel required>Photo of the issue</FormLabel>
          <PhotoUploadZone preview={preview} onFileSelect={handleFileSelect} onRemove={handleRemovePhoto} />
        </FormSection>

        <FormSection visible={formVisible} delay={80}>
          <FormLabel>Description</FormLabel>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            onFocus={() => setDescFocused(true)}
            onBlur={() => setDescFocused(false)}
            rows={4}
            placeholder="e.g. Large pothole causing traffic hazard near the bus stop"
            className="form-input form-textarea w-full"
          />
          <p
            className={`form-field-hint mt-2 text-xs text-slate-400 transition-opacity duration-200 ease-out ${
              descFocused ? 'opacity-100' : 'opacity-0'
            }`}
          >
            Describe what you see — the clearer, the better.
          </p>
        </FormSection>

        <FormSection visible={formVisible} delay={160}>
          <FormLabel>Address (optional)</FormLabel>
          <input
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="123 Main Street, Metro City"
            className="form-input w-full"
          />
        </FormSection>

        <FormSection visible={formVisible} delay={240}>
          <FormLabel required>Location</FormLabel>
          <MapPicker lat={lat} lng={lng} onChange={(a, b) => { setLat(a); setLng(b) }} />
        </FormSection>

        {error && (
          <p className="text-red-700 text-sm bg-red-50 border border-red-100 rounded-[1rem] px-4 py-3">{error}</p>
        )}

        <FormSection visible={formVisible} delay={320}>
          <button
            type="submit"
            disabled={submitting}
            className="form-btn-submit w-full min-h-[48px] py-3.5 rounded-[1.1rem] font-semibold text-white disabled:opacity-70 flex items-center justify-center gap-2"
          >
            {submitting ? (
              <>
                <span className="form-submit-spinner" aria-hidden />
                <span>Analyzing & drafting complaint…</span>
              </>
            ) : (
              'Submit & Review Draft'
            )}
          </button>
        </FormSection>
      </form>
    </div>
  )
}
