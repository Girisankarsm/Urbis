import { useCallback, useEffect, useState } from 'react'
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from 'react-leaflet'
import L from 'leaflet'

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

/** Pans the map when the user requests their GPS location. */
function FlyToLocation({ lat, lng, flyKey }: { lat: number; lng: number; flyKey: number }) {
  const map = useMap()

  useEffect(() => {
    if (flyKey > 0) {
      map.flyTo([lat, lng], 17, { duration: 0.8 })
    }
  }, [flyKey, lat, lng, map])

  return null
}

export function MapPicker({ lat, lng, onChange }: MapPickerProps) {
  const [position, setPosition] = useState<[number, number]>([lat, lng])
  const [flyKey, setFlyKey] = useState(0)
  const [locating, setLocating] = useState(false)

  useEffect(() => {
    setPosition([lat, lng])
  }, [lat, lng])

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
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords
        handleChange(latitude, longitude)
        setFlyKey((k) => k + 1)
        setLocating(false)
      },
      (err) => {
        setLocating(false)
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

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center gap-2">
        <p className="text-sm text-slate-600">Click the map to pin the issue location</p>
        <button
          type="button"
          onClick={locateMe}
          disabled={locating}
          className="text-sm px-3 py-1.5 bg-civic-600 text-white rounded-lg hover:bg-civic-700 disabled:opacity-60 whitespace-nowrap"
        >
          {locating ? 'Locating…' : '📍 Use my location'}
        </button>
      </div>
      <div className="h-64 border rounded-xl overflow-hidden">
        <MapContainer center={position} zoom={15} className="h-full w-full">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <Marker position={position} />
          <ClickHandler onChange={handleChange} />
          <FlyToLocation lat={position[0]} lng={position[1]} flyKey={flyKey} />
        </MapContainer>
      </div>
      <p className="text-xs text-slate-500 font-mono">
        {position[0].toFixed(5)}, {position[1].toFixed(5)}
      </p>
    </div>
  )
}
