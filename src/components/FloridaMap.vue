<template>
  <div class="map-container">
    <div v-if="loading" class="loading">Loading map…</div>
    <div v-if="error" class="error">{{ error }}</div>

    <div class="controls">
      <label :class="{ active: layer === 'cuban' }" @click="setLayer('cuban')">
        <span class="swatch cuban-swatch"></span> Cuban
      </label>
      <label :class="{ active: layer === 'puerto_rican' }" @click="setLayer('puerto_rican')">
        <span class="swatch puerto_rican-swatch"></span> Puerto Rican
      </label>
      <label :class="{ active: layer === 'venezuelan' }" @click="setLayer('venezuelan')">
        <span class="swatch venezuelan-swatch"></span> Venezuelan
      </label>
      <label :class="{ active: layer === 'colombian' }" @click="setLayer('colombian')">
        <span class="swatch colombian-swatch"></span> Colombian
      </label>
      <label :class="{ active: layer === 'jamaican' }" @click="setLayer('jamaican')">
        <span class="swatch jamaican-swatch"></span> Jamaican
      </label>
      <label :class="{ active: layer === 'other_hispanic' }" @click="setLayer('other_hispanic')">
        <span class="swatch other_hispanic-swatch"></span> Other Hispanic
      </label>
      <label :class="{ active: layer === 'young' }" @click="setLayer('young')">
        <span class="swatch young-swatch"></span> Youth (% 18-34)
      </label>
      <label :class="{ active: layer === 'middle_age' }" @click="setLayer('middle_age')">
        <span class="swatch middle_age-swatch"></span> Middle Age (% 35-49)
      </label>
      <label :class="{ active: layer === 'women' }" @click="setLayer('women')">
        <span class="swatch women-swatch"></span> Women
      </label>
      <label :class="{ active: layer === 'black' }" @click="setLayer('black')">
        <span class="swatch black-swatch"></span> Black
      </label>
      <label :class="{ active: layer === 'democrat' }" @click="setLayer('democrat')">
        <span class="swatch democrat-swatch"></span> Registered Dems
      </label>
      <label :class="{ active: layer === 'unaffiliated' }" @click="setLayer('unaffiliated')">
        <span class="swatch unaffiliated-swatch"></span> NPA/Unaffiliated
      </label>
      <label :class="{ active: layer === 'republican' }" @click="setLayer('republican')">
        <span class="swatch republican-swatch"></span> Registered Repubs
      </label>
    </div>

    <div class="map-wrapper">
      <div id="fl-map" ref="mapEl"></div>
      <button class="sources-button" @click="showSourcesModal = true">
        Sources
      </button>
    </div>

    <div v-if="layer !== 'state'" class="legend">
      <div class="legend-title">
        {{ layer === 'cuban'           ? '% Cuban'
         : layer === 'puerto_rican'    ? '% Puerto Rican'
         : layer === 'venezuelan'      ? '% Venezuelan'
         : layer === 'colombian'       ? '% Colombian'
         : layer === 'jamaican'        ? '% Jamaican'
         : layer === 'other_hispanic'  ? '% Other Hispanic'
         : layer === 'young'           ? '% age 18–34'
         : layer === 'middle_age'      ? '% Middle Age (35-49)'
         : layer === 'women'           ? '% Women'
         : layer === 'black'           ? '% Black'
         : layer === 'democrat'        ? '% Registered Dems'
         : layer === 'republican'      ? '% Registered Repubs'
         :                               '% NPA/Unaffiliated' }}
      </div>
      <div class="legend-scale">
        <span v-for="item in activeLegend" :key="item.label" class="legend-item">
          <span class="legend-color" :style="{ background: item.color }"></span>
          {{ item.label }}
        </span>
      </div>
      <div class="legend-note">
        {{ ['cuban', 'puerto_rican', 'venezuelan', 'colombian', 'jamaican', 'other_hispanic', 'young', 'middle_age', 'women', 'black'].includes(layer) 
         ? 'Source: ACS 2024 5-yr, Census tracts within Florida'
         : 'Source: FL Division of Elections (County level)' }}
      </div>
    </div>

    <!-- Sources Modal -->
    <div v-if="showSourcesModal" class="modal-overlay" @click="showSourcesModal = false">
      <div class="modal-content" @click.stop>
        <h3>Data Sources</h3>
        <p><strong>Demographics (Source: American Community Survey 2024 5-yr Estimates, Census tracts within Florida)</strong></p>
        <ul>
          <li><strong>Cuban:</strong> % of population identifying as Cuban</li>
          <li><strong>Puerto Rican:</strong> % of population identifying as Puerto Rican</li>
          <li><strong>Venezuelan:</strong> % of population identifying as Venezuelan</li>
          <li><strong>Colombian:</strong> % of population identifying as Colombian</li>
          <li><strong>Jamaican:</strong> % of population identifying as Jamaican</li>
          <li><strong>Other Hispanic:</strong> % of population identifying as Other Hispanic</li>
          <li><strong>Youth (% 18-34):</strong> % of population aged 18 to 34</li>
          <li><strong>Middle Age (% 35-49):</strong> % of population aged 35 to 49</li>
          <li><strong>Women:</strong> % of the population identifying as female</li>
          <li><strong>Black:</strong> % of the population identifying as Black or African American</li>
        </ul>
        <p><strong>Voter Registration (Source: FL Division of Elections, County level)</strong></p>
        <ul>
          <li><strong>Registered Dems:</strong> % of registered voters affiliated with the Democratic Party</li>
          <li><strong>NPA/Unaffiliated:</strong> % of registered voters with No Party Affiliation (NPA) or unaffiliated</li>
          <li><strong>Registered Repubs:</strong> % of registered voters affiliated with the Republican Party</li>
        </ul>
        <button class="close-button" @click="showSourcesModal = false">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

type LayerName = 'state' | 'cuban' | 'puerto_rican' | 'venezuelan' | 'colombian' | 'jamaican' | 'other_hispanic' | 'young' | 'middle_age' | 'women' | 'black' | 'democrat' | 'unaffiliated' | 'republican'

const mapEl = ref<HTMLElement | null>(null)
const loading = ref(true)
const error = ref('')
const layer = ref<LayerName>('state')
const showSourcesModal = ref(false)

let map: L.Map | null = null
let stateLayer: L.GeoJSON | null = null

let cubanLayer: L.GeoJSON | null = null
let puertoRicanLayer: L.GeoJSON | null = null
let venezuelanLayer: L.GeoJSON | null = null
let colombianLayer: L.GeoJSON | null = null
let jamaicanLayer: L.GeoJSON | null = null
let otherHispanicLayer: L.GeoJSON | null = null

let youngLayer: L.GeoJSON | null = null
let middleAgeLayer: L.GeoJSON | null = null
let womenLayer: L.GeoJSON | null = null
let blackLayer: L.GeoJSON | null = null
let democratLayer: L.GeoJSON | null = null
let unaffiliatedLayer: L.GeoJSON | null = null
let republicanLayer: L.GeoJSON | null = null

let demoData: any = null
let voterData: any = null

// Demographic specific color scales
const cubanBreaks = [0, 5, 10, 15, 25, 100]
const cubanColors = ['#f1eef6', '#d7b5d8', '#df65b0', '#dd1c77', '#980043']

const prBreaks = [0, 3, 7, 12, 20, 100]
const prColors = ['#eff3ff', '#bdd7e7', '#6baed6', '#3182bd', '#08519c']

const venBreaks = [0, 1, 3, 5, 10, 100]
const venColors = ['#edf8e9', '#bae4b3', '#74c476', '#31a354', '#006d2c']

const colBreaks = [0, 1, 3, 5, 10, 100]
const colColors = ['#ffffb2', '#fecc5c', '#fd8d3c', '#f03b20', '#bd0026']

const jamBreaks = [0, 1, 2, 4, 8, 100]
const jamColors = ['#f6eff7', '#d0d1e6', '#a6bddb', '#67a9cf', '#1c9099']

const otherHispBreaks = [0, 5, 10, 15, 20, 100]
const otherHispColors = ['#feebe2', '#fbb4b9', '#f768a1', '#c51b8a', '#7a0177']

const youngBreaks = [0, 15, 20, 25, 30, 100]
const youngColors  = ['#f7fbff', '#9ecae1', '#4292c6', '#2171b5', '#084594']

const middleAgeBreaks = [0, 15, 20, 25, 30, 100]
const middleAgeColors = ['#f7fcf5', '#e5f5e0', '#a1d99b', '#31a354', '#006d2c']

const womenBreaks = [0, 40, 45, 50, 55, 100]
const womenColors = ['#f2f0f7', '#cbc9e2', '#9e9ac8', '#756bb1', '#54278f']

const blackBreaks = [0, 5, 15, 30, 50, 100]
const blackColors = ['#ffffd4', '#fed98e', '#fe9929', '#d95f0e', '#993404']

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
    layer.value === 'cuban'          ? [cubanBreaks, cubanColors]
    : layer.value === 'puerto_rican' ? [prBreaks, prColors]
    : layer.value === 'venezuelan'   ? [venBreaks, venColors]
    : layer.value === 'colombian'    ? [colBreaks, colColors]
    : layer.value === 'jamaican'     ? [jamBreaks, jamColors]
    : layer.value === 'other_hispanic'? [otherHispBreaks, otherHispColors]
    : layer.value === 'young'        ? [youngBreaks, youngColors]
    : layer.value === 'middle_age'   ? [middleAgeBreaks, middleAgeColors]
    : layer.value === 'women'        ? [womenBreaks, womenColors]
    : layer.value === 'black'        ? [blackBreaks, blackColors]
    : layer.value === 'democrat'     ? [demBreaks, demColors]
    : layer.value === 'republican'   ? [repBreaks, repColors]
    :                                  [unaffBreaks, unaffColors]
  return colors.map((c, i) => ({
    color: c,
    label: `${breaks[i]}–${breaks[i + 1]}%`,
  }))
})

function createDemoLayer(propName: string, breaks: number[], colors: string[], title: string) {
  return L.geoJSON(demoData, {
    style: (f) => ({
      fillColor: colorFor(f?.properties[propName] ?? 0, breaks, colors),
      fillOpacity: 0.75,
      color: '#666',
      weight: 0.5,
    }),
    onEachFeature: (f, l) => {
      const p = f.properties
      l.bindTooltip(
        `<strong>${p.name || 'Tract ' + p.TRACT}</strong><br>` +
        `${title}: <b>${p[propName]}%</b><br>` +
        `Pop: ${p.total_pop?.toLocaleString() || 'N/A'}`,
        { sticky: true }
      )
    },
  })
}

function buildDemoLayers() {
  if (!map) return

  if (demoData) {
    cubanLayer = createDemoLayer('pct_cuban', cubanBreaks, cubanColors, 'Cuban')
    puertoRicanLayer = createDemoLayer('pct_puerto_rican', prBreaks, prColors, 'Puerto Rican')
    venezuelanLayer = createDemoLayer('pct_venezuelan', venBreaks, venColors, 'Venezuelan')
    colombianLayer = createDemoLayer('pct_colombian', colBreaks, colColors, 'Colombian')
    jamaicanLayer = createDemoLayer('pct_jamaican', jamBreaks, jamColors, 'Jamaican')
    otherHispanicLayer = createDemoLayer('pct_other_hispanic', otherHispBreaks, otherHispColors, 'Other Hispanic')
    youngLayer = createDemoLayer('pct_young', youngBreaks, youngColors, 'Age 18–34')
    middleAgeLayer = createDemoLayer('pct_middle_age', middleAgeBreaks, middleAgeColors, 'Middle Age (35-49)')
    womenLayer = createDemoLayer('pct_women', womenBreaks, womenColors, 'Women')
    blackLayer = createDemoLayer('pct_black', blackBreaks, blackColors, 'Black')
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
          (p.pct_dem != null ? `Registered Dems: <b>${p.pct_dem}%</b>` : 'No data'),
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
          (p.pct_rep != null ? `Registered Repubs: <b>${p.pct_rep}%</b>` : 'No data'),
          { sticky: true }
        )
      },
    })
  }
}

function setLayer(name: LayerName) {
  if (!map) return
  layer.value = name

  // Remove all demographic layers
  cubanLayer?.remove()
  puertoRicanLayer?.remove()
  venezuelanLayer?.remove()
  colombianLayer?.remove()
  jamaicanLayer?.remove()
  otherHispanicLayer?.remove()
  youngLayer?.remove()
  middleAgeLayer?.remove()
  womenLayer?.remove()
  blackLayer?.remove()

  // Remove voter layers
  democratLayer?.remove()
  unaffiliatedLayer?.remove()
  republicanLayer?.remove()
  
  // Remove state boundary
  stateLayer?.remove()

  // Add back the selected layer + state boundary where appropriate
  if (name === 'state') {
    stateLayer?.addTo(map)
  } else if (name === 'cuban') {
    cubanLayer?.addTo(map)
    stateLayer?.addTo(map)
  } else if (name === 'puerto_rican') {
    puertoRicanLayer?.addTo(map)
    stateLayer?.addTo(map)
  } else if (name === 'venezuelan') {
    venezuelanLayer?.addTo(map)
    stateLayer?.addTo(map)
  } else if (name === 'colombian') {
    colombianLayer?.addTo(map)
    stateLayer?.addTo(map)
  } else if (name === 'jamaican') {
    jamaicanLayer?.addTo(map)
    stateLayer?.addTo(map)
  } else if (name === 'other_hispanic') {
    otherHispanicLayer?.addTo(map)
    stateLayer?.addTo(map)
  } else if (name === 'young') {
    youngLayer?.addTo(map)
    stateLayer?.addTo(map)
  } else if (name === 'middle_age') {
    middleAgeLayer?.addTo(map)
    stateLayer?.addTo(map)
  } else if (name === 'women') {
    womenLayer?.addTo(map)
    stateLayer?.addTo(map)
  } else if (name === 'black') {
    blackLayer?.addTo(map)
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
  font-size: 11px;
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
.cuban-swatch         { background: #dd1c77; }
.puerto_rican-swatch  { background: #3182bd; }
.venezuelan-swatch    { background: #31a354; }
.colombian-swatch     { background: #f03b20; }
.jamaican-swatch      { background: #67a9cf; }
.other_hispanic-swatch{ background: #c51b8a; }

.young-swatch         { background: #2171b5; }
.middle_age-swatch    { background: #31a354; }
.women-swatch         { background: #756bb1; }
.black-swatch         { background: #d95f0e; }
.democrat-swatch      { background: #31a354; }
.unaffiliated-swatch  { background: #fd8d3c; }
.republican-swatch    { background: #fb6a4a; }

.map-wrapper {
  position: relative;
  width: 100%;
  max-width: 900px;
}

#fl-map {
  width: 100%;
  height: 600px;
  border: 1px solid #ccc;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.sources-button {
  position: absolute;
  top: 50%;
  left: 20px;
  transform: translateY(-50%);
  z-index: 1000;
  cursor: pointer;
  padding: 6px 14px;
  border-radius: 6px;
  border: 1px solid #ddd;
  font-size: 11px;
  display: flex;
  align-items: center;
  gap: 8px;
  user-select: none;
  background: #fff;
  transition: all 0.2s;
  box-shadow: 0 2px 5px rgba(0,0,0,0.15);
  color: #333;
  text-decoration: none;
}

.sources-button:hover {
  background: #f8f9fa;
  box-shadow: 0 4px 8px rgba(0,0,0,0.2);
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

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.modal-content {
  background: #fff;
  padding: 2rem;
  border-radius: 8px;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  text-align: left;
  box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}

.modal-content h3 {
  margin-top: 0;
  color: #2c3e50;
}

.modal-content ul {
  margin-bottom: 1.5rem;
  padding-left: 1.5rem;
}

.modal-content li {
  margin-bottom: 0.25rem;
}

.close-button {
  margin-top: 1rem;
  padding: 8px 16px;
  background: #2c3e50;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
  transition: background 0.2s;
}

.close-button:hover {
  background: #1a252f;
}
</style>
