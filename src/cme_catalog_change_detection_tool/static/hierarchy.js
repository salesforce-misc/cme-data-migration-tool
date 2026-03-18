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

const FILTER_HIDDEN_ROW_CLASS = 'filter-highlight-only-hidden';

function rowHasHighlightCell(tr) {
  return tr.querySelector('td.highlight-cell') != null;
}

function isSectionHeaderRow(tr) {
  return tr.classList.contains('section-header');
}

/**
 * Highlighted only: show full <tr> for rows with .highlight-cell; always keep section-header rows.
 * Other data rows are hidden.
 */
function applyHighlightFilter(onlyHighlighted) {
  const tbody = document.querySelector('tbody');
  if (!tbody) return;
  tbody.querySelectorAll('td').forEach((td) => {
    td.style.display = '';
  });
  tbody.querySelectorAll('tr').forEach((tr) => {
    if (!onlyHighlighted) {
      tr.classList.remove(FILTER_HIDDEN_ROW_CLASS);
      return;
    }
    if (isSectionHeaderRow(tr) || rowHasHighlightCell(tr)) {
      tr.classList.remove(FILTER_HIDDEN_ROW_CLASS);
    } else {
      tr.classList.add(FILTER_HIDDEN_ROW_CLASS);
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
