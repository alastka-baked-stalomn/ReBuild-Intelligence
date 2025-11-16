const form = document.getElementById('project-form');
const statusEl = document.getElementById('status');
const resultsEl = document.getElementById('results');
const apiBase =
  document.body.dataset.apiBase || `${window.location.protocol}//${window.location.hostname}:8000`;

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
  const segments = [
    {
      title: 'Summary',
      content: `<strong>${result.project_name}</strong>: ${result.summary}`,
    },
    {
      title: 'Reuse breakdown',
      content: `Reused: ${result.reuse_breakdown.reused_pct}% | New: ${result.reuse_breakdown.new_pct}% | CO₂ saved: ${result.cost_and_carbon.co2_saved_tons} t`,
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

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  statusEl.textContent = 'Uploading + running simulations...';
  resultsEl.innerHTML = '';

  const formData = new FormData(form);

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
    statusEl.textContent =
      'Failed to reach backend. Check server logs. ' + (error instanceof Error ? error.message : '');
  }
});
