// Auto-dismiss flash messages after 5s
document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => el.remove(), 5000);
  });

  // Modal helpers  
  function openModal(id) {
    document.getElementById(id).classList.add('open');
  }
  
  function closeModal(id) {
    document.getElementById(id).classList.remove('open');
  }
  
  // Close modal on overlay click
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', function(e) {
      if (e.target === this) this.classList.remove('open');
    });
  });
  
  // Confirm delete forms
  document.querySelectorAll('form[data-confirm]').forEach(form => {
    form.addEventListener('submit', function(e) {
      if (!confirm(this.dataset.confirm || 'Are you sure?')) {
        e.preventDefault();
      }
    });
  });
  
  // Simple chart renderer (bar + line) using canvas — no library
  function drawBarChart(canvasId, labels, values, color = '#15803d') {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width  = canvas.offsetWidth;
    const H = canvas.height = 180;
    ctx.clearRect(0, 0, W, H);
    const pad = { top: 16, right: 16, bottom: 36, left: 42 };
    const cW  = W - pad.left - pad.right;
    const cH  = H - pad.top  - pad.bottom;
    const max = Math.max(...values, 1);
  
    // Grid lines
    ctx.strokeStyle = '#f3f4f6';
    ctx.lineWidth   = 1;
    [0, 0.25, 0.5, 0.75, 1].forEach(t => {
      const y = pad.top + cH * (1 - t);
      ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(pad.left + cW, y); ctx.stroke();
      ctx.fillStyle = '#9ca3af';
      ctx.font      = '10px system-ui';
      ctx.textAlign = 'right';
      ctx.fillText(Math.round(max * t), pad.left - 5, y + 4);
    });
  
    // Bars
    const barW = Math.max(6, cW / values.length - 4);
    values.forEach((v, i) => {
      const x   = pad.left + i * (cW / values.length) + (cW / values.length - barW) / 2;
      const bH  = (v / max) * cH;
      const y   = pad.top + cH - bH;
      ctx.fillStyle = color;
  
      ctx.beginPath();
      ctx.roundRect(x, y, barW, bH, [3, 3, 0, 0]);
      ctx.fill();
  
      // Label
      ctx.fillStyle = '#6b7280';
      ctx.font      = '9px system-ui';
      ctx.textAlign = 'center';
  
      const lbl = labels[i] || '';
      ctx.fillText(lbl.length > 6 ? lbl.slice(0, 5) + '…' : lbl, x + barW / 2, H - pad.bottom + 14);
    });
  }
  
  function drawLineChart(canvasId, labels, values, color = '#3b82f6') {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width  = canvas.offsetWidth;
    const H = canvas.height = 160;
    ctx.clearRect(0, 0, W, H);
  
    const pad = { top: 14, right: 14, bottom: 30, left: 38 };
    const cW  = W - pad.left - pad.right;
    const cH  = H - pad.top  - pad.bottom;
    const max = Math.max(...values, 1);
    const min = Math.min(...values, 0);
    const range = max - min || 1;
  
    const toX = i => pad.left + (i / (values.length - 1 || 1)) * cW;
    const toY = v => pad.top + cH - ((v - min) / range) * cH;
  
    // Grid
    ctx.strokeStyle = '#f3f4f6';
    ctx.lineWidth   = 1;
    [0, 0.5, 1].forEach(t => {
      const y = pad.top + cH * (1 - t);
      ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(pad.left + cW, y); ctx.stroke();
      ctx.fillStyle = '#9ca3af'; ctx.font = '10px system-ui'; ctx.textAlign = 'right';
      ctx.fillText(Math.round(min + range * t), pad.left - 4, y + 4);
    });
    if (values.length < 2) return;
  
    // Filled area
    ctx.beginPath();
    ctx.moveTo(toX(0), toY(values[0]));
    values.forEach((v, i) => { if (i > 0) ctx.lineTo(toX(i), toY(v)); });
    ctx.lineTo(toX(values.length - 1), pad.top + cH);
    ctx.lineTo(toX(0), pad.top + cH);
    ctx.closePath();
  
    ctx.fillStyle = color + '22';
    ctx.fill();
  
    // Line
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth   = 2;
  
    ctx.moveTo(toX(0), toY(values[0]));
    values.forEach((v, i) => { if (i > 0) ctx.lineTo(toX(i), toY(v)); });
    ctx.stroke();
  
    // Points
    values.forEach((v, i) => {
      ctx.beginPath();
      ctx.arc(toX(i), toY(v), 3.5, 0, Math.PI * 2);
      ctx.fillStyle = color; ctx.fill();
      ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.stroke();
    });
  
    // X labels
    values.forEach((v, i) => {
      if (i % Math.max(1, Math.floor(values.length / 6)) === 0) {
        ctx.fillStyle = '#6b7280'; ctx.font = '9px system-ui'; ctx.textAlign = 'center';
        const lbl = labels[i] || '';
        ctx.fillText(lbl.length > 5 ? lbl.slice(0, 4) + '…' : lbl, toX(i), H - pad.bottom + 14);
      }
    });
  }