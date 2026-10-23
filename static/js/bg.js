(function () {
  'use strict';

  var THREE_CDN = 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js';
  var GLTF_CDN = 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/js/loaders/GLTFLoader.js';

  function loadScript(src, onload) {
    var script = document.createElement('script');
    script.src = src;
    script.async = true;
    script.crossOrigin = 'anonymous';
    script.onload = onload;
    document.head.appendChild(script);
  }

  // Home scene: cyan wireframe globe, glowing amber surface dots, tilted satellite ring, and optional robot.glb
  function buildHomeScene(THREE, group, scale, isDesktop) {
    var globeGeo = new THREE.SphereGeometry(1.55, 22, 16);
    var globeMat = new THREE.MeshBasicMaterial({ color: 0x22d3ee, wireframe: true, transparent: true, opacity: 0.24 });
    group.add(new THREE.Mesh(globeGeo, globeMat));

    var dotCount = Math.max(40, Math.round(160 * scale));
    var dotPositions = new Float32Array(dotCount * 3);
    for (var i = 0; i < dotCount; i++) {
      var phi = Math.acos(2 * Math.random() - 1);
      var theta = 2 * Math.PI * Math.random();
      var r = 1.57;
      dotPositions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      dotPositions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      dotPositions[i * 3 + 2] = r * Math.cos(phi);
    }
    var dotGeo = new THREE.BufferGeometry();
    dotGeo.setAttribute('position', new THREE.BufferAttribute(dotPositions, 3));
    var dotMat = new THREE.PointsMaterial({ color: 0xf59e0b, size: 0.055, transparent: true, opacity: 0.9 });
    group.add(new THREE.Points(dotGeo, dotMat));

    var ringGeo = new THREE.TorusGeometry(2.35, 0.012, 8, 96);
    var ringMat = new THREE.MeshBasicMaterial({ color: 0x22d3ee, transparent: true, opacity: 0.45 });
    var ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = Math.PI / 2.8;
    ring.rotation.y = Math.PI / 7;
    group.add(ring);

    var satGeo = new THREE.SphereGeometry(0.06, 8, 8);
    var satMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b });
    var sat = new THREE.Mesh(satGeo, satMat);
    sat.position.set(2.35, 0, 0);
    ring.add(sat);

    group.position.x = isDesktop ? 2.1 : 0;
    tryLoadRobot(THREE, group);
    return function (t) {
      ring.rotation.z = t * 0.35;
    };
  }

  // Optional robot .glb (< 2 MB) from /static/models/robot.glb that turns toward the cursor
  function tryLoadRobot(THREE, group) {
    if (!window.fetch) return;
    fetch('/static/models/robot.glb', { method: 'HEAD' })
      .then(function (res) {
        var size = parseInt(res.headers.get('content-length') || '0', 10);
        if (!res.ok || (size > 0 && size > 2 * 1024 * 1024)) return;
        loadScript(GLTF_CDN, function () {
          if (!THREE.GLTFLoader) return;
          new THREE.GLTFLoader().load('/static/models/robot.glb', function (gltf) {
            var model = gltf.scene;
            model.scale.set(0.6, 0.6, 0.6);
            model.position.set(-0.4, -0.5, 1.2);
            group.add(model);
          });
        });
      })
      .catch(function () {});
  }

  // News scene: lightweight dim cyan particle field with larger amber signal dots
  function buildNewsScene(THREE, group, scale) {
    group.add(makeParticles(THREE, Math.round(85 * scale), 9, 0x22d3ee, 0.035, 0.38));
    group.add(makeParticles(THREE, Math.round(14 * scale), 8, 0xf59e0b, 0.075, 0.75));
    return null;
  }

  // Blog index scene: violet wireframe crystal surrounded by soft particles
  function buildBlogScene(THREE, group, scale) {
    var crystalGeo = new THREE.OctahedronGeometry(1.4, 0);
    var crystalMat = new THREE.MeshBasicMaterial({ color: 0x8b5cf6, wireframe: true, transparent: true, opacity: 0.42 });
    var crystal = new THREE.Mesh(crystalGeo, crystalMat);
    group.add(crystal);
    group.add(makeParticles(THREE, Math.round(65 * scale), 8, 0x8b5cf6, 0.04, 0.45));
    return function (t) {
      crystal.rotation.y = t * 0.2;
      crystal.rotation.x = Math.sin(t * 0.4) * 0.15;
    };
  }

  // Dashboard scene: three tilted orbit rings in cyan and amber
  function buildDashboardScene(THREE, group) {
    var specs = [
      { r: 1.5, color: 0x22d3ee, rx: 1.1, ry: 0.3, speed: 0.22 },
      { r: 2.0, color: 0xf59e0b, rx: -0.8, ry: 0.6, speed: -0.16 },
      { r: 2.5, color: 0x22d3ee, rx: 0.5, ry: -0.9, speed: 0.12 }
    ];
    var rings = specs.map(function (s) {
      var mesh = new THREE.Mesh(
        new THREE.TorusGeometry(s.r, 0.012, 8, 90),
        new THREE.MeshBasicMaterial({ color: s.color, transparent: true, opacity: 0.42 })
      );
      mesh.rotation.x = s.rx;
      mesh.rotation.y = s.ry;
      mesh.userData.speed = s.speed;
      group.add(mesh);
      return mesh;
    });
    return function (t) {
      rings.forEach(function (r) { r.rotation.z = t * r.userData.speed; });
    };
  }

  // Calm default scene: subtle slate and cyan particles for articles, auth, and info pages
  function buildCalmScene(THREE, group, scale) {
    group.add(makeParticles(THREE, Math.round(75 * scale), 9, 0x64748b, 0.035, 0.36));
    group.add(makeParticles(THREE, Math.round(20 * scale), 8, 0x22d3ee, 0.04, 0.32));
    return null;
  }

  function makeParticles(THREE, count, spread, color, size, opacity) {
    var n = Math.max(12, count);
    var pos = new Float32Array(n * 3);
    for (var i = 0; i < n * 3; i++) {
      pos[i] = (Math.random() - 0.5) * spread;
    }
    var geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    var mat = new THREE.PointsMaterial({ color: color, size: size, transparent: true, opacity: opacity });
    return new THREE.Points(geo, mat);
  }

  function initNovaBackground() {
    if (!document.body) return;
    var sceneType = (document.body.getAttribute('data-scene') || 'calm').toLowerCase();
    var existingCanvas = document.getElementById('nova-bg-canvas');
    if (sceneType === 'none') {
      if (existingCanvas) existingCanvas.remove();
      return;
    }

    var canvas = existingCanvas || document.createElement('canvas');
    if (!existingCanvas) {
      canvas.id = 'nova-bg-canvas';
      canvas.setAttribute('aria-hidden', 'true');
      document.body.insertBefore(canvas, document.body.firstChild);
    }
    var baseOpacity = sceneType === 'home' ? 0.9 : 0.58;
    canvas.style.opacity = String(baseOpacity);

    loadScript(THREE_CDN, function () {
      var THREE = window.THREE;
      if (!THREE) return;

      var renderer;
      try {
        renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true, powerPreference: 'low-power' });
      } catch (e) {
        return;
      }
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      renderer.setSize(window.innerWidth, window.innerHeight);

      var scene = new THREE.Scene();
      var camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 100);
      camera.position.z = 5.5;

      var group = new THREE.Group();
      scene.add(group);

      var scale = window.innerWidth < 700 ? 0.4 : 1;
      var isDesktop = window.innerWidth >= 960;
      var tickScene = null;

      if (sceneType === 'home') tickScene = buildHomeScene(THREE, group, scale, isDesktop);
      else if (sceneType === 'news') tickScene = buildNewsScene(THREE, group, scale);
      else if (sceneType === 'blog') tickScene = buildBlogScene(THREE, group, scale);
      else if (sceneType === 'dashboard') tickScene = buildDashboardScene(THREE, group);
      else tickScene = buildCalmScene(THREE, group, scale);

      var reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      var isTouch = window.matchMedia && window.matchMedia('(pointer: coarse)').matches;
      var targetX = 0;
      var targetY = 0;

      if (!isTouch) {
        window.addEventListener('pointermove', function (e) {
          targetX = (e.clientX / window.innerWidth - 0.5) * 0.55;
          targetY = (e.clientY / window.innerHeight - 0.5) * 0.45;
        }, { passive: true });
      }

      if (sceneType === 'home') {
        window.addEventListener('scroll', function () {
          var fade = Math.max(0, 1 - window.scrollY / (window.innerHeight * 0.85));
          canvas.style.opacity = String((baseOpacity * fade).toFixed(3));
        }, { passive: true });
      }

      window.addEventListener('resize', function () {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
        if (sceneType === 'home') group.position.x = window.innerWidth >= 960 ? 2.1 : 0;
      }, { passive: true });

      var start = performance.now();
      function animate(now) {
        requestAnimationFrame(animate);
        if (document.hidden) return;
        var t = (now - start) * 0.001;

        if (!reducedMotion) {
          group.rotation.y += 0.0012;
          group.rotation.x += 0.0004;
          if (tickScene) tickScene(t);
        }

        if (!isTouch) {
          group.rotation.y += (targetX - group.rotation.y) * 0.03;
          group.rotation.x += (targetY - group.rotation.x) * 0.03;
          camera.position.x += (targetX * 0.45 - camera.position.x) * 0.04;
          camera.position.y += (-targetY * 0.35 - camera.position.y) * 0.04;
        }

        renderer.render(scene, camera);
      }
      requestAnimationFrame(animate);
    });
  }

  if (document.readyState === 'complete') {
    initNovaBackground();
  } else {
    window.addEventListener('load', initNovaBackground, { once: true });
  }
})();
