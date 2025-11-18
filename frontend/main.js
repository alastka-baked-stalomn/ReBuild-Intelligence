import * as THREE from './node_modules/three/build/three.module.js';

const APP_VERSION = 'v0.6.0';
const form = document.getElementById('project-form');
const statusEl = document.getElementById('status');
const resultsEl = document.getElementById('results');
const versionEl = document.getElementById('app-version');
const testButton = document.getElementById('load-test-data');
const exportButton = document.getElementById('export-obj');
const apiBase =
  document.body.dataset.apiBase || `${window.location.protocol}//${window.location.hostname}:8000`;

if (versionEl) {
  versionEl.textContent = APP_VERSION;
}

const canvas = document.getElementById('scene');
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(60, 1, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(window.devicePixelRatio || 1);
renderer.setClearColor(new THREE.Color('#020408'));

camera.position.set(0, 2.5, 8);
const sun = new THREE.DirectionalLight('#ffffff', 1.2);
sun.position.set(4, 5, 6);
scene.add(sun);
scene.add(new THREE.AmbientLight('#7fb9ff', 0.45));

const pieceState = { meshes: [] };

function resizeRenderer() {
  const target = renderer.domElement;
  const width = target.clientWidth || target.parentElement?.clientWidth || target.width;
  const height = target.clientHeight || target.parentElement?.clientHeight || target.height;
  if (!width || !height) {
    return;
  }
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

window.addEventListener('resize', resizeRenderer);
resizeRenderer();

function clearPieces() {
  pieceState.meshes.forEach((mesh) => scene.remove(mesh));
  pieceState.meshes = [];
}

function normalizeCenter(center = {}, idx = 0) {
  const fallbackX = idx * 0.65 - 2;
  return {
    x: typeof center.x === 'number' ? center.x : fallbackX,
    y: typeof center.y === 'number' ? center.y : 0.6 + idx * 0.05,
    z: typeof center.z === 'number' ? center.z : 0,
  };
}

function addPieces(pieces = []) {
  clearPieces();
  if (!Array.isArray(pieces) || pieces.length === 0) {
    return;
  }
  pieces.forEach((piece, idx) => {
    const geometry = new THREE.BoxGeometry(0.5 + idx * 0.02, 0.35 + idx * 0.015, 0.5);
    const material = new THREE.MeshStandardMaterial({ color: '#4bd3ff', metalness: 0.25, roughness: 0.35 });
    material.color.offsetHSL(idx * 0.03, 0, 0);
    const mesh = new THREE.Mesh(geometry, material);
    const center = normalizeCenter(piece?.center_of_mass, idx);
    mesh.position.set(center.x, center.y, center.z);
    pieceState.meshes.push(mesh);
    scene.add(mesh);
  });
}

function animate() {
  requestAnimationFrame(animate);
  pieceState.meshes.forEach((mesh, idx) => {
    mesh.rotation.y += 0.008 + idx * 0.0015;
    mesh.rotation.x = 0.2 + idx * 0.003;
  });
  renderer.render(scene, camera);
}
animate();

function createPlaceholder(message) {
  const paragraph = document.createElement('p');
  paragraph.className = 'placeholder';
  paragraph.textContent = message;
  return paragraph;
}

function createList(items = [], emptyLabel = 'No data yet') {
  if (!items.length) {
    return createPlaceholder(emptyLabel);
  }
  const list = document.createElement('ul');
  items.forEach((item) => {
    const li = document.createElement('li');
    li.textContent = typeof item === 'string' ? item : JSON.stringify(item);
    list.appendChild(li);
  });
  return list;
}

function createKeyValueList(source = {}, emptyLabel = 'No values computed yet') {
  const entries = Object.entries(source || {});
  if (!entries.length) {
    return createPlaceholder(emptyLabel);
  }
  const dl = document.createElement('dl');
  entries.forEach(([key, value]) => {
    const dt = document.createElement('dt');
    dt.textContent = key;
    const dd = document.createElement('dd');
    dd.textContent = value == null ? '—' : String(value);
    dl.append(dt, dd);
  });
  return dl;
}

function createProjectFormData() {
  const formData = new FormData(form);
  const assetInput = form.querySelector('input[name="asset_files"]');
  const scanInput = form.querySelector('input[name="scan_files"]');

  if (assetInput?.files?.length) {
    formData.delete('asset_files');
    Array.from(assetInput.files).forEach((file) => formData.append('asset_files', file));
  }
  if (scanInput?.files?.length) {
    formData.delete('scan_files');
    Array.from(scanInput.files).forEach((file) => formData.append('scan_files', file));
  }

  return formData;
}

function createPieceTable(pieces = []) {
  if (!pieces.length) {
    return createPlaceholder('No piece plans yet.');
  }
  const table = document.createElement('table');
  table.className = 'piece-table';
  const head = document.createElement('tr');
  ['Piece', 'Mass (kg)', 'Reuse score', 'Cut angle', 'Waste↓'].forEach((label) => {
    const th = document.createElement('th');
    th.textContent = label;
    head.appendChild(th);
  });
  table.appendChild(head);
  pieces.forEach((piece) => {
    const row = document.createElement('tr');
    const cells = [
      piece?.piece_id || 'piece',
      piece?.mass_kg ?? '—',
      piece?.reuse_score ?? '—',
      piece?.optimal_cut_angle ?? '—',
      piece?.waste_reduction ?? '—',
    ];
    cells.forEach((value) => {
      const cell = document.createElement('td');
      cell.textContent = String(value);
      row.appendChild(cell);
    });
    table.appendChild(row);
  });
  return table;
}

function createCard(title, bodyContent) {
  const card = document.createElement('div');
  card.className = 'card';
  const heading = document.createElement('h3');
  heading.textContent = title;
  card.appendChild(heading);
  card.appendChild(bodyContent);
  return card;
}

function renderCards(result) {
  resultsEl.innerHTML = '';
  const reuse = result?.reuse_breakdown || {};
  const feasibility = result?.material_feasibility || {};
  const env = result?.environmental_impact || result?.pollution_model || {};
  const disasters = result?.disaster_simulation || {};
  const structural = result?.structural_analysis || {};
  const fea = result?.finite_element_analysis || {};
  const cost = result?.cost_and_carbon || {};
  const pieces = Array.isArray(result?.piece_plans) ? result.piece_plans : [];
  const recommendations = Array.isArray(result?.recommendations) ? result.recommendations : [];
  const cutting = Array.isArray(result?.cutting_instructions) ? result.cutting_instructions : [];
  const aiText = typeof result?.ai_engineering === 'string' && result.ai_engineering.trim().length > 0
    ? result.ai_engineering
    : 'AI reasoning unavailable. Configure OPENAI_API_KEY on the backend to enable it.';

  const summaryParagraph = document.createElement('p');
  summaryParagraph.textContent = `${
    result?.project_name || 'Project'
  } — ${result?.summary || 'Deterministic metrics ready.'}`;
  resultsEl.appendChild(createCard('Summary', summaryParagraph));
  resultsEl.appendChild(createCard('AI engineering intelligence', buildAiBlock(aiText)));
  resultsEl.appendChild(createCard('Piece plans', createPieceTable(pieces)));
  resultsEl.appendChild(createCard('Reuse breakdown', createKeyValueList(reuse)));
  resultsEl.appendChild(createCard('Disaster simulations', createKeyValueList(disasters)));
  resultsEl.appendChild(createCard('Structural analysis', createKeyValueList(structural)));
  resultsEl.appendChild(createCard('Finite element analysis', createKeyValueList(fea)));
  resultsEl.appendChild(createCard('Environmental impact', createKeyValueList(env)));
  resultsEl.appendChild(createCard('Material feasibility', buildFeasibility(feasibility)));
  resultsEl.appendChild(createCard('Cost & CO₂', createKeyValueList(cost)));
  resultsEl.appendChild(createCard('Recommendations', createList(recommendations, 'No recommendations yet.')));
  resultsEl.appendChild(createCard('KUKA cutting plan', createList(cutting, 'No cutting steps yet.')));
}

function buildAiBlock(text) {
  const wrapper = document.createElement('div');
  text.split(/\n+/).forEach((line) => {
    const trimmed = line.trim();
    if (!trimmed) return;
    const paragraph = document.createElement('p');
    paragraph.textContent = trimmed;
    wrapper.appendChild(paragraph);
  });
  if (!wrapper.children.length) {
    wrapper.appendChild(createPlaceholder(text));
  }
  return wrapper;
}

function buildFeasibility(feasibility) {
  if (!feasibility || typeof feasibility !== 'object') {
    return createPlaceholder('Feasibility metrics unavailable.');
  }
  const container = document.createElement('div');
  const reuseList = createList(feasibility.reusable_components || [], 'No reusable components listed.');
  const newList = createList(feasibility.needs_new_components || [], 'No new components listed.');
  const changeList = createList(feasibility.suggested_plan_changes || [], 'No change log yet.');
  const ratio = document.createElement('p');
  ratio.textContent = `Recycled ratio: ${feasibility.recycled_ratio ?? 0} | Roof new %: ${
    feasibility.roof_new_pct ?? 0
  }`;
  const segments = [
    { title: 'Reusable', node: reuseList },
    { title: 'Needs new', node: newList },
    { title: 'Suggested changes', node: changeList },
  ];
  segments.forEach(({ title, node }) => {
    const block = document.createElement('div');
    block.className = 'feasibility-block';
    const heading = document.createElement('h4');
    heading.textContent = title;
    block.appendChild(heading);
    block.appendChild(node);
    container.appendChild(block);
  });
  container.appendChild(ratio);
  return container;
}

if (testButton) {
  const demoPayload = {
    project_name: 'Circular Habitat Test',
    description:
      'Adaptive reuse of roman-influenced civic hall using mixed masonry and timber bays. KUKA cells available.',
    transport_plan: 'Hybrid trucks + conveyor shuttles',
    human_built: 'true',
    site_location: 'Amsterdam, NL',
    soil_profile: 'Dense rock with shallow aquifer',
    hazard_profile: 'Flood + storm surge',
    demolition_notes:
      'Selective demo with concrete shear walls, salvaged brick, structural timber trusses ready for scanning.',
    lidar_notes: 'High-resolution LiDAR sweep (5mm) completed Oct 2025; includes void mapping.',
  };

  testButton.addEventListener('click', () => {
    Object.entries(demoPayload).forEach(([name, value]) => {
      const field = form.querySelector(`[name="${name}"]`);
      if (!field) return;
      field.value = value;
    });
    setStatus('Loaded representative test data. Adjust if needed, then run the algorithm.');
  });
}

if (exportButton) {
  exportButton.addEventListener('click', async () => {
    setStatus('Preparing OBJ export...');
    try {
      const formData = createProjectFormData();
      const response = await fetch(`${apiBase}/api/export-obj`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `Export failed with status ${response.status}`);
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'pieces.obj';
      a.click();
      URL.revokeObjectURL(url);
      setStatus('OBJ export downloaded.');
    } catch (error) {
      console.error(error);
      const message = error instanceof Error ? error.message : 'Unexpected error';
      setStatus(`Failed to export OBJ. ${message}`, true);
    }
  });
}

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.toggle('error', Boolean(isError));
}

async function submitForm(event) {
  event.preventDefault();
  setStatus('Uploading and running simulations...');
  resultsEl.innerHTML = '';

  const formData = createProjectFormData();

  try {
    const response = await fetch(`${apiBase}/api/process`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `API returned ${response.status}`);
    }
    const data = await response.json().catch(() => {
      throw new Error('API returned invalid JSON.');
    });
    setStatus('Simulation ready.');
    renderCards(data || {});
    addPieces(data?.piece_plans || []);
  } catch (error) {
    console.error(error);
    const message = error instanceof Error ? error.message : 'Unexpected error';
    setStatus(`Failed to reach backend. ${message}`, true);
  }
}

form.addEventListener('submit', submitForm);
