import { useEffect } from 'react'
import { useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet.markercluster'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'

export interface InfraMapMarker {
  category: string
  icon: string
  lat: number
  lng: number
  name?: string | null
  distance_m?: number | null
}

const ICON_EMOJI: Record<string, string> = {
  school: '🏫',
  hospital: '🏥',
  bus_stop: '🚌',
  station: '🚉',
}

export function InfrastructureMarkerCluster({ markers }: { markers: InfraMapMarker[] }) {
  const map = useMap()

  useEffect(() => {
    if (!markers.length) return

    const group = L.markerClusterGroup({ maxClusterRadius: 50, showCoverageOnHover: false })
    markers.forEach((m) => {
      const icon = L.divIcon({
        className: 'infra-map-marker',
        html: `<span style="font-size:16px;line-height:1">${ICON_EMOJI[m.icon] || '📍'}</span>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
      })
      const marker = L.marker([m.lat, m.lng], { icon })
      const label = m.name ? `${m.name}${m.distance_m ? ` (${Math.round(m.distance_m)}m)` : ''}` : m.category
      marker.bindTooltip(label)
      group.addLayer(marker)
    })

    map.addLayer(group)
    return () => {
      map.removeLayer(group)
    }
  }, [map, markers])

  return null
}
