import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { createPetition, uploadPhoto } from '../api/client'
import { MapPicker } from '../components/MapPicker'

const DEFAULT_LAT = 12.9716
const DEFAULT_LNG = 77.5946

export function NewIssuePage() {
  const navigate = useNavigate()
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [description, setDescription] = useState('')
  const [address, setAddress] = useState('')
  const [lat, setLat] = useState(DEFAULT_LAT)
  const [lng, setLng] = useState(DEFAULT_LNG)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (!f) return
    setFile(f)
    setPreview(URL.createObjectURL(f))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) {
      setError('Please upload a photo of the issue')
      return
    }
    setLoading(true)
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
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold text-civic-900 mb-2">Report a Civic Issue</h2>
      <p className="text-slate-600 mb-6">
        Photograph the problem, pin the location, and CivicLens will route your complaint to the right department.
      </p>

      <form onSubmit={handleSubmit} className="space-y-6 bg-white rounded-2xl shadow-sm border p-6">
        <div>
          <label className="block text-sm font-medium mb-2">Photo of the issue *</label>
          <div className="border-2 border-dashed border-slate-200 rounded-xl p-4 text-center hover:border-civic-400 transition-colors">
            {preview ? (
              <img src={preview} alt="Preview" className="max-h-48 mx-auto rounded-lg mb-3" />
            ) : (
              <p className="text-slate-400 py-8">📷 Upload a photo</p>
            )}
            <input type="file" accept="image/*" capture="environment" onChange={onFileChange} className="text-sm" />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            placeholder="e.g. Large pothole causing traffic hazard near the bus stop"
            className="w-full border rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-civic-500 focus:outline-none"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Address (optional)</label>
          <input
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="123 Main Street, Metro City"
            className="w-full border rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-civic-500 focus:outline-none"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Location *</label>
          <MapPicker lat={lat} lng={lng} onChange={(a, b) => { setLat(a); setLng(b) }} />
        </div>

        {error && <p className="text-red-600 text-sm">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 bg-civic-600 text-white font-semibold rounded-xl hover:bg-civic-700 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Analyzing & drafting complaint…' : 'Submit & Review Draft'}
        </button>
      </form>
    </div>
  )
}
