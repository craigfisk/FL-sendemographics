<template>
  <div class="map-container">
    <div v-if="loading" class="loading">Loading map…</div>
    <div v-if="error" class="error">{{ error }}</div>

    <div class="controls">
      <label :class="{ active: layer === 'state' }" @click="setLayer('state')">
        <span class="swatch state-swatch"></span> State outline
      </label>
      <label :class="{ active: layer === 'hispanic' }" @click="setLayer('hispanic')">
        <span class="swatch hispanic-swatch"></span> Spanish-speaking (% Hispanic/Latino)
      </label>
      <label :class="{ active: layer === 'young' }" @click="setLayer('young')">
        <span class="swatch young-swatch"></span> Young voters (% age 18–34)
      </label>
      <label :class="{ active: layer === 'democrat' }" @click="setLayer('democrat')">
        <span class="swatch democrat-swatch"></span> Registered Democrats (% of voters)
      </label>
      <label :class="{ active: layer === 'unaffiliated' }" @click="setLayer('unaffiliated')">
        <span class="swatch unaffiliated-swatch"></span> NPA/Unaffiliated (% of voters)
      </label>
      <label :class="{ active: layer === 'republican' }" @click="setLayer('republican')">
        <span class="swatch republican-swatch"></span> Registered Republicans (% of voters)
      </label>
    </div>

    <div id="fl-map" ref="mapEl"></div>

    <div v-if="layer !== 'state'" class="legend">
      <div class="legend-title">
        {{ layer === 'hispanic'    ? '% Hispanic/Latino'
         : layer === 'young'       ? '% age 18–34'
         : layer === 'democrat'    ? '% Registered Democrat'
         : layer === 'republican'  ? '% Registered Republican'
         :                           '% NPA/Unaffiliated' }}
      </div>
      <div class="legend-scale">
        <span v-for="item in activeLegend" :key="item.label" class="legend-item">
          <span class="legend-color" :style="{ background: item.color }"></span>
          {{ item.label }}
        </span>
      </div>
      <div class="legend-note">
        {{ layer === 'hispanic' ? 'Source: ACS 2024 5-yr, Census tracts within Florida'
         : layer === 'young'    ? 'Source: ACS 2024 5-yr, voting-age pop.'
         :                        'Source: FL Division of Elections (County level)' }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

type LayerName = 'state' | 'hispanic' | 'young' | 'democrat' | 'unaffiliated' | 'republican'

const mapEl = ref<HTMLElement | null>(null)
const loading = ref(true)
const error = ref('')
const layer = ref<LayerName>('state')

let map: L.Map | null = null
let stateLayer: L.GeoJSON | null = null
let hispanicLayer: L.GeoJSON | null = null
let youngLayer: L.GeoJSON | null = null
let democratLayer: L.GeoJSON | null = null
let unaffiliatedLayer: L.GeoJSON | null = null
let republicanLayer: L.GeoJSON | null = null

let demoData: any = null
let voterData: any = null

// Color scales - adjusted ranges for Florida demographics/politics
const hispanicBreaks = [0, 10, 20, 35, 50, 100]
const hispanicColors = ['#fff5f0', '#fca082', '#fb5b34', '#cb1a1c', '#67000d']

const youngBreaks = [0, 15, 20, 25, 30, 100]
const youngColors  = ['#f7fbff', '#9ecae1', '#4292c6', '#2171b5', '#084594']

const demBreaks = [0, 25, 35, 45, 55, 100]
const demColors = ['#edf8e9', '#bae4b3', '#74c476', '#31a354', '#006d2c']

const unaffBreaks = [0, 15, 20, 25, 30, 100]
const unaffColors = ['#feedde', '#fdbe85', '#fd8d3c', '#e6550d', '#a63603']

const repBreaks = [0, 30, 40, 50, 60, 100]
const repColors = ['#fee5d9', '#fcbba1', '#fc9272', '#fb6a4a', '#cb181d']

function colorFor(value: number, breaks: number[], colors: string[]): string {
  if (value == null) return '#ccc'
  for (let i = 0; i < breaks.length - 1; i++) {
    if (value < breaks[i + 1]) return colors[i]
  }
  return colors[colors.length - 1]
}

const activeLegend = computed(() => {
  const [breaks, colors] =
    layer.value === 'hispanic'     ? [hispanicBreaks, hispanicColors]
    : layer.value === 'young'      ? [youngBreaks,    youngColors]
    : layer.value === 'democrat'   ? [demBreaks,      demColors]
    : layer.value === 'republican' ? [repBreaks,      repColors]
    :                                [unaffBreaks,    unaffColors]
  return colors.map((c, i) => ({
    color: c,
    label: `${breaks[i]}–${breaks[i + 1]}%`,
  }))
})

function buildDemoLayers() {
  if (!map) return

  if (demoData) {
    hispanicLayer = L.geoJSON(demoData, {
      style: (f) => ({
        fillColor: colorFor(f?.properties.pct_hispanic ?? 0, hispanicBreaks, hispanicColors),
        fillOpacity: 0.75,
        color: '#666',
        weight: 0.5,
      }),
      onEachFeature: (f, l) => {
        const p = f.properties
        l.bindTooltip(
          `<strong>${p.name || 'Tract ' + p.TRACT}</strong><br>` +
          `Hispanic/Latino: <b>${p.pct_hispanic}%</b><br>` +
          `Spanish-speaking: <b>${p.pct_spanish ?? p.pct_hispanic}%</b><br>` +
          `Pop: ${p.total_pop?.toLocaleString() || 'N/A'}`,
          { sticky: true }
        )
      },
    })

    youngLayer = L.geoJSON(demoData, {
      style: (f) => ({
        fillColor: colorFor(f?.properties.pct_young ?? 0, youngBreaks, youngColors),
        fillOpacity: 0.75,
        color: '#666',
        weight: 0.5,
      }),
      onEachFeature: (f, l) => {
        const p = f.properties
        l.bindTooltip(
          `<strong>${p.name || 'Tract ' + p.TRACT}</strong><br>` +
          `Age 18–34: <b>${p.pct_young}%</b><br>` +
          `Pop: ${p.total_pop?.toLocaleString() || 'N/A'}`,
          { sticky: true }
        )
      },
    })
  }

  if (voterData) {
    democratLayer = L.geoJSON(voterData, {
      style: (f) => ({
        fillColor: colorFor(f?.properties.pct_dem, demBreaks, demColors),
        fillOpacity: 0.75,
        color: '#666',
        weight: 0.5,
      }),
      onEachFeature: (f, l) => {
        const p = f.properties
        const locName = p.county || p.municipality || p.name || 'Unknown'
        l.bindTooltip(
          `<strong>${locName}</strong><br>` +
          (p.pct_dem != null ? `Registered Democrat: <b>${p.pct_dem}%</b>` : 'No data'),
          { sticky: true }
        )
      },
    })

    unaffiliatedLayer = L.geoJSON(voterData, {
      style: (f) => ({
        fillColor: colorFor(f?.properties.pct_unaffiliated, unaffBreaks, unaffColors),
        fillOpacity: 0.75,
        color: '#666',
        weight: 0.5,
      }),
      onEachFeature: (f, l) => {
        const p = f.properties
        const locName = p.county || p.municipality || p.name || 'Unknown'
        l.bindTooltip(
          `<strong>${locName}</strong><br>` +
          (p.pct_unaffiliated != null ? `NPA/Unaffiliated: <b>${p.pct_unaffiliated}%</b>` : 'No data'),
          { sticky: true }
        )
      },
    })

    republicanLayer = L.geoJSON(voterData, {
      style: (f) => ({
        fillColor: colorFor(f?.properties.pct_rep, repBreaks, repColors),
        fillOpacity: 0.75,
        color: '#666',
        weight: 0.5,
      }),
      onEachFeature: (f, l) => {
        const p = f.properties
        const locName = p.county || p.municipality || p.name || 'Unknown'
        l.bindTooltip(
          `<strong>${locName}</strong><br>` +
          (p.pct_rep != null ? `Registered Republican: <b>${p.pct_rep}%</b>` : 'No data'),
          { sticky: true }
        )
      },
    })
  }
}

function setLayer(name: LayerName) {
  if (!map) return
  layer.value = name
  hispanicLayer?.remove()
  youngLayer?.remove()
  democratLayer?.remove()
  unaffiliatedLayer?.remove()
  republicanLayer?.remove()
  stateLayer?.remove()

  if (name === 'state') {
    stateLayer?.addTo(map)
  } else if (name === 'hispanic') {
    hispanicLayer?.addTo(map)
    stateLayer?.addTo(map)
  } else if (name === 'young') {
    youngLayer?.addTo(map)
    stateLayer?.addTo(map)
  } else if (name === 'democrat') {
    democratLayer?.addTo(map)
    stateLayer?.addTo(map)
  } else if (name === 'unaffiliated') {
    unaffiliatedLayer?.addTo(map)
    stateLayer?.addTo(map)
  } else if (name === 'republican') {
    republicanLayer?.addTo(map)
    stateLayer?.addTo(map)
  }
}

watch(layer, setLayer)

onMounted(async () => {
  if (!mapEl.value) return

  // Center on Florida
  map = L.map(mapEl.value).setView([27.76, -81.68], 6)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 18,
  }).addTo(map)

  try {
    const [stateRes, demoRes] = await Promise.all([
      fetch('/florida.geojson'),
      fetch('/florida-demo.geojson'),
    ])
    
    if (!stateRes.ok) throw new Error(`state HTTP ${stateRes.status}`)
    if (!demoRes.ok)  throw new Error(`demo HTTP ${demoRes.status}`)

    const stateGeojson = await stateRes.json()
    demoData = await demoRes.json()

    const voterRes = await fetch('/florida-voters.geojson').catch(() => null)
    if (voterRes?.ok) {
      voterData = await voterRes.json()
    }

    stateLayer = L.geoJSON(stateGeojson, {
      style: { color: '#2c3e50', weight: 2, fillOpacity: 0, interactive: false },
    })

    buildDemoLayers()
    setLayer('state')

    stateLayer!.addTo(map)
    map.fitBounds(stateLayer!.getBounds(), { padding: [20, 20] })

  } catch (e: any) {
    error.value = `Failed to load map data: ${e.message}`
    console.error(e)
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  map?.remove()
})
</script>

<style scoped>
.map-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  font-family: sans-serif;
}

.controls {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  justify-content: center;
  max-width: 900px;
}

.controls label {
  cursor: pointer;
  padding: 6px 14px;
  border-radius: 6px;
  border: 1px solid #ddd;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  user-select: none;
  background: #fff;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.controls label:hover {
  background: #f0f0f0;
}

.controls label.active {
  border-color: #2c3e50;
  background: #f8f9fa;
  font-weight: 600;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.swatch {
  display: inline-block;
  width: 16px;
  height: 16px;
  border-radius: 3px;
}

.state-swatch         { background: #2c3e50; }
.hispanic-swatch      { background: #fb5b34; }
.young-swatch         { background: #2171b5; }
.democrat-swatch      { background: #31a354; }
.unaffiliated-swatch  { background: #fd8d3c; }
.republican-swatch    { background: #fb6a4a; }

#fl-map {
  width: 100%;
  max-width: 900px;
  height: 600px;
  border: 1px solid #ccc;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.loading, .error { margin-bottom: 1rem; padding: 1rem; background: #fff; border-radius: 4px; color: #555; }
.error { color: #c0392b; border-left: 4px solid #c0392b; }

.legend {
  margin-top: 1rem;
  font-size: 13px;
  text-align: center;
  background: #fff;
  padding: 10px 20px;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.legend-title { font-weight: bold; margin-bottom: 6px; color: #333; }

.legend-scale {
  display: flex;
  gap: 8px;
  justify-content: center;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.legend-color {
  display: inline-block;
  width: 20px;
  height: 14px;
  border: 1px solid #999;
  border-radius: 2px;
}

.legend-note { color: #666; margin-top: 8px; font-size: 11px; font-style: italic; }
</style>
