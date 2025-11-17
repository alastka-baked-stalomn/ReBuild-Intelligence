const APP_VERSION = 'v0.5.0';
const form = document.getElementById('project-form');
const statusEl = document.getElementById('status');
const resultsEl = document.getElementById('results');
const versionEl = document.getElementById('app-version');
const testButton = document.getElementById('load-test-data');
const apiBase =
  document.body.dataset.apiBase || `${window.location.protocol}//${window.location.hostname}:8000`;

if (versionEl) {
  versionEl.textContent = APP_VERSION;
}

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(60, 1, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('scene'), antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setClearColor('#020408');
const light = new THREE.DirectionalLight('#ffffff', 1.1);
light.position.set(2, 3, 4);
scene.add(light);
scene.add(new THREE.AmbientLight('#93b7ff', 0.3));
camera.position.set(3, 3, 6);

const controls = { objects: [] };

function resizeRenderer() {
  const canvas = renderer.domElement;
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  if (width === 0 || height === 0) return;
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

window.addEventListener('resize', resizeRenderer);
resizeRenderer();

function clearScene() {
  controls.objects.forEach((mesh) => scene.remove(mesh));
  controls.objects = [];
}

function addPieces(pieces) {
  clearScene();
  const material = new THREE.MeshStandardMaterial({ color: '#4bd3ff', metalness: 0.3, roughness: 0.2 });
  pieces.forEach((piece, idx) => {
    const geometry = new THREE.BoxGeometry(0.6, 0.4 + idx * 0.03, 0.6);
    const mesh = new THREE.Mesh(geometry, material.clone());
    mesh.position.set(piece.center_of_mass.x, piece.center_of_mass.y * 0.2, piece.center_of_mass.z);
    mesh.material.color.offsetHSL(idx * 0.07, 0, 0);
    scene.add(mesh);
    controls.objects.push(mesh);
  });
}

function renderLoop() {
  requestAnimationFrame(renderLoop);
  controls.objects.forEach((mesh, idx) => {
    mesh.rotation.y += 0.003 + idx * 0.0005;
  });
  renderer.render(scene, camera);
}
renderLoop();

function renderCards(result) {
  resultsEl.innerHTML = '';
  const reuse = result.reuse_breakdown || {};
  const feasibility = result.material_feasibility || {};
  const env = result.environmental_impact || result.pollution_model || {};
  const fea = result.finite_element_analysis || {};
  const cost = result.cost_and_carbon || {};
  const aiSummary = (result.ai_engineering || '').replace(/\n/g, '<br />');
  const segments = [
    {
      title: 'Summary',
      content: `<strong>${result.project_name}</strong>: ${result.summary}`,
    },
    {
      title: 'AI Engineering Intelligence',
      content:
        aiSummary ||
        'AI reasoning unavailable. Ensure the backend has OPENAI_API_KEY configured so GPT output can be generated.',
    },
    {
      title: 'Reuse breakdown',
      content: `Reused: ${reuse.reused_pct}% | New: ${reuse.new_pct}% | Roof new: ${reuse.roof_new_pct}%`,
    },
    {
      title: 'Material feasibility',
      content: `Reusable: ${(feasibility.reusable_components || []).join(', ') || 'TBD'}<br />
        Needs new: ${(feasibility.needs_new_components || []).join(', ') || 'Minimal'}<br />
        Suggested changes: ${(feasibility.suggested_plan_changes || []).join(' • ')}`,
    },
    {
      title: 'Simulations',
      content: Object.entries(result.disaster_simulation)
        .map(([k, v]) => `<div><strong>${k}:</strong> ${v}</div>`)
        .join(''),
    },
    {
      title: 'Structural analysis',
      content: Object.entries(result.structural_analysis)
        .map(([k, v]) => `<div>${k}: <strong>${v}</strong></div>`)
        .join(''),
    },
    {
      title: 'Finite element analysis',
      content: Object.entries(fea)
        .map(([k, v]) => `<div>${k}: <strong>${v}</strong></div>`)
        .join(''),
    },
    {
      title: 'Environmental impact (sound + light)',
      content: Object.entries(env)
        .map(([k, v]) => `<div>${k}: <strong>${v}</strong></div>`)
        .join(''),
    },
    {
      title: 'Cost & carbon analysis',
      content: `<div>Baseline: $${cost.baseline_cost}</div>
        <div>Reclaimed savings: $${cost.reclaimed_savings}</div>
        <div>Net cost: $${cost.net_cost}</div>
        <div>CO₂ saved: ${cost.co2_saved_tons} t</div>
        <div>Recycled material value: $${cost.recycled_material_value}</div>`,
    },
    {
      title: 'Recommendations',
      content: result.recommendations.map((r) => `<div>${r}</div>`).join(''),
    },
  ];

  segments.forEach((segment) => {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `<h3>${segment.title}</h3><div>${segment.content}</div>`;
    resultsEl.appendChild(card);
  });

  const cuttingCard = document.createElement('div');
  cuttingCard.className = 'card';
  cuttingCard.innerHTML = `<h3>KUKA cutting plan</h3>${result.cutting_instructions
    .map((line) => `<div>${line}</div>`)
    .join('')}`;
  resultsEl.appendChild(cuttingCard);
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
      if (field.tagName === 'SELECT' || field.tagName === 'INPUT' || field.tagName === 'TEXTAREA') {
        field.value = value;
      }
    });
    statusEl.textContent = 'Loaded representative test data. Adjust if needed, then run the algorithm.';
  });
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  statusEl.textContent = 'Uploading + running simulations...';
  resultsEl.innerHTML = '';

  const formData = new FormData(form);
  const assetInput = form.querySelector('input[name="asset_files"]');
  const scanInput = form.querySelector('input[name="scan_files"]');

  if (assetInput?.files) {
    for (const file of assetInput.files) {
      formData.append('asset_files', file);
    }
  }
  if (scanInput?.files) {
    for (const file of scanInput.files) {
      formData.append('scan_files', file);
    }
  }

  try {
    const response = await fetch(`${apiBase}/api/process`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      const message = await response.text();
      throw new Error(message || 'API error');
    }
    const data = await response.json();
    statusEl.textContent = 'Simulation ready';
    renderCards(data);
    addPieces(data.piece_plans || []);
  } catch (error) {
    console.error(error);
    const message = error instanceof Error ? error.message : '';
    statusEl.textContent = `Failed to reach backend. ${message}`.trim();
  }
});
