import { useEffect, useState } from 'react'
import { MapContainer, Marker, TileLayer, useMapEvents } from 'react-leaflet'
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

export function MapPicker({ lat, lng, onChange }: MapPickerProps) {
  const [position, setPosition] = useState<[number, number]>([lat, lng])

  useEffect(() => {
    setPosition([lat, lng])
  }, [lat, lng])

  const handleChange = (newLat: number, newLng: number) => {
    setPosition([newLat, newLng])
    onChange(newLat, newLng)
  }

  const locateMe = () => {
    if (!navigator.geolocation) return
    navigator.geolocation.getCurrentPosition(
      (pos) => handleChange(pos.coords.latitude, pos.coords.longitude),
      () => alert('Could not get your location. Please pin manually on the map.'),
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <p className="text-sm text-slate-600">Click the map to pin the issue location</p>
        <button
          type="button"
          onClick={locateMe}
          className="text-sm px-3 py-1.5 bg-civic-600 text-white rounded-lg hover:bg-civic-700"
        >
          📍 Use my location
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
        </MapContainer>
      </div>
      <p className="text-xs text-slate-500 font-mono">
        {position[0].toFixed(5)}, {position[1].toFixed(5)}
      </p>
    </div>
  )
}
