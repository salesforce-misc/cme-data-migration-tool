function toggleRow(el) {
  const tr = el.closest('tr');
  const depth = parseInt(tr.dataset.depth || '0', 10);
  const collapsed = tr.classList.toggle('collapsed');
  el.textContent = collapsed ? 'chevron_right' : 'expand_more';
  let next = tr.nextElementSibling;
  if (collapsed) {
    while (next) {
      const nd = parseInt(next.dataset.depth || '0', 10);
      if (nd <= depth) break;
      next.style.display = 'none';
      next = next.nextElementSibling;
    }
  } else {
    let suppressionDepth = null;
    while (next) {
      const nd = parseInt(next.dataset.depth || '0', 10);
      if (nd <= depth) break;
      if (suppressionDepth !== null) {
        if (nd > suppressionDepth) {
          next = next.nextElementSibling;
          continue;
        } else {
          suppressionDepth = null;
        }
      }
      next.style.display = '';
      if (next.classList.contains('collapsed')) {
        suppressionDepth = nd;
      }
      next = next.nextElementSibling;
    }
  }
}

function getDepth(tr) {
  return parseInt(tr.dataset.depth || '0', 10);
}

function isHighlighted(tr) {
  const tds = tr.querySelectorAll('td');
  if (!tds || tds.length < 3) return false;
  return tds[1].classList.contains('highlight-cell') || tds[2].classList.contains('highlight-cell');
}

function applyHighlightFilter(onlyHighlighted) {
  const tbody = document.querySelector('tbody');
  if (!tbody) return;
  const rows = Array.from(tbody.querySelectorAll('tr'));
  if (!onlyHighlighted) {
    rows.forEach(r => r.style.display = '');
    return;
  }
  const depths = rows.map(getDepth);
  const include = new Set();

  // Seed with highlighted rows (ignore section headers)
  rows.forEach((r, idx) => {
    if (!r.classList.contains('section-header') && isHighlighted(r)) {
      include.add(idx);
    }
  });

  // Add ancestors and descendants of highlighted rows
  include.forEach((idx) => {
    const baseDepth = depths[idx];
    // ancestors
    let j = idx - 1;
    let minDepth = baseDepth;
    while (j >= 0) {
      const dj = depths[j];
      if (dj < minDepth) {
        include.add(j);
        minDepth = dj;
      }
      j--;
    }
    // descendants
    let k = idx + 1;
    while (k < rows.length) {
      const dk = depths[k];
      if (dk <= baseDepth) break;
      include.add(k);
      k++;
    }
  });

  // Include section headers that scope any included rows
  rows.forEach((r, idx) => {
    if (r.classList.contains('section-header')) {
      const headerDepth = depths[idx];
      let k = idx + 1;
      let shouldInclude = false;
      while (k < rows.length) {
        const dk = depths[k];
        if (dk <= headerDepth) break;
        if (include.has(k)) { shouldInclude = true; break; }
        k++;
      }
      if (shouldInclude) include.add(idx);
    }
  });

  // Show/hide rows and expand any included collapsed parents
  rows.forEach((r, idx) => {
    r.style.display = include.has(idx) ? '' : 'none';
    if (include.has(idx) && r.classList.contains('collapsed')) {
      r.classList.remove('collapsed');
      const icon = r.querySelector('.toggle-icon');
      if (icon) icon.textContent = 'expand_more';
    }
  });
}

document.addEventListener('DOMContentLoaded', function() {
  const chk = document.getElementById('filter-highlighted');
  if (chk) {
    chk.addEventListener('change', function(e) {
      applyHighlightFilter(!!e.target.checked);
    });
  }
});
