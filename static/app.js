const sampleSubjects = [
  { subject: 'Mathematics', attended: 45, total: 56 },
  { subject: 'Physics', attended: 28, total: 40 },
  { subject: 'Chemistry', attended: 32, total: 38 },
  { subject: 'Data Structures', attended: 50, total: 60 },
];

const state = {
  target: 75,
  subjects: [...sampleSubjects],
};

const chartPalette = {
  safe: '#4ade80',
  warn: '#fbbf24',
  danger: '#f87171',
  blue: '#7aa8ff',
  line: '#9bb8ff',
};

function bunkCalc(total, attended, target) {
  if (total === 0) return null;

  const pct = (attended / total) * 100;

  let bunkCount = 0;
  let futureTotal = total + 1;
  while ((attended / futureTotal) * 100 >= target) {
    bunkCount += 1;
    futureTotal += 1;
  }

  let extra = 0;
  let ft = total;
  let fa = attended;
  while ((fa / ft) * 100 < target) {
    ft += 1;
    fa += 1;
    extra += 1;
  }

  const status = pct >= target + 5 ? 'safe' : pct >= target ? 'warn' : 'danger';

  return {
    pct: Number(pct.toFixed(2)),
    safe_skips: bunkCount,
    classes_needed: extra,
    status,
  };
}

function computeSummary(subjects, target) {
  const results = subjects
    .map((subject, index) => ({
      ...subject,
      _index: index,
      ...bunkCalc(subject.total, subject.attended, target),
    }))
    .filter((item) => item && item.pct !== undefined);

  if (!results.length) {
    return {
      summary: {
        overallPct: 0,
        overallStatus: 'danger',
        safeSkips: 0,
        classesNeeded: 0,
        subjectCount: 0,
        safeCount: 0,
        warnCount: 0,
        dangerCount: 0,
      },
      subjects: [],
    };
  }

  const totalAttended = results.reduce((sum, item) => sum + item.attended, 0);
  const totalClasses = results.reduce((sum, item) => sum + item.total, 0);
  const overallPct = totalClasses ? Number(((totalAttended / totalClasses) * 100).toFixed(2)) : 0;
  const overallStatus = overallPct >= target + 5 ? 'safe' : overallPct >= target ? 'warn' : 'danger';

  const safeCount = results.filter((item) => item.status === 'safe').length;
  const warnCount = results.filter((item) => item.status === 'warn').length;
  const dangerCount = results.filter((item) => item.status === 'danger').length;

  return {
    summary: {
      overallPct,
      overallStatus,
      safeSkips: results.reduce((sum, item) => sum + item.safe_skips, 0),
      classesNeeded: results.reduce((sum, item) => sum + item.classes_needed, 0),
      subjectCount: results.length,
      safeCount,
      warnCount,
      dangerCount,
    },
    subjects: results,
  };
}

function updateTargetLabel() {
  const targetValue = document.getElementById('targetValue');
  targetValue.textContent = `${state.target}%`;
}

function renderMetrics(summary) {
  const overallAttendance = document.getElementById('overallAttendance');
  const overallMeta = document.getElementById('overallMeta');
  const safeSkips = document.getElementById('safeSkips');
  const classesNeeded = document.getElementById('classesNeeded');
  const subjectCount = document.getElementById('subjectCount');
  const statusBreakdown = document.getElementById('statusBreakdown');
  const overallBadge = document.getElementById('overallBadge');

  overallAttendance.textContent = `${summary.overallPct}%`;
  overallMeta.textContent = `${state.subjects.reduce((sum, item) => sum + item.attended, 0)} of ${state.subjects.reduce((sum, item) => sum + item.total, 0)} classes`;
  safeSkips.textContent = summary.safeSkips;
  classesNeeded.textContent = summary.classesNeeded;
  subjectCount.textContent = summary.subjectCount;
  statusBreakdown.textContent = `${summary.safeCount} safe · ${summary.warnCount} borderline`;

  const badgeMap = {
    safe: ['Safe', 'rgba(74, 222, 128, 0.12)', 'var(--green)'],
    warn: ['Borderline', 'rgba(251, 191, 36, 0.12)', 'var(--yellow)'],
    danger: ['Shortage', 'rgba(248, 113, 113, 0.12)', 'var(--red)'],
  };

  const [label, bg, color] = badgeMap[summary.overallStatus] || badgeMap.danger;
  overallBadge.textContent = label;
  overallBadge.style.background = bg;
  overallBadge.style.color = color;
  overallBadge.style.borderColor = color.replace('var(', '').replace(')', '') === 'var(--green)' ? 'rgba(74, 222, 128, 0.3)' : 'rgba(248, 113, 113, 0.3)';
}

function renderSubjectCards(results) {
  const subjectList = document.getElementById('subjectList');
  subjectList.innerHTML = '';

  results.forEach((item) => {
    const card = document.createElement('article');
    card.className = 'subject-item';

    const percentColor = item.status === 'safe' ? chartPalette.safe : item.status === 'warn' ? chartPalette.warn : chartPalette.danger;
    const progressWidth = Math.min(Math.max(item.pct, 0), 100);
    const message = item.safe_skips > 0
      ? `You can skip <strong>${item.safe_skips}</strong> more class${item.safe_skips !== 1 ? 'es' : ''} safely.`
      : `Attend <strong>${item.classes_needed}</strong> consecutive class${item.classes_needed !== 1 ? 'es' : ''} to recover.`;

    card.innerHTML = `
      <div class="subject-top">
        <div class="subject-name">${item.subject}</div>
        <div class="subject-actions">
          <span class="status-badge status-${item.status}">${item.status === 'safe' ? 'Safe' : item.status === 'warn' ? 'Borderline' : 'Shortage'}</span>
          <button class="remove-btn" data-index="${item._index}" aria-label="Remove ${item.subject}">Remove</button>
        </div>
      </div>
      <div class="subject-percent" style="color:${percentColor}">${item.pct}%</div>
      <div class="progress-bar"><span style="width:${progressWidth}%; background: linear-gradient(90deg, ${percentColor}, ${chartPalette.blue});"></span></div>
      <div class="subject-meta">${item.attended} attended / ${item.total} total · target ${state.target}%</div>
      <div class="subject-message">${message}</div>
    `;

    subjectList.appendChild(card);
  });

  subjectList.querySelectorAll('.remove-btn').forEach((button) => {
    button.addEventListener('click', (event) => {
      const index = Number(event.currentTarget.dataset.index);
      if (Number.isNaN(index)) return;
      state.subjects.splice(index, 1);
      renderApp();
    });
  });
}

function buildCharts(summary, results) {
  const attendanceCtx = document.getElementById('attendanceChart');
  const statusCtx = document.getElementById('statusChart');
  const skipCtx = document.getElementById('skipChart');

  if (window.__attendanceChart) window.__attendanceChart.destroy();
  if (window.__statusChart) window.__statusChart.destroy();
  if (window.__skipChart) window.__skipChart.destroy();

  window.__attendanceChart = new Chart(attendanceCtx, {
    type: 'bar',
    data: {
      labels: results.map((item) => item.subject),
      datasets: [{
        data: results.map((item) => item.pct),
        backgroundColor: results.map((item) => item.status === 'safe' ? chartPalette.safe : item.status === 'warn' ? chartPalette.warn : chartPalette.danger),
        borderRadius: 12,
        borderSkipped: false,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.parsed.y}%`,
          },
        },
      },
      scales: {
        y: {
          suggestedMin: 0,
          suggestedMax: 110,
          grid: { color: 'rgba(148, 163, 184, 0.12)' },
          ticks: { color: '#93a9c8' },
        },
        x: {
          grid: { display: false },
          ticks: { color: '#93a9c8' },
        },
      },
    },
  });

  window.__statusChart = new Chart(statusCtx, {
    type: 'doughnut',
    data: {
      labels: ['Safe', 'Borderline', 'Shortage'],
      datasets: [{
        data: [summary.safeCount, summary.warnCount, summary.dangerCount],
        backgroundColor: [chartPalette.safe, chartPalette.warn, chartPalette.danger],
        borderWidth: 0,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '58%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#dfeaff', boxWidth: 12 },
        },
      },
    },
  });

  window.__skipChart = new Chart(skipCtx, {
    type: 'bar',
    data: {
      labels: results.map((item) => item.subject),
      datasets: [
        {
          label: 'Safe skips',
          data: results.map((item) => item.safe_skips),
          backgroundColor: chartPalette.safe,
          borderRadius: 10,
        },
        {
          label: 'Classes needed',
          data: results.map((item) => item.classes_needed),
          backgroundColor: chartPalette.danger,
          borderRadius: 10,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#dfeaff' } },
      },
      scales: {
        y: {
          grid: { color: 'rgba(148, 163, 184, 0.12)' },
          ticks: { color: '#93a9c8' },
        },
        x: {
          grid: { display: false },
          ticks: { color: '#93a9c8' },
        },
      },
    },
  });
}

function renderApp() {
  const { summary, subjects: results } = computeSummary(state.subjects, state.target);
  renderMetrics(summary);
  renderSubjectCards(results);
  buildCharts(summary, results);
}

function addSubject() {
  const name = document.getElementById('subjectName').value.trim();
  const attended = Number(document.getElementById('attendedValue').value || 0);
  const total = Number(document.getElementById('totalValue').value || 0);

  if (!name || total <= 0) return;

  state.subjects.push({ subject: name, attended, total });
  document.getElementById('subjectName').value = '';
  renderApp();
}

function parseCsv(text) {
  const rows = text.trim().split(/\r?\n/).filter(Boolean);
  if (!rows.length) return [];

  const headers = rows[0].split(',').map((item) => item.trim().toLowerCase());
  const subjectIndex = headers.findIndex((header) => header.includes('subject'));
  const attendedIndex = headers.findIndex((header) => header.includes('att'));
  const totalIndex = headers.findIndex((header) => header.includes('tot'));

  if (subjectIndex === -1 || attendedIndex === -1 || totalIndex === -1) {
    return [];
  }

  return rows.slice(1).map((row) => {
    const values = row.split(',');
    return {
      subject: values[subjectIndex]?.trim() || '',
      attended: Number(values[attendedIndex] || 0),
      total: Number(values[totalIndex] || 0),
    };
  }).filter((item) => item.subject && item.total > 0);
}

function handleCsvUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = () => {
    const rows = parseCsv(reader.result);
    if (!rows.length) {
      alert('CSV should include Subject, Attended, and Total columns.');
      return;
    }

    state.subjects = rows;
    renderApp();
  };
  reader.readAsText(file);
}

function bindEvents() {
  document.getElementById('targetSlider').addEventListener('input', (event) => {
    state.target = Number(event.target.value);
    updateTargetLabel();
    renderApp();
  });

  document.getElementById('addSubjectBtn').addEventListener('click', addSubject);
  document.getElementById('csvUpload').addEventListener('change', handleCsvUpload);
  document.getElementById('sampleDataBtn').addEventListener('click', () => {
    state.subjects = [...sampleSubjects];
    renderApp();
  });
}

function init() {
  updateTargetLabel();
  bindEvents();
  renderApp();
}

init();
