// RoadSoS — Three.js 3D Background
// Animated road network with glowing nodes

(function() {
  try {
  const canvas = document.getElementById("bg-canvas");
  if (!canvas) return;

  const scene    = new THREE.Scene();
  const camera   = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setClearColor(0x0D1B2A, 0.0); // fully transparent — body bg shows through
  camera.position.set(0, 8, 18);
  camera.lookAt(0, 0, 0);

  // Fog
  scene.fog = new THREE.FogExp2(0x0d1b2a, 0.04);

  // ── Grid (road network) ──────────────────────────────────────────────────
  const gridMat = new THREE.LineBasicMaterial({ color: 0x1a3a5c, transparent: true, opacity: 0.4 });
  const gridGeo = new THREE.BufferGeometry();
  const gridPts = [];
  for (let i = -20; i <= 20; i += 2) {
    gridPts.push(-20, 0, i,  20, 0, i);
    gridPts.push(i, 0, -20,  i, 0, 20);
  }
  gridGeo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(gridPts), 3));
  scene.add(new THREE.LineSegments(gridGeo, gridMat));

  // ── Glowing node spheres (hospitals, police etc) ─────────────────────────
  const nodePositions = [
    [-6,0,-4], [4,0,-6], [-3,0,5], [7,0,3], [-8,0,8],
    [2,0,-10], [-5,0,-12], [9,0,-3], [0,0,7], [-10,0,2],
  ];
  const nodeColors = [0x00bcd4, 0xe53935, 0x43a047, 0x1565c0, 0xff8f00];
  const nodes = [];

  nodePositions.forEach(([x, y, z], i) => {
    const color = nodeColors[i % nodeColors.length];
    // Core sphere
    const geo  = new THREE.SphereGeometry(0.18, 16, 16);
    const mat  = new THREE.MeshBasicMaterial({ color });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(x, y, z);
    scene.add(mesh);

    // Glow ring
    const ringGeo = new THREE.RingGeometry(0.28, 0.42, 32);
    const ringMat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.3, side: THREE.DoubleSide });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = -Math.PI / 2;
    ring.position.set(x, 0.01, z);
    scene.add(ring);

    nodes.push({ mesh, ring, mat, ringMat, phase: Math.random() * Math.PI * 2, speed: 0.5 + Math.random() });
  });

  // ── Animated data packets (moving dots on roads) ──────────────────────────
  const packetCount = 30;
  const packetGeo   = new THREE.SphereGeometry(0.08, 8, 8);
  const packets     = [];

  for (let i = 0; i < packetCount; i++) {
    const isHoriz = Math.random() > 0.5;
    const lane    = (Math.floor(Math.random() * 10) - 5) * 2;
    const mat     = new THREE.MeshBasicMaterial({
      color: [0x00bcd4, 0xe53935, 0xffffff][Math.floor(Math.random() * 3)],
      transparent: true, opacity: 0.8,
    });
    const mesh = new THREE.Mesh(packetGeo, mat);
    const start = (Math.random() - 0.5) * 40;
    mesh.position.set(
      isHoriz ? start : lane,
      0.12,
      isHoriz ? lane   : start
    );
    scene.add(mesh);
    packets.push({
      mesh, mat, isHoriz, lane,
      pos: start,
      speed: (Math.random() * 0.06 + 0.03) * (Math.random() > 0.5 ? 1 : -1),
    });
  }

  // ── Floating triangles (RoadSoS logo motif) ───────────────────────────────
  const triGeo = new THREE.ConeGeometry(0.3, 0.6, 3);
  const tris   = [];
  for (let i = 0; i < 8; i++) {
    const mat  = new THREE.MeshBasicMaterial({
      color: 0xe53935, transparent: true, opacity: 0.15 + Math.random() * 0.2,
      wireframe: true,
    });
    const mesh = new THREE.Mesh(triGeo, mat);
    mesh.position.set(
      (Math.random() - 0.5) * 30,
      1 + Math.random() * 4,
      (Math.random() - 0.5) * 30
    );
    mesh.rotation.x = Math.random() * Math.PI;
    mesh.rotation.z = Math.random() * Math.PI;
    scene.add(mesh);
    tris.push({ mesh, mat, vy: (Math.random()-0.5)*0.005, rx: (Math.random()-0.5)*0.01 });
  }

  // ── Connection lines between nodes ────────────────────────────────────────
  const lineMat = new THREE.LineBasicMaterial({ color: 0x1565c0, transparent: true, opacity: 0.25 });
  for (let i = 0; i < nodePositions.length - 1; i++) {
    const [x1,,z1] = nodePositions[i];
    const [x2,,z2] = nodePositions[i+1];
    const pts = [new THREE.Vector3(x1,0.05,z1), new THREE.Vector3(x2,0.05,z2)];
    const geo = new THREE.BufferGeometry().setFromPoints(pts);
    scene.add(new THREE.Line(geo, lineMat));
  }

  // ── Animate ───────────────────────────────────────────────────────────────
  const clock = new THREE.Clock();
  function animate() {
    requestAnimationFrame(animate);
    const t = clock.getElapsedTime();

    // Pulse nodes
    nodes.forEach(n => {
      const pulse = Math.sin(t * n.speed + n.phase);
      n.mat.opacity = 0.7 + pulse * 0.3;
      n.ringMat.opacity = 0.1 + (pulse + 1) * 0.15;
      n.ring.scale.setScalar(1 + (pulse + 1) * 0.2);
    });

    // Move packets
    packets.forEach(p => {
      p.pos += p.speed;
      if (p.pos > 20) p.pos = -20;
      if (p.pos < -20) p.pos = 20;
      if (p.isHoriz) p.mesh.position.x = p.pos;
      else           p.mesh.position.z = p.pos;
      p.mat.opacity = 0.4 + Math.sin(t * 3 + p.pos) * 0.4;
    });

    // Float triangles
    tris.forEach(tri => {
      tri.mesh.position.y += tri.vy;
      tri.mesh.rotation.x += tri.rx;
      if (tri.mesh.position.y > 6 || tri.mesh.position.y < 0.5) tri.vy *= -1;
    });

    // Slow camera drift
    camera.position.x = Math.sin(t * 0.05) * 3;
    camera.position.z = 18 + Math.cos(t * 0.07) * 2;
    camera.lookAt(0, 0, 0);

    renderer.render(scene, camera);
  }
  animate();

  // Resize
  window.addEventListener("resize", () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });
  } catch(e) {
    console.warn('[3D BG] Three.js error:', e);
  }
})();
