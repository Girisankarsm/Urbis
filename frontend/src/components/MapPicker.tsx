import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from 'react-leaflet'
import L from 'leaflet'

import { LocationPinIcon } from './form/FormIcons'

import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

delete (L.Icon.Default.prototype as unknown as { _getIconUrl?: unknown })._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
})

interface MapPickerProps {
  lat: number
  lng: number
  onChange: (lat: number, lng: number) => void
}

function ClickHandler({ onChange }: { onChange: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) {
      onChange(e.latlng.lat, e.latlng.lng)
    },
  })
  return null
}

function FlyToLocation({ lat, lng, flyKey }: { lat: number; lng: number; flyKey: number }) {
  const map = useMap()

  useEffect(() => {
    if (flyKey > 0) {
      map.flyTo([lat, lng], 17, { duration: 0.8 })
    }
  }, [flyKey, lat, lng, map])

  return null
}

function createPinIcon(dropAnim: boolean) {
  return L.divIcon({
    className: 'form-map-marker',
    html: `<div class="form-map-pin-inner${dropAnim ? ' form-map-pin-drop' : ''}">
      <svg viewBox="0 0 24 32" width="28" height="36" fill="none" stroke="#0369a1" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 30s8-7 8-14a8 8 0 10-16 0c0 7 8 14 8 14z"/>
        <circle cx="12" cy="16" r="3" fill="#e8a87c" stroke="#0369a1"/>
      </svg>
    </div>`,
    iconSize: [28, 36],
    iconAnchor: [14, 36],
  })
}

export function MapPicker({ lat, lng, onChange }: MapPickerProps) {
  const [position, setPosition] = useState<[number, number]>([lat, lng])
  const [flyKey, setFlyKey] = useState(0)
  const [locating, setLocating] = useState(false)
  const [pinDropKey, setPinDropKey] = useState(0)
  const [pinPulse, setPinPulse] = useState(false)
  const prevPosition = useRef(position)

  useEffect(() => {
    setPosition([lat, lng])
  }, [lat, lng])

  useEffect(() => {
    if (prevPosition.current[0] !== position[0] || prevPosition.current[1] !== position[1]) {
      setPinDropKey((k) => k + 1)
      prevPosition.current = position
    }
  }, [position])

  const handleChange = useCallback(
    (newLat: number, newLng: number) => {
      setPosition([newLat, newLng])
      onChange(newLat, newLng)
    },
    [onChange],
  )

  const locateMe = () => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser.')
      return
    }

    setLocating(true)
    setPinPulse(true)
    setTimeout(() => setPinPulse(false), 600)

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords
        handleChange(latitude, longitude)
        setFlyKey((k) => k + 1)
        setLocating(false)
      },
      (err) => {
        setLocating(false)
        setPinPulse(false)
        if (err.code === err.PERMISSION_DENIED) {
          alert('Location permission denied. Allow location access in your browser, then try again.')
        } else if (err.code === err.TIMEOUT) {
          alert('Location request timed out. Try again or pin manually on the map.')
        } else {
          alert('Could not get your location. Please pin manually on the map.')
        }
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 },
    )
  }

  const pinIcon = useMemo(() => createPinIcon(true), [pinDropKey])

  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-600 leading-relaxed">
        Click the map to pin the issue location
      </p>

      <button
        type="button"
        onClick={locateMe}
        disabled={locating}
        className="form-btn-locate w-full sm:w-auto sm:ml-auto flex items-center justify-center gap-2 min-h-[48px] px-5 py-2.5 rounded-[1.1rem] font-medium text-white disabled:opacity-60"
      >
        <LocationPinIcon className={`w-4 h-4 shrink-0 ${pinPulse ? 'form-pin-pulse-once' : ''}`} />
        {locating ? 'Locating…' : 'Use my location'}
      </button>

      <div className="form-map-wrap h-[clamp(11rem,42vw,16rem)] rounded-[1.25rem] overflow-hidden border border-stone-200/80 shadow-[0_4px_20px_-8px_rgba(12,74,110,0.12)]">
        <MapContainer center={position} zoom={15} className="h-full w-full">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <Marker key={pinDropKey} position={position} icon={pinIcon} />
          <ClickHandler onChange={handleChange} />
          <FlyToLocation lat={position[0]} lng={position[1]} flyKey={flyKey} />
        </MapContainer>
      </div>

      <p className="form-coord-chip inline-flex items-center gap-1.5 text-xs text-slate-500 font-mono bg-stone-50 border border-stone-200/80 rounded-full px-3 py-1.5">
        <span className="w-1.5 h-1.5 rounded-full bg-warm-400/80 shrink-0" aria-hidden />
        {position[0].toFixed(5)}, {position[1].toFixed(5)}
      </p>
    </div>
  )
}
